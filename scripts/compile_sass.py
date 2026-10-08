from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from typing import cast


def configured_sass_version() -> str:
    import tomllib

    path: Path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with path.open("rb") as config_file:
        version = cast(
            str | object,
            tomllib.load(config_file)["tool"]["sass"]["version"],
        )
    return validate_sass_version(version)


def validate_sass_version(version: object) -> str:
    if not isinstance(version, str) or not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+", version
    ):
        raise ValueError(
            f"Sass version must be a major.minor.patch string; got {version!r}"
        )
    return version


def check_installed_sass_version(expected: object) -> None:
    expected_version: str = validate_sass_version(expected)
    actual: str = "unavailable"
    try:
        result = subprocess.run(
            ["sass", "--version"], check=True, capture_output=True, text=True
        )
    except OSError as error:
        actual = str(error)
    except subprocess.CalledProcessError as error:
        stdout = cast("str | bytes | None", error.stdout)
        stderr = cast("str | bytes | None", error.stderr)
        output = (stdout or stderr or "").strip()
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        actual = f"exit {error.returncode}: {output}"
    else:
        actual = result.stdout.strip()
        # Dart Sass may append implementation details after the version token.
        tokens = actual.split()
        if tokens and tokens[0] == expected_version:
            return
    raise RuntimeError(
        f"""
        Sass version check failed: expected {expected_version}; actual {actual!r}.
        Install sass@{expected_version} and ensure sass is on PATH.
        """
    )


def compile_scss(input_file: Path, output_file: Path) -> None:
    _ = subprocess.run(["sass", input_file, output_file], check=True)


class ParsedArgs(argparse.Namespace):
    print_configured_version: bool = False
    check_installed_version: str | None = None


def parse_args() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    _ = mode.add_argument("--print-configured-version", action="store_true")
    _ = mode.add_argument("--check-installed-version")
    args = cast(ParsedArgs, parser.parse_args())
    if args.print_configured_version:
        print(configured_sass_version())
        raise SystemExit(0)
    if args.check_installed_version is not None:
        check_installed_sass_version(args.check_installed_version)
        raise SystemExit(0)


def main() -> None:
    parse_args()

    check_installed_sass_version(configured_sass_version())
    from app import config

    static_dir: Path = (
        Path(config.__file__).resolve().parent / config.STATIC_FOLDER
    ).resolve()

    scss_file: Path = static_dir.joinpath("sass/style.scss")
    css_file: Path = static_dir.joinpath("css/style.css")

    compile_scss(scss_file, css_file)


if __name__ == "__main__":
    main()
