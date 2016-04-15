# encoding: utf-8
import os

from flask import request, current_app, render_template, redirect, url_for, flash, jsonify
from flask.ext.login import login_required

from . import movie
from .. import db
from ..models.movie import Poster


@movie.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Poster.query.order_by(Poster.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTERS_PER_PAGE'], error_out=False)
    return render_template('movie/index.html', posters=pagination.items, pagination=pagination)


@movie.route('/poster/<int:poster_id>')
def poster(poster_id):
    the_poster = Poster.query.filter_by(id=poster_id).first()
    return jsonify(the_poster)


@movie.route('/add', methods=['GET', 'POST'])
@login_required
def add_poster():
    pass


@movie.route('/edit/<int:poster_id>', methods=['GET', 'POST'])
@login_required
def edit_poster(poster_id):
    pass


@movie.route('/delete/<int:poster_id>')
@login_required
def delete_poster(poster_id):
    poster = Poster.query.get_or_404(poster_id)
    redirect_url = request.args.get('redirect', url_for('.index'))
    db.session.delete(poster)
    flash('Post ({0}) is deleted.'.format(str(poster_id)))
    return redirect(redirect_url)


@movie.route('/poster/<int:still_id>/stills')
def poster_stills(poster_id):
    poster = Poster.query.get_or_404(poster_id)
    return jsonify(poster.stills)


@movie.route('/edit-still')
def edit_still(still_id):
    pass


@login_required
def delete_still(still_id):
    pass


@movie.route('/upload-poster', methods=['GET', 'POST'])
def upload_poster():
    """
    上传电影海报
    :param poster_id: 海报对应的数据库ID
    :param file['poster']: 海报图片
    :return: JSON格式的结果
    """
    if request.method == 'POST':
        poster_id = request.args.get('poster_id')
        f = request.files['poster']
        file_path = os.path.join(current_app.static_folder, 'img/poster/')
        try:
            assert poster_id and f
            file_ext = os.path.splitext(f.filename)[1]
            f.save(file_path + poster_id + file_ext)
            return 'success'
        except AssertionError and IOError:
            return 'failed'
    else:
        return 'GET is unsupported.'


@movie.route('/upload-still', methods=['GET', 'POST'])
def upload_still():
    """
    上传电影剧照
    :param still_id: 剧照记录对应的数据库ID
    :param file['still']: 剧照图片
    :return: JSON格式的结果
    """
    if request.method == 'POST':
        still_id = request.args.get('still_id')
        f = request.files['still']
        file_path = os.path.join(current_app.static_folder, 'img/stills/')
        try:
            assert still_id and f
            file_ext = os.path.splitext(f.filename)[1]
            f.save(file_path + still_id + file_ext)
            return 'success'
        except AssertionError and IOError:
            return 'failed'
    else:
        return 'GET is unsupported.'
