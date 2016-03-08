# encoding: utf-8
"""
from flask import render_template
from flask.ext.login import login_required, current_user
from . import movie
from .. import db
from ..models.movie import Poster, Stills


@movie.route('/')
def index():
    pass


@movie.route('/poster/<int:id>')
def poster(id):
    pass


@movie.route('/new')
@login_required
def add():
    pass


@movie.route('/edit/<int:id>')
@login_required
def edit(id):
    pass


@movie.route('/delete/<int:id>')
@login_required
def delete(id):
    pass


@movie.route('/delete-still/<int:id>')
@login_required
def delete_still(id):
    pass
"""
from flask import request, redirect, render_template, url_for, flash
from . import movie
from .. import us_image


@movie.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = us_image.save(request.files['photo'])
        # rec = Photo(filename=filename, user=g.user.id)
        # rec.store()
        flash("Photo saved.")
        # return redirect(url_for('show', id=rec.id))
    return render_template('movie/upload.html')
