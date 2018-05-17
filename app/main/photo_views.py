# -*- coding: utf-8 -*-
import os
import urllib2
from datetime import datetime, timedelta
from StringIO import StringIO
from flask import request, current_app, render_template, redirect, abort, url_for, flash, send_from_directory
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, FileField
from wtforms.validators import Length, Regexp, ValidationError
from . import photo_blueprint as photo
from .. import db
from ..models.user import Permission
from ..models.photo import PhotoPost as Post, PhotoImage as Image, PhotoCategory as Category, PhotoTag as Tag
from ..tools.decoraters import permission_required
from ..tools import save_post_image


def get_iso_timestamp_cn(timestamp=datetime.utcnow(), timezone=8):
    return (timestamp + timedelta(hours=timezone)).strftime(u'%Y-%m-%d %H:%M:%S')


def get_post_dir(post):
    return os.path.join(current_app.data_path, u'photo', post.category.name,
                        (post.timestamp + timedelta(hours=8)).strftime(u'%Y-%m-%d ') + post.title)


def validate_post_title(title, timestamp=datetime.utcnow()):
    t_min = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    t_max = timestamp.replace(hour=23, minute=59, second=59, microsecond=999999)
    return False if Post.query.filter(Post.timestamp>=t_min, Post.timestamp<=t_max).filter_by(title=title).first() else True


########################################################################################################################
# photo Forms
########################################################################################################################

class _PostForm(FlaskForm):
    category = SelectField(u'分类', coerce=int)
    private = SelectField(u'是否公开', choices=[(0, u'所有人可见'), (1, u'仅自己可见')], coerce=int)
    title = StringField(u'相册名称', validators=[Length(0, 60)])
    persons = StringField(u'参与人员', validators=[Length(0, 100)])
    address = StringField(u'地点', validators=[Length(0, 140)])
    introduction = TextAreaField(u'相册备注与说明')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(_PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(c.id, c.name) for c in Category.query.filter_by(disabled=False).all()]

    def from_post(self, post):
        self.category.data = post.category_id
        self.private.data = post.private
        self.title.data = post.title
        self.persons.data = post.persons
        self.address.data = post.address
        self.introduction.data = post.introduction
        return self

    def to_post(self, post):
        post.category_id = self.category.data
        post.private = self.private.data
        post.title = self.title.data
        post.persons = self.persons.data
        post.address = self.address.data
        post.introduction = self.introduction.data
        return post


class AddPostForm(_PostForm):

    def validate_title(self, field):
        if not validate_post_title(field.data):
            raise ValidationError(u'同一天内的图册标题必须唯一')


class EditPostForm(_PostForm):
    pass


class _ImageForm(FlaskForm):
    private = SelectField(u'是否公开', choices=[(0, u'所有人可见'), (1, u'仅自己可见')], coerce=int)
    comment = StringField(u'备注')
    submit = SubmitField(u'更新')


class AddImageForm(_ImageForm):
    method = SelectField(u'上传方式', choices=[(u'file', u'本地图片'), (u'url', u'网络图片')], validators=[Regexp(u'^file|url$')])
    img_file = FileField(u'剧照图片')
    img_url = StringField(u'剧照URL', validators=[])


class EditImageForm(_ImageForm):
    pass


########################################################################################################################
# photo Views
########################################################################################################################

@photo.route(u'/', methods=[u'GET'])
def index():
    """
    访问权限：无
    :return:
    """
    page = request.args.get(u'page', 1, type=int)
    c_id = request.args.get(u'c_id', None, type=int)
    query = Post.query.filter(Category.disabled==False)
    if not current_user.can(Permission.VIEW_PRIVATE_PHOTO):
        query = query.filter(Category.private==False, Post.private==False)
    if c_id:
        query = query.filter_by(category_id=c_id)
    pagination = query.order_by(Post.timestamp.desc()).paginate(page, per_page=20, error_out=False)
    return render_template(u'photo/photo_index.html', posts=pagination.items, pagination=pagination,
                           categories=Category.query.all(), c_sel=c_id)


@photo.route(u'/post/<int:post_id>/', methods=[u'GET'])
def get_post(post_id):
    """
    访问权限：已登录，或者访问公开图册
    :param post_id:
    :return:
    """
    page = request.args.get(u'page', 1, type=int)
    post = Post.query.get_or_404(post_id)
    query = post.images
    if post.category.disabled:
        abort(404)
    if not current_user.can(Permission.VIEW_PRIVATE_PHOTO):
        if post.private or post.category.private:
            abort(403)
        query = query.filter_by(private=False)
    pagination = query.order_by(Image.timestamp.asc()).paginate(page, per_page=10, error_out=False)
    post.ping()
    return render_template(u'photo/photo_post.html', post=post, images=pagination.items, pagination=pagination, form=AddImageForm())


@photo.route(u'/add/', methods=[u'GET', u'POST'])
@permission_required(Permission.CURD_PHOTO)
def add_post():
    """
    访问权限：
    :return:
    """
    post = Post()
    form = AddPostForm()
    if form.validate_on_submit():
        try:
            form.to_post(post)
            db.session.add(post)  # SQLAlchemy自动创建对应的文件夹
            db.session.flush()
            db.session.commit()
            os.mkdir(get_post_dir(post))
        except Exception, e:
            db.session.rollback()
            flash(u'ERROR: %s' % e.message)
        else:
            return redirect(url_for(u'.get_post', post_id=post.id))
    return render_template(u'photo/edit_post.html', post_id=None, form=form)


@photo.route(u'/edit/<int:post_id>/', methods=[u'GET', u'POST'])
@permission_required(Permission.CURD_PHOTO)
def edit_post(post_id):
    """
    检查事项：所选Category是否有效；
    :param post_id:
    :return:
    """
    page = request.args.get(u'page', 1, type=int)
    post = Post.query.get_or_404(post_id)
    form = EditPostForm()
    forms = []
    if form.validate_on_submit():
        try:
            if form.category.data != post.category_id and Category.query.get(form.category.data).disabled:
                raise ValueError(u'不能修改为已经废弃的目录')
            if form.title.data != post.title and not validate_post_title(form.title.data, post.timestamp):
                raise ValueError(u'与同一天内的其它图册名字冲突')
            old_dir = get_post_dir(post)
            form.to_post(post)
            post.last_modify = datetime.utcnow()
            db.session.merge(post)
            db.session.flush()
            post.category = Category.query.get_or_404(post.category_id)  # TODO: 执行flush()后post.category未更新！
            new_dir = get_post_dir(post)
            if old_dir != new_dir:
                os.rename(old_dir, new_dir)
            db.session.commit()
        except Exception, e:
            db.session.rollback()
            flash(u'ERROR: %s' % e.message)
        else:
            return redirect(url_for(u'photo.get_post', post_id=post.id))
    form.from_post(post)
    if post.category.disabled:
        form.category.choices.append((post.category_id, post.category.name))
    pagination = post.images.order_by(Image.timestamp.asc()).paginate(page, per_page=10, error_out=False)
    for p in pagination.items:
        f = EditImageForm()
        f.id = p.id
        f.filename = p.f_name
        f.private.data = 1 if p.private else 0
        f.comment.data = p.comment
        forms.append(f)
    return render_template(u'photo/edit_post.html', post_id=post_id, form=form, forms=forms, pagination=pagination)


@photo.route(u'/delete/<int:post_id>/', methods=[u'GET'])
@permission_required(Permission.CURD_PHOTO)
def delete_post(post_id):
    """
    访问权限：
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    redirect_url = request.args.get(u'redirect', url_for(u'photo.index'))
    try:
        post_dir = get_post_dir(post)
        for image in post.images:
            db.session.delete(image)
            os.remove(os.path.join(post_dir, image.f_name))
            post.count -= 1
        db.session.delete(post)
        os.rmdir(post_dir)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        flash(u'ERROR: %s' % e.message)
    return redirect(redirect_url)


@photo.route(u'/edit_tags/<int:post_id>/', methods=[u'POST'])
@permission_required(Permission.CURD_PHOTO)
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


@photo.route(u'/add-image/<int:post_id>/', methods=[u'POST'])
@permission_required(Permission.CURD_PHOTO)
def add_image(post_id):
    """
    访问权限：已登录，或者访问公开图册
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    form = AddImageForm()
    if form.validate_on_submit():
        method = form.method.data
        try:
            post.index += 1
            post.count += 1
            name = u'%03d' % post.index
            p = Image(post_id=post.id, f_name=name+u'.jpg', comment=form.comment.data, private=bool(form.private.data))
            db.session.add(p)
            db.session.flush()
            if method == u'file':
                img = request.files[u'img_file']
            elif method == u'url':
                img = StringIO(urllib2.urlopen(form.img_url.data).read())
                img.seek(0)
            else:
                raise ValueError(u'无效的图片上传方式')
            save_post_image(img, get_post_dir(post), name, limit=False)
            db.session.commit()
        except Exception, e:
            db.session.rollback()
            flash(u'ERROR: %s' % e.message)
    return redirect(url_for(u'.get_post', post_id=post_id))


@photo.route(u'/edit-image/<int:image_id>/', methods=[u'POST'])
@permission_required(Permission.CURD_PHOTO)
def edit_image(image_id):
    """
    修改图片的可见性及备注信息
    :param image_id:
    :return:
    """
    image = Image.query.get_or_404(image_id)
    try:
        comment = request.form.get(u'comment')
        private = request.form.get(u'private')
        assert comment and private
        image = Image.query.get(image_id)
        assert image
        image.comment = comment
        image.private = True if private == u'1' else False
        db.session.merge(image)
        db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_for(u'.edit_post', post_id=image.post_id))


@photo.route(u'/delete-image/<int:image_id>/', methods=[u'GET'])
@permission_required(Permission.CURD_PHOTO)
def delete_image(image_id):
    """
    删除图片
    :param image_id:
    :return:
    """
    image = Image.query.get_or_404(image_id)
    try:
        image = Image.query.get(image_id)
        post = Post.query.get(image.post_id)
        assert image and post
        db.session.delete(image)
        os.remove(os.path.join(get_post_dir(post), image.f_name))
        post.count -= 1
        db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_for(u'.edit_post', post_id=image.post_id))


@photo.route(u'/image/<int:post_id>/<filename>', methods=[u'GET'])
def serve_image(post_id, filename):
    """
    图片获取接口(部署时实际使用WEB容器完成)
    :param post_id:
    :param filename:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    return send_from_directory(get_post_dir(post), filename)
