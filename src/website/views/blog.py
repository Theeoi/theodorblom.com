#!/usr/bin/env python
"""Views for the /blog url."""

from app.database.models import Blogpost
from app.database import db
from slugify import slugify
from markdown import markdown
from flask_login import current_user, login_required
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)

blog = Blueprint("blog", __name__, url_prefix="/blog")


def _validated_post_form(blogpost=None):
    """Return normalized fields, or flash a validation error and return None."""
    title = request.form.get("title", "")
    slug = slugify(title)
    slug_exists = Blogpost.query.filter_by(slug=slug).first()

    if not title:
        flash("Title is too short!", category="error")
        return None
    if not slug:
        flash("Title must generate a nonempty slug!", category="error")
        return None
    if slug_exists and (blogpost is None or slug_exists.id != blogpost.id):
        flash("Blogpost title already exists!", category="error")
        current_app.logger.warning("Attempted to create duplicate blogpost!")
        return None

    return {
        "title": title,
        "slug": slug,
        "tags": request.form.get("tags", ""),
        "content": request.form.get("content", ""),
        "published": bool(request.form.get("published")),
    }


@blog.route("/")
def index():
    """Definition of the /blog site."""
    blogposts = Blogpost.query.filter_by(published=True).all()

    return render_template(
        "pages/blog/index.html.jinja", user=current_user, blogposts=blogposts
    )


@blog.route("/editor", methods=["GET", "POST"])
@login_required
def create_post():
    """Definition of the /blog/editor site."""
    drafts = Blogpost.query.filter_by(published=False).all()

    if request.method == "POST":
        fields = _validated_post_form()
        if fields is not None:
            new_post = Blogpost(**fields)
            db.session.add(new_post)
            db.session.commit()
            flash("Blogpost created!", category="success")
            current_app.logger.info(f"Blogpost with id {new_post.id}" f" was created.")
            return redirect(url_for("blog.post", slug=new_post.slug))

    return render_template(
        "pages/blog/editor.html.jinja",
        user=current_user,
        blogpost=None,
        blogposts=drafts,
    )


@blog.route("/editor/<id>", methods=["GET", "POST"])
@login_required
def edit_post(id):
    """
    Definition of the /blog/editor/<id> slug.

    Opens the editor with the content of blogpost with the given <id>.
    """
    blogpost = Blogpost.query.filter_by(id=id).first()
    drafts = Blogpost.query.filter_by(published=False).all()

    if not blogpost:
        flash("Blogpost does not exist and can not be edited.", category="error")
        return redirect(url_for("blog.index"))
    else:
        if request.method == "POST":
            fields = _validated_post_form(blogpost)
            if fields is not None:
                blogpost.slug = fields["slug"]
                blogpost.title = fields["title"]
                blogpost.tags = fields["tags"]
                blogpost.content = fields["content"]
                blogpost.published = fields["published"]

                db.session.add(blogpost)
                db.session.commit()
                flash("Blogpost edited!", category="success")
                current_app.logger.info(
                    f"Blogpost with id {blogpost.id}" f" was edited."
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
def delete_post(id):
    """
    Definition of the /blog/delete/<id> slug.

    Deletes blogpost with the given <id>.
    """
    blogpost = Blogpost.query.filter_by(id=id).first()

    if not blogpost:
        flash("Blogpost does not exist and could not be deleted.", category="error")
        current_app.logger.warning(
            "Deletion of non-existing blogpost was" " attempted."
        )
    else:
        db.session.delete(blogpost)
        db.session.commit()
        flash("Post successfully deleted.", category="success")
        current_app.logger.info(f"Blogpost with id {blogpost.id} was deleted.")

    return redirect(url_for("blog.index"))


@blog.route("/post/<slug>")
def post(slug):
    """
    Definition of the /blog/post/<slug> site.

    This is where the blogpost with the specified slug is viewed.
    """
    blogpost = Blogpost.query.filter_by(slug=slug).first()

    if not blogpost:
        flash("No blogpost with that slug exists.", category="error")
        return redirect(url_for("blog.index"))

    html = markdown(
        blogpost.content, extensions=["toc", "fenced_code", "codehilite", "sane_lists"]
    )

    return render_template(
        "pages/blog/post.html.jinja", user=current_user, blogpost=blogpost, html=html
    )
