# encoding: utf-8
import os
import datetime
import urllib2
from StringIO import StringIO
from PIL import Image

from flask import render_template, request, current_app, send_file

from flask.ext.login import login_required, current_user

from . import main
from .. import db
from ..tools import quadrating_image, thumbnail_image


@main.route('/upload-avatar', methods=['GET', 'POST'])
@login_required
def upload_avatar(max_size=256):
    """
    上传头像:
    * 保存为PNG格式,在img/avatar/目录下,名字为20位十六进制,不带后缀名;
    * 保存为正方形,截取图像内居中到最大正方形大小,超过256像素时进行压缩处理;
    * NOTICE: 由于前端使用美图秀秀API,上传到头像默认为150*150大小,这里的头像处理后不超过这个值.
    :return: 'user/edit_avatar.html' (GET) or 'string' (POST)
    """
    if request.method == 'POST':
        try:
            f = request.files['upload_file']  # avatar resolution: 256*256
            file_path = os.path.join(current_app.static_folder, 'img/avatar/')
            file_name = current_user.id + '.jpg'
            img = Image.open(f)
            img_min = img.size[0] if img.size[0] < img.size[1] else img.size[1]
            new_size = img_min if img_min < max_size else max_size
            img = quadrating_image(img, new_size)
            img.save(file_path + file_name, 'JPG')  # quality=70
            current_user.avatar_hash = file_name
            db.session.add(current_user)
        except IOError:
            return 'failed'
        # return redirect(url_for('user_np.profile'))
        return 'success'
    else:
        return render_template('user/edit_avatar.html')


_avatar_default_timestamp = '2016-00-00'


@main.route('/avatar/<ava_hash>')  # /img/avatar/<hash>?size=xxx
def get_avatar(ava_hash):
    """
    获取用户头像:
    * 头像的三种来源: www.gravatar.com, 本地头像, 默认头像(前两种方式获取失败)
    * 不指定图像大小时,获取本地头像将返回存储的原图,返回默认头像时使用256*256大小
    * 默认头像的预置分辨率由'available_size'指定:(16, 32, 64, 128, 256, 18, 40, 200)
    :param ava_hash:
    :arg size: 图像大小,分辨率为size*size的正方形
    :return:
    """
    global _avatar_default_timestamp

    size = request.args.get('s')
    try:
        # parameter validation check: original or 1~1024 resolution
        if size is not None:
            size_i = int(size)
            if size_i <= 0 or size_i > 1024:
                raise ValueError
        # 128bit hash: load avatar from "www.gravatar.com".
        if len(ava_hash) == 32:
            raise StandardError  # uncomment this line
            if datetime.date.today() == _avatar_default_timestamp:
                raise StandardError
            if request.is_secure:
                url = 'https://secure.gravatar.com/avatar/'
            else:
                url = 'http://www.gravatar.com/avatar/'
            url = url + '{hash}?d={d}&r={r}'.format(hash=hash, d='identicon', r='g')
            if size is not None:
                url = url + '&s=' + size
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
                return send_file(path) if size is None else send_file(thumbnail_image(path, int(size)))
            else:
                raise IOError
        # Invalid hash string
        else:
            raise StandardError
    # serving default avatar from local disk storage
    except StandardError:
        available_size = (16, 32, 64, 128, 256, 18, 40, 200)
        avatar_path = os.path.join(current_app.static_folder, 'img/avatar/')
        if size is None:
            return send_file(avatar_path + 'default_256.png', mimetype='image/png')
        elif int(size) in available_size:
            return send_file(
                avatar_path + 'default_{size}.png'.format(size=size),
                mimetype='image/png')
        else:
            return send_file(
                thumbnail_image(avatar_path + 'default_256.png', int(size)),
                mimetype='image/png')


@main.route('/upload-files', methods=['GET', 'POST'])
def upload_files():
    pass
