#!/usr/bin/env python
"""App definitions of the website package."""
from os import path
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    """Create and return the flask-app."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py', silent=True)
    db.init_app(app)

    # import and register views here
    from .views.home import home
    from .views.blog import blog
    from .views.auth import auth

    app.register_blueprint(home)
    app.register_blueprint(blog)
    app.register_blueprint(auth)

    from .models import User

    create_db(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_db(app):
    """Create the database if is does not exist."""
    if not path.exists("instance/" + app.config["SQL_DB_NAME"]):
        app.logger.error("Database was not found!")
        with app.app_context():
            db.create_all()
            app.logger.info("Created new database.")
