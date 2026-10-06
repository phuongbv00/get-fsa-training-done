"""Single source of truth for the package version and identity.

`pyproject.toml` reads the version via `[tool.hatch.version]`;
`scripts/sync_version.py` propagates it to the skill payload's `VERSION` file.
"""

__version__ = "1.0.0"

PACKAGE_NAME = "get-fsa-training-done"
CLI_NAME = "get-fsa-training-done"
#: The short name every guide and message uses; both are installed.
SHORT_NAME = "gftd"
