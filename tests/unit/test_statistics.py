from flask import Flask, g
from flask.testing import FlaskClient
from sqlalchemy import select
from sqlalchemy.sql import func

from app.database import db
from app.database.models import Request


def test_no_static_request(test_client: FlaskClient) -> None:
    _ = test_client.get("/")
    with test_client.get("/static/resources/icons/icon.png") as response:
        assert response.status_code == 200

    request: Request | None = db.session.scalar(
        select(Request).order_by(Request.date.desc())
    )
    assert request is not None
    assert request.path is not None
    assert "static" not in request.path
    assert request.path == "/"
    assert request.date is not None


def test_undispatched_request_context_does_not_record_hit(
    test_client: FlaskClient,
) -> None:
    app: Flask = test_client.application

    with app.app_context():
        count_before: int = db.session.execute(
            select(func.count()).select_from(Request)
        ).scalar_one()

        with app.test_request_context("/"):
            assert "request_date" not in g

        assert (
            db.session.execute(
                select(func.count()).select_from(Request)
            ).scalar_one()
            == count_before
        )
