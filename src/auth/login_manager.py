#!/usr/bin/env python

from flask_login import LoginManager

from .authentication import load_user
from app.config import LOGIN_VIEW

login_manager = LoginManager()


def init_login_manager(app):
    login_manager.login_view = LOGIN_VIEW  # type: ignore
    login_manager.user_loader(load_user)
    login_manager.init_app(app)
