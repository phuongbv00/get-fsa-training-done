"""Single source of truth for the package version and identity.

`pyproject.toml` reads the version via `[tool.hatch.version]`;
`scripts/sync_version.py` propagates it to `package.json` and every skill
payload's `VERSION` file.
"""

__version__ = "0.2.0"

PACKAGE_NAME = "get-fsa-training-done"
CLI_NAME = "get-fsa-training-done"
