# -*- coding: utf-8 -*-
import hashlib
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from .. import db, login_manager


class Permission():
    """
    系统资源访问权限: 每个权限用一位表示.
    """
    LOGIN_BASIC = 1 << 0

    CURD_BLOG = 1 << 1
    CURD_MUSIC = 1 << 2
    CURD_MOVIE = 1 << 3
    CURD_PHOTO = 1 << 4

    VIEW_PRIVATE_BLOG = 1 << 5
    VIEW_PRIVATE_MUSIC = 1 << 6
    VIEW_PRIVATE_MOVIE = 1 << 7
    VIEW_PRIVATE_PHOTO = 1 << 8

    CURD_ALL = CURD_BLOG | CURD_MUSIC | CURD_MOVIE | CURD_PHOTO
    VIEW_PRIVATE = VIEW_PRIVATE_BLOG | VIEW_PRIVATE_MUSIC | VIEW_PRIVATE_MOVIE | VIEW_PRIVATE_PHOTO

    # 系统管理角色,不包含查看私有内容及编辑内容权限.
    ADMIN = 1 << 31


class Role():
    """
    用户角色(权限集): 每一位代表一种权限,由Permission经过"与"操作计算得出.
    为简单起见,系统不支持根据用户角色赋予对应的权限集合.这里定义的`Role`类只用作权限初始化赋值,修改用户权限只能通过后台手动修改.
    """
    USER = Permission.LOGIN_BASIC
    ROOT = 0xffffffff
    ADMIN = USER | Permission.ADMIN
    DEFAULT = USER


class User(UserMixin, db.Model):
    __tablename__ = u'user'
    id = db.Column(db.Integer, primary_key=True)
    confirmed = db.Column(db.Boolean, default=False)
    permissions = db.Column(db.Integer, default=Role.DEFAULT)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode(u'utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError(u'password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config[u'SECRET_KEY'], expiration)
        return s.dumps({u'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config[u'SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get(u'confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config[u'SECRET_KEY'], expiration)
        return s.dumps({u'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config[u'SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get(u'reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config[u'SECRET_KEY'], expiration)
        return s.dumps({u'change_email': self.id, u'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config[u'SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get(u'change_email') != self.id:
            return False
        new_email = data.get(u'new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode(u'utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return (self.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default=u'identicon', rating=u'g'):
        if request.is_secure:
            url = u'https://secure.gravatar.com/avatar'
        else:
            url = u'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode(u'utf-8')).hexdigest()
        return u'{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    """
    def to_json(self):
        json_user = {
            u'url': url_for(u'api.get_user', id=self.id, _external=True),
            u'username': self.username,
            u'member_since': self.member_since,
            u'last_seen': self.last_seen,
        }
        return json_user

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config[u'SECRET_KEY'], expires_in=expiration)
        return s.dumps({u'id': self.id}).decode(u'ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config[u'SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data[u'id'])
    """

    def __repr__(self):
        return u'<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
