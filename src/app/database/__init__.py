#!/usr/bin/env python
"""Definitions of the database sub-package.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialize the database with the app.

    Args:
        app (Flask): A Flask app instance.
    """
    db.init_app(app)


def create_dbs(app):
    """Create the databases if they do not already exist.

    Args:
        app (Flask): A Flask app instance.
    """
    with app.app_context():
        db.create_all()

    # TODO: #33 Improve create_dbs for betted logging of database issues.
