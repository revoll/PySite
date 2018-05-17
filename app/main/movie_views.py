# -*- coding: utf-8 -*-
import os
import shutil
import urllib2
from StringIO import StringIO
from datetime import datetime
from flask import request, current_app, render_template, redirect, abort, url_for, flash, send_from_directory
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, FileField, ValidationError
from wtforms.validators import DataRequired, Length, URL, Regexp
from . import movie_blueprint as movie
from .. import db
from ..models.user import Permission
from ..models.movie import MoviePost as Post, MovieStill as Still, MovieCategory as Category, MovieTag as Tag
from ..tools.decoraters import permission_required
from ..tools import save_post_image


def get_post_dir(post):
    return os.path.join(current_app.data_path, u'movie', post.category.name, post.name)


########################################################################################################################
# Movie Forms
########################################################################################################################

class _PostForm(FlaskForm):
    name = StringField(u'电影名', validators=[DataRequired(), Length(1, 50)])
    private = SelectField(u'是否公开', choices=[(0, u'所有人可见'), (1, u'仅自己可见')], coerce=int)
    reference = StringField(u'豆瓣链接', validators=[Length(0, 80), URL()])
    method = SelectField(u'上传方式', choices=[(u'file', u'本地图片'), (u'url', u'网络图片')], validators=[Regexp(u'^file|url$')])
    img_file = FileField(u'海报图片')
    img_url = StringField(u'海报URL', validators=[])
    o_name = StringField(u'原名', validators=[Length(0, 50)])
    alias = StringField(u'别名', validators=[Length(0, 160)])
    director = StringField(u'导演', validators=[Length(0, 40)])
    screenwriter = StringField(u'编剧', validators=[Length(0, 40)])
    performers = StringField(u'主演', validators=[Length(0, 200)])
    category = SelectField(u'分类', coerce=int)
    country = StringField(u'地区', validators=[Length(0, 100)])
    length = StringField(u'片长', validators=[Length(0, 60)])
    release_date = StringField(u'上映日期', validators=[Length(0, 60)])
    introduction = TextAreaField(u'电影简介')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(_PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(c.id, c.name) for c in Category.query.filter_by(disabled=False).all()]

    def from_post(self, post):
        if self.method.data is None:
            self.method.data = u'file'
        self.name.data = post.name
        self.private.data = 1 if post.private else 0
        self.o_name.data = post.o_name
        self.alias.data = post.alias
        self.director.data = post.director
        self.screenwriter.data = post.screenwriter
        self.performers.data = post.performers
        self.category.data = post.category_id
        self.country.data = post.country
        self.length.data = post.length
        self.release_date.data = post.release_date
        self.reference.data = post.reference
        self.introduction.data = post.introduction
        return self

    def to_post(self, post):
        post.name = self.name.data
        post.private = True if self.private.data else False
        post.o_name = self.o_name.data
        post.alias = self.alias.data
        post.director = self.director.data
        post.screenwriter = self.screenwriter.data
        post.performers = self.performers.data
        post.category_id = self.category.data
        post.country = self.country.data
        post.length = self.length.data
        post.release_date = self.release_date.data
        post.reference = self.reference.data
        post.introduction = self.introduction.data
        return post


class AddPostForm(_PostForm):

    def validate_name(self, field):
        if Post.query.filter_by(name=field.data).first() is not None:
            raise ValidationError(u'相同电影名已经存在，不能重复添加。')


class EditPostForm(_PostForm):
    pass


class _StillForm(FlaskForm):
    time_min = StringField(u'时间（分）', validators=[Regexp(u'^\d{0,3}$', message=u'最大支持999分钟')])
    time_sec = StringField(u'时间（秒）', validators=[Regexp(u'^[0-5]?\d?$', message=u'不在0-59秒范围内')])
    private = SelectField(u'是否公开', choices=[(0, u'所有人可见'), (1, u'仅自己可见')], coerce=int)
    comment = StringField(u'我想说')
    submit = SubmitField(u'更新')


class AddStillForm(_StillForm):
    method = SelectField(u'上传方式', choices=[(u'file', u'本地图片'), (u'url', u'网络图片')], validators=[Regexp(u'^file|url$')])
    img_file = FileField(u'剧照图片')
    img_url = StringField(u'剧照URL', validators=[])


class EditStillForm(_StillForm):
    pass


########################################################################################################################
# Movie Views
########################################################################################################################

@movie.route(u'/', methods=[u'GET'])
def index():
    """
    访问权限：无
    :return:
    """
    page = request.args.get(u'page', 1, type=int)
    c_id = request.args.get(u'c_id', None, type=int)
    query = Post.query.filter(Category.disabled==False)
    if not current_user.can(Permission.VIEW_PRIVATE_MOVIE):
        query = query.filter(Category.private==False, Post.private==False)
    if c_id:
        query = query.filter_by(category_id=c_id)
    pagination = query.order_by(Post.timestamp.desc()).paginate(page, per_page=10, error_out=False)
    for p in pagination.items:
        p.introduction_cut = p.introduction if len(p.introduction) <= 140 else p.introduction[:140] + u' ......'
    return render_template(u'movie/movie_index.html', posts=pagination.items, pagination=pagination,
                           categories=Category.query.all(), c_sel=c_id)


@movie.route(u'/post/<int:post_id>/', methods=[u'GET'])
def get_post(post_id):
    """
    访问权限：已登录，或者访问公开海报
    :param post_id:
    :return:
    """
    page = request.args.get(u'page', 1, type=int)
    post = Post.query.get_or_404(post_id)
    query = post.stills
    if post.category.disabled:
        abort(404)  # abort 410 exactly
    if not current_user.can(Permission.VIEW_PRIVATE_MOVIE):
        if post.private or post.category.private:
            abort(403)
        query = query.filter_by(private=False)
    pagination = query.order_by(Still.timeline.asc()).paginate(page, per_page=20, error_out=False)
    post.ping()
    return render_template(u'movie/movie_post.html', post=post, stills=pagination.items,
                           pagination=pagination, form=AddStillForm())


@movie.route(u'/add/', methods=[u'GET', u'POST'])
@permission_required(Permission.CURD_MOVIE)
def add_post():
    """
    访问权限：
    :return:
    """
    form = AddPostForm()
    if form.validate_on_submit():
        method = form.method.data
        try:
            post = form.to_post(Post())
            db.session.add(post)
            db.session.flush()
            if method == u'file':
                img = request.files[u'img_file']
            elif method == u'url':
                img = StringIO(urllib2.urlopen(form.img_url.data).read())
                img.seek(0)
            else:
                raise ValueError(u'无效的图片上传方式')
            save_post_image(img, get_post_dir(post), u'archive')
            db.session.commit()
        except Exception, e:
            db.session.rollback()
            flash(u'ERROR: %s' % e.message)
        else:
            flash(u'海报添加成功！')
            return redirect(url_for(u'movie.get_post', post_id=post.id))
    return render_template(u'movie/edit_post.html', form=form, id=None)


@movie.route(u'/edit/<int:post_id>/', methods=[u'GET', u'POST'])
@permission_required(Permission.CURD_MOVIE)
def edit_post(post_id):
    """
    检查事项：电影名是否冲突；所选Category是否有效；
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    form = EditPostForm()
    if form.validate_on_submit():
        try:
            if form.category.data != post.category_id and Category.query.get(form.category.data).disabled:
                raise ValueError(u'不能修改')
            old_dir = get_post_dir(post)
            form.to_post(post)
            post.last_modify = datetime.utcnow()
            db.session.merge(post)
            method = form.method.data
            db.session.flush()
            post.category = Category.query.get_or_404(post.category_id)  # TODO: 执行flush()后post.category未更新！
            new_dir = get_post_dir(post)
            if old_dir != new_dir:
                os.rename(old_dir, new_dir)
            if method == u'file':
                img = request.files[u'img_file']
            elif method == u'url':
                img = StringIO(urllib2.urlopen(form.img_url.data).read())
                img.seek(0)
            else:
                raise ValueError(u'无效的图片上传方式')
            try:
                save_post_image(img, new_dir, u'archive')
            except Exception:
                pass
            db.session.commit()
        except Exception, e:
            db.session.rollback()
            flash(u'ERROR: %s' % e.message)
        else:
            flash(u'海报更新成功！')
            return redirect(url_for(u'movie.get_post', post_id=post.id))
    form.from_post(post)
    if post.category.disabled:
        form.category.choices.append((post.category_id, post.category.name))
    return render_template(u'movie/edit_post.html', form=form, id=post_id)


@movie.route(u'/delete/<int:post_id>/', methods=[u'GET'])
@permission_required(Permission.CURD_MOVIE)
def delete_post(post_id):
    """
    访问权限：
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    redirect_url = request.args.get(u'redirect', url_for(u'movie.index'))
    path = get_post_dir(post)
    try:
        for still in post.stills:
            db.session.delete(still)
        db.session.delete(post)
        if os.path.exists(path):
            shutil.rmtree(path)
        db.session.commit()
    except Exception, e:
        db.session.roolback()
        flash(u'ERROR: %s' % e.message)
    return redirect(redirect_url)


@movie.route(u'/edit_tags/<int:post_id>/', methods=[u'POST'])
@permission_required(Permission.CURD_MOVIE)
def edit_tags(post_id):
    """
    编辑标签
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    try:
        post.tags = []
        for t_n in request.form:
            tag = Tag.query.get(request.form[t_n])
            if tag:
                post.tags.append(tag)
            else:
                abort(400)
        db.session.merge(post)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        flash(u'ERROR: %s' % e.message)
    return redirect(url_for(u'.get_post', post_id=post_id))


@movie.route(u'/add-still/<int:post_id>/', methods=[u'GET', u'POST'])
@permission_required(Permission.CURD_MOVIE)
def add_still(post_id):
    """
    访问权限：
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    redirect_url = request.args.get(u'redirect', url_for(u'.get_post', post_id=post_id))
    form = AddStillForm()
    if form.validate_on_submit():
        method = form.method.data
        try:
            still = Still(timeline=Still.timeline_str_to_int(form.time_min.data, form.time_sec.data),
                          comment=form.comment.data, post_id=post.id, private=bool(form.private.data))
            db.session.add(still)
            db.session.flush()
            if method == u'file':
                img = request.files[u'img_file']
            elif method == u'url':
                img = StringIO(urllib2.urlopen(form.img_url.data).read())
                img.seek(0)
            else:
                raise ValueError(u'无效的图片上传方式')
            save_post_image(img, get_post_dir(post), str(still.id))
            db.session.commit()
        except Exception, e:
            db.session.roolback()
            flash(u'ERROR: %s' % e.message)
    else:
        # 如果表单验证发现错误，跳转后下一个页面的表单无法提示错误，只能采用flash的方式来提示错误。
        for e in form.errors:
            flash(u'ERROR: %s - %s' % (e, form.errors[e][0]))
    if form.method.data is None:
        form.method.data = u'file'
    return redirect(redirect_url)


@movie.route(u'/edit-stills/<int:post_id>/', methods=[u'GET'])
@permission_required(Permission.CURD_MOVIE)
def edit_stills(post_id):
    """
    访问权限：
    :param post_id:
    :return:
    """
    page = request.args.get(u'page', 1, type=int)
    post = Post.query.get_or_404(post_id)
    pagination = post.stills.order_by(Still.timeline.asc()).paginate(page, per_page=15, error_out=False)
    forms = []
    for still in pagination.items:
        form = EditStillForm()
        form.id = still.id
        form.private.data = 1 if still.private else 0
        form.time_min.data, form.time_sec.data = Still.timeline_int_to_str(still.timeline)
        form.comment.data = still.comment
        forms.append(form)
    return render_template(u'movie/edit_stills.html', post=post,
                           form=AddStillForm(), forms=forms, pagination=pagination)


@movie.route(u'/edit-still/<int:still_id>/', methods=[u'POST'])
@permission_required(Permission.CURD_MOVIE)
def edit_still(still_id):
    """
    访问权限：
    :param still_id:
    :return:
    """
    still = Still.query.get_or_404(still_id)
    form = EditStillForm()
    if form.validate_on_submit():
        still.private = True if form.private.data else False
        still.timeline = Still.timeline_str_to_int(form.time_min.data, form.time_sec.data)
        still.comment = form.comment.data
        try:
            db.session.merge(still)
            db.session.commit()
        except Exception, e:
            db.session.rollback()
            flash(u'ERROR: %s' % e.message)
    return redirect(url_for(u'movie.edit_stills', post_id=still.post_id))


@movie.route(u'/delete-still/<int:still_id>/', methods=[u'GET'])
@permission_required(Permission.CURD_MOVIE)
def delete_still(still_id):
    """
    访问权限：
    :param still_id:
    :return:
    """
    still = Still.query.get_or_404(still_id)
    post = Post.query.get_or_404(still.post_id)
    path = get_post_dir(post)
    img_prefix = os.path.join(path, str(still_id))
    try:
        db.session.delete(still)
        if os.path.exists(img_prefix + u'.jpg'):
            os.remove(img_prefix + u'.jpg')
        if os.path.exists(img_prefix + u'_raw.jpg'):
            os.remove(img_prefix + u'_raw.jpg')
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        flash(u'ERROR: %s' % e.message)
    return redirect(url_for(u'movie.edit_stills', post_id=still.post_id))


@movie.route(u'/image/<int:post_id>/<filename>', methods=[u'GET'])
def serve_image(post_id, filename):
    """
    图片获取接口(部署时实际使用WEB容器完成)
    :param post_id:
    :param filename:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    return send_from_directory(get_post_dir(post), filename)
