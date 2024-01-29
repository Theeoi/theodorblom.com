#!/usr/bin/env python
"""App definitions of the website package."""
from os import path
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sitemap import Sitemap

from .statistics import Statistics

db = SQLAlchemy()
ext = Sitemap()
migrate = Migrate()
statistics = Statistics()


def create_app(test_config=None) -> Flask:
    """Create and return the flask-app."""
    app = Flask(__name__, instance_relative_config=True)
    # Load default app config
    app.config.from_object("app.default_config")
    # Load any instance config (if it exists)
    app.config.from_pyfile("config.py", silent=True)
    # Update with supplied test-config
    if test_config is not None:
        app.config.update(test_config)
    db.init_app(app)
    ext.init_app(app)

    # import and register views here
    from .views.home import home
    from .views.auth import auth
    from .views.blog import blog

    app.register_blueprint(home)
    app.register_blueprint(auth)
    app.register_blueprint(blog)

    from .models import User, Request

    create_db(app)
    migrate.init_app(app, db)
    statistics.init_app(app, db, Request)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_db(app) -> None:
    """Create the database if is does not exist."""
    # TODO: Refactor this to a for loop or similar
    if not path.exists(
        f"{app.instance_path}/{app.config['SQLALCHEMY_BINDS']['auth'].split('/')[-1]}"
    ):
        app.logger.error(
            f"Database {app.config['SQLALCHEMY_BINDS']['auth']} was not found!"
        )
        with app.app_context():
            db.create_all(bind_key="auth")
            app.logger.info("Created new database.")
    if not path.exists(
        f"{app.instance_path}/{app.config['SQLALCHEMY_BINDS']['blog'].split('/')[-1]}"
    ):
        app.logger.error(
            f"Database {app.config['SQLALCHEMY_BINDS']['blog']} was not found!"
        )
        with app.app_context():
            db.create_all(bind_key="blog")
            app.logger.info("Created new database.")

    with app.app_context():
        db.create_all(bind_key=None)
