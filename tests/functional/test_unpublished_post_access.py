from unittest.mock import Mock

import pytest
from slugify import slugify

from app.database import db
from app.database.models import Blogpost
from conftest import TEST_BLOGPOST


@pytest.fixture
def post_data():
    data = TEST_BLOGPOST.copy()
    data.update(
        title="Private post title sentinel",
        tags="private-tag-sentinel",
        content="**Private post body sentinel**",
    )
    data.pop("published")
    data.pop("slug", None)
    return data


@pytest.fixture
def saved_post(test_client, post_data):
    post = Blogpost(
        **post_data, slug=slugify(post_data["title"]), published=False
    )
    db.session.add(post)
    db.session.commit()
    yield post
    db.session.delete(post)
    db.session.commit()


@pytest.mark.parametrize("published", [False, None])
def test_private_post_is_indistinguishable_from_missing(
    test_client, saved_post, published, monkeypatch
):
    saved_post.published = published
    db.session.commit()
    render_markdown = Mock()
    monkeypatch.setattr("website.views.blog.markdown", render_markdown)

    response = test_client.get(f"/blog/post/{saved_post.slug}")
    missing = test_client.get("/blog/post/nonexistent-post-sentinel")

    assert response.status_code == missing.status_code == 404
    assert "Location" not in response.headers
    assert response.data == missing.data
    for value in (
        saved_post.title, saved_post.tags, saved_post.content, saved_post.slug,
        "Private post body sentinel",
    ):
        assert value not in response.text
    render_markdown.assert_not_called()


@pytest.mark.parametrize("published", [False, None])
def test_admin_can_preview_private_post(
    test_client, authenticated_user, saved_post, published
):
    saved_post.published = published
    db.session.commit()

    response = test_client.get(f"/blog/post/{saved_post.slug}")

    assert response.status_code == 200
    assert saved_post.title in response.text
    assert "<strong>Private post body sentinel</strong>" in response.text
    assert '<p class="metainfo">Draft</p>' in response.text
    assert f'href="/blog/editor/{saved_post.id}"' in response.text


@pytest.mark.parametrize("authenticated", [False, True])
def test_published_post_remains_accessible(
    test_client, saved_post, authenticated, request
):
    if authenticated:
        request.getfixturevalue("authenticated_user")
    saved_post.published = True
    db.session.commit()

    response = test_client.get(f"/blog/post/{saved_post.slug}")

    assert response.status_code == 200
    assert saved_post.title in response.text
    assert "<strong>Private post body sentinel</strong>" in response.text


@pytest.mark.parametrize("published", [False, None])
def test_private_post_is_absent_from_index(test_client, saved_post, published):
    saved_post.published = published
    db.session.commit()

    response = test_client.get("/blog/")

    assert response.status_code == 200
    for value in (saved_post.title, saved_post.tags, saved_post.slug):
        assert value not in response.text
    assert "Private post body sentinel" not in response.text


def test_new_draft_can_be_previewed_but_not_opened_anonymously(
    test_client, authenticated_user, post_data
):
    response = test_client.post("/blog/editor", data=post_data.copy())
    assert response.status_code == 302
    post = Blogpost.query.filter_by(slug=slugify(post_data["title"])).one()
    try:
        assert post.published is False
        url = response.headers["Location"]
        assert url.endswith(f"/blog/post/{post.slug}")
        preview = test_client.get(url)
        assert preview.status_code == 200
        assert "<strong>Private post body sentinel</strong>" in preview.text

        test_client.get("/auth/logout")
        response = test_client.get(url)
        assert response.status_code == 404
        assert post.title not in response.text
        assert "Private post body sentinel" not in response.text
    finally:
        db.session.delete(post)
        db.session.commit()


def test_unpublishing_blocks_the_old_public_url(
    test_client, saved_post, post_data, request
):
    saved_post.published = True
    db.session.commit()
    url = f"/blog/post/{saved_post.slug}"
    assert test_client.get(url).status_code == 200

    request.getfixturevalue("authenticated_user")
    response = test_client.post(
        f"/blog/editor/{saved_post.id}", data=post_data.copy()
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith(url)
    assert saved_post.published is False
    preview = test_client.get(url)
    assert preview.status_code == 200
    assert "<strong>Private post body sentinel</strong>" in preview.text

    test_client.get("/auth/logout")
    response = test_client.get(url)
    assert response.status_code == 404
    assert saved_post.title not in response.text
    assert "Private post body sentinel" not in response.text
