from html.parser import HTMLParser
from uuid import uuid4

import pytest
from slugify import slugify

from app.database import db
from app.database.models import Blogpost


class EditorForm(HTMLParser):
    """Read actual editor controls, decoding HTML entities as a browser would."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.values = {}
        self.in_form = False
        self.in_content = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.in_form = attrs.get("class") == "blog-form"
        if not self.in_form:
            return
        if tag == "input" and attrs.get("name") in ("title", "tags", "published"):
            name = attrs["name"]
            assert name not in self.values
            self.values[name] = (
                "checked" in attrs if name == "published" else attrs["value"]
            )
        if tag == "textarea" and attrs.get("name") == "content":
            assert "content" not in self.values
            self.values["content"] = ""
            self.in_content = True

    def handle_data(self, data):
        if self.in_content:
            self.values["content"] += data

    def handle_endtag(self, tag):
        if tag == "textarea" and self.in_content:
            # HTML ignores the first newline immediately after <textarea>.
            if self.values["content"].startswith("\n"):
                self.values["content"] = self.values["content"][1:]
            self.in_content = False
        if tag == "form":
            self.in_form = False


@pytest.fixture
def editor_posts(test_client, authenticated_user):
    prefix = "issue-79-" + uuid4().hex
    stored = {
        "title": prefix + ' stored "quotes" & <title>',
        "tags": 'stored, "quotes", <tags>, &amp;',
        "content": '\n# Stored Markdown\n\n"Quotes" &amp; </textarea><script>stored</script>\n',
        "published": False,
    }
    original = Blogpost(slug=slugify(stored["title"]), **stored)
    duplicate = Blogpost(
        slug=prefix + "-duplicate",
        title=prefix + " duplicate",
        tags="duplicate",
        content="Existing content",
        published=True,
    )
    db.session.add_all([original, duplicate])
    db.session.commit()
    try:
        yield prefix, original.id, duplicate.title, stored
    finally:
        db.session.rollback()
        Blogpost.query.filter(Blogpost.slug.startswith(prefix)).delete(
            synchronize_session=False
        )
        db.session.commit()


def post_snapshot():
    # Scalar rows cannot silently change with ORM objects during request teardown.
    return [
        tuple(row)
        for row in db.session.query(
            Blogpost.id,
            Blogpost.slug,
            Blogpost.title,
            Blogpost.tags,
            Blogpost.content,
            Blogpost.published,
            Blogpost.date_created,
        )
        .order_by(Blogpost.id)
        .all()
    ]


def test_new_editor_defaults(test_client, editor_posts):
    response = test_client.get("/blog/editor")

    assert response.status_code == 200
    assert EditorForm(response.text).values == {
        "title": "",
        "tags": "",
        "content": "",
        "published": False,
    }


@pytest.mark.parametrize("published", [False, True])
def test_edit_editor_stored_values(test_client, editor_posts, published):
    _, post_id, _, stored = editor_posts
    Blogpost.query.filter_by(id=post_id).update({"published": published})
    db.session.commit()
    before = post_snapshot()

    response = test_client.get(f"/blog/editor/{post_id}")

    assert response.status_code == 200
    assert EditorForm(response.text).values == dict(stored, published=published)
    assert post_snapshot() == before


def test_edit_editor_null_tags(test_client, editor_posts):
    _, post_id, _, stored = editor_posts
    # Keep NULL tags out of draft cards, whose rendering is outside this issue.
    Blogpost.query.filter_by(id=post_id).update({"tags": None, "published": True})
    db.session.commit()
    before = post_snapshot()

    response = test_client.get(f"/blog/editor/{post_id}")

    assert response.status_code == 200
    assert EditorForm(response.text).values == dict(stored, tags="", published=True)
    assert post_snapshot() == before


@pytest.mark.parametrize("editing", [False, True], ids=["create", "edit"])
def test_rejected_editor_omitted_tags(test_client, editor_posts, editing):
    _, post_id, duplicate_title, _ = editor_posts
    before = post_snapshot()
    data = {"title": duplicate_title, "content": "# Attempted content\n"}
    url = f"/blog/editor/{post_id}" if editing else "/blog/editor"

    response = test_client.post(url, data=data)

    assert response.status_code == 200
    assert "Blogpost title already exists!" in response.text
    assert EditorForm(response.text).values == dict(data, tags="", published=False)
    assert post_snapshot() == before


@pytest.mark.parametrize("editing", [False, True], ids=["create", "edit"])
@pytest.mark.parametrize("published", [False, True], ids=["unchecked", "checked"])
@pytest.mark.parametrize("empty_tags", [False, True], ids=["tags", "empty-tags"])
@pytest.mark.parametrize(
    "rejection, message",
    [
        ("duplicate", "Blogpost title already exists!"),
        ("empty-title", "Title is too short!"),
        ("empty-content", "Blogpost is too short!"),
    ],
)
def test_rejected_editor_input(
    test_client, editor_posts, editing, published, empty_tags, rejection, message
):
    prefix, post_id, duplicate_title, stored = editor_posts
    stored = dict(stored, published=not published)
    Blogpost.query.filter_by(id=post_id).update({"published": stored["published"]})
    db.session.commit()
    before = post_snapshot()
    values = {
        "title": prefix + ' attempted "quotes" & <title>',
        "tags": "" if empty_tags else 'attempted, "quotes", <tags>, &amp;',
        "content": '\n# Attempted Markdown\n\n"Quotes" &amp; </textarea><script>attempted</script>\n',
        "published": published,
    }
    if rejection == "duplicate":
        # Different title, same slug: exercise the actual uniqueness rule.
        values["title"] = duplicate_title + ' "!"'
    elif rejection == "empty-title":
        values["title"] = ""
    else:
        values["content"] = ""
    data = {key: value for key, value in values.items() if key != "published"}
    if published:
        data["published"] = "True"
    url = f"/blog/editor/{post_id}" if editing else "/blog/editor"

    response = test_client.post(url, data=data)

    assert response.status_code == 200
    assert message in response.text
    assert EditorForm(response.text).values == values
    assert post_snapshot() == before

    response = test_client.get(url)
    assert response.status_code == 200
    assert EditorForm(response.text).values == (
        stored if editing else dict(title="", tags="", content="", published=False)
    )
    assert post_snapshot() == before

    if rejection in ("duplicate", "empty-title"):
        values["title"] = prefix + ' corrected "quotes" & <title>'
    else:
        values["content"] = '\n# Corrected Markdown\n\n"Quotes" &amp; </textarea>\n'
    data.update(title=values["title"], content=values["content"])

    response = test_client.post(url, data=data)

    assert response.status_code == 302
    assert response.headers["Location"] == "/blog/post/" + slugify(values["title"])
    saved = (
        db.session.query(
            Blogpost.id, Blogpost.title, Blogpost.tags, Blogpost.content, Blogpost.published
        )
        .filter_by(slug=slugify(values["title"]))
        .one()
    )
    assert dict(zip(("title", "tags", "content", "published"), saved[1:])) == values
    assert Blogpost.query.count() == len(before) + (0 if editing else 1)
    if editing:
        assert saved.id == post_id
    assert [row for row in post_snapshot() if row[0] != saved.id] == [
        row for row in before if row[0] != saved.id
    ]

    response = test_client.get(f"/blog/editor/{saved.id}")
    assert response.status_code == 200
    assert EditorForm(response.text).values == values
