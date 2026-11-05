import runpy
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def script_path(pytestconfig: pytest.Config) -> Path:
    return pytestconfig.rootpath / "scripts" / "compile_sass.py"


@pytest.fixture
def sass_script(script_path: Path) -> dict[str, Callable[..., object]]:
    return runpy.run_path(str(script_path))


def test_compile_scss(
    sass_script: dict[str, Callable[..., object]], tmp_path: Path
) -> None:
    """Use a checked compiler command and propagate compiler failures."""
    source: Path = tmp_path / "input with spaces.scss"
    target: Path = tmp_path / "output with spaces.css"
    command: list[str | Path] = ["sass", source, target]
    error = subprocess.CalledProcessError(65, command)
    with patch("subprocess.run", side_effect=error) as run, pytest.raises(
        subprocess.CalledProcessError
    ) as exc:
        _ = sass_script["compile_scss"](source, target)

    run.assert_called_once_with(command, check=True)
    assert exc.value is error


@pytest.mark.parametrize(
    "output", ["1.104.0\n", "1.104.0 compiled with dart2js 3.11.2\n"]
)
def test_matching_version(sass_script: dict[str, Callable[..., object]], output: str) -> None:
    completed = subprocess.CompletedProcess(
        args=["sass", "--version"], returncode=0, stdout=output, stderr=""
    )
    with patch("subprocess.run", return_value=completed):
        _ = sass_script["check_installed_sass_version"]("1.104.0")


@pytest.mark.parametrize("output", ["", "garbage", "1.103.0"])
def test_mismatching_version(sass_script: dict[str, Callable[..., object]], output: str) -> None:
    completed = subprocess.CompletedProcess(
        args=["sass", "--version"], returncode=0, stdout=output, stderr=""
    )
    with patch("subprocess.run", return_value=completed), pytest.raises(
        RuntimeError
    ) as exc:
        _ = sass_script["check_installed_sass_version"]("1.104.0")
    message = str(exc.value)
    assert "expected 1.104.0" in message
    assert f"actual {output!r}" in message
    assert "Install sass@1.104.0" in message
    assert "ensure sass is on PATH" in message


def test_missing_sass(sass_script: dict[str, Callable[..., object]]) -> None:
    with patch("subprocess.run", side_effect=FileNotFoundError("missing")), pytest.raises(
        RuntimeError
    ) as exc:
        _ = sass_script["check_installed_sass_version"]("1.104.0")
    message = str(exc.value)
    assert "expected 1.104.0" in message
    assert "actual 'missing'" in message
    assert "Install sass@1.104.0" in message


def test_failing_sass_command(sass_script: dict[str, Callable[..., object]]) -> None:
    error = subprocess.CalledProcessError(2, "sass", stderr=" broken\n")
    with patch("subprocess.run", side_effect=error), pytest.raises(RuntimeError) as exc:
        _ = sass_script["check_installed_sass_version"]("1.104.0")
    message = str(exc.value)
    assert "expected 1.104.0" in message
    assert "actual 'exit 2: broken'" in message
    assert "Install sass@1.104.0" in message


@pytest.mark.parametrize("version", ["bad", 123])
def test_invalid_sass_version(sass_script: dict[str, Callable[..., object]], version: object) -> None:
    with pytest.raises(ValueError):
        _ = sass_script["validate_sass_version"](version)


def test_print_configured_version(
    script_path: Path, sass_script: dict[str, Callable[..., object]]
) -> None:
    result = subprocess.run(
        [sys.executable, script_path, "--print-configured-version"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == sass_script["configured_sass_version"]()


def test_check_installed_version_does_not_require_project_dependencies(
    script_path: Path, tmp_path: Path
) -> None:
    """The remote version check must run before project dependencies are installed."""
    # Reaching the Sass diagnostic proves no project import failed first.
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            script_path,
            "--check-installed-version",
            "1.104.0",
        ],
        cwd=tmp_path,
        env={"PATH": ""},
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode != 0
    assert "Sass version check failed: expected 1.104.0" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
