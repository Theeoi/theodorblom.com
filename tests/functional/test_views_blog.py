#!/usr/bin/env python

import re

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


class TestBlogpostValidation:
    """Exercise form policy through real requests, persistence, and rendering."""

    @pytest.fixture
    def posts(self, test_client):
        """Own only these posts; the module-scoped database serves other tests."""
        posts = [
            Blogpost(**dict(
                TEST_BLOGPOST, title=title, slug=slugify(title), published=published
            ))
            for title, published in [
                ("Validation original", True),
                ("Validation existing", False),
            ]
        ]
        db.session.add_all(posts)
        db.session.commit()
        ids = [post.id for post in posts]
        try:
            yield posts
        finally:
            db.session.rollback()
            Blogpost.query.filter(
                (Blogpost.id.in_(ids)) | (Blogpost.slug == "validation-new")
            ).delete(synchronize_session="fetch")
            db.session.commit()

    @pytest.mark.parametrize("editing", [False, True], ids=["create", "edit"])
    @pytest.mark.parametrize(
        "fields, error",
        [
            pytest.param({"title": None}, "Title is too short!", id="missing-title"),
            pytest.param({"title": ""}, "Title is too short!", id="empty-title"),
            pytest.param(
                {"title": "!!!"}, "Title must generate a nonempty slug!",
                id="punctuation-title",
            ),
            pytest.param(
                {"title": None, "content": None, "tags": None},
                "Title is too short!", id="missing-fields",
            ),
            pytest.param(
                {"title": "Validation existing"},
                "Blogpost title already exists!", id="duplicate-title",
            ),
            pytest.param(
                {"title": "Validation existing!!!"},
                "Blogpost title already exists!", id="duplicate-slug",
            ),
        ],
    )
    def test_invalid_input_does_not_change_posts(
        self, test_client, authenticated_user, posts, editing, fields, error
    ):
        """Rejected titles must neither insert posts nor mutate any saved fields."""
        url = f"/blog/editor/{posts[0].id}" if editing else "/blog/editor"
        data = dict(title="Validation new", tags="changed,tags", content="Changed")
        data.update(fields)
        data = {key: value for key, value in data.items() if value is not None}

        def snapshot():
            # Scalar rows avoid shared ORM objects masking teardown-time commits.
            db.session.expire_all()
            return Blogpost.query.with_entities(
                *Blogpost.__table__.columns
            ).order_by(Blogpost.id).all()

        before = snapshot()
        response = test_client.post(url, data=data)

        assert response.status_code == 200
        assert error in response.text
        assert snapshot() == before

    @pytest.mark.parametrize("published", [False, True], ids=["draft", "published"])
    @pytest.mark.parametrize("operation", ["create", "edit", "edit-own-title"])
    @pytest.mark.parametrize(
        "content", ["Updated content", "", None],
        ids=["content", "blank-content", "omitted-content"],
    )
    def test_optional_fields_are_saved_and_render(
        self, test_client, authenticated_user, posts, operation, published, content
    ):
        """Blank/omitted content and omitted tags are valid, including own-title edits."""
        original = posts[0]
        original_id = original.id
        title = original.title if operation == "edit-own-title" else "Validation new"
        slug = slugify(title)
        editing = operation != "create"
        url = f"/blog/editor/{original_id}" if editing else "/blog/editor"
        data = {"title": title}
        if content is not None:
            data["content"] = content
        if published:
            data["published"] = "True"
        count = Blogpost.query.count()

        response = test_client.post(url, data=data)

        assert response.status_code == 302
        assert response.headers["Location"] == f"/blog/post/{slug}"
        db.session.expire_all()
        saved = Blogpost.query.filter_by(slug=slug).one()
        saved_id = saved.id
        assert (saved.title, saved.tags, saved.content, saved.published) == (
            title, "", content or "", published
        )
        assert Blogpost.query.count() == count + (0 if editing else 1)
        if editing:
            assert saved_id == original_id

        detail = test_client.get(response.headers["Location"])
        assert detail.status_code == 200
        assert f"<h1>{title}</h1>" in detail.text
        if content:
            assert content in detail.text
        cards = test_client.get("/blog/" if published else "/blog/editor")
        assert cards.status_code == 200
        assert f"<h3>{title}</h3>" in cards.text
        editor = test_client.get(f"/blog/editor/{saved_id}")
        assert editor.status_code == 200
        assert re.search(r'name="tags"\s+value=""', editor.text)

    def test_existing_null_tags_render_publicly_without_writes(self, test_client, posts):
        """Legacy NULL tags must render publicly without silently repairing data."""
        original = posts[0]
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
        self, test_client, authenticated_user, posts
    ):
        """Draft cards and editor fields tolerate NULL tags without database writes."""
        draft = posts[1]
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
