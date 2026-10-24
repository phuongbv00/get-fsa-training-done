#!/bin/sh
# Make this skill's CLI available on a machine that has only the skill folder:
# a hosted agent's sandbox (Claude Managed Agents, given the skill as an
# upload), or any machine the skill was copied to without its CLI.
#
# It installs get-fsa-training-done at the version in ../VERSION — payload and
# CLI ship in lockstep — unless that version is already reachable, then builds
# the environment the worker commands run in. The first run needs a network;
# every later run finds what the first one installed and touches nothing.
#
# Progress goes to stderr. The last line on stdout names the command to call
# the CLI with:  FSA: <command>
set -eu

skill_dir=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
version=$(tr -d ' \r\n' < "$skill_dir/VERSION")
package="get-fsa-training-done==$version"

say() { printf 'get-fsa-training-done setup: %s\n' "$*" >&2; }

# The CLI, as a command name or path (cli_bin), or as `<python> -m` (cli_py).
cli_bin=''
cli_py=''

cli() {
	if [ -n "$cli_bin" ]; then "$cli_bin" "$@"; else "$cli_py" -m get_fsa_training_done "$@"; fi
}

# `--version` prints "get-fsa-training-done X.Y.Z"; only this exact version will do.
at_version() {
	[ "$("$@" --version 2>/dev/null | awk '{ print $NF }')" = "$version" ]
}

new_enough() {
	"$1" -c 'import sys; sys.exit(sys.version_info < (3, 12))' 2>/dev/null
}

pythons() {
	for name in python3 python3.14 python3.13 python3.12 python; do
		path=$(command -v "$name" 2>/dev/null) || continue
		new_enough "$path" && printf '%s\n' "$path"
	done
	return 0
}

find_cli() {
	bins="get-fsa-training-done $HOME/.local/bin/get-fsa-training-done"
	if command -v uv >/dev/null 2>&1; then
		bins="$bins $(uv tool dir --bin 2>/dev/null || true)/get-fsa-training-done"
	fi
	for candidate in $bins; do
		if at_version "$candidate"; then
			cli_bin=$candidate
			return 0
		fi
	done
	for python in $(pythons); do
		if at_version "$python" -m get_fsa_training_done; then
			cli_py=$python
			return 0
		fi
	done
	return 1
}

install_cli() {
	python=$(pythons | head -n 1)
	if command -v uv >/dev/null 2>&1; then
		say "installing $package with uv"
		uv tool install --force --quiet "$package" >&2 && return 0
	fi
	if [ -n "$python" ]; then
		say "installing $package into $python"
		"$python" -m pip install --quiet --disable-pip-version-check "$package" >&2 && return 0
		"$python" -m pip install --quiet --disable-pip-version-check --user "$package" >&2 && return 0
	fi
	if command -v pipx >/dev/null 2>&1; then
		say "installing $package with pipx"
		if [ -n "$python" ]; then
			pipx install --force --python "$python" "$package" >&2 && return 0
		else
			pipx install --force "$package" >&2 && return 0
		fi
	fi
	say "could not install $package: it needs Python 3.12+ with pip, uv or pipx, and a network"
	return 1
}

if ! find_cli; then
	install_cli
	if ! find_cli; then
		say "installed $package but cannot find its command; see the output above"
		exit 1
	fi
fi

# Build the workers' environment now, while the network is known to work.
cli env ensure >&2

if [ -n "$cli_bin" ]; then
	printf 'FSA: %s\n' "$cli_bin"
else
	printf 'FSA: %s -m get_fsa_training_done\n' "$cli_py"
fi
