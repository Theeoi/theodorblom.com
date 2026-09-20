#!/usr/bin/env python

import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import call, patch

import pytest

from app import config


@pytest.fixture
def script_path(pytestconfig):
    return pytestconfig.rootpath / "scripts" / "compile_sass.py"


@pytest.fixture
def sass_script(script_path):
    # Python 3.8's runpy expects a string; filesystem paths stay as Path objects.
    return runpy.run_path(str(script_path))


def test_compile_scss(sass_script, tmp_path):
    """Use a checked compiler command and propagate compiler failures."""
    source = tmp_path / "input with spaces.scss"
    target = tmp_path / "output with spaces.css"
    command = ["sass", source, target]
    error = subprocess.CalledProcessError(65, command)
    with patch("subprocess.run", side_effect=error) as run:
        with pytest.raises(subprocess.CalledProcessError) as exc:
            sass_script["compile_scss"](source, target)

    run.assert_called_once_with(command, check=True)
    assert exc.value is error


def test_entrypoint_from_different_cwd(script_path, tmp_path, monkeypatch):
    """Use configured paths from any cwd without starting the app or its databases."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "STATIC_FOLDER", "../custom static")
    static_dir = (
        Path(config.__file__).resolve().parent / config.STATIC_FOLDER
    ).resolve()

    with patch.dict(sys.modules, {"wsgi": None}):
        with patch(
            "app.create_app",
            side_effect=AssertionError("App startup during build"),
        ):
            with patch("subprocess.run") as run:
                runpy.run_path(str(script_path), run_name="__main__")

    assert run.call_args_list == [
        call(["sass", "--version"], check=True),
        call(
            [
                "sass",
                static_dir / "sass/style.scss",
                static_dir / "css/style.css",
            ],
            check=True,
        ),
    ]


def test_entrypoint_missing_sass(script_path, tmp_path):
    """A real Python process must exit unsuccessfully when the CLI is unavailable."""
    result = subprocess.run(
        [sys.executable, "-I", script_path],
        cwd=tmp_path,
        env={"PATH": ""},
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Sass CLI tool is not installed." in result.stderr
