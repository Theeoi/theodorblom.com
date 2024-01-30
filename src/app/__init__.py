#!/usr/bin/env python
"""app init
"""
from flask import Flask
from flask_migrate import Migrate
from flask_sitemap import Sitemap
from flask_login import LoginManager

from app.default_config import TEMPLATE_FOLDER, STATIC_FOLDER
from app.database import db, init_db, create_dbs
from website.statistics import Statistics


ext = Sitemap()
migrate = Migrate()
statistics = Statistics()


def create_app(test_config=None):
    """Create and return the flask-app."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=TEMPLATE_FOLDER,
        static_folder=STATIC_FOLDER,
    )
    # Load default app config
    app.config.from_object("app.default_config")
    # Load any instance config (if it exists)
    app.config.from_pyfile("config.py", silent=True)
    # Update with supplied test-config
    if test_config is not None:
        app.config.update(test_config)
    init_db(app)
    ext.init_app(app)

    # import and register views here
    from website.views.home import home
    from website.views.auth import auth
    from website.views.blog import blog

    app.register_blueprint(home)
    app.register_blueprint(auth)
    app.register_blueprint(blog)

    from app.database.models import User, Request

    create_dbs(app)
    migrate.init_app(app, db)
    statistics.init_app(app, db, Request)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"  # type: ignore
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
