#!/usr/bin/env python

from flask import Flask, g

from app.database.models import Request


def test_no_static_request(test_client):
    test_client.get("/")
    with test_client.get("/static/resources/icons/icon.png") as response:
        assert response.status_code == 200

    request = Request.query.order_by(Request.date.desc()).first()
    assert Request is not None
    assert "static" not in request.path
    assert request.path == "/"
    assert Request.date is not None

def test_undispatched_request_context_does_not_record_hit(test_client) -> None:
    app: Flask = test_client.application

    with app.app_context():
        count_before: int = Request.query.count()

        with app.test_request_context("/"):
            assert "request_date" not in g

        assert Request.query.count() == count_before
