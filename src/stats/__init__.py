from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.database.models import Request

from .main import Statistics

statistics = Statistics()


def init_statistics(app: Flask, db: SQLAlchemy, model: type[Request] = Request):
    statistics.init_app(app, db, model)
