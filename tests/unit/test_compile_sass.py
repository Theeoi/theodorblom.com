#!/usr/bin/env python

import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import call, patch

import pytest
from app import config


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/compile_sass.py"


@pytest.fixture(autouse=True)
def no_app_startup():
    """Asset builds must not import WSGI or create an app (and its databases)."""
    with patch.dict(sys.modules, {"wsgi": None}):
        with patch("app.create_app", side_effect=AssertionError("App startup during build")):
            yield


@pytest.fixture
def sass_script():
    # Python 3.8's runpy expects a string; filesystem paths stay as Path objects.
    return runpy.run_path(str(SCRIPT))


@pytest.mark.parametrize("returncode", [0, 1])
def test_check_sass_installation(sass_script, returncode):
    """Check the version command and propagate failure, regardless of local Sass."""
    command = ["sass", "--version"]
    error = subprocess.CalledProcessError(returncode, command) if returncode else None
    with patch("subprocess.run", side_effect=error) as run:
        if returncode:
            with pytest.raises(subprocess.CalledProcessError) as exc:
                sass_script["check_sass_installation"]()
            assert exc.value is error
        else:
            sass_script["check_sass_installation"]()

    run.assert_called_once_with(command, check=True)


@pytest.mark.parametrize("returncode", [0, 65])
def test_compile_scss(sass_script, tmp_path, returncode):
    """Require check=True and propagate compiler errors even when Sass is installed."""
    source = tmp_path / "input with spaces.scss"
    target = tmp_path / "output with spaces.css"
    command = ["sass", source, target]
    error = subprocess.CalledProcessError(returncode, command) if returncode else None
    with patch("subprocess.run", side_effect=error) as run:
        if returncode:
            with pytest.raises(subprocess.CalledProcessError) as exc:
                sass_script["compile_scss"](source, target)
            assert exc.value is error
        else:
            sass_script["compile_scss"](source, target)

    run.assert_called_once_with(command, check=True)


def test_entrypoint_from_different_cwd(tmp_path, monkeypatch):
    """Use the configured static folder, not a duplicated layout or the current cwd."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "STATIC_FOLDER", "../custom static")
    static_dir = (Path(config.__file__).resolve().parent / config.STATIC_FOLDER).resolve()

    with patch("subprocess.run") as run:
        runpy.run_path(str(SCRIPT), run_name="__main__")

    assert run.call_args_list == [
        call(["sass", "--version"], check=True),
        call(["sass", static_dir / "sass/style.scss", static_dir / "css/style.css"], check=True),
    ]


def test_entrypoint_missing_sass(tmp_path):
    """A real Python process must exit unsuccessfully when the CLI is unavailable."""
    result = subprocess.run(
        [sys.executable, "-I", SCRIPT],
        cwd=tmp_path,
        env={"PATH": ""},
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Sass CLI tool is not installed." in result.stderr
