#!/usr/bin/env python

import re

import pytest
from slugify import slugify

from app.database import db
from app.database.models import Blogpost


@pytest.fixture
def posts(test_client):
    original = Blogpost(
        title="Original title",
        slug="original-title",
        tags="original,tags",
        content="Original content",
        published=True,
    )
    duplicate = Blogpost(
        title="Existing title",
        slug="existing-title",
        tags="existing,tags",
        content="Existing content",
        published=False,
    )
    db.session.add_all([original, duplicate])
    db.session.commit()
    try:
        yield original, duplicate
    finally:
        # The module-scoped client shares its database across parametrized cases.
        db.session.rollback()
        Blogpost.query.delete(synchronize_session="fetch")
        db.session.commit()


@pytest.mark.parametrize("editing", [False, True], ids=["create", "edit"])
@pytest.mark.parametrize(
    "fields, error",
    [
        pytest.param({"title": None}, "Title is too short!", id="missing-title"),
        pytest.param({"title": ""}, "Title is too short!", id="empty-title"),
        pytest.param(
            {"title": "!!!"},
            "Title must generate a nonempty slug!",
            id="punctuation-title",
        ),
        pytest.param(
            {"content": None}, "Blogpost is too short!", id="missing-content"
        ),
        pytest.param({"content": ""}, "Blogpost is too short!", id="empty-content"),
        pytest.param(
            {"title": None, "content": None, "tags": None},
            "Title is too short!",
            id="missing-fields",
        ),
        pytest.param(
            {"title": "Existing title"},
            "Blogpost title already exists!",
            id="duplicate-title",
        ),
        pytest.param(
            {"title": "Existing title!!!"},
            "Blogpost title already exists!",
            id="duplicate-slug",
        ),
    ],
)
def test_invalid_input_does_not_change_posts(
    test_client, authenticated_user, posts, editing, fields, error
):
    original, _ = posts
    url = f"/blog/editor/{original.id}" if editing else "/blog/editor"
    data = {"title": "Changed title", "tags": "changed,tags", "content": "Changed"}
    for field, value in fields.items():
        if value is None:
            data.pop(field)
        else:
            data[field] = value

    # Keep scalar snapshots: request statistics teardown commits the shared session.
    before = [
        (p.id, p.slug, p.title, p.tags, p.content, p.published, p.date_created)
        for p in Blogpost.query.order_by(Blogpost.id).all()
    ]
    response = test_client.post(url, data=data)

    db.session.expire_all()
    after = [
        (p.id, p.slug, p.title, p.tags, p.content, p.published, p.date_created)
        for p in Blogpost.query.order_by(Blogpost.id).all()
    ]
    assert response.status_code == 200
    assert error in response.text
    assert len(after) == len(before)
    assert after == before


@pytest.mark.parametrize("published", [False, True], ids=["draft", "published"])
@pytest.mark.parametrize("operation", ["create", "edit", "edit-own-title"])
def test_omitted_tags_are_saved_empty_and_render(
    test_client, authenticated_user, posts, operation, published
):
    original, _ = posts
    original_id = original.id
    title = original.title if operation == "edit-own-title" else "New title"
    slug = slugify(title)
    editing = operation != "create"
    url = f"/blog/editor/{original_id}" if editing else "/blog/editor"
    data = {"title": title, "content": "Updated content"}
    if published:
        data["published"] = "True"
    count = Blogpost.query.count()

    response = test_client.post(url, data=data)

    assert response.status_code == 302
    assert response.headers["Location"] == f"/blog/post/{slug}"
    db.session.expire_all()
    saved = Blogpost.query.filter_by(slug=slug).one()
    saved_id = saved.id
    assert saved.tags == ""
    assert saved.title == title
    assert saved.content == data["content"]
    assert saved.published == published
    assert Blogpost.query.count() == count + (0 if editing else 1)
    if editing:
        assert saved_id == original_id

    detail = test_client.get(response.headers["Location"])
    assert detail.status_code == 200
    assert f"<h1>{title}</h1>" in detail.text
    assert "Updated content" in detail.text
    cards = test_client.get("/blog/" if published else "/blog/editor")
    assert cards.status_code == 200
    assert f"<h3>{title}</h3>" in cards.text
    editor = test_client.get(f"/blog/editor/{saved_id}")
    assert editor.status_code == 200
    assert re.search(r'name="tags"\s+value=""', editor.text)


def test_existing_null_tags_render_publicly_without_writes(test_client, posts):
    original, _ = posts
    original.tags = None
    db.session.commit()
    post_id, slug, title = original.id, original.slug, original.title

    for url, heading in [("/blog/", "h3"), (f"/blog/post/{slug}", "h1")]:
        response = test_client.get(url)
        assert response.status_code == 200
        assert f"<{heading}>{title}</{heading}>" in response.text
        db.session.expire_all()
        assert Blogpost.query.filter_by(id=post_id).one().tags is None


def test_existing_null_tags_render_draft_editors_without_writes(
    test_client, authenticated_user, posts
):
    _, draft = posts
    draft.tags = None
    db.session.commit()
    post_id, title = draft.id, draft.title

    for url in ["/blog/editor", f"/blog/editor/{post_id}"]:
        response = test_client.get(url)
        assert response.status_code == 200
        assert f"<h3>{title}</h3>" in response.text
        assert re.search(r'name="tags"\s+value=""', response.text)
        db.session.expire_all()
        assert Blogpost.query.filter_by(id=post_id).one().tags is None
