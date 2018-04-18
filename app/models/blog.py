# -*- coding: utf-8 -*-
import bleach
from datetime import datetime
from markdown import markdown
from .. import db


class BlogCategory(db.Model):
    """ 类型（目录） """
    __tablename__ = u'blog_category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    private = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, default=False)

    tags = db.relationship(u'BlogTag', back_populates=u'category', lazy=u'dynamic')
    posts = db.relationship(u'BlogPost', back_populates=u'category', lazy=u'dynamic')

    def to_json(self):
        json_type = {
            u'id': self.id,
            u'name': self.name,
            u'private': self.private,
            u'disabled': self.disabled,
            u'tags': [t.to_json() for t in self.tags]
        }
        return json_type


class BlogTagging(db.Model):
    """ Post与标签关联表 """
    __tablename__ = u're_blog_tag'

    post_id = db.Column(db.Integer, db.ForeignKey(u'blog_post.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey(u'blog_tag.id'), primary_key=True)


class BlogTag(db.Model):
    """ 标签 """
    __tablename__ = u'blog_tag'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(12), nullable=False)  # unique=False
    category_id = db.Column(db.Integer, db.ForeignKey(u'blog_category.id'), nullable=False)

    category = db.relationship(u'BlogCategory', back_populates=u'tags')
    posts = db.relationship(u'BlogPost', secondary=u're_blog_tag', back_populates=u'tags', lazy=u'dynamic')

    def to_json(self):
        json_tag = {
            u'id': self.id,
            u'name': self.name,
            u'category_id': self.category_id
        }
        return json_tag


class BlogPost(db.Model):
    """ 博客文章 """
    __tablename__ = u'blog_post'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey(u'blog_category.id'))
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, default=u'')
    body_html = db.Column(db.Text, default=u'')
    private = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship(u'BlogCategory', back_populates=u'posts')
    tags = db.relationship(u'BlogTag', secondary=u're_blog_tag', back_populates=u'posts')

    @staticmethod
    def on_changed_category(target, value, oldvalue, initiator):
        target.tags = []

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = [u'a', u'abbr', u'acronym', u'b', u'blockquote', u'code',
                        u'em', u'i', u'li', u'ol', u'pre', u'strong', u'ul',
                        u'h1', u'h2', u'h3', u'p', u'img']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format=u'html'), tags=allowed_tags, strip=True))

db.event.listen(BlogPost.category_id, u'set', BlogPost.on_changed_category)
# db.event.listen(BlogPost.body, 'set', BlogPost.on_changed_body)
