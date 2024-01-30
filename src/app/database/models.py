#!/usr/bin/env python
"""Define database models."""

from app.database import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    """Database model for a website user."""

    __bind_key__ = "auth"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())


class Blogpost(db.Model):
    """Database model for a blogpost."""

    __bind_key__ = "blog"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True)
    title = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    published = db.Column(db.Boolean, index=True)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now(), index=True)


class Request(db.Model):
    """Database model for a webpage request. Used for website statistics."""

    index = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime(timezone=True))
    path = db.Column(db.String)
    remote_address = db.Column(db.String)
    referrer = db.Column(db.String)
