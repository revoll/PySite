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
    def __init__(self):
        pass

    # 评论
    CREATE_COMMENT = 0
    BROWSE_COMMENT = 1
    MODIFY_COMMENT = 2
    DELETE_COMMENT = 3

    # 博客
    CREATE_BLOG = 4
    BROWSE_BLOG = 5
    MODIFY_BLOG = 6
    DELETE_BLOG = 7

    # 电影海报
    CREATE_POSTER = 8
    BROWSE_POSTER = 9
    MODIFY_POSTER = 10
    DELETE_POSTER = 11

    # 电影剧照
    CREATE_STILLS = 12
    BROWSE_STILLS = 13
    MODIFY_STILLS = 14
    DELETE_STILLS = 15

    # 管理所有用户的对应板块的内容
    ADMIN_COMMENT = 56
    ADMIN_BLOG = 57
    ADMIN_POSTER = 58
    ADMIN_STILLS = 59
    ADMIN_SUPER = 62  # 最高位不使用，因为数据库使用64位有符号长整形类型

    @staticmethod
    def index_to_value(index):
        if (index >= 0) and (index < 64):
            return 1 << index
        else:
            raise ValueError

    @staticmethod
    def value_to_index(value):
        index = 0
        while value > 1:
            index += 1
            value >>= 1
        return index

    @staticmethod
    def index_array_to_value(index_array):
        value = 0
        for index in index_array:
            value |= Permission.index_to_value(index)
        return value

    @staticmethod
    def value_to_index_array(value):
        index_array = []
        counter = 0
        while value > 0:
            if value & 1:
                index_array.append(counter)
            value >>= 1
            counter += 1
        return index_array

    # 开放最基本的权限，仅能一般性地浏览网站公开的内容
    BASIC = (1 << CREATE_COMMENT) | (1 << BROWSE_COMMENT) | \
            (1 << BROWSE_BLOG) | (1 << BROWSE_POSTER) | (1 << BROWSE_STILLS)
    ANONYMOUS = BASIC
    SUPER_ADMIN = 0x7FFFFFFFFFFFFFFF | (1 << ADMIN_SUPER)


permission_detail = [

    (Permission.CREATE_COMMENT, 'Comment - Create'),
    (Permission.BROWSE_COMMENT, 'Comment - Browse'),
    (Permission.MODIFY_COMMENT, 'Comment - Modify'),
    (Permission.DELETE_COMMENT, 'Comment - Delete'),

    (Permission.CREATE_BLOG, 'Blog - Create'),
    (Permission.BROWSE_BLOG, 'Blog - Browse'),
    (Permission.MODIFY_BLOG, 'Blog - Modify'),
    (Permission.DELETE_BLOG, 'Blog - Delete'),

    (Permission.CREATE_POSTER, 'Poster - Create'),
    (Permission.BROWSE_POSTER, 'Poster - Browse'),
    (Permission.MODIFY_POSTER, 'Poster - Modify'),
    (Permission.DELETE_POSTER, 'Poster - Delete'),

    (Permission.CREATE_STILLS, 'Stills - Create'),
    (Permission.BROWSE_STILLS, 'Stills - Browse'),
    (Permission.MODIFY_STILLS, 'Stills - Modify'),
    (Permission.DELETE_STILLS, 'Stills - Delete'),

    (Permission.ADMIN_COMMENT, 'Admin - Comment'),
    (Permission.ADMIN_BLOG, 'Admin - Blog'),
    (Permission.ADMIN_POSTER, 'Admin - Poster'),
    (Permission.ADMIN_STILLS, 'Admin - Stills'),
    (Permission.ADMIN_SUPER, 'Admin - Super!'),
]


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=1000001)  # autoincrement takes no effect here.
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    permission = db.Column(db.BigInteger, default=Permission.BASIC)  # 64bit ?
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
            self.permission = -1

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
        hash = self.avatar or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}?s={size}'.format(url=url_for('main.get_avatar', ava_hash=hash), size=size)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def can(self, permissions):
        check = 1 << permissions
        return (self.permission & check) == check

    def is_super_admin(self):
        return self.permission & Permission.ADMIN_SUPER

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
    def can(self, permissions):
        return (Permission.ANONYMOUS & permissions) == permissions

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
