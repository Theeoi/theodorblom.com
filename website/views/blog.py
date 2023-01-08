#!/usr/bin/env python
"""
Views for the /blog url.
"""

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

    # blogposts.tags = tuple(blogposts.tags.split(","))

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
            current_app.logger.info(f"Blogpost with slug {slug} \
                                    was created.")
            return redirect(url_for("blog.post", slug=slug))

    return render_template("blog/editor.html", user=current_user)


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
