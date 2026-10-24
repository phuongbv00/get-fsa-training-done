#!/bin/sh
# Make this skill's CLI available on a machine that has only the skill folder:
# a hosted agent's sandbox (Claude Managed Agents, given the skill as an
# upload), or any machine the skill was copied to without its CLI.
#
# It installs get-fsa-training-done at the version in ../VERSION — payload and
# CLI ship in lockstep — into a virtualenv of its own, so no system or user
# Python is touched, then builds the environment the worker commands run in.
# The first run needs a network (PyPI); every later run finds what the first
# one installed and touches nothing.
#
# Progress goes to stderr. The last line on stdout names the command to call
# the CLI with:  FSA: <command>
set -eu

skill_dir=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
version=$(tr -d ' \r\n' < "$skill_dir/VERSION")
package="get-fsa-training-done==$version"
data_home=${XDG_DATA_HOME:-${HOME:-/tmp}/.local/share}
venv="$data_home/get-fsa-training-done/cli"

say() { printf 'get-fsa-training-done setup: %s\n' "$*" >&2; }

cli=''

# `--version` prints "get-fsa-training-done X.Y.Z"; only this exact version will do.
try_cli() {
	[ -n "$1" ] || return 1
	[ "$("$1" --version 2>/dev/null | awk '{ print $NF }')" = "$version" ] || return 1
	cli=$1
}

find_cli() {
	try_cli "$(command -v get-fsa-training-done 2>/dev/null || true)" && return 0
	try_cli "$venv/bin/get-fsa-training-done"
}

python_312() {
	for name in python3 python3.14 python3.13 python3.12; do
		path=$(command -v "$name" 2>/dev/null) || continue
		if "$path" -c 'import sys; sys.exit(sys.version_info < (3, 12))' 2>/dev/null; then
			printf '%s\n' "$path"
			return 0
		fi
	done
	return 1
}

install_cli() {
	rm -rf "$venv"
	mkdir -p "$(dirname -- "$venv")"
	if command -v uv >/dev/null 2>&1; then
		say "installing $package into $venv with uv"
		uv venv --quiet --python '>=3.12' "$venv" >&2 &&
			uv pip install --quiet --python "$venv/bin/python" "$package" >&2 && return 0
	elif python=$(python_312); then
		say "installing $package into $venv"
		"$python" -m venv "$venv" >&2 &&
			"$venv/bin/python" -m pip install --quiet --disable-pip-version-check "$package" >&2 &&
			return 0
	fi
	say "could not install $package: it needs uv, or Python 3.12+ with venv and pip, and PyPI"
	return 1
}

if ! find_cli; then
	install_cli
	if ! find_cli; then
		say "installed $package but its command does not report $version; see the output above"
		exit 1
	fi
fi

# Build the workers' environment now, while the network is known to work.
"$cli" env ensure >&2

printf 'FSA: %s\n' "$cli"
