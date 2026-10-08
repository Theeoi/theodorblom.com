import traceback
from collections.abc import Callable, Generator
from pathlib import Path
from typing import TypedDict, cast
from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask

from app import create_app
from app.config import DevelopmentConfig
from app.database import db


class FactoryArgs(TypedDict, total=False):
    mode: str
    test_config: dict[str, object]


@pytest.fixture
def instance(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    # Also isolate no-argument calls used by the production entrypoint.
    def auto_find_instance_path(_self: Flask) -> str:
        return str(tmp_path)

    monkeypatch.setattr(Flask, "auto_find_instance_path", auto_find_instance_path)
    return tmp_path / "config.py"


@pytest.fixture
def database_startup(monkeypatch: MonkeyPatch) -> tuple[Mock, Mock]:
    init_db = Mock()
    create_dbs = Mock()
    monkeypatch.setattr("app.init_db", init_db)
    monkeypatch.setattr("app.create_dbs", create_dbs)
    return init_db, create_dbs


@pytest.fixture
def cleanup_app(request: pytest.FixtureRequest) -> Generator[Callable[..., None]]:
    _ = cast(Path, request.getfixturevalue("instance"))
    apps: list[Flask] = []

    def register(app: Flask) -> None:
        apps.append(app)

    try:
        yield register
    finally:
        for app in reversed(apps):
            with app.app_context():
                try:
                    db.session.remove()
                finally:
                    for engine in db.engines.values():
                        engine.dispose()


@pytest.mark.parametrize(
    "source",
    [
        None,
        "SECRET_KEY = 'syntax-secret' !",
        "raise RuntimeError('exception-secret')",
        "# No secret configured",
        "SECRET_KEY = '   '",
        "SECRET_KEY = 'secret_dev'",
        "SECRET_KEY = b'secret_dev'",
        "SECRET_KEY = 123",
        "SECRET_KEY = 'valid-secret'; DEBUG = True",
        "SECRET_KEY = 'valid-secret'; TESTING = True",
    ],
)
def test_production_rejects_invalid_config(instance: Path, database_startup: tuple[Mock, Mock], source: str | None) -> None:
    if source is not None:
        _ = instance.write_text(source)

    with pytest.raises(RuntimeError) as exc:
        _ = create_app()

    rendered = "".join(
        traceback.format_exception(type(exc.value), exc.value, exc.tb)
    )
    for secret in ("syntax-secret", "exception-secret", "valid-secret"):
        assert secret not in rendered
    if source is None or source.startswith(("raise", "SECRET_KEY = 'syntax")):
        assert "Production requires a readable, valid config.py" in str(
            exc.value
        )
        assert str(instance) in str(exc.value)
    for startup in database_startup:
        startup.assert_not_called()
    assert not list(instance.parent.glob("*.db"))


def test_unreadable_config(instance: Path, database_startup: tuple[Mock, Mock], monkeypatch: MonkeyPatch) -> None:
    def unreadable(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("unreadable-secret")

    # Deterministic even when tests run with privileges that bypass file modes.
    monkeypatch.setattr("flask.config.Config.from_pyfile", unreadable)
    with pytest.raises(RuntimeError, match="readability") as exc:
        _ = create_app()
    assert "Production requires a readable, valid config.py" in str(exc.value)
    assert str(instance) in str(exc.value)
    assert "unreadable-secret" not in "".join(
        traceback.format_exception(type(exc.value), exc.value, exc.tb)
    )
    for startup in database_startup:
        startup.assert_not_called()


@pytest.mark.parametrize(
    ("kwargs", "secret"),
    [({}, "a"), ({"mode": "production"}, b"a")],
)
def test_valid_production_factory(instance: Path, cleanup_app: Callable[..., None], kwargs: FactoryArgs, secret: str) -> None:
    _ = instance.write_text(f"SECRET_KEY = {secret!r}\n")
    app = create_app(**kwargs)
    cleanup_app(app)
    assert app.config["SECRET_KEY"] == secret
    assert not app.debug
    assert not app.testing
    assert {path.name for path in instance.parent.glob("*.db")} == {
        "auth.db",
        "blog.db",
        "default.db",
    }


@pytest.mark.usefixtures("instance")
@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": "unknown"},
        {"test_config": {}},
        {"mode": "testing"},
    ],
)
def test_invalid_factory_arguments(
    database_startup: tuple[Mock, Mock],
    kwargs: FactoryArgs
) -> None:
    with pytest.raises(ValueError):
        _ = create_app(**kwargs)
    for startup in database_startup:
        startup.assert_not_called()


@pytest.mark.parametrize("with_config", [False, True])
def test_development_optional_config(instance: Path, cleanup_app: Callable[..., None], with_config: bool) -> None:
    if with_config:
        _ = instance.write_text("SECRET_KEY = 'local-secret'\nDEBUG = True\n")
    app = create_app(mode="development")
    cleanup_app(app)
    assert app.config["SECRET_KEY"] == (
        "local-secret" if with_config else DevelopmentConfig.SECRET_KEY
    )
    assert app.debug is with_config


def test_testing_skips_instance_config(instance: Path, cleanup_app: Callable[..., None]) -> None:
    _ = instance.write_text(
        "raise AssertionError('Instance config must not execute')"
    )
    app = create_app(
        {
            "SECRET_KEY": "isolated-test-secret",
            "TESTING": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_BINDS": {
                "auth": "sqlite:///:memory:",
                "blog": "sqlite:///:memory:",
            },
        },
        mode="testing",
    )
    cleanup_app(app)
    assert app.testing
    assert app.config["SECRET_KEY"] == "isolated-test-secret"
    assert not list(instance.parent.glob("*.db"))
