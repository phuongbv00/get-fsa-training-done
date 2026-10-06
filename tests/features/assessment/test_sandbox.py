"""The sandbox's safety rules are in the `docker run` it builds, so that is
what these check. One test runs a real container, when Docker is here."""

from __future__ import annotations

import shutil
import subprocess

import pytest

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.assessment.core import sandbox


def build(profile="postgres", tmp_path=None, command=("psql", "-c", "select 1"), **kwargs):
    return sandbox.run_argv(
        profile, tmp_path, list(command), name="gftd-test", volume="gftd-test", **kwargs
    )


def flag_value(argv, flag):
    return [argv[i + 1] for i, item in enumerate(argv) if item == flag]


@pytest.mark.parametrize("profile", list(sandbox.PROFILES))
def test_every_run_is_offline_bounded_and_read_only(profile, tmp_path):
    argv = build(profile, tmp_path, command=["true"])
    assert flag_value(argv, "--network") == ["none"]
    assert "--rm" in argv
    assert flag_value(argv, "--cap-drop") == ["ALL"]
    assert flag_value(argv, "--security-opt") == ["no-new-privileges"]
    assert flag_value(argv, "--memory") and flag_value(argv, "--pids-limit")
    assert "--read-only" in argv
    assert {t.split(":")[0] for t in flag_value(argv, "--tmpfs")} >= {"/work", "/tmp"}
    assert all("size=" in t for t in flag_value(argv, "--tmpfs"))
    mounts = flag_value(argv, "--mount")
    assert f"type=bind,src={tmp_path.resolve()},dst=/src,readonly" in mounts
    assert [m for m in mounts if m.startswith("type=volume")][0].endswith(",readonly")


def test_the_command_is_passed_as_arguments_not_spliced_into_the_shell(tmp_path):
    argv = build(tmp_path=tmp_path, command=["psql", "-c", "select 1; drop table x"])
    assert argv[-5:] == ["sandbox", "0", "psql", "-c", "select 1; drop table x"]


def test_init_files_are_arguments_in_order_before_the_command(tmp_path):
    """A file name is data: `$(...)` in one must never reach the shell as text."""
    names = ["schema.sql", "a$(touch pwned)`id`.sql"]
    for name in names:
        (tmp_path / name).write_text("select 1;", encoding="utf-8")
    targets = sandbox.init_targets(tmp_path, names)
    argv = build(tmp_path=tmp_path, init=targets, command=["true"])
    script = argv[argv.index("-c") + 1]
    assert "pwned" not in script and "schema" not in script
    assert argv[-4:] == ["2", "/work/schema.sql", "/work/a$(touch pwned)`id`.sql", "true"]


def test_a_mount_path_with_a_comma_is_quoted(tmp_path):
    odd = tmp_path / "a,b"
    odd.mkdir()
    bind = [m for m in flag_value(build(tmp_path=odd), "--mount") if m.startswith("type=bind")]
    assert bind == [f'type=bind,"src={odd.resolve()}",dst=/src,readonly']


def test_an_init_file_outside_the_mount_is_refused(tmp_path):
    outside = tmp_path / "outside.sql"
    outside.write_text("", encoding="utf-8")
    mount = tmp_path / "mount"
    mount.mkdir()
    with pytest.raises(UsageError):
        sandbox.init_targets(mount, [str(outside)])


def test_a_profile_without_init_refuses_init_files(tmp_path):
    with pytest.raises(UsageError):
        build("python", tmp_path, command=["pytest"], init=["/work/x.sql"])


def test_the_prefetch_keeps_the_network_and_never_the_offline_switch(tmp_path):
    argv = sandbox.prefetch_argv("maven", tmp_path, name="p", volume="v")
    assert "--network" not in argv
    assert not any(value.startswith("MAVEN_ARGS") for value in flag_value(argv, "--env"))
    assert "MAVEN_ARGS=-o -B -Dmaven.repo.local=/deps/m2" in flag_value(
        build("maven", tmp_path, command=["mvn", "test"]), "--env"
    )


def test_the_prefetch_volume_is_writable_and_the_run_volume_is_not(tmp_path):
    prefetch = flag_value(
        sandbox.prefetch_argv("python", tmp_path, name="p", volume="v"), "--mount"
    )
    assert "type=volume,src=v,dst=/deps" in prefetch


@pytest.mark.parametrize(
    "line",
    [
        "-e .",
        ".",
        "./pkg",
        "pkg @ file:///x",
        "git+https://example.com/x.git",
        "-r other.txt",
        "https://example.com/x.whl",
    ],
)
def test_a_python_requirement_that_could_run_project_code_is_refused(tmp_path, line):
    (tmp_path / "requirements.txt").write_text(f"pytest\n{line}\n", encoding="utf-8")
    with pytest.raises(UsageError):
        sandbox.refuse_unsafe_prefetch("python", tmp_path)


def test_plain_python_requirements_are_fetched(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "# tools\nrequests>=2.31,<3\nuvicorn[standard]==0.30.0\nrich ; python_version >= '3.12'\n",
        encoding="utf-8",
    )
    sandbox.refuse_unsafe_prefetch("python", tmp_path)


def test_maven_build_extensions_are_refused_before_prefetch(tmp_path):
    (tmp_path / "pom.xml").write_text(
        "<project><build><extensions><extension/></extensions></build></project>",
        encoding="utf-8",
    )
    with pytest.raises(UsageError):
        sandbox.refuse_unsafe_prefetch("maven", tmp_path)


def test_the_maven_prefetch_drops_the_projects_maven_config(tmp_path):
    script = sandbox.prefetch_argv("maven", tmp_path, name="p", volume="v")[-1]
    assert "rm -rf .mvn" in script.split("dependency:go-offline")[0]


def test_postgres_needs_no_prefetch(tmp_path):
    assert sandbox.prefetch_argv("postgres", tmp_path, name="p", volume="v") is None


def docker_ready() -> bool:
    """Docker, its daemon and the postgres image, all answering promptly.

    A runner can have the client and a daemon that never answers (Windows
    runners run Windows containers), so a slow or failing probe means skip,
    never an error at collection time.
    """
    if not shutil.which("docker"):
        return False
    try:
        info = subprocess.run(["docker", "info"], capture_output=True, timeout=30)
        image = subprocess.run(
            ["docker", "image", "inspect", sandbox.PROFILES["postgres"].image],
            capture_output=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return info.returncode == 0 and image.returncode == 0


@pytest.mark.skipif(not docker_ready(), reason="docker and the postgres image are not present")
def test_a_real_seed_loads_and_a_failing_assertion_fails(tmp_path):
    (tmp_path / "schema.sql").write_text("create table t(id int primary key);", encoding="utf-8")
    (tmp_path / "seed.sql").write_text("insert into t values (1), (2);", encoding="utf-8")
    check = (
        "do $$ begin if (select count(*) from t) <> {n} then raise exception 'bad'; end if; end $$;"
    )
    init = ["schema.sql", "seed.sql"]
    assert sandbox.run("postgres", tmp_path, ["psql", "-c", check.format(n=2)], init=init) == 0
    assert (
        sandbox.run(
            "postgres",
            tmp_path,
            ["psql", "-v", "ON_ERROR_STOP=1", "-c", check.format(n=3)],
            init=init,
        )
        != 0
    )
