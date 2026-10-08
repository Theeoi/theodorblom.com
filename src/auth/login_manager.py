from flask import Flask
from flask_login import LoginManager

from app.config import LOGIN_VIEW

from .authentication import load_user

login_manager = LoginManager()


def init_login_manager(app: Flask):
    login_manager.login_view = LOGIN_VIEW
    _ = login_manager.user_loader(load_user)
    login_manager.init_app(app)
