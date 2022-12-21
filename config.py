#!/usr/bin/env python
"""
Configuration file for flask app.

Define default (dev) configuration variables here.
Production variables are configured on the server.
"""

HOST = "0.0.0.0"
DEBUG = True
SECRET_KEY = "dev"
SQL_DB_NAME = "database.db"
SQLALCHEMY_DATABASE_URI = f"sqlite:///{SQL_DB_NAME}"
