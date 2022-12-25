#!/usr/bin/env python
"""Define database models."""

from . import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    """Database model for a website user."""

    __bind_key__ = "auth"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
