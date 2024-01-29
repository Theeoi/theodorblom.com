#!/usr/bin/env python
"""Run the website."""

from app import create_app


def main():
    app = create_app()
    app.run(host=app.config["HOST"], debug=app.config["DEBUG"])


if __name__ == "__main__":
    main()
