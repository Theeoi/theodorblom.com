"""Views for the /blog url."""

from collections.abc import Sequence

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from markdown import markdown
from slugify import slugify
from sqlalchemy import select

from app.database import db
from app.database.models import Blogpost

blog = Blueprint("blog", __name__, url_prefix="/blog")


@blog.route("/")
def index():
    """Definition of the /blog site."""
    blogposts: Sequence[Blogpost] = db.session.scalars(
        select(Blogpost).where(Blogpost.published.is_(True))
    ).all()

    return render_template(
        "pages/blog/index.html.jinja", user=current_user, blogposts=blogposts
    )


@blog.route("/editor", methods=["GET", "POST"])
@login_required
def create_post():
    """Definition of the /blog/editor site."""
    drafts: Sequence[Blogpost] = db.session.scalars(
        select(Blogpost).where(Blogpost.published.is_(False))
    ).all()

    if request.method == "POST":
        title = request.form.get("title", "")
        tags = request.form.get("tags", "")
        content = request.form.get("content", "")
        published = bool(request.form.get("published"))

        slug = slugify(title)

        slug_exists: Blogpost | None = db.session.scalar(
            select(Blogpost).where(Blogpost.slug == slug)
        )

        if slug_exists:
            flash("Blogpost title already exists!", category="error")
            current_app.logger.warning(
                "Attempted to create duplicate blogpost!"
            )
        elif len(title) < 1:
            flash("Title is too short!", category="error")
        elif len(content) < 1:
            flash("Blogpost is too short!", category="error")
        else:
            new_post = Blogpost()
            new_post.slug = slug
            new_post.title = title
            new_post.tags = tags
            new_post.content = content
            new_post.published = published

            db.session.add(new_post)
            db.session.commit()
            flash("Blogpost created!", category="success")
            current_app.logger.info(
                f"Blogpost with id {new_post.id} was created."
            )
            return redirect(url_for("blog.post", slug=slug))

    return render_template(
        "pages/blog/editor.html.jinja",
        user=current_user,
        blogpost=None,
        blogposts=drafts,
    )


@blog.route("/editor/<id>", methods=["GET", "POST"])
@login_required
def edit_post(id: int):
    """
    Definition of the /blog/editor/<id> slug.

    Opens the editor with the content of blogpost with the given <id>.
    """
    blogpost: Blogpost | None = db.session.scalar(
        select(Blogpost).where(Blogpost.id == id)
    )
    drafts: Sequence[Blogpost] = db.session.scalars(
        select(Blogpost).where(Blogpost.published.is_(False))
    ).all()

    if not blogpost:
        flash(
            "Blogpost does not exist and can not be edited.", category="error"
        )
        return redirect(url_for("blog.index"))
    else:
        if request.method == "POST":
            title = request.form.get("title", "")
            tags = request.form.get("tags", "")
            content = request.form.get("content", "")
            published = bool(request.form.get("published"))

            slug = slugify(title)

            slug_exists: Blogpost | None = db.session.scalar(
                select(Blogpost).where(Blogpost.slug == slug)
            )

            if slug_exists and slug_exists.id != blogpost.id:
                flash("Blogpost title already exists!", category="error")
                current_app.logger.warning(
                    "Attempted to create duplicate blogpost!"
                )
            elif len(title) < 1:
                flash("Title is too short!", category="error")
            elif len(content) < 1:
                flash("Blogpost is too short!", category="error")
            else:
                blogpost.slug = slug
                blogpost.title = title
                blogpost.tags = tags
                blogpost.content = content
                blogpost.published = published

                db.session.add(blogpost)
                db.session.commit()
                flash("Blogpost edited!", category="success")
                current_app.logger.info(
                    f"Blogpost with id {blogpost.id} was edited."
                )
                return redirect(url_for("blog.post", slug=blogpost.slug))

    return render_template(
        "pages/blog/editor.html.jinja",
        user=current_user,
        blogpost=blogpost,
        blogposts=drafts,
    )


@blog.route("/delete/<id>")
@login_required
def delete_post(id: int):
    """
    Definition of the /blog/delete/<id> slug.

    Deletes blogpost with the given <id>.
    """
    blogpost: Blogpost | None = db.session.scalar(
        select(Blogpost).where(Blogpost.id == id)
    )

    if not blogpost:
        flash(
            "Blogpost does not exist and could not be deleted.",
            category="error",
        )
        current_app.logger.warning(
            "Deletion of non-existing blogpost was attempted."
        )
    else:
        db.session.delete(blogpost)
        db.session.commit()
        flash("Post successfully deleted.", category="success")
        current_app.logger.info(f"Blogpost with id {blogpost.id} was deleted.")

    return redirect(url_for("blog.index"))


@blog.route("/post/<slug>")
def post(slug: str):
    """
    Definition of the /blog/post/<slug> site.

    This is where the blogpost with the specified slug is viewed.
    """
    blogpost: Blogpost | None = db.session.scalar(
        select(Blogpost).where(Blogpost.slug == slug)
    )

    if not blogpost:
        flash("No blogpost with that slug exists.", category="error")
        return redirect(url_for("blog.index"))

    html = markdown(
        blogpost.content or "",
        extensions=["toc", "fenced_code", "codehilite", "sane_lists"],
    )

    return render_template(
        "pages/blog/post.html.jinja",
        user=current_user,
        blogpost=blogpost,
        html=html,
    )
