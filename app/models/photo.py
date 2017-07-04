# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
from flask import current_app
from .. import db


class PhotoCategory(db.Model):
    """ 类型（目录） """
    __tablename__ = u'photo_category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    private = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, default=False)

    tags = db.relationship(u'PhotoTag', back_populates=u'category', lazy=u'dynamic')
    posts = db.relationship(u'PhotoPost', back_populates=u'category', lazy=u'dynamic')

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
        new_path = os.path.join(current_app.data_path, u'photo', value)
        old_path = os.path.join(current_app.data_path, u'photo', oldvalue) if target.id else None
        if old_path and os.path.exists(old_path):
            os.rename(old_path, new_path)
        else:
            os.makedirs(new_path)

    @staticmethod
    def after_delete(mapper, connection, target):
        os.rmdir(os.path.join(current_app.data_path, u'photo', target.name))

db.event.listen(PhotoCategory.name, u'set', PhotoCategory.on_changed_name)
db.event.listen(PhotoCategory, u'after_delete', PhotoCategory.after_delete)


class PhotoTagging(db.Model):
    """ Post与标签关联表 """
    __tablename__ = u're_photo_tag'

    post_id = db.Column(db.Integer, db.ForeignKey(u'photo_post.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey(u'photo_tag.id'), primary_key=True)


class PhotoTag(db.Model):
    """ 标签 """
    __tablename__ = u'photo_tag'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(12), nullable=False)  # unique=False
    category_id = db.Column(db.Integer, db.ForeignKey(u'photo_category.id'), nullable=False)

    category = db.relationship(u'PhotoCategory', back_populates=u'tags')
    posts = db.relationship(u'PhotoPost', secondary=u're_photo_tag', back_populates=u'tags', lazy=u'dynamic')

    def to_json(self):
        json_tag = {
            u'id': self.id,
            u'name': self.name,
            u'category_id': self.category_id
        }
        return json_tag


class PhotoPost(db.Model):
    """ 图片相册 """
    __tablename__ = u'photo_post'

    id = db.Column(db.Integer, primary_key=True, autoincrement=1000001)
    category_id = db.Column(db.Integer, db.ForeignKey(u'photo_category.id'))
    private = db.Column(db.Boolean, default=False)
    title = db.Column(db.String(100), default=u'无标题的图册')
    persons = db.Column(db.String(100), default=u'')
    address = db.Column(db.String(140), default=u'')
    introduction = db.Column(db.Text, default=u'')
    count = db.Column(db.Integer, default=0)  # 图片数量
    index = db.Column(db.Integer, default=0)  # 图片命名计数器，从index+1开始命名
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())

    category = db.relationship(u'PhotoCategory', back_populates=u'posts')
    tags = db.relationship(u'PhotoTag', secondary=u're_photo_tag', back_populates=u'posts')
    images = db.relationship(u'PhotoImage', backref=u'post', lazy=u'dynamic')

    @staticmethod
    def on_changed_category(target, value, oldvalue, initiator):
        target.tags = []

db.event.listen(PhotoPost.category_id, u'set', PhotoPost.on_changed_category)


class PhotoImage(db.Model):
    """ 相册图片 """
    __tablename__ = u'photo_image'

    id = db.Column(db.Integer, primary_key=True, autoincrement=1)
    post_id = db.Column(db.Integer, db.ForeignKey(u'photo_post.id'))
    private = db.Column(db.Boolean, default=False)
    f_name = db.Column(db.String(40), nullable=False)
    comment = db.Column(db.Text, default=u'')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())
