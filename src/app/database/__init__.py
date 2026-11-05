"""Definitions of the database sub-package."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app: Flask):
    """Initialize the database with the app."""
    db.init_app(app)


def create_dbs(app: Flask):
    """Create the databases if they do not already exist."""
    with app.app_context():
        db.create_all()
