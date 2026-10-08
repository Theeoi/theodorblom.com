import pytest
from flask.testing import FlaskClient
from slugify import slugify
from sqlalchemy import select

from app.database import db
from app.database.models import Blogpost


class TestIndex:
    def test_blog(self, test_client: FlaskClient) -> None:
        response = test_client.get("/blog", follow_redirects=True)
        assert response.status_code == 200
        assert b"Blogposts" in response.get_data()
        assert b'<section id="blogposts"' in response.get_data()

    def test_blog_entry(
        self, test_client: FlaskClient, blogpost: Blogpost
    ) -> None:
        response = test_client.get("/blog", follow_redirects=True)
        assert response.status_code == 200
        assert f"<h3>{blogpost.title}</h3>" in response.text
        assert blogpost.date_created is not None
        assert (
            f'class="metainfo">{blogpost.date_created.date()}' in response.text
        )
        assert b'<div class="tags"' in response.get_data()


class TestPost:
    def test_post(self, test_client: FlaskClient, blogpost: Blogpost) -> None:
        response = test_client.get(f"/blog/post/{blogpost.slug}")
        assert response.status_code == 200
        assert b'<article class="blogpost"' in response.get_data()
        assert f"<h1>{blogpost.title}</h1>" in response.text
        assert b'<p class="tags"' in response.get_data()
        assert blogpost.date_created is not None
        assert (
            f'class="metainfo">Posted: {blogpost.date_created.date()}'
        ) in response.text
        assert b'<div id="content"' in response.get_data()

    @pytest.mark.usefixtures("authenticated_user")
    def test_post_admin(
        self, test_client: FlaskClient, blogpost: Blogpost
    ) -> None:
        response = test_client.get(f"/blog/post/{blogpost.slug}")
        assert response.status_code == 200
        assert f'href="/blog/editor/{blogpost.id}"' in response.text
        assert f'href="/blog/delete/{blogpost.id}"' in response.text

    def test_post_not_exist(self, test_client: FlaskClient) -> None:
        response = test_client.get("/blog/post/testing-slug")
        assert response.status_code == 302
        assert "/blog/" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"No blogpost with that slug exists." in response.get_data()

    def test_delete_redirect(
        self, test_client: FlaskClient, blogpost: Blogpost
    ) -> None:
        num_posts: int = len(db.session.scalars(select(Blogpost)).all())
        response = test_client.get(f"/blog/delete/{blogpost.id}")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]
        assert num_posts == len(db.session.scalars(select(Blogpost)).all())

    @pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SAWarning")
    @pytest.mark.usefixtures("authenticated_user")
    def test_delete_post(
        self, test_client: FlaskClient, blogpost: Blogpost
    ) -> None:
        response = test_client.get(f"/blog/delete/{blogpost.id}")
        assert response.status_code == 302
        assert "/blog/" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"Post successfully deleted." in response.get_data()
        assert (
            db.session.scalar(
                select(Blogpost).where(Blogpost.id == blogpost.id)
            )
            is None
        )

    @pytest.mark.usefixtures("authenticated_user")
    def test_delete_post_no_exist(self, test_client: FlaskClient) -> None:
        response = test_client.get("/blog/delete/1")
        assert response.status_code == 302
        assert "/blog/" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"Blogpost does not exist" in response.get_data()


class TestEditor:
    def test_editor_redirect(self, test_client: FlaskClient) -> None:
        response = test_client.get("/blog/editor")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    def test_editor_id_redirect(
        self, test_client: FlaskClient, blogpost: Blogpost
    ) -> None:
        response = test_client.get(f"/blog/editor/{blogpost.id}")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    @pytest.mark.usefixtures("authenticated_user")
    def test_editor_page(self, test_client: FlaskClient):
        response = test_client.get("/blog/editor")
        print(response.text)
        assert response.status_code == 200
        assert b"Create blogpost" in response.get_data()
        assert b'id="title"' in response.get_data()
        assert b'id="tags"' in response.get_data()
        assert b"<textarea" in response.get_data()
        assert b'<label for="published"' in response.get_data()
        assert b'<input type="submit" id="create-post"' in response.get_data()
        assert b"Drafts" in response.get_data()

    @pytest.mark.usefixtures("authenticated_user")
    def test_create_post(
        self,
        test_client: FlaskClient,
        test_blogpost: dict[str, object],
    ):
        slug = slugify(str(test_blogpost["title"]))
        response = test_client.post("/blog/editor", data=test_blogpost)
        assert response.status_code == 302
        assert f"/blog/post/{slug}" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"Blogpost created!" in response.get_data()
        assert (
            db.session.scalar(select(Blogpost).where(Blogpost.slug == slug))
            is not None
        )

    @pytest.mark.usefixtures("authenticated_user")
    def test_create_duplicate_post(
        self,
        test_client: FlaskClient,
        test_blogpost: dict[str, object],
    ):
        response = test_client.post("/blog/editor", data=test_blogpost)
        assert response.status_code == 200
        assert b"Blogpost title already exists!" in response.get_data()
        assert b"Create blogpost" in response.get_data()
        _ = test_client.get("/blog/delete/1")

    @pytest.mark.usefixtures("authenticated_user")
    def test_create_post_short_title(
        self,
        test_client: FlaskClient,
        test_blogpost: dict[str, object],
    ) -> None:
        DATA: dict[str, str | object] = {
            "title": "",
            "tags": test_blogpost["tags"],
            "content": test_blogpost["content"],
            "published": test_blogpost["published"],
        }
        response = test_client.post("/blog/editor", data=DATA)
        assert response.status_code == 200
        assert b"Title is too short!" in response.get_data()
        assert b"Create blogpost" in response.get_data()

    @pytest.mark.usefixtures("authenticated_user")
    def test_create_post_short_content(
        self,
        test_client: FlaskClient,
        test_blogpost: dict[str, object],
    ) -> None:
        DATA: dict[str, str | object] = {
            "title": "A new test title",
            "tags": test_blogpost["tags"],
            "content": "",
            "published": test_blogpost["published"],
        }
        response = test_client.post("/blog/editor", data=DATA)
        assert response.status_code == 200
        assert b"Blogpost is too short!" in response.get_data()
        assert b"Create blogpost" in response.get_data()

    @pytest.mark.usefixtures("authenticated_user")
    def test_edit_post_no_exist(self, test_client: FlaskClient) -> None:
        response = test_client.get("/blog/editor/1")
        assert response.status_code == 302
        assert "/blog" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"Blogpost does not exist" in response.get_data()

    @pytest.mark.usefixtures("authenticated_user")
    def test_edit_post_get(
        self, test_client: FlaskClient, blogpost: Blogpost
    ) -> None:
        response = test_client.get(f"/blog/editor/{blogpost.id}")
        assert response.status_code == 200
        assert f'value="{blogpost.title}"' in response.text
        assert f'value="{blogpost.tags}"' in response.text
        assert f"{blogpost.content}</textarea" in response.text

    @pytest.mark.usefixtures("authenticated_user")
    def test_edit_post_post(
        self, test_client: FlaskClient, blogpost: Blogpost
    ) -> None:
        DATA = {
            "title": blogpost.title,
            "tags": blogpost.tags,
            "content": f"{blogpost.content} Now with an edit!",
            "published": blogpost.published,
        }
        slug = slugify(str(DATA["title"]))
        response = test_client.post(f"/blog/editor/{blogpost.id}", data=DATA)
        assert response.status_code == 302
        assert f"/blog/post/{slug}" in response.headers["Location"]
        response = test_client.get(response.headers["Location"])
        assert response.status_code == 200
        assert b"Blogpost edited!" in response.get_data()
        assert b"Now with an edit!" in response.get_data()

    @pytest.mark.usefixtures("authenticated_user")
    def test_post_markdown_overwrite(
        self, test_client: FlaskClient, blogpost: Blogpost
    ) -> None:
        _ = test_client.get(f"/blog/post/{blogpost.slug}")
        response = test_client.get(f"/blog/editor/{blogpost.id}")
        assert response.status_code == 200
        assert "<p>" not in blogpost.content
