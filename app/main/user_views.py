# encoding: utf-8
import os
import datetime
import urllib2
from PIL import Image
from StringIO import StringIO

from flask import render_template, redirect, url_for, flash, request, current_app, send_file
from flask.ext.login import login_required, current_user

from . import user
from .user_forms import EditProfileForm, EditProfileAdminForm
from .. import db
from ..models.user import User
from ..models.blog import Post
from ..tools.decorators import admin_required


def index_array_to_value(index_array):
    value = 0
    for index in index_array:
        value |= 1 << index
    return value


def value_to_index_array(value):
    index_array = []
    counter = 0
    while value > 0:
        if value & 1:
            index_array.append(counter)
        value >>= 1
        counter += 1
    return index_array


@user.route('/')
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.member_since.desc()).paginate(
        page, per_page=current_app.config['FLASKY_USERS_PER_PAGE'], error_out=False)
    users = pagination.items
    for i in range(0, len(users)):
        users[i].permission_bin = bin(users[i].permission | 1 << 63)[-16:]
    return render_template('user/users.html', users=pagination.items, pagination=pagination)


@user.route('/p/<username>/')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    return render_template('user/profile.html', user=user, posts=pagination.items, pagination=pagination)


@user.route('/edit-profile/', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('main.profile', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('user/edit_profile.html', form=form)


@user.route('/edit-profile/<int:user_id>/', methods=['GET', 'POST'])
@admin_required
def edit_profile_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.permission = index_array_to_value(form.permission.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('user.profile', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.permission.data = value_to_index_array(user.permission)
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('user/edit_profile.html', form=form, user=user)


def quadrating_image(img, size=150):
    if not isinstance(img, Image.Image) or size <= 0:
        return img  # None
    if img.size[0] != img.size[1]:
        if img.size[0] > img.size[1]:
            i_size = img.size[1]
            i_diff = (img.size[0] - img.size[1]) / 2
            box = (i_diff, 0, i_size + i_diff, i_size)
        else:
            i_size = img.size[0]
            i_diff = (img.size[1] - img.size[0]) / 2
            box = (0, i_diff, i_size, i_size + i_diff)
        img = img.crop(box)
    return img.resize((size, size), Image.ANTIALIAS)


def thumbnail_image(image_path, size=150, fmt='JPEG'):
    img_sio = StringIO()
    img = Image.open(image_path)
    # img.thumbnail((th_size, th_size), Image.ANTIALIAS)
    img = quadrating_image(img, size)
    img.save(img_sio, fmt)  # quality=70
    img_sio.seek(0)
    return img_sio


_avatar_default_timestamp = '2016-00-00'


@user.route('/avatar/<ava_hash>')  # /img/avatar/<hash>?size=xxx
def get_avatar(ava_hash, max_size=512):
    """
    获取用户头像:
    * 头像一般有三种来源: www.gravatar.com, 本地头像, 默认头像: 这里首先处理www.gravatar.com的
      头像请求,网络访问失败则返回默认头像. 对于本地存储的用户默认头像,可以通过web容器直传.
    :param ava_hash:
    :arg size: 图像大小,分辨率为size*size的正方形
    :return:
    """
    global _avatar_default_timestamp

    size = request.args.get('s', 0, type=int)
    size = max_size if size > max_size or size < 0 else size

    try:
        # 128bit hash: load avatar from "www.gravatar.com".
        if len(ava_hash) == 32:
            raise StandardError  # uncomment this line
            assert datetime.date.today() != _avatar_default_timestamp
            if request.is_secure:
                url = 'https://secure.gravatar.com/avatar/'
            else:
                url = 'http://www.gravatar.com/avatar/'
            url = url + '{hash}?d={d}&r={r}'.format(hash=hash, d='identicon', r='g')
            if size > 0:
                url += '&s={s}'.format(s=size)
            try:
                img_io = StringIO(urllib2.urlopen(url).read())
            except IOError:
                _avatar_default_timestamp = datetime.date.today()
                raise IOError
            img_io.seek(0)
            return send_file(img_io)
        # 80bit hash: seek from local disk storage
        elif ava_hash[-4:] == '.jpg':
            path = os.path.join(current_app.static_folder, 'img/avatar/', ava_hash)
            if os.path.isfile(path):
                return send_file(path) if size == 0 else send_file(thumbnail_image(path, size))
            else:
                raise IOError
        # Invalid hash string
        else:
            raise StandardError
    # serving default avatar from local disk storage
    except StandardError:
        path = os.path.join(current_app.static_folder, 'img/avatar/default_256.jpg')
        return send_file(path) if size == 0 else send_file(thumbnail_image(path, size))


@user.route('/upload-avatar/', methods=['GET', 'POST'])
@login_required
def upload_avatar():
    """
    上传头像:
    * 保存为JPEG格式,在img/avatar/目录下,名字为USER_ID.jpg;
    * 保存为正方形,截取图像内居中到最大正方形大小,超过256像素时进行压缩处理;
    * NOTICE: 由于前端使用美图秀秀API,上传的头像默认为150*150大小,这里的头像处理后不超过这个值.
    :return: 'user/edit_avatar.html' (GET) or 'string' (POST)
    """
    if request.method == 'POST':
        max_size = request.args.get('max_size', 256, type=int)
        file_path = os.path.join(current_app.static_folder, 'img/avatar/')
        file_name = '{0}.jpg'.format(current_user.id)
        try:
            img = Image.open(request.files['avatar'])
            img_min = img.size[0] if img.size[0] < img.size[1] else img.size[1]
            new_size = img_min if img_min < max_size else max_size
            img = quadrating_image(img, new_size)
            img.save(file_path + file_name, 'JPEG')  # quality=70
            if current_user.avatar != file_name:
                try:
                    current_user.avatar = file_name
                    db.session.add(current_user)
                    db.session.commit()
                except Exception:
                    db.rollback()
                    raise IOError
            return 'success'
        except IOError:
            return 'failed'
    else:
        return render_template('user/edit_avatar.html')
