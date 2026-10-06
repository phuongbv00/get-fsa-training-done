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
  the run then reads offline and read-only. What could make that resolver run
  the project's code is refused before it starts: a Python requirement that is
  not a plain wheel from an index, and Maven build extensions.
- **The source is mounted read-only** and copied into a tmpfs work directory,
  and the container's own filesystem is read-only, so nothing the run does
  reaches the host and every byte it can write is in a size-bounded tmpfs.
- **Bounded**: CPU, memory, process count, disk and wall-clock time are capped,
  and the container and its volume are removed afterwards, however the run
  ends.
- **The init files and the command are arguments**, never text spliced into
  the shell script, so no file name can turn into a command.

Docker is optional, like the `.rar` extractor: nothing else in the package
needs it, and `sandbox check` says whether this machine has it.
"""

from __future__ import annotations

import re
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
    #: How one `--init` file is applied; the file is in `$f`, never spliced
    #: into the text. Empty means the profile takes no init files.
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
    #: Writable tmpfs mounts beyond `/work` and `/tmp`, as `path:size`; the
    #: rest of the container's filesystem is read-only.
    writable: tuple[str, ...] = ()


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
        init='psql -v ON_ERROR_STOP=1 -q -f "$f"',
        env={
            "POSTGRES_HOST_AUTH_METHOD": "trust",
            "PGUSER": "postgres",
            "PGDATABASE": "postgres",
            "PGHOST": "/var/run/postgresql",
        },
        capabilities=("CHOWN", "DAC_OVERRIDE", "FOWNER", "SETGID", "SETUID"),
        writable=("/var/lib/postgresql/data:1g", "/var/run/postgresql:16m"),
    ),
    "maven": Profile(
        image="maven:3.9-eclipse-temurin-21",
        # `go-offline` misses the test provider surefire picks at run time, so
        # read surefire's version from the effective POM and fetch its JUnit
        # Platform provider explicitly. Only resolver goals run here; the build
        # lifecycle, and with it any plugin the project binds, does not. The
        # project's `.mvn/` (extensions, JVM and Maven options) is removed
        # first, and build extensions are refused before the container starts.
        prefetch=(
            "cd /work && rm -rf .mvn && M='mvn -B -q -Dmaven.repo.local=/deps/m2' && "
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
        # Wheels only: building an sdist runs its setup code. Local, editable
        # and URL requirements are refused before the container starts.
        prefetch=(
            "cd /work && P='pip install -q --no-compile --only-binary=:all: --target /deps/py' && "
            "if [ -f requirements.txt ]; then $P -r requirements.txt; fi && $P pytest"
        ),
        env={
            "PYTHONPATH": "/deps/py",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PIP_NO_CACHE_DIR": "1",
        },
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
    #: Size of the work directory, the one place the run writes the project.
    work: str = "1g"
    #: Size of `/tmp`, also the run's `HOME`.
    tmp: str = "512m"


#: A requirement line the prefetch may resolve: a package name, extras, and
#: version markers. Anything else — `-e .`, `./pkg`, a URL, `name @ file:...`,
#: an option line — could make pip run code from the project or the network.
_PLAIN_REQUIREMENT = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9._,\s-]+\])?"
    r"\s*([<>=!~]=?\s*[A-Za-z0-9.*+!_-]+\s*(,\s*[<>=!~]=?\s*[A-Za-z0-9.*+!_-]+\s*)*)?"
    r"\s*(;[^@]*)?$"
)
_MAVEN_EXTENSIONS = re.compile(r"<extensions?>", re.IGNORECASE)


def refuse_unsafe_prefetch(profile_name: str, mount: Path) -> None:
    """Stop before a prefetch that could run the project's own code online.

    The prefetch is the one step with a network, so it may run only a resolver
    over declarations. A Python requirement that points at the project, a URL
    or an option, and a Maven build extension (loaded into Maven itself while
    the model is read), are each a way to run arbitrary code at that point.
    """
    if profile_name == "python":
        requirements = mount / "requirements.txt"
        if not requirements.is_file():
            return
        refused = [
            line
            for line in (
                raw.split("#", 1)[0].strip()
                for raw in requirements.read_text(encoding="utf-8").splitlines()
            )
            if line and not _PLAIN_REQUIREMENT.match(line)
        ]
        if refused:
            raise UsageError(
                "requirements.txt has lines the prefetch will not resolve: " + "; ".join(refused),
                hint="only plain index requirements (name, extras, versions) are fetched; "
                "install anything else inside the run, where there is no network",
            )
    elif profile_name == "maven":
        poms = [mount / "pom.xml", *mount.glob("*/pom.xml")]
        flagged = [
            str(pom.relative_to(mount))
            for pom in poms
            if pom.is_file() and _MAVEN_EXTENSIONS.search(pom.read_text(encoding="utf-8"))
        ]
        if flagged:
            raise UsageError(
                "the project declares Maven build extensions, which run inside Maven "
                "while the network is on: " + ", ".join(flagged),
                hint="remove the <extensions> from a copy of the project, or run without "
                "--prefetch against dependencies fetched from a trusted project",
            )


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


def script(chosen: Profile) -> str:
    """The shell the container runs.

    Its arguments are the init-file count, the init files, then the command,
    so neither a file name nor the command is ever parsed as shell text.
    """
    lines = ["set -e", f"cp -a {SOURCE}/. {WORK}/", f"cd {WORK}"]
    if chosen.setup:
        lines.append(chosen.setup)
    lines.append("n=$1; shift")
    if chosen.init:
        lines.append(f'while [ "$n" -gt 0 ]; do f=$1; shift; {chosen.init}; n=$((n - 1)); done')
    lines.append('exec "$@"')
    return "\n".join(lines)


def _mount_field(key: str, value: str) -> str:
    """One `--mount` field, quoted CSV-style when the value needs it."""
    field_text = f"{key}={value}"
    if any(ch in value for ch in ',"'):
        return '"' + field_text.replace('"', '""') + '"'
    return field_text


def _base(
    name: str,
    volume: str,
    mount: Path,
    chosen: Profile,
    limits: Limits,
    env: dict[str, str],
    *,
    deps_readonly: bool,
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
        "--read-only",
        "--mount",
        f"type=bind,{_mount_field('src', str(mount.resolve()))},dst={SOURCE},readonly",
        "--mount",
        f"type=volume,src={volume},dst={DEPS}" + (",readonly" if deps_readonly else ""),
        "--tmpfs",
        f"{WORK}:exec,size={limits.work}",
        "--tmpfs",
        f"/tmp:exec,size={limits.tmp}",
    ]
    for writable in chosen.writable:
        path, size = writable.rsplit(":", 1)
        argv += ["--tmpfs", f"{path}:size={size}"]
    for capability in chosen.capabilities:
        argv += ["--cap-add", capability]
    for key, value in {"HOME": "/tmp", **env}.items():
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
    argv = _base(name, volume, mount, chosen, limits or Limits(), env, deps_readonly=True)
    argv += ["--network", "none", "--entrypoint", "sh", chosen.image]
    init = init or []
    argv += ["-c", script(chosen), "sandbox", str(len(init)), *init, *command]
    return argv


def prefetch_argv(
    profile_name: str, mount: Path, *, name: str, volume: str, limits: Limits | None = None
) -> list[str] | None:
    """The `docker run` that fills `/deps`, or None when the profile needs nothing."""
    chosen = profile(profile_name)
    if not chosen.prefetch:
        return None
    argv = _base(name, volume, mount, chosen, limits or Limits(), chosen.env, deps_readonly=False)
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
    if prefetch:
        refuse_unsafe_prefetch(profile_name, mount)
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
        # However the run ended — finished, timed out, interrupted — remove the
        # containers first: a volume still attached to one cannot be removed.
        for container in (name, f"{name}-prefetch"):
            subprocess.run(["docker", "rm", "-f", container], capture_output=True, timeout=60)
        subprocess.run(["docker", "volume", "rm", "-f", volume], capture_output=True, timeout=60)


def _execute(argv: list[str], name: str, timeout: int) -> int:
    try:
        return subprocess.run(argv, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        print(f"sandbox: killed after {timeout}s")
        return 124
