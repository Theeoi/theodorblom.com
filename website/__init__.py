#!/usr/bin/env python
"""App definitions of the website package."""
from os import path
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sitemap import Sitemap

db = SQLAlchemy()
ext = Sitemap()
migrate = Migrate()


def create_app() -> Flask:
    """Create and return the flask-app."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py', silent=True)
    db.init_app(app)
    ext.init_app(app)

    # import and register views here
    from .views.home import home
    from .views.auth import auth
    from .views.blog import blog

    app.register_blueprint(home)
    app.register_blueprint(auth)
    app.register_blueprint(blog)

    from .models import User

    create_db(app)
    migrate.init_app(app, db)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_db(app) -> None:
    """Create the database if is does not exist."""
    if not path.exists("instance/" +
                       app.config["SQLALCHEMY_BINDS"]["auth"].split('/')[-1]):
        app.logger.error(
            f"Database {app.config['SQLALCHEMY_BINDS']['auth']} was not found!"
        )
        with app.app_context():
            db.create_all(bind_key="auth")
            app.logger.info("Created new database.")
    if not path.exists("instance/" +
                       app.config["SQLALCHEMY_BINDS"]["blog"].split('/')[-1]):
        app.logger.error(
            f"Database {app.config['SQLALCHEMY_BINDS']['blog']} was not found!"
        )
        with app.app_context():
            db.create_all(bind_key="blog")
            app.logger.info("Created new database.")
