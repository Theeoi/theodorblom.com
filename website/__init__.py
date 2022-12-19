#!/usr/bin/env python
"""App definitions of the website package."""
from flask import Flask


def create_app(enable_instance: bool = False):
    """
    Create and return the flask-app.

    If you want to run the app with your instance configuration, set
    "enable_instance = True" and change app.config.from_pyfile accordingly.
    """
    app = Flask(__name__, instance_relative_config=enable_instance)
    app.config.from_object('config')
    if enable_instance:
        app.config.from_pyfile('config.py')

    # import and register views here
    from .views.home import home
    from .views.blog import blog

    app.register_blueprint(home)
    app.register_blueprint(blog)

    return app
