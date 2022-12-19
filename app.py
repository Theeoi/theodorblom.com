#!/usr/bin/env python
"""Run the website."""
from website import create_app

ENABLE_INSTANCE: bool = True

if __name__ == "__main__":
    app = create_app(ENABLE_INSTANCE)
    app.run(host=app.config["HOST"], debug=app.config["DEBUG"])
