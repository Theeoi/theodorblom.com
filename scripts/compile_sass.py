#!/usr/bin/env python

import argparse
import re
import subprocess
from pathlib import Path


def configured_sass_version():
    import tomli

    path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with path.open("rb") as config_file:
        version = tomli.load(config_file)["tool"]["sass"]["version"]
    validate_sass_version(version)
    return version


def validate_sass_version(version):
    if not isinstance(version, str) or not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+", version
    ):
        raise ValueError(
            f"Sass version must be a major.minor.patch string; got {version!r}"
        )


def check_installed_sass_version(expected):
    validate_sass_version(expected)
    actual = "unavailable"
    try:
        result = subprocess.run(
            ["sass", "--version"], check=True, capture_output=True, text=True
        )
    except OSError as error:
        actual = str(error)
    except subprocess.CalledProcessError as error:
        output = (error.stdout or error.stderr or "").strip()
        actual = f"exit {error.returncode}: {output}"
    else:
        actual = result.stdout.strip()
        # Dart Sass may append implementation details after the version token.
        tokens = actual.split()
        if tokens and tokens[0] == expected:
            return
    raise RuntimeError(
        f"""
        Sass version check failed: expected {expected}; actual {actual!r}.
        Install sass@{expected} and ensure sass is on PATH.
        """
    )


def compile_scss(input_file, output_file):
    _ = subprocess.run(["sass", input_file, output_file], check=True)


def parse_args():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    _ = mode.add_argument("--print-configured-version", action="store_true")
    _ = mode.add_argument("--check-installed-version")
    args = parser.parse_args()
    if args.print_configured_version:
        print(configured_sass_version())
        raise SystemExit(0)
    if args.check_installed_version is not None:
        check_installed_sass_version(args.check_installed_version)
        raise SystemExit(0)


def main():
    parse_args()

    check_installed_sass_version(configured_sass_version())
    from app import config

    static_dir = (
        Path(config.__file__).resolve().parent / config.STATIC_FOLDER
    ).resolve()

    scss_file = static_dir.joinpath("sass/style.scss")
    css_file = static_dir.joinpath("css/style.css")

    compile_scss(scss_file, css_file)


if __name__ == "__main__":
    main()
