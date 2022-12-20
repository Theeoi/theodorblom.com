#!/usr/bin/env python
"""App definitions of the website package."""
from flask import Flask


def create_app():
    """Create and return the flask-app."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py', silent=True)

    # import and register views here
    from .views.home import home
    from .views.blog import blog

    app.register_blueprint(home)
    app.register_blueprint(blog)

    return app
