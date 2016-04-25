# encoding: utf-8
from datetime import datetime
import hashlib

from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, url_for
from flask.ext.login import UserMixin, AnonymousUserMixin

from .. import db, login_manager


class Permission:
    """
    * 各个板块权限说明：
        XXX_CREATE - 创建新的内容
        XXX_BROWSE - 查看板块中的内容
        XXX_MODIFY - 修改其它用户的内容
        XXX_DELETE - 删除其它用户的内容
    * 内容访问权限设置说明（以博客为例）：
        仅自己可见： ADMIN_SUPER
        自定义权限： e.g. BLOG_MODIFY | BLOG_DELETE | ...
        完全地公开： 0x00
    """
    # 电影剧照
    CREATE_STILLS = 1 << 0
    BROWSE_STILLS = 1 << 1
    MODIFY_STILLS = 1 << 2
    DELETE_STILLS = 1 << 3
    # 电影海报
    CREATE_POSTER = 1 << 4
    BROWSE_POSTER = 1 << 5
    MODIFY_POSTER = 1 << 6
    DELETE_POSTER = 1 << 7
    # 资源
    UPLOAD_FILES = 1 << 8
    BROWSE_FILES = 1 << 9

    # 各个权限标志位的说明，可用于表单展示
    detail = [
        (0, 'Poster - Create'),
        (1, 'Poster - Browse'),
        (2, 'Poster - Modify'),
        (3, 'Poster - Delete'),

        (4, 'Stills - Create'),
        (5, 'Stills - Browse'),
        (6, 'Stills - Modify'),
        (7, 'Stills - Delete'),

        (8, 'Files - Upload'),
        (9, 'Files - Browse'),
    ]

    roles = {
        # 开放最基本的权限，仅能一般性地浏览网站公开的内容
        'administrator': 0x7FFFFFFFFFFFFFFF,
        'anonymous': (1 << BROWSE_POSTER) | (1 << BROWSE_STILLS),
        'default': (1 << BROWSE_STILLS) | (1 << CREATE_STILLS) | (1 << BROWSE_POSTER) | (1 << BROWSE_FILES),
    }

    def __init__(self):
        pass


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=1000001)  # autoincrement takes no effect here.
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    permission = db.Column(db.BigInteger, default=Permission.roles['default'])  # 64bit ?
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar = db.Column(db.String(32))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    posters = db.relationship('Poster', backref='author', lazy='dynamic')
    stills = db.relationship('Still', backref='author', lazy='dynamic')

    @staticmethod
    def on_changed_email(target, value, oldvalue, initiator):
        if value is not None:
            target.avatar = hashlib.md5(value.encode('utf-8')).hexdigest()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.permission is None and self.email == current_app.config['FLASKY_SUPER_ADMIN']:
            self.permission = Permission.roles['super_admin']

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def gravatar(self, size=128):
        # if request.is_secure:
        #    url = 'https://secure.gravatar.com/avatar'
        # else:
        #    url = 'http://www.gravatar.com/avata'
        ava_hash = self.avatar or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}?s={size}'.format(url=url_for('main.get_avatar', ava_hash=ava_hash), size=size)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def can(self, permission):
        return (self.permission & permission) == permission

    def is_admin(self):
        return self.permission == Permission.roles['administrator']

    """
    def to_json(self):
        json_user = {
            'url': url_for('api.get_post', id=self.id, _external=True),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts': url_for('api.get_user_posts', id=self.id, _external=True),
            'followed_posts': url_for('api.get_user_followed_posts',
                                      id=self.id, _external=True),
            'post_count': self.posts.count()
        }
        return json_user

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])
    """
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<User %r>' % self.username


db.event.listen(User.email, 'set', User.on_changed_email)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permission):
        return (Permission.roles['anonymous'] & permission) == permission

    def is_admin(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
