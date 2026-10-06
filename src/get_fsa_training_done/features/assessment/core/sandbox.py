"""Run something testable — a seed script, a JUnit suite, a pytest run — in a
disposable Docker container.

Two callers need this. Designing an exam has to prove its supplied files work
before a candidate sees them: a `seed.sql` that fails to load, or a mock API
that answers wrongly, is a defect in the exam. Grading sometimes needs the same
proof about a submission. Either way the code being run is not ours, so the
container is the safety boundary, and its rules live here rather than in a
workflow the model is trusted to follow:

- **No network** while the code runs. Dependencies are fetched first, in a
  separate step that runs only the build tool's own resolver, into a volume
  the run then reads offline.
- **The source is mounted read-only** and copied into a tmpfs work directory,
  so nothing the run does reaches the host.
- **Bounded**: CPU, memory, process count and wall-clock time are capped, and
  the container and its volume are removed afterwards.

Docker is optional, like the `.rar` extractor: nothing else in the package
needs it, and `sandbox check` says whether this machine has it.
"""

from __future__ import annotations

import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from get_fsa_training_done.errors import MissingToolError, UsageError

SOURCE = "/src"
WORK = "/work"
DEPS = "/deps"


@dataclass(frozen=True)
class Profile:
    """One toolchain image, pinned, and what it needs around the command."""

    image: str
    #: Shell run inside the container before `--init` files and the command.
    setup: str = ""
    #: How one `--init` file is applied, with `{file}` replaced; empty means
    #: the profile takes no init files.
    init: str = ""
    #: Shell that fetches dependencies into `/deps`, with the network on. It
    #: must run only the build tool's resolver, never the project's own code.
    prefetch: str = ""
    env: dict[str, str] = field(default_factory=dict)
    #: Set only for the run itself, never for the prefetch: what makes the
    #: build tool stay offline and read the prefetched dependencies.
    run_env: dict[str, str] = field(default_factory=dict)
    #: Capabilities added back after `--cap-drop ALL`. The postgres entrypoint
    #: has to chown its data directory and drop to the postgres user.
    capabilities: tuple[str, ...] = ()


PROFILES: dict[str, Profile] = {
    "postgres": Profile(
        image="postgres:16-alpine",
        # The entrypoint runs initdb behind a temporary server on the same
        # socket, then stops it and starts the real one. Waiting for a
        # connection alone can catch the temporary server, and the init files
        # then die mid-run when it stops — so wait for the entrypoint to say
        # initialisation is over before waiting for the real server.
        setup=(
            "docker-entrypoint.sh postgres >/tmp/postgres.log 2>&1 &\n"
            "for _ in $(seq 1 240); do "
            "grep -q 'init process complete' /tmp/postgres.log && break; sleep 0.5; done\n"
            "for _ in $(seq 1 240); do psql -q -c 'select 1' >/dev/null 2>&1 && break; "
            "sleep 0.5; done\n"
            "psql -q -c 'select 1' >/dev/null 2>&1 || { cat /tmp/postgres.log; exit 1; }"
        ),
        init='psql -v ON_ERROR_STOP=1 -q -f "{file}"',
        env={
            "POSTGRES_HOST_AUTH_METHOD": "trust",
            "PGUSER": "postgres",
            "PGDATABASE": "postgres",
            "PGHOST": "/var/run/postgresql",
        },
        capabilities=("CHOWN", "DAC_OVERRIDE", "FOWNER", "SETGID", "SETUID"),
    ),
    "maven": Profile(
        image="maven:3.9-eclipse-temurin-21",
        # `go-offline` misses the test provider surefire picks at run time, so
        # read surefire's version from the effective POM and fetch its JUnit
        # Platform provider explicitly. Only resolver goals run here; the build
        # lifecycle, and with it any plugin the project binds, does not.
        prefetch=(
            "cd /work && M='mvn -B -q -Dmaven.repo.local=/deps/m2' && "
            "$M dependency:go-offline dependency:resolve-plugins && "
            "$M help:effective-pom -Doutput=/tmp/effective.xml && "
            "V=$(grep -A1 '<artifactId>maven-surefire-plugin</artifactId>' /tmp/effective.xml "
            "| sed -n 's:.*<version>\\(.*\\)</version>.*:\\1:p' | head -1) && "
            'if [ -n "$V" ]; then $M dependency:get '
            "-Dartifact=org.apache.maven.surefire:surefire-junit-platform:$V; fi && "
            # Surefire also adds a launcher matching the project's JUnit Platform.
            "P=$($M dependency:list -DoutputFile=/tmp/deps.txt >/dev/null; "
            "sed -n 's/.*org.junit.platform:junit-platform-engine:jar:\\([^:]*\\):.*/\\1/p' "
            "/tmp/deps.txt | head -1) && "
            'if [ -n "$P" ]; then $M dependency:get '
            "-Dartifact=org.junit.platform:junit-platform-launcher:$P; fi"
        ),
        run_env={"MAVEN_ARGS": "-o -B -Dmaven.repo.local=/deps/m2"},
    ),
    "python": Profile(
        image="python:3.12-slim",
        prefetch=(
            "cd /work && if [ -f requirements.txt ]; then "
            "pip install -q --no-compile --target /deps/py -r requirements.txt; fi && "
            "pip install -q --no-compile --target /deps/py pytest"
        ),
        env={"PYTHONPATH": "/deps/py", "PYTHONDONTWRITEBYTECODE": "1"},
        setup='export PATH="/deps/py/bin:$PATH"',
    ),
    "node": Profile(
        image="node:20-alpine",
        prefetch=(
            "cd /work && mkdir -p /deps/node && cp package*.json /deps/node/ && "
            "cd /deps/node && (npm ci --ignore-scripts --no-audit --no-fund || "
            "npm install --ignore-scripts --no-audit --no-fund)"
        ),
        setup='[ -d /deps/node/node_modules ] && ln -s /deps/node/node_modules "$PWD/node_modules"',
    ),
}


@dataclass(frozen=True)
class Limits:
    cpus: str = "2"
    memory: str = "2g"
    pids: int = 512
    timeout: int = 600


def profile(name: str) -> Profile:
    try:
        return PROFILES[name]
    except KeyError:
        raise UsageError(f"unknown profile {name!r}; choose from {', '.join(PROFILES)}") from None


def init_targets(mount: Path, files: list[str]) -> list[str]:
    """Each `--init` file as the container sees it, refusing one outside the mount.

    The container sees only the mounted directory, so a file elsewhere would
    fail inside it with an error that names a path the user never typed.
    """
    targets: list[str] = []
    for raw in files:
        path = (mount / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        try:
            relative = path.relative_to(mount.resolve())
        except ValueError:
            raise UsageError(f"--init {raw} is outside --mount {mount}") from None
        if not path.is_file():
            raise UsageError(f"--init {raw} does not exist")
        targets.append(str(PurePosixPath(WORK, *relative.parts)))
    return targets


def script(chosen: Profile, init: list[str]) -> str:
    """The shell the container runs; the command arrives as its arguments."""
    lines = ["set -e", f"cp -a {SOURCE}/. {WORK}/", f"cd {WORK}"]
    if chosen.setup:
        lines.append(chosen.setup)
    for target in init:
        lines.append(chosen.init.format(file=target))
    lines.append('exec "$@"')
    return "\n".join(lines)


def _base(
    name: str, volume: str, mount: Path, chosen: Profile, limits: Limits, env: dict[str, str]
) -> list[str]:
    argv = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--cpus",
        limits.cpus,
        "--memory",
        limits.memory,
        "--pids-limit",
        str(limits.pids),
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--mount",
        f"type=bind,src={mount.resolve()},dst={SOURCE},readonly",
        "--mount",
        f"type=volume,src={volume},dst={DEPS}",
        "--tmpfs",
        f"{WORK}:exec,size=1g",
    ]
    for capability in chosen.capabilities:
        argv += ["--cap-add", capability]
    for key, value in env.items():
        argv += ["--env", f"{key}={value}"]
    return argv


def run_argv(
    profile_name: str,
    mount: Path,
    command: list[str],
    *,
    init: list[str] | None = None,
    name: str,
    volume: str,
    limits: Limits | None = None,
) -> list[str]:
    """The `docker run` that executes the command, with the network off."""
    chosen = profile(profile_name)
    if not command:
        raise UsageError("give the command to run after --, e.g. -- mvn test")
    if init and not chosen.init:
        raise UsageError(f"the {profile_name} profile takes no --init files")
    env = {**chosen.env, **chosen.run_env}
    argv = _base(name, volume, mount, chosen, limits or Limits(), env)
    argv += ["--network", "none", "--entrypoint", "sh", chosen.image]
    argv += ["-c", script(chosen, init or []), "sandbox", *command]
    return argv


def prefetch_argv(
    profile_name: str, mount: Path, *, name: str, volume: str, limits: Limits | None = None
) -> list[str] | None:
    """The `docker run` that fills `/deps`, or None when the profile needs nothing."""
    chosen = profile(profile_name)
    if not chosen.prefetch:
        return None
    argv = _base(name, volume, mount, chosen, limits or Limits(), chosen.env)
    argv += ["--entrypoint", "sh", chosen.image]
    argv += ["-c", f"set -e\ncp -a {SOURCE}/. {WORK}/\n{chosen.prefetch}"]
    return argv


def docker_path() -> str:
    """Where `docker` is, or an empty string; `doctor` reports it as optional."""
    return shutil.which("docker") or ""


def docker() -> str:
    path = docker_path()
    if not path:
        raise MissingToolError(
            "docker is not installed or not on PATH",
            hint="install Docker to run testable artifacts in a sandbox; nothing else needs it",
        )
    return path


def check() -> str:
    """The daemon's version, proving the client can reach it."""
    docker()
    done = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if done.returncode != 0:
        raise MissingToolError(
            "docker is installed but its daemon is not reachable",
            hint=(done.stderr.strip() or "start Docker and retry"),
        )
    return done.stdout.strip()


def run(
    profile_name: str,
    mount: Path,
    command: list[str],
    *,
    init: list[str] | None = None,
    prefetch: bool = False,
    limits: Limits | None = None,
) -> int:
    """Run the command in a fresh container and return its exit code."""
    docker()
    limits = limits or Limits()
    if not mount.is_dir():
        raise UsageError(f"--mount {mount} is not a directory")
    token = uuid.uuid4().hex[:12]
    name, volume = f"gftd-sandbox-{token}", f"gftd-sandbox-{token}"
    targets = init_targets(mount, init or [])
    try:
        if prefetch:
            fetch = prefetch_argv(
                profile_name, mount, name=f"{name}-prefetch", volume=volume, limits=limits
            )
            if fetch is not None:
                code = _execute(fetch, f"{name}-prefetch", limits.timeout)
                if code != 0:
                    print(f"sandbox: fetching dependencies failed (exit {code})")
                    return code
        argv = run_argv(
            profile_name, mount, command, init=targets, name=name, volume=volume, limits=limits
        )
        return _execute(argv, name, limits.timeout)
    finally:
        subprocess.run(["docker", "volume", "rm", "-f", volume], capture_output=True, timeout=60)


def _execute(argv: list[str], name: str, timeout: int) -> int:
    try:
        return subprocess.run(argv, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", name], capture_output=True, timeout=60)
        print(f"sandbox: killed after {timeout}s")
        return 124
