#!/usr/bin/env python

import pytest
from app import create_app, create_db, db
from website.models import User, Blogpost
from werkzeug.security import generate_password_hash
from slugify import slugify

ADMIN_USER = {
    "username": "adminPhil",
    "password": "superphilsPassword123",
}

TEST_BLOGPOST = {
    "title": "Blogpost in Testing",
    "tags": "test, pytest, blogpost",
    "content": "This is a test blogpost!",
    "published": True,
}


@pytest.fixture(scope="module")
def test_client():
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_BINDS": {
            "auth": "sqlite:///:memory:",
            "blog": "sqlite:///:memory:",
        },
    }
    flask_app = create_app(test_config)

    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            create_db(flask_app)
            yield testing_client
            db.session.remove()
            db.drop_all()


@pytest.fixture(scope="function")
def admin_user():
    user = User(
        username=ADMIN_USER["username"],
        password=generate_password_hash(ADMIN_USER["password"], method="scrypt"),
    )
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()


@pytest.fixture(scope="function")
def authenticated_user(test_client, admin_user):
    test_client.post("/auth/login", data=ADMIN_USER)
    yield admin_user
    test_client.get("/auth/logout")


@pytest.fixture(scope="function")
def blogpost():
    TEST_BLOGPOST["slug"] = slugify(TEST_BLOGPOST["title"])
    blogpost = Blogpost(**TEST_BLOGPOST)
    db.session.add(blogpost)
    db.session.commit()
    yield blogpost
    db.session.delete(blogpost)
    db.session.commit()
