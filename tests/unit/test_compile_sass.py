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


def test_entrypoint_from_different_cwd(script_path, sass_script, tmp_path, monkeypatch):
    """Use configured paths from any cwd without starting the app or its databases."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [str(script_path)])
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
                run.return_value.stdout = sass_script["expected_sass_version"]()
                runpy.run_path(str(script_path), run_name="__main__")

    assert run.call_args_list == [
        call(["sass", "--version"], check=True, capture_output=True, text=True),
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
    assert "Sass version check failed: expected" in result.stderr
    assert "ensure sass is on PATH" in result.stderr


@pytest.mark.parametrize(
    "output", ["1.104.0\n", "1.104.0 compiled with dart2js 3.11.2\n"]
)
def test_matching_version(sass_script, output):
    with patch("subprocess.run") as run:
        run.return_value.stdout = output
        sass_script["check_sass_installation"]("1.104.0")


@pytest.mark.parametrize(
    "output", ["", "garbage", "1.104.00", "1.104.0-dev", "1.103.0"]
)
def test_invalid_actual_version(sass_script, output):
    with patch("subprocess.run") as run:
        run.return_value.stdout = output
        with pytest.raises(RuntimeError) as exc:
            sass_script["check_sass_installation"]("1.104.0")
    assert str(exc.value) == (
        f"Sass version check failed: expected 1.104.0; actual {output!r}. "
        "Install sass@1.104.0 and ensure sass is on PATH."
    )


@pytest.mark.parametrize(
    "error, actual",
    [
        (FileNotFoundError("missing"), "missing"),
        (subprocess.CalledProcessError(2, "sass", output="broken"),
         "exit 2: broken"),
        (subprocess.CalledProcessError(2, "sass", stderr=" broken\n"),
         "exit 2: broken"),
        (subprocess.CalledProcessError(2, "sass"), "exit 2: "),
    ],
)
def test_unavailable_version(sass_script, error, actual):
    with patch("subprocess.run", side_effect=error):
        with pytest.raises(RuntimeError) as exc:
            sass_script["check_sass_installation"]("1.104.0")
    assert str(exc.value) == (
        f"Sass version check failed: expected 1.104.0; actual {actual!r}. "
        "Install sass@1.104.0 and ensure sass is on PATH."
    )


@pytest.mark.parametrize("version", [None, 123, "bad"])
def test_invalid_expected_version_diagnostic(sass_script, version):
    with pytest.raises(ValueError) as exc:
        sass_script["validate_version"](version)
    assert str(exc.value) == (
        "Expected Sass version must be a major.minor.patch string; "
        f"got {version!r}"
    )


@pytest.mark.parametrize(
    "declaration", ['version = "1.104.0"', 'version = "1.104.0" # comment']
)
def test_config_parser(sass_script, tmp_path, declaration):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (tmp_path / "pyproject.toml").write_text("[tool.sass]\n" + declaration)
    reader = sass_script["expected_sass_version"]
    reader.__globals__["__file__"] = str(scripts / "compile_sass.py")
    assert reader() == "1.104.0"


@pytest.mark.parametrize(
    "config_text",
    ["", '[tool.sass]\nversion = 123', '[tool.sass]\nversion = "bad"', '[tool.sass'],
)
def test_bad_config(sass_script, tmp_path, config_text):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (tmp_path / "pyproject.toml").write_text(config_text)
    reader = sass_script["expected_sass_version"]
    reader.__globals__["__file__"] = str(scripts / "compile_sass.py")
    with pytest.raises((KeyError, ValueError)):
        reader()


def test_preflight_without_site_packages(script_path, tmp_path):
    """The remote interface needs neither tomli nor the application installed."""
    result = subprocess.run(
        [sys.executable, "-I", "-S", script_path, "--expected-version", "1.104.0"],
        cwd=tmp_path,
        env={"PATH": ""},
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Sass version check failed: expected 1.104.0" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
