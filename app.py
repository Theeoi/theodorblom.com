#!/usr/bin/env python
"""Run the website."""
from website import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host=app.config["HOST"], debug=app.config["DEBUG"])
