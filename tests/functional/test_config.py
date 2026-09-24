#!/usr/bin/env python

import traceback
from unittest.mock import Mock

import pytest
from flask import Flask

from app import create_app
from app.config import DevelopmentConfig


@pytest.fixture
def instance(tmp_path, monkeypatch):
    # Also isolate no-argument calls used by the production entrypoint.
    monkeypatch.setattr(Flask, "auto_find_instance_path", lambda self: str(tmp_path))
    return tmp_path / "config.py"


@pytest.fixture
def database_startup(monkeypatch):
    init_db = Mock()
    create_dbs = Mock()
    monkeypatch.setattr("app.init_db", init_db)
    monkeypatch.setattr("app.create_dbs", create_dbs)
    return init_db, create_dbs


@pytest.mark.parametrize("source", [
    None,
    "SECRET_KEY = 'syntax-secret' !",
    "raise RuntimeError('exception-secret')",
    "# No secret configured",
    "SECRET_KEY = None",
    "SECRET_KEY = ''",
    "SECRET_KEY = b''",
    "SECRET_KEY = '   '",
    "SECRET_KEY = b'   '",
    "SECRET_KEY = 'secret_dev'",
    "SECRET_KEY = b'secret_dev'",
    "SECRET_KEY = 123",
    "SECRET_KEY = True",
    "SECRET_KEY = ['wrong-type-secret']",
    "SECRET_KEY = {'wrong-type-secret': 1}",
    "SECRET_KEY = 'valid-secret'; DEBUG = True",
    "SECRET_KEY = 'valid-secret'; TESTING = True",
])
def test_production_rejects_invalid_config(instance, database_startup, source):
    if source is not None:
        instance.write_text(source)

    with pytest.raises(RuntimeError) as exc:
        create_app()

    rendered = "".join(
        traceback.format_exception(type(exc.value), exc.value, exc.tb)
    )
    for secret in (
        "syntax-secret", "exception-secret", "wrong-type-secret", "valid-secret"
    ):
        assert secret not in rendered
    if source is None or source.startswith(("raise", "SECRET_KEY = 'syntax")):
        assert "Production requires a readable, valid config.py" in str(exc.value)
        assert str(instance) in str(exc.value)
    for startup in database_startup:
        startup.assert_not_called()
    assert not list(instance.parent.glob("*.db"))


def test_unreadable_config(instance, database_startup, monkeypatch):
    def unreadable(*args, **kwargs):
        raise PermissionError("unreadable-secret")

    # Deterministic even when tests run with privileges that bypass file modes.
    monkeypatch.setattr("flask.config.Config.from_pyfile", unreadable)
    with pytest.raises(RuntimeError, match="readability") as exc:
        create_app()
    assert "Production requires a readable, valid config.py" in str(exc.value)
    assert str(instance) in str(exc.value)
    assert "unreadable-secret" not in "".join(
        traceback.format_exception(type(exc.value), exc.value, exc.tb)
    )
    for startup in database_startup:
        startup.assert_not_called()


@pytest.mark.parametrize("mode", [None, "production"])
@pytest.mark.parametrize("secret", ["a", b"a"])
def test_valid_production_factory(instance, mode, secret):
    instance.write_text("SECRET_KEY = {!r}\n".format(secret))
    app = create_app() if mode is None else create_app(mode=mode)
    assert app.config["SECRET_KEY"] == secret
    assert not app.debug
    assert not app.testing
    assert app.instance_path == str(instance.parent)
    assert {path.name for path in instance.parent.glob("*.db")} == {
        "auth.db", "blog.db", "default.db"
    }
    with app.test_client() as client:
        assert client.get("/").status_code == 200


@pytest.mark.parametrize("kwargs", [
    {"mode": "unknown"},
    {"mode": None},
    {"test_config": {"TESTING": True}},
    {"mode": "production", "test_config": {}},
    {"mode": "development", "test_config": {}},
    {"mode": "testing"},
])
def test_invalid_factory_arguments(instance, database_startup, kwargs):
    with pytest.raises(ValueError):
        create_app(**kwargs)
    for startup in database_startup:
        startup.assert_not_called()


@pytest.mark.parametrize("with_config", [False, True])
def test_development_optional_config(instance, with_config):
    if with_config:
        instance.write_text("SECRET_KEY = 'local-secret'\nDEBUG = True\n")
    app = create_app(mode="development")
    assert app.config["SECRET_KEY"] == (
        "local-secret" if with_config else DevelopmentConfig.SECRET_KEY
    )
    assert app.debug is with_config


def test_testing_skips_instance_config(instance):
    instance.write_text("raise AssertionError('Instance config must not execute')")
    app = create_app({
        "SECRET_KEY": "isolated-test-secret",
        "TESTING": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_BINDS": {
            "auth": "sqlite:///:memory:",
            "blog": "sqlite:///:memory:",
        },
    }, mode="testing")
    assert app.testing
    assert app.config["SECRET_KEY"] == "isolated-test-secret"
    assert not list(instance.parent.glob("*.db"))
    with app.test_client() as client:
        assert client.get("/").status_code == 200
