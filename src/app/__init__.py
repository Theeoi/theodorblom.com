#!/usr/bin/env python

from flask import Flask
from flask_migrate import Migrate
from flask_sitemap import Sitemap

from app.config import TEMPLATE_FOLDER, STATIC_FOLDER, load_configs
from app.database import db, init_db, create_dbs
from stats import init_statistics
from website.views import register_blueprints
from auth import init_login_manager


ext = Sitemap()
migrate = Migrate()


def create_app(test_config=None):
    """Create and return the flask-app."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=TEMPLATE_FOLDER,
        static_folder=STATIC_FOLDER,
    )
    load_configs(app, test_config)
    init_db(app)
    ext.init_app(app)

    register_blueprints(app)

    create_dbs(app)
    migrate.init_app(app, db)

    init_statistics(app, db)

    init_login_manager(app)

    return app
