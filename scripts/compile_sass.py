#!/usr/bin/env python

import argparse
import re
import subprocess
from pathlib import Path


def expected_sass_version():
    import tomli

    path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with path.open("rb") as config_file:
        version = tomli.load(config_file)["tool"]["sass"]["version"]
    validate_version(version)
    return version


def validate_version(version):
    if not isinstance(version, str) or not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+", version
    ):
        raise ValueError(
            "Expected Sass version must be a major.minor.patch string; got {!r}".format(
                version
            )
        )


def check_sass_installation(expected):
    validate_version(expected)
    actual = "unavailable"
    try:
        result = subprocess.run(
            ["sass", "--version"], check=True, capture_output=True, text=True
        )
    except OSError as error:
        actual = str(error)
    except subprocess.CalledProcessError as error:
        actual = "exit {}: {}".format(
            error.returncode, (error.stdout or error.stderr or "").strip()
        )
    else:
        actual = result.stdout.strip()
        # Dart Sass may append implementation information after the version token.
        tokens = actual.split()
        if tokens and tokens[0] == expected:
            return
    raise RuntimeError(
        "Sass version check failed: expected {}; actual {!r}. "
        "Install sass@{} and ensure sass is on PATH.".format(expected, actual, expected)
    )


def compile_scss(input_file, output_file):
    subprocess.run(["sass", input_file, output_file], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--print-version", action="store_true")
    mode.add_argument("--expected-version")
    args = parser.parse_args()
    if args.print_version:
        print(expected_sass_version())
        raise SystemExit(0)
    if args.expected_version is not None:
        check_sass_installation(args.expected_version)
        raise SystemExit(0)

    check_sass_installation(expected_sass_version())
    from app import config

    static_dir = (
        Path(config.__file__).resolve().parent / config.STATIC_FOLDER
    ).resolve()

    scss_file = static_dir.joinpath("sass/style.scss")
    css_file = static_dir.joinpath("css/style.css")

    compile_scss(scss_file, css_file)
