#!/usr/bin/env python

from website.models import Request


def test_no_static_request(test_client):
    test_client.get('/')
    response = test_client.get(
        '/static/resources/icons/theodorblom-favicon-cursor.svg'
    )
    assert response.status_code == 200

    request = Request.query.order_by(Request.date.desc()).first()
    assert 'static' not in request.path
    assert request.path == '/'
