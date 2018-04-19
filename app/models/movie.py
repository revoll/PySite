# -*- coding: utf-8 -*-
import os
from datetime import datetime
from flask import current_app
from .. import db


"""
str_country = u'中国大陆,香港,台湾,' \
              u'美国,日本,英国,法国,韩国,德国,意大利,印度,泰国,西班牙,欧洲,加拿大,澳大利亚,俄罗斯,伊朗,爱尔兰,' \
              u'瑞典,巴西,波兰,丹麦,捷克,阿根廷,比利时,墨西哥,奥地利,荷兰,新西兰,土耳其,匈牙利,以色列,新加坡'
"""


class MovieCategory(db.Model):
    """ 类型（目录） """
    __tablename__ = u'movie_category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    private = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, default=False)

    tags = db.relationship(u'MovieTag', back_populates=u'category', lazy=u'dynamic')
    posts = db.relationship(u'MoviePost', back_populates=u'category', lazy=u'dynamic')

    def to_json(self):
        json_type = {
            u'id': self.id,
            u'name': self.name,
            u'private': self.private,
            u'disabled': self.disabled,
            u'tags': [t.to_json() for t in self.tags]
        }
        return json_type

    @staticmethod
    def on_changed_name(target, value, oldvalue, initiator):
        new_path = os.path.join(current_app.data_path, u'movie', value)
        old_path = os.path.join(current_app.data_path, u'movie', oldvalue) if target.id else None
        if old_path and os.path.exists(old_path):
            os.rename(old_path, new_path)
        else:
            os.makedirs(new_path)

    @staticmethod
    def after_delete(mapper, connection, target):
        os.rmdir(os.path.join(current_app.data_path, u'movie', target.name))

db.event.listen(MovieCategory.name, u'set', MovieCategory.on_changed_name)
db.event.listen(MovieCategory, u'after_delete', MovieCategory.after_delete)


class MovieTagging(db.Model):
    """ Post与标签关联表 """
    __tablename__ = u're_movie_tag'

    post_id = db.Column(db.Integer, db.ForeignKey(u'movie_post.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey(u'movie_tag.id'), primary_key=True)


class MovieTag(db.Model):
    """ 标签 """
    __tablename__ = u'movie_tag'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(12), nullable=False)  # unique=False
    category_id = db.Column(db.Integer, db.ForeignKey(u'movie_category.id'), nullable=False)

    category = db.relationship(u'MovieCategory', back_populates=u'tags')
    posts = db.relationship(u'MoviePost', secondary=u're_movie_tag', back_populates=u'tags', lazy=u'dynamic')

    def to_json(self):
        json_tag = {
            u'id': self.id,
            u'name': self.name,
            u'category_id': self.category_id
        }
        return json_tag


class MoviePost(db.Model):
    """ 电影海报 """
    __tablename__ = u'movie_post'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey(u'movie_category.id'), nullable=False)
    private = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    reference = db.Column(db.String(80), default=u'')  # i.e. https://movie.douban.com/...
    name = db.Column(db.String(50), unique=True)
    o_name = db.Column(db.String(50), default=u'')
    alias = db.Column(db.String(160), default=u'')
    director = db.Column(db.String(40), default=u'')
    screenwriter = db.Column(db.String(40), default=u'')
    performers = db.Column(db.String(200), default=u'')
    length = db.Column(db.String(60), default=u'')
    release_date = db.Column(db.String(60), default=u'')
    country = db.Column(db.String(100), default=u'')
    introduction = db.Column(db.Text, default=u'')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    last_modify = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship(u'MovieCategory', back_populates=u'posts')
    tags = db.relationship(u'MovieTag', secondary=u're_movie_tag', back_populates=u'posts')
    stills = db.relationship(u'MovieStill', backref=u'post', lazy=u'dynamic')

    def ping(self):
        self.view_count += 1
        db.session.merge(self)

    @staticmethod
    def on_changed_category(target, value, oldvalue, initiator):
        target.tags = []

db.event.listen(MoviePost.category_id, u'set', MoviePost.on_changed_category)


class MovieStill(db.Model):
    """ 电影剧照 """
    __tablename__ = u'movie_still'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timeline = db.Column(db.Integer, default=0)
    comment = db.Column(db.Text, default=u'')
    post_id = db.Column(db.Integer, db.ForeignKey(u'movie_post.id'))
    private = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def timeline_str_to_int(str_min, str_sec):
        if str_min == u'':
            str_min = u'0'
        if str_sec == u'':
            str_sec = u'0'
        try:
            time = int(str_min) * 60 + int(str_sec)
        except ValueError:
            return 0
        return time

    @staticmethod
    def timeline_int_to_str(int_time):
        if int_time < 0:
            int_time = 0
        sec = int_time % 60
        min = int_time / 60
        return str(min), str(sec)
