#!/usr/bin/env python

from unittest.mock import Mock

import pytest
from slugify import slugify
from conftest import TEST_BLOGPOST
from app.database import db
from app.database.models import Blogpost


class TestIndex:
    def test_blog(self, test_client):
        response = test_client.get("/blog", follow_redirects=True)
        assert response.status_code == 200
        assert b"Blogposts" in response.data
        assert b'<section id="blogposts"' in response.data

    def test_blog_entry(self, test_client, blogpost):
        response = test_client.get("/blog", follow_redirects=True)
        assert response.status_code == 200
        assert f"<h3>{blogpost.title}</h3>" in response.text
        assert f'class="metainfo">{blogpost.date_created.date()}' in response.text
        assert b'<div class="tags"' in response.data


class TestPost:
    def test_post(self, test_client, blogpost):
        response = test_client.get(f"/blog/post/{blogpost.slug}")
        assert response.status_code == 200
        assert b'<article class="blogpost"' in response.data
        assert f"<h1>{blogpost.title}</h1>" in response.text
        assert b'<p class="tags"' in response.data
        assert (
            f'class="metainfo">Posted: ' f"{blogpost.date_created.date()}"
        ) in response.text
        assert b'<div id="content"' in response.data

    def test_post_admin(self, test_client, authenticated_user, blogpost):
        response = test_client.get(f"/blog/post/{blogpost.slug}")
        assert response.status_code == 200
        assert f'href="/blog/editor/{blogpost.id}"' in response.text
        assert f'href="/blog/delete/{blogpost.id}"' in response.text

    def test_post_not_exist(self, test_client):
        response = test_client.get("/blog/post/testing-slug")
        assert response.status_code == 404
        assert "Location" not in response.headers

    def test_delete_redirect(self, test_client, blogpost):
        num_posts = len(Blogpost.query.all())
        response = test_client.get(f"/blog/delete/{blogpost.id}")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]
        assert num_posts == len(Blogpost.query.all())

    @pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SAWarning")
    def test_delete_post(self, test_client, authenticated_user, blogpost):
        response = test_client.get(f"/blog/delete/{blogpost.id}")
        assert response.status_code == 302
        assert "/blog/" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"Post successfully deleted." in response.data
        assert Blogpost.query.filter_by(id=blogpost.id).first() is None

    def test_delete_post_no_exist(self, test_client, authenticated_user):
        response = test_client.get("/blog/delete/1")
        assert response.status_code == 302
        assert "/blog/" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"Blogpost does not exist" in response.data


class TestEditor:
    def test_editor_redirect(self, test_client):
        response = test_client.get("/blog/editor")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    def test_editor_id_redirect(self, test_client, blogpost):
        response = test_client.get(f"/blog/editor/{blogpost.id}")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    def test_editor_page(self, test_client, authenticated_user):
        response = test_client.get("/blog/editor")
        print(response.text)
        assert response.status_code == 200
        assert b"Create blogpost" in response.data
        assert b'id="title"' in response.data
        assert b'id="tags"' in response.data
        assert b"<textarea" in response.data
        assert b'<label for="published"' in response.data
        assert b'<input type="submit" id="create-post"' in response.data
        assert b"Drafts" in response.data

    def test_create_post(self, test_client, authenticated_user):
        slug = slugify(TEST_BLOGPOST["title"])
        response = test_client.post("/blog/editor", data=TEST_BLOGPOST)
        assert response.status_code == 302
        assert f"/blog/post/{slug}" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"Blogpost created!" in response.data
        assert Blogpost.query.filter_by(slug=slug).first() is not None

    def test_create_duplicate_post(self, test_client, authenticated_user):
        response = test_client.post("/blog/editor", data=TEST_BLOGPOST)
        assert response.status_code == 200
        assert b"Blogpost title already exists!" in response.data
        assert b"Create blogpost" in response.data
        test_client.get("/blog/delete/1")

    def test_create_post_short_title(self, test_client, authenticated_user):
        DATA = {
            "title": "",
            "tags": TEST_BLOGPOST["tags"],
            "content": TEST_BLOGPOST["content"],
            "published": TEST_BLOGPOST["published"],
        }
        response = test_client.post("/blog/editor", data=DATA)
        assert response.status_code == 200
        assert b"Title is too short!" in response.data
        assert b"Create blogpost" in response.data

    def test_create_post_short_content(self, test_client, authenticated_user):
        DATA = {
            "title": "A new test title",
            "tags": TEST_BLOGPOST["tags"],
            "content": "",
            "published": TEST_BLOGPOST["published"],
        }
        response = test_client.post("/blog/editor", data=DATA)
        assert response.status_code == 200
        assert b"Blogpost is too short!" in response.data
        assert b"Create blogpost" in response.data

    def test_edit_post_no_exist(self, test_client, authenticated_user):
        response = test_client.get("/blog/editor/1")
        assert response.status_code == 302
        assert "/blog" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"Blogpost does not exist" in response.data

    def test_edit_post_get(self, test_client, authenticated_user, blogpost):
        response = test_client.get(f"/blog/editor/{blogpost.id}")
        assert response.status_code == 200
        assert f'value="{blogpost.title}"' in response.text
        assert f'value="{blogpost.tags}"' in response.text
        assert f"{blogpost.content}</textarea" in response.text

    def test_edit_post_post(self, test_client, authenticated_user, blogpost):
        DATA = {
            "title": blogpost.title,
            "tags": blogpost.tags,
            "content": f"{blogpost.content} Now with an edit!",
            "published": blogpost.published,
        }
        slug = slugify(DATA["title"])
        response = test_client.post(f"/blog/editor/{blogpost.id}", data=DATA)
        assert response.status_code == 302
        assert f"/blog/post/{slug}" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"Blogpost edited!" in response.data
        assert b"Now with an edit!" in response.data

    def test_post_markdown_overwrite(self, test_client, authenticated_user, blogpost):
        test_client.get(f"/blog/post/{blogpost.slug}")
        response = test_client.get(f"/blog/editor/{blogpost.id}")
        assert response.status_code == 200
        assert "<p>" not in blogpost.content


class TestPostAccess:
    """Exercise publication rules through requests, auth, the DB, and templates."""

    @pytest.fixture
    def post_data(self):
        data = TEST_BLOGPOST.copy()
        data.update(
            title="Private post title sentinel",
            tags="private-tag-sentinel",
            content="**Private post body sentinel**",
        )
        # Unchecked editor checkboxes are omitted; ignore shared-fixture slugs.
        data.pop("published")
        data.pop("slug", None)
        return data

    @pytest.fixture
    def saved_post(self, test_client, post_data):
        """Own one distinct post without disturbing the module's other posts."""
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
        self, test_client, saved_post, published, monkeypatch
    ):
        """False and NULL must reveal neither a post's existence nor its content."""
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
        # Denied requests must stop before processing private Markdown.
        render_markdown.assert_not_called()

    @pytest.mark.parametrize("published", [False, None])
    def test_admin_can_preview_private_post(
        self, test_client, authenticated_user, saved_post, published
    ):
        """Both private states retain rendered admin previews and editor links."""
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
        self, test_client, saved_post, authenticated, request
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
    def test_private_post_is_absent_from_index(
        self, test_client, saved_post, published
    ):
        """The public listing must not disclose private metadata or excerpts."""
        saved_post.published = published
        db.session.commit()

        response = test_client.get("/blog/")

        assert response.status_code == 200
        for value in (saved_post.title, saved_post.tags, saved_post.slug):
            assert value not in response.text
        assert "Private post body sentinel" not in response.text

    def test_new_draft_can_be_previewed_but_not_opened_anonymously(
        self, test_client, authenticated_user, post_data
    ):
        """An editor-created draft's preview URL must become private on logout."""
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
        self, test_client, saved_post, post_data, request
    ):
        """Unpublishing revokes public access even when the slug is already known."""
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
