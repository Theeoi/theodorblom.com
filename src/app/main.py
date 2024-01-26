#!/usr/bin/env python
"""Run the website."""
from website import create_app

app = create_app()


def main():
    app.run(host=app.config["HOST"], debug=app.config["DEBUG"])


if __name__ == "__main__":
    main()
