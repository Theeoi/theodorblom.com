#!/usr/bin/env python
"""Views for the /blog url."""

from ..models import Blogpost
from .. import db
from slugify import slugify
from markdown import markdown
from flask_login import current_user, login_required
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app)

blog = Blueprint('blog', __name__, url_prefix='/blog')


@blog.route('/')
def index():
    """Definition of the /blog site."""
    blogposts = Blogpost.query.all()

    return render_template("blog/index.html", user=current_user,
                           blogposts=blogposts)


@blog.route('/editor/', methods=['GET', 'POST'])
@login_required
def create_post():
    """Definition of the /blog/editor site."""
    if request.method == 'POST':
        title = request.form.get("title")
        tags = request.form.get("tags")
        content = request.form.get("content")

        slug = slugify(title)

        slug_exists = Blogpost.query.filter_by(slug=slug).first()

        if slug_exists:
            flash("Blogpost title already exists!", category='error')
            current_app.logger.warning(
                "Attempted to create duplicate blogpost!")
        elif len(title) < 1:
            flash("Title is too short!", category='error')
        elif len(content) < 1:
            flash("Blogpost is too short!", category='error')
        else:
            new_post = Blogpost(slug=slug, title=title,
                                tags=tags, content=content)
            db.session.add(new_post)
            db.session.commit()
            flash("Blogpost created!", category='success')
            current_app.logger.info(f"Blogpost with id {new_post.id}"
                                    f" was created.")
            return redirect(url_for("blog.post", slug=slug))

    return render_template("blog/editor.html", user=current_user,
                           blogpost=None)


@blog.route('/editor/<id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    """
    Definition of the /blog/editor/<id> slug.

    Opens the editor with the content of blogpost with the given <id>.
    """
    blogpost = Blogpost.query.filter_by(id=id).first()

    if not blogpost:
        flash("Blogpost does not exist and can not be edited.",
              category='error')
        return redirect(url_for("blog.index"))
    else:
        if request.method == 'POST':
            title = request.form.get("title")
            tags = request.form.get("tags")
            content = request.form.get("content")

            slug = slugify(title)

            slug_exists = Blogpost.query.filter_by(slug=slug).first()

            if slug_exists and slug_exists.id != blogpost.id:
                flash("Blogpost title already exists!", category='error')
                current_app.logger.warning(
                    "Attempted to create duplicate blogpost!")
            elif len(title) < 1:
                flash("Title is too short!", category='error')
            elif len(content) < 1:
                flash("Blogpost is too short!", category='error')
            else:
                blogpost.slug = slug
                blogpost.title = title
                blogpost.tags = tags
                blogpost.content = content

                db.session.add(blogpost)
                db.session.commit()
                flash("Blogpost edited!", category='success')
                current_app.logger.info(f"Blogpost with id {blogpost.id}"
                                        f" was edited.")
                return redirect(url_for("blog.post", slug=blogpost.slug))

    return render_template("blog/editor.html", user=current_user,
                           blogpost=blogpost)


@blog.route('/delete/<id>')
@login_required
def delete_post(id):
    """
    Definition of the /blog/delete/<id> slug.

    Deletes blogpost with the given <id>.
    """
    blogpost = Blogpost.query.filter_by(id=id).first()

    if not blogpost:
        flash("Blogpost does not exist and could not be deleted.",
              category='error')
        current_app.logger.warning("Deletion of non-existing blogpost was"
                                   " attempted.")
    else:
        db.session.delete(blogpost)
        db.session.commit()
        flash("Post successfully deleted.", category='success')
        current_app.logger.info(f"Blogpost with id {blogpost.id} was deleted.")

    return redirect(url_for("blog.index"))


@blog.route('/post/<slug>')
def post(slug):
    """
    Definition of the /blog/post/<slug> site.

    This is where the blogpost with the specified slug is viewed.
    """
    blogpost = Blogpost.query.filter_by(slug=slug).first()

    if not blogpost:
        flash('No blogpost with that slug exists.', category='error')
        return redirect(url_for("blog.index"))

    blogpost.content = markdown(blogpost.content, extensions=['toc',
                                                              'fenced_code',
                                                              'codehilite'])

    return render_template("blog/post.html", user=current_user,
                           blogpost=blogpost)
