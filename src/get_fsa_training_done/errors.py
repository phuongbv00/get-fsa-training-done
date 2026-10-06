"""Exception types that map onto CLI exit codes."""

from __future__ import annotations


class FsaTrainerSkillsError(Exception):
    """Base class. `cli.run` prints `ERROR: <msg>` and exits with `exit_code`."""

    exit_code = 1

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class UsageError(FsaTrainerSkillsError):
    """Bad flags or a missing required argument."""

    exit_code = 2


class NotInstalledError(FsaTrainerSkillsError):
    """No managed install found where one was expected."""

    exit_code = 3


class UnmanagedDestinationError(FsaTrainerSkillsError):
    """Destination exists but carries no receipt (or someone else's)."""

    exit_code = 4


class VerificationError(FsaTrainerSkillsError):
    """A `verify` run found structural problems."""

    exit_code = 1


class EnvironmentError_(FsaTrainerSkillsError):
    """The managed venv could not be created or provisioned."""

    exit_code = 5


class MissingToolError(FsaTrainerSkillsError):
    """A required external binary (Chrome, an archive extractor) is absent."""

    exit_code = 6
