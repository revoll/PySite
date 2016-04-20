# encoding: utf-8
import os
import shutil
import urllib2
from StringIO import StringIO
from PIL import Image

from flask import request, current_app, render_template, redirect, url_for, flash
from flask.ext.login import login_required, current_user

from . import movie
from .movie_forms import PosterForm, StillForm, StillForm2
from .. import db
from ..models.movie import Poster, Still


def poster_form_to_model(form, poster):
    poster.name = form.name.data
    poster.o_name = form.o_name.data
    poster.alias = form.alias.data
    poster.director = form.director.data
    poster.screenwriter = form.screenwriter.data
    poster.performers = form.performers.data
    poster.type_id = int(form.type.data)
    poster.country = form.country.data
    poster.length = form.length.data
    poster.release_date = form.release_date.data
    poster.douban_link = form.douban_link.data
    poster.introduction = form.introduction.data


def poster_model_to_form(poster, form):
    form.name.data = poster.name
    form.o_name.data = poster.o_name
    form.alias.data = poster.alias
    form.director.data = poster.director
    form.screenwriter.data = poster.screenwriter
    form.performers.data = poster.performers
    form.type.data = str(poster.type_id)
    form.country.data = poster.country
    form.length.data = poster.length
    form.release_date.data = poster.release_date
    form.douban_link.data = poster.douban_link
    form.introduction.data = poster.introduction


def save_poster_image(f, path, name, limit):
    if not os.path.exists(path):
        os.mkdir(path)
    img_1 = img_2 = Image.open(f)
    if img_1.size[0] > limit or img_1.size[1] > limit:
        if img_1.size[0] > img_1.size[1]:
            img_2 = img_1.resize((limit, int(float(limit) * img_1.size[1] / img_1.size[0])), Image.ANTIALIAS)
        else:
            img_2 = img_1.resize((int(float(limit) * img_1.size[0] / img_1.size[1]), limit), Image.ANTIALIAS)
    img_1.save(os.path.join(path, name + '_raw.jpg'), 'JPEG')
    img_2.save(os.path.join(path, name + '.jpg'), 'JPEG')


@movie.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Poster.query.order_by(Poster.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTERS_PER_PAGE'], error_out=False)
    for poster in pagination.items:
        if len(poster.introduction) > 140:
            poster.introduction_cut = poster.introduction[:140] + u' ......'
        else:
            poster.introduction_cut = poster.introduction
    return render_template('movie/index.html', posters=pagination.items, pagination=pagination)


@movie.route('/poster/<int:poster_id>')
def poster(poster_id):
    the_poster = Poster.query.get_or_404(poster_id)
    page = request.args.get('page', 1, type=int)
    pagination = the_poster.stills.order_by(Still.timeline.asc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTER_STILLS_PER_PAGE'],
        error_out=False)
    return render_template('movie/poster.html', poster=the_poster, form_new=StillForm(),
                           stills=pagination.items, pagination=pagination)


@movie.route('/add', methods=['GET', 'POST'])
def add_poster():
    form = PosterForm()
    if form.validate_on_submit():
        try:
            the_poster = Poster(author=current_user._get_current_object())
            poster_form_to_model(form, the_poster)
            db.session.add(the_poster)
            db.session.commit()
            the_poster = Poster.query.filter_by(name=form.name.data).first()
            assert the_poster
            method = form.method.data
            if method == u'file':
                img = request.files['img_file']
                assert img
            elif method == u'url':
                url = form.img_url.data
                img = StringIO(urllib2.urlopen(url).read())
                img.seek(0)
            else:
                raise ValueError
            path = os.path.join(current_app.static_folder, 'img/poster', str(the_poster.id))
            save_poster_image(img, path, 'archive', current_app.config['FLASKY_IMAGE_RESOLUTION_LIMIT'])
            flash(u'海报添加成功！')
            return redirect(url_for('movie.poster', poster_id=the_poster.id))
        except Exception:
            db.session.rollback()
            flash(u'海报添加时发生了错误...')
    return render_template('movie/edit_poster.html', form=form, id=None)


@movie.route('/edit/<int:poster_id>', methods=['GET', 'POST'])
@login_required
def edit_poster(poster_id):
    the_poster = Poster.query.get_or_404(poster_id)
    form = PosterForm()
    if form.validate_on_submit():
        try:
            poster_form_to_model(form, the_poster)
            db.session.add(the_poster)
            method = form.method.data
            if method == u'file':
                img = request.files['img_file']
            elif method == u'url':
                url = form.img_url.data
                if url == u'':
                    img = None
                else:
                    img = StringIO(urllib2.urlopen(url).read())
                    img.seek(0)
            else:
                raise ValueError
            if img:
                path = os.path.join(current_app.static_folder, 'img/poster', str(poster_id))
                save_poster_image(img, path, 'archive', current_app.config['FLASKY_IMAGE_RESOLUTION_LIMIT'])
            flash(u'海报更新成功！')
            return redirect(url_for('movie.poster', poster_id=the_poster.id))
        except Exception:
            db.session.rollback()
            flash(u'海报更新时发生了错误...')
    poster_model_to_form(the_poster, form)
    return render_template('movie/edit_poster.html', form=form, id=poster_id)


@movie.route('/delete/<int:poster_id>')
def delete_poster(poster_id):
    the_poster = Poster.query.get_or_404(poster_id)
    redirect_url = request.args.get('redirect', url_for('movie.index'))
    try:
        db.session.delete(the_poster)
        path = os.path.join(current_app.static_folder, 'img/poster', str(poster_id))
        if os.path.exists(path):
            shutil.rmtree(path)
        flash(u'《' + the_poster.name + u'》已被成功删除！')
    except Exception:
        db.session.rollback()
        flash(u'《' + the_poster.name + u'》删除失败...')
    return redirect(redirect_url)


@movie.route('/poster/<int:poster_id>/add-still', methods=['GET', 'POST'])
def add_still(poster_id):
    the_poster = Poster.query.get_or_404(poster_id)
    redirect_url = request.args.get('redirect', url_for('movie.poster', poster_id=poster_id))
    form = StillForm()
    if form.validate_on_submit():
        try:
            the_still = Still(timeline=Still.timeline_str_to_int(form.time_min.data, form.time_sec.data),
                              comment=form.comment.data, poster=the_poster,
                              author=current_user._get_current_object())
            db.session.add(the_still)
            db.session.commit()
            the_still = Still.query.filter_by(
                poster_id=poster_id, timeline=the_still.timeline).order_by(Still.timestamp.desc()).first()
            assert the_still
            method = form.method.data
            if method == u'file':
                img = request.files['img_file']
                assert img
            elif method == u'url':
                url = form.img_url.data
                img = StringIO(urllib2.urlopen(url).read())
                img.seek(0)
            else:
                raise ValueError
            path = os.path.join(current_app.static_folder, 'img/poster', str(poster_id))
            save_poster_image(img, path, str(the_still.id), current_app.config['FLASKY_IMAGE_RESOLUTION_LIMIT'])
            flash(u'剧照添加成功！')
        except Exception:
            db.session.rollback()
            flash(u'剧照添加时发生了错误...')
    return redirect(redirect_url)


@movie.route('/poster/<int:poster_id>/edit-stills', methods=['GET'])
def edit_stills(poster_id):
    the_poster = Poster.query.get_or_404(poster_id)
    page = request.args.get('page', 1, type=int)
    pagination = the_poster.stills.order_by(Still.timeline.asc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTER_STILLS_PER_PAGE'], error_out=False)
    forms = []
    for still in pagination.items:
        form = StillForm2()
        form.id = still.id
        form.time_min.data, form.time_sec.data = Still.timeline_int_to_str(still.timeline)
        form.comment.data = still.comment
        forms.append(form)
    return render_template('movie/edit_stills.html', poster_id=poster_id,
                           form_new=StillForm(), forms=forms, pagination=pagination)


@movie.route('/edit-still/<int:still_id>', methods=['POST'])
def edit_still(still_id):
    the_still = Still.query.get_or_404(still_id)
    form = StillForm2()
    if form.validate_on_submit():
        try:
            the_still.timeline = Still.timeline_str_to_int(form.time_min.data, form.time_sec.data)
            the_still.comment = form.comment.data
            db.session.add(the_still)
            flash(u'剧照更新成功！')
        except Exception:
            db.session.rollback()
            flash(u'剧照更新时发生了错误...')
    return redirect(url_for('movie.edit_stills', poster_id=the_still.poster_id))


@movie.route('/delete-still/<int:still_id>')
def delete_still(still_id):
    the_still = Still.query.get_or_404(still_id)
    try:
        db.session.delete(the_still)
        path = os.path.join(current_app.static_folder, 'img/poster', str(the_still.poster_id))
        img_prefix = os.path.join(path, str(still_id))
        if os.path.exists(img_prefix + '.jpg'):
            os.remove(img_prefix + '.jpg')
        if os.path.exists(img_prefix + '_raw.jpg'):
            os.remove(img_prefix + '_raw.jpg')
        flash(u'剧照已被成功删除！')
    except Exception:
        db.session.rollback()
        flash(u'剧照删除失败...')
    return redirect(url_for('movie.edit_stills', poster_id=the_still.poster_id))
