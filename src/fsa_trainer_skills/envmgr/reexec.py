"""Re-execute the current command inside the managed venv.

`os.execve` replaces this process, so stdout, stderr and the exit code pass
straight through with no wrapper in between. The package itself is never
installed *into* the venv — `fsa_trainer_skills` is pure Python, so putting its parent
directory on `PYTHONPATH` is enough, and the venv is left holding only the
third-party dependencies it exists for.

Windows takes the subprocess branch: `os.execv` there returns control to the
shell before the child finishes, which breaks exit-code propagation.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import bootstrap, stamp

IN_VENV_ENV = "FSA_TRAINER_SKILLS_IN_VENV"
NO_VENV_ENV = "FSA_TRAINER_SKILLS_NO_VENV"
OFFLINE_ENV = "FSA_TRAINER_SKILLS_OFFLINE"


def disabled() -> bool:
    return os.environ.get(NO_VENV_ENV, "").strip().lower() in {"1", "true", "yes"}


def already_inside() -> bool:
    return os.environ.get(IN_VENV_ENV) == "1"


def enter(*groups: str, argv: list[str] | None = None, offline: bool = False) -> None:
    """Re-exec into the venv for `groups`. Returns normally if already there."""
    if disabled() or already_inside():
        return

    offline = offline or os.environ.get(OFFLINE_ENV, "").strip().lower() in {"1", "true", "yes"}
    venv = bootstrap.ensure(*groups, offline=offline)
    target = stamp.venv_python(venv)

    try:
        if Path(sys.executable).resolve() == target.resolve():
            return
    except OSError:
        pass

    package_parent = str(Path(__file__).resolve().parents[2])
    existing = os.environ.get("PYTHONPATH", "")
    pythonpath = os.pathsep.join(p for p in (package_parent, existing) if p)

    env = dict(os.environ)
    env[IN_VENV_ENV] = "1"
    env["PYTHONPATH"] = pythonpath

    args = argv if argv is not None else sys.argv[1:]
    cmd = [str(target), "-m", "fsa_trainer_skills", *args]

    if os.name == "nt":  # pragma: no cover - platform specific
        raise SystemExit(subprocess.run(cmd, env=env).returncode)
    sys.stdout.flush()
    sys.stderr.flush()
    os.execve(str(target), cmd, env)
