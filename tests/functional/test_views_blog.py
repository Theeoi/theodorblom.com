#!/usr/bin/env python

import pytest
from markupsafe import escape
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
    @pytest.mark.parametrize("url", ["/blog/", "/blog/post/{slug}"])
    def test_post_metadata_is_escaped(self, test_client, blogpost, url):
        blogpost.title = '<b title="title">Title & \'quotes\'</b>'
        blogpost.tags = '<i title="tag">Tag & \'quotes\'</i>'
        db.session.commit()

        response = test_client.get(url.format(slug=blogpost.slug))
        assert response.status_code == 200
        for value in (blogpost.title, blogpost.tags):
            assert str(escape(value)) in response.text
            assert value not in response.text

    def test_post_markdown_still_renders_html(self, test_client, blogpost):
        blogpost.content = "**Bold** & text\n\n`<example>`"
        db.session.commit()

        response = test_client.get(f"/blog/post/{blogpost.slug}")
        assert response.status_code == 200
        assert "<strong>Bold</strong> &amp; text" in response.text
        assert "<code>&lt;example&gt;</code>" in response.text
        assert "&lt;strong&gt;" not in response.text

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
        assert response.status_code == 302
        assert "/blog/" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"No blogpost with that slug exists." in response.data

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
    def test_editor_values_are_escaped(
        self, test_client, authenticated_user, blogpost
    ):
        blogpost.title = 'Title " data-marker="injected" & \'quotes\' <b>'
        blogpost.tags = 'Tag " data-marker="injected" & \'quotes\' <i>'
        blogpost.content = '</textarea><b title="marker">Text & \'quotes\'</b>'
        db.session.commit()

        response = test_client.get(f"/blog/editor/{blogpost.id}")
        assert response.status_code == 200
        for value in (blogpost.title, blogpost.tags):
            assert f'value="{escape(value)}"' in response.text
        assert f"{escape(blogpost.content)}</textarea>" in response.text
        assert 'data-marker="injected"' not in response.text
        assert response.text.count("</textarea>") == 1

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
