from collections.abc import Generator

import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from slugify import slugify
from werkzeug.security import generate_password_hash

from app import create_app
from app.database import create_dbs, db
from app.database.models import Blogpost, User


@pytest.fixture
def test_blogpost() -> dict[str, object]:
    TEST_BLOGPOST: dict[str, object] = {
        "title": "Blogpost in Testing",
        "tags": "test, pytest, blogpost",
        "content": "This is a test blogpost!",
        "published": True,
    }
    return TEST_BLOGPOST


@pytest.fixture
def admin_credentials() -> dict[str, str]:
    ADMIN_CREDENTIALS: dict[str, str] = {
        "username": "adminPhil",
        "password": "superphilsPassword123",
    }
    return ADMIN_CREDENTIALS


@pytest.fixture(scope="module")
def test_client() -> Generator[FlaskClient]:
    test_config: dict[str, object] = {
        "SECRET_KEY": "test-secret",
        "TESTING": True,
        "SQLALCHEMY_BINDS": {
            "auth": "sqlite:///:memory:",
            "blog": "sqlite:///:memory:",
        },
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    }
    flask_app: Flask = create_app(test_config, mode="testing")

    with flask_app.app_context():
        try:
            create_dbs(flask_app)
            with flask_app.test_client() as testing_client:
                yield testing_client
        finally:
            try:
                db.session.remove()
                db.drop_all()
            finally:
                for engine in db.engines.values():
                    engine.dispose()


@pytest.fixture(scope="function")
def admin_user(admin_credentials: dict[str, str]) -> Generator[User]:
    user = User()
    user.username = admin_credentials["username"]
    user.password = generate_password_hash(
        admin_credentials["password"], method="scrypt"
    )
    try:
        db.session.add(user)
        db.session.commit()
        yield user
    except Exception as e:
        db.session.rollback()
        print(f"Error during commit: {e}")
        raise
    finally:
        db.session.close()
    db.session.delete(user)
    db.session.commit()


@pytest.fixture(scope="function")
def authenticated_user(
    test_client: FlaskClient, admin_user: User, admin_credentials: dict[str, str]
) -> Generator[User]:
    _ = test_client.post("/auth/login", data=admin_credentials)
    yield admin_user
    _ = test_client.get("/auth/logout")


@pytest.fixture(scope="function")
def blogpost(test_blogpost: dict[str, object]) -> Generator[Blogpost]:
    test_blogpost["slug"] = slugify(str(test_blogpost["title"]))
    blogpost = Blogpost(**test_blogpost)
    db.session.add(blogpost)
    db.session.commit()
    yield blogpost
    db.session.delete(blogpost)
    db.session.commit()
