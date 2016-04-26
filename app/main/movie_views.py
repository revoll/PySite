# encoding: utf-8
import os
import shutil
import urllib2
from StringIO import StringIO
from PIL import Image

from flask import request, current_app, render_template, redirect, abort, url_for, flash

from flask.ext.login import current_user, login_required

from . import movie
from .movie_forms import AddPosterForm, EditPosterForm, AddStillForm, EditStillForm
from .. import db
from ..models.movie import Poster, Still
from ..models.user import Permission
from ..tools.decorators import permission_required


def poster_form_to_model(form, poster):

    poster.name = form.name.data
    poster.private = True if form.private.data else False
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
    form.private.data = 1 if poster.private else 0
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
    """
    将图片分别保存为原图,以及最大分辨率不超过规定值(1200px)的裁剪图
    :param f:
    :param path:
    :param name:
    :param limit:
    :return:
    """
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
    """
    访问权限: 无
    :return:
    """
    page = request.args.get('page', 1, type=int)
    admin = current_user.can(Permission.ADMIN_POSTER)
    if admin:
        query = Poster.query
    else:
        query = Poster.query.filter_by(private=False)
    pagination = query.order_by(Poster.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTERS_PER_PAGE'], error_out=False)
    for poster in pagination.items:
        if len(poster.introduction) > 140:
            poster.introduction_cut = poster.introduction[:140] + u' ......'
        else:
            poster.introduction_cut = poster.introduction

    return render_template('movie/index.html', posters=pagination.items, pagination=pagination, admin=admin)


@movie.route('/poster/<int:poster_id>/')
def get_poster(poster_id):
    """
    访问权限: 登陆, 海报为公开访问或自己创建时才可访问, 剧照为公开或自己创建时才能看到.
    :param poster_id:
    :return:
    """
    page = request.args.get('page', 1, type=int)
    poster = Poster.query.get_or_404(poster_id)
    admin = current_user.can(Permission.ADMIN_POSTER)
    if poster.private and not admin:
        abort(403)
    if admin:
        query = poster.stills
    else:
        query = poster.stills.filter_by(private=False)
    pagination = query.order_by(Still.timeline.asc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTER_STILLS_PER_PAGE'], error_out=False)

    return render_template('movie/poster.html', poster=poster, form_new=AddStillForm(),
                           stills=pagination.items, pagination=pagination, admin=admin)


@movie.route('/add/', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADMIN_POSTER)
def add_poster():
    form = AddPosterForm()

    if form.validate_on_submit():
        flag = True
        img = None
        poster = None
        method = form.method.data

        if method == u'file':
            img = request.files['img_file']
            flag = True if img else False
        elif method == u'url':
            url = form.img_url.data
            try:
                img = StringIO(urllib2.urlopen(url).read())
                img.seek(0)
            except IOError:
                flag = False
        else:
            flag = False

        if flag:
            poster = Poster(author=current_user)
            poster_form_to_model(form, poster)
            try:
                db.session.add(poster)
                db.session.commit()
                poster = Poster.query.filter_by(name=poster.name).first()
            except Exception:
                flag = False
                db.session.rollback()

        if flag and poster:
            path = os.path.join(current_app.static_folder, 'img/poster', str(poster.id))
            save_poster_image(img, path, 'archive', current_app.config['FLASKY_IMAGE_RESOLUTION_LIMIT'])

        if flag:
            flash(u'海报添加成功！')
            return redirect(url_for('movie.get_poster', poster_id=poster.id))
        else:
            flash(u'海报添加时发生了错误...')

    form.method.data = u'file'
    return render_template('movie/edit_poster.html', form=form, id=None)


@movie.route('/edit/<int:poster_id>/', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADMIN_POSTER)
def edit_poster(poster_id):
    poster = Poster.query.get_or_404(poster_id)
    form = EditPosterForm()

    if form.validate_on_submit():
        flag = True
        img = None
        method = form.method.data

        try:
            poster_form_to_model(form, poster)
            db.session.add(poster)
            db.session.commit()
        except Exception:
            flag = False
            db.session.rollback()

        if flag:
            url = form.img_url.data
            if method == u'file':
                img = request.files['img_file']
            elif method == u'url' and url:
                try:
                    img = StringIO(urllib2.urlopen(url).read())
                    img.seek(0)
                except IOError:
                    flag = False
            else:
                flag = False
        if flag and img:
            path = os.path.join(current_app.static_folder, 'img/poster', str(poster_id))
            save_poster_image(img, path, 'archive', current_app.config['FLASKY_IMAGE_RESOLUTION_LIMIT'])

        if flag:
            flash(u'海报更新成功！')
            return redirect(url_for('movie.get_poster', poster_id=poster.id))
        else:
            flash(u'海报更新时发生了错误...')

    poster_model_to_form(poster, form)
    form.method.data = u'file'
    return render_template('movie/edit_poster.html', form=form, id=poster_id)


@movie.route('/delete/<int:poster_id>/')
@login_required
@permission_required(Permission.ADMIN_POSTER)
def delete_poster(poster_id):
    poster = Poster.query.get_or_404(poster_id)
    redirect_url = request.args.get('redirect', url_for('movie.index'))
    flag = True
    path = os.path.join(current_app.static_folder, 'img/poster', str(poster_id))

    try:
        db.session.delete(poster)
        db.session.commit()
    except Exception:
        flag = False
        db.session.rollback()

    if flag and os.path.exists(path):
        shutil.rmtree(path)

    if flag:
        flash(u'《' + poster.name + u'》已被成功删除！')
    else:
        flash(u'《' + poster.name + u'》删除失败...')

    return redirect(redirect_url)


@movie.route('/poster/<int:poster_id>/add-still/', methods=['GET', 'POST'])
@login_required
# @permission_required(Permission.ADMIN_POSTER)
def add_still(poster_id):
    poster = Poster.query.get_or_404(poster_id)
    redirect_url = request.args.get('redirect', url_for('movie.get_poster', poster_id=poster_id))
    form = AddStillForm()

    if form.validate_on_submit():
        flag = True
        img = None
        still = None
        method = form.method.data

        if method == u'file':
            img = request.files['img_file']
            flag = True if img else False
        elif method == u'url':
            url = form.img_url.data
            try:
                img = StringIO(urllib2.urlopen(url).read())
                img.seek(0)
            except IOError:
                flag = False
        else:
            flag = False

        if flag:
            still = Still(timeline=Still.timeline_str_to_int(form.time_min.data, form.time_sec.data),
                          comment=form.comment.data, poster=poster,
                          private=True if form.private.data else False, author=current_user)
            try:
                db.session.add(still)
                db.session.commit()
                still = Still.query.filter_by(
                    poster_id=poster_id, timeline=still.timeline).order_by(Still.timestamp.desc()).first()
            except Exception:
                flag = False
                db.session.rollback()

        if flag and still:
            path = os.path.join(current_app.static_folder, 'img/poster', str(poster_id))
            save_poster_image(img, path, str(still.id), current_app.config['FLASKY_IMAGE_RESOLUTION_LIMIT'])

        if flag:
            flash(u'剧照添加成功！')
        else:
            flash(u'剧照添加时发生了错误...')

    form.method.data = u'file'
    return redirect(redirect_url)


@movie.route('/poster/<int:poster_id>/edit-stills/', methods=['GET'])
@login_required
@permission_required(Permission.ADMIN_POSTER)
def edit_stills(poster_id):

    page = request.args.get('page', 1, type=int)
    poster = Poster.query.get_or_404(poster_id)
    pagination = poster.stills.order_by(Still.timeline.asc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTER_STILLS_PER_PAGE'], error_out=False)
    forms = []
    for still in pagination.items:
        form = EditStillForm()
        form.id = still.id
        form.private.data = 1 if still.private else 0
        form.time_min.data, form.time_sec.data = Still.timeline_int_to_str(still.timeline)
        form.comment.data = still.comment
        forms.append(form)
    return render_template('movie/edit_stills.html', poster_id=poster_id,
                           form_new=AddStillForm(), forms=forms, pagination=pagination)


@movie.route('/edit-still/<int:still_id>/', methods=['POST'])
@login_required
@permission_required(Permission.ADMIN_POSTER)
def edit_still(still_id):
    still = Still.query.get_or_404(still_id)
    form = EditStillForm()

    if form.validate_on_submit() and ():
        flag = True
        still.private = True if form.private.data else False
        still.timeline = Still.timeline_str_to_int(form.time_min.data, form.time_sec.data)
        still.comment = form.comment.data

        try:
            db.session.add(still)
            db.session.commit()
        except Exception:
            flag = False
            db.session.rollback()

        if flag:
            flash(u'剧照更新成功！')
        else:
            flash(u'剧照更新时发生了错误...')

    return redirect(url_for('movie.edit_stills', poster_id=still.poster_id))


@movie.route('/delete-still/<int:still_id>/')
@login_required
@permission_required(Permission.ADMIN_POSTER)
def delete_still(still_id):
    still = Still.query.get_or_404(still_id)
    flag = True
    path = os.path.join(current_app.static_folder, 'img/poster', str(still.poster_id))
    img_prefix = os.path.join(path, str(still_id))

    try:
        db.session.delete(still)
        db.session.commit()
    except Exception:
        flag = False
        db.session.rollback()

    if flag:
        if os.path.exists(img_prefix + '.jpg'):
            os.remove(img_prefix + '.jpg')
        if os.path.exists(img_prefix + '_raw.jpg'):
            os.remove(img_prefix + '_raw.jpg')

    if flag:
        flash(u'剧照已被成功删除！')
    else:
        flash(u'剧照删除失败...')

    return redirect(url_for('movie.edit_stills', poster_id=still.poster_id))
