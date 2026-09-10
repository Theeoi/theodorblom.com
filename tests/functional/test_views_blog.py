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


class TestEditorInput:
    @pytest.fixture
    def editable_post(self, test_client):
        post = Blogpost(
            slug="editor-input",
            title="Editor input",
            tags="stored",
            content="Stored content",
            published=False,
        )
        db.session.add(post)
        db.session.commit()
        yield post
        db.session.delete(post)
        db.session.commit()

    def test_create_defaults(self, test_client, authenticated_user):
        response = test_client.get("/blog/editor")

        assert response.status_code == 200
        assert 'name="title"\n               value=""' in response.text
        assert 'name="tags"\n               value=""' in response.text
        assert 'onfocus="this.placeholder=\'\'">\n</textarea>' in response.text
        assert 'name="published"\n            value="True"' in response.text
        assert 'checked="checked"' not in response.text

    @pytest.mark.parametrize(
        "tags,published", [('"tags" & <tags>', False), ("", True), (None, True)]
    )
    def test_edit_stored_values(
        self, test_client, authenticated_user, blogpost, tags, published
    ):
        title = 'Stored "quotes" & <title>'
        content = '\n# Markdown\n"quotes" &amp; </textarea><script>stored</script>\n'
        # Keep NULL tags out of draft cards; their rendering belongs to #78.
        blogpost.title, blogpost.content = title, content
        blogpost.tags, blogpost.published = tags, published
        db.session.commit()

        response = test_client.get(f"/blog/editor/{blogpost.id}")

        assert response.status_code == 200
        assert f'name="title"\n               value="{escape(title)}"' in response.text
        assert f'name="tags"\n               value="{escape(tags or "")}"' in response.text
        assert (
            f'onfocus="this.placeholder=\'\'">\n{escape(content)}</textarea>'
            in response.text
        )
        assert 'name="published"\n            value="True"' in response.text
        assert ('checked="checked"' in response.text) == published
        assert db.session.query(Blogpost.tags).filter_by(id=blogpost.id).scalar() == tags

    @pytest.mark.parametrize("editing", [False, True], ids=["create", "edit"])
    @pytest.mark.parametrize(
        "duplicate,published,tags",
        [
            (True, True, '"tags" & <tags>'),
            (True, False, None),
            (False, True, ""),
            (False, False, ""),
        ],
        ids=[
            "duplicate-checked", "duplicate-unchecked-omitted-tags",
            "empty-title-checked", "empty-title-unchecked-empty-content",
        ],
    )
    def test_rejected_then_corrected(
        self, test_client, authenticated_user, blogpost, editable_post,
        editing, duplicate, published, tags,
    ):
        editable_post.published = not published
        db.session.commit()
        # Scalar snapshots catch accidental writes by the statistics teardown commit.
        posts = db.session.query(
            Blogpost.id,
            Blogpost.slug,
            Blogpost.title,
            Blogpost.tags,
            Blogpost.content,
            Blogpost.published,
            Blogpost.date_created,
        ).order_by(Blogpost.id)
        before = posts.all()
        url = f"/blog/editor/{editable_post.id}" if editing else "/blog/editor"
        title = blogpost.title + ' "!"' if duplicate else ""
        content = (
            '\n# Attempted Markdown\n"quotes" &amp; '
            '</textarea><script>attempted</script>\n'
        )
        if not duplicate and not published:
            content = ""  # Rejected for its title, not a blank-content policy.
        data = dict(title=title, content=content)
        if tags is not None:
            data["tags"] = tags
        if published:
            data["published"] = "True"

        response = test_client.post(url, data=data)

        assert response.status_code == 200
        message = "Blogpost title already exists!" if duplicate else "Title is too short!"
        assert message in response.text
        assert f'name="title"\n               value="{escape(title)}"' in response.text
        assert f'name="tags"\n               value="{escape(tags or "")}"' in response.text
        assert (
            f'onfocus="this.placeholder=\'\'">\n{escape(content)}</textarea>'
            in response.text
        )
        assert 'name="published"\n            value="True"' in response.text
        assert ('checked="checked"' in response.text) == published
        assert posts.all() == before

        response = test_client.get(url)
        assert response.status_code == 200
        stored_title = "Editor input" if editing else ""
        assert f'name="title"\n               value="{stored_title}"' in response.text
        assert ('checked="checked"' in response.text) == (editing and not published)
        assert posts.all() == before

        data.update(title='Editor input corrected "quotes"', tags=tags or "")
        data["content"] = content or "Corrected content"
        response = test_client.post(url, data=data)
        saved = Blogpost.query.filter_by(slug=slugify(data["title"])).one_or_none()
        try:
            assert response.status_code == 302
            assert response.headers["Location"] == "/blog/post/" + slugify(data["title"])
            assert saved is not None
            assert (saved.title, saved.tags, saved.content, saved.published) == (
                data["title"], data["tags"], data["content"], published,
            )
            assert Blogpost.query.count() == len(before) + (0 if editing else 1)
            if editing:
                assert saved.id == editable_post.id
            assert [row for row in posts.all() if row.id != saved.id] == [
                row for row in before if row.id != saved.id
            ]
        finally:
            if not editing and saved is not None:
                db.session.delete(saved)
                db.session.commit()
