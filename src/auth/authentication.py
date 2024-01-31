#!/usr/bin/env python

from app.database.models import User


def load_user(id):
    return User.query.get(int(id))
