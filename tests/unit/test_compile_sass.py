#!/usr/bin/env python

import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import call, patch

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "compile_sass.py"


@pytest.fixture
def sass_script():
    with patch.dict(sys.modules, {"wsgi": None}):
        return runpy.run_path(str(SCRIPT))


def test_check_sass_installation(sass_script):
    with patch("subprocess.run") as run:
        sass_script["check_sass_installation"]()

    run.assert_called_once_with(["sass", "--version"], check=True)


def test_check_sass_installation_failure(sass_script):
    error = subprocess.CalledProcessError(1, ["sass", "--version"])
    with patch("subprocess.run", side_effect=error):
        with pytest.raises(subprocess.CalledProcessError) as exc:
            sass_script["check_sass_installation"]()

    assert exc.value is error


def test_check_sass_installation_missing(sass_script):
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError, match="Sass CLI tool is not installed"):
            sass_script["check_sass_installation"]()


def test_compile_scss(sass_script, tmp_path):
    source = tmp_path / "input with spaces.scss"
    target = tmp_path / "output with spaces.css"
    with patch("subprocess.run") as run:
        sass_script["compile_scss"](source, target)

    run.assert_called_once_with(["sass", source, target], check=True)


def test_compile_scss_failure(sass_script):
    error = subprocess.CalledProcessError(65, ["sass", "input.scss", "output.css"])
    with patch("subprocess.run", side_effect=error):
        with pytest.raises(subprocess.CalledProcessError) as exc:
            sass_script["compile_scss"]("input.scss", "output.css")

    assert exc.value is error


@pytest.mark.parametrize("fails", [False, True])
def test_entrypoint_from_different_cwd(tmp_path, monkeypatch, fails):
    monkeypatch.chdir(tmp_path)
    static_dir = SCRIPT.parent.parent / "src" / "website" / "static"
    command = ["sass", static_dir / "sass/style.scss", static_dir / "css/style.css"]
    error = subprocess.CalledProcessError(65, command)
    results = [
        subprocess.CompletedProcess(["sass", "--version"], 0),
        error if fails else subprocess.CompletedProcess(command, 0),
    ]

    with patch.dict(sys.modules, {"wsgi": None}):
        with patch("subprocess.run", side_effect=results) as run:
            if fails:
                with pytest.raises(subprocess.CalledProcessError) as exc:
                    runpy.run_path(str(SCRIPT), run_name="__main__")
                assert exc.value is error
            else:
                runpy.run_path(str(SCRIPT), run_name="__main__")

    assert run.call_args_list == [
        call(["sass", "--version"], check=True),
        call(command, check=True),
    ]


def test_entrypoint_missing_sass(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT)],
        cwd=tmp_path,
        env={"PATH": ""},
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Sass CLI tool is not installed." in result.stderr
