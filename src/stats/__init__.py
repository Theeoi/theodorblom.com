#!/usr/bin/env python
from app.database.models import Request
from .main import Statistics

statistics = Statistics()


def init_statistics(app, db, model=Request):
    statistics.init_app(app, db, model)
