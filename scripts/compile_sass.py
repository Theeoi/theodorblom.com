#!/usr/bin/env python

import subprocess
from pathlib import Path

from app import config


def check_sass_installation():
    try:
        subprocess.run(["sass", "--version"], check=True)
    except FileNotFoundError:
        raise FileNotFoundError("Sass CLI tool is not installed.")


def compile_scss(input_file, output_file):
    subprocess.run(["sass", input_file, output_file], check=True)


if __name__ == "__main__":
    static_dir = (Path(config.__file__).resolve().parent / config.STATIC_FOLDER).resolve()

    scss_file = static_dir.joinpath("sass/style.scss")
    css_file = static_dir.joinpath("css/style.css")

    check_sass_installation()
    compile_scss(scss_file, css_file)
