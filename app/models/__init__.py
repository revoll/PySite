# -*- coding: utf-8 -*-
from datetime import date, datetime
from .. import db


class Passbook(db.Model):
    """
    密码簿数据库
    """
    __tablename__ = u'my_passbook'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(20), default=u'')
    name = db.Column(db.String(40), nullable=False)
    host = db.Column(db.String(40), nullable=False)
    username = db.Column(db.String(40), default=u'')
    password = db.Column(db.Text, default=u'')
    comments = db.Column(db.Text, default=u'')

    def to_json(self):
        json_type = {
            u'id': self.id,
            u'keyword': self.keyword,
            u'name': self.name,
            u'host': self.host,
            u'username': self.username,
            u'password': self.password,
            u'comments': self.comments
        }
        return json_type


class Cashbook(db.Model):
    """
    记账本数据库
    """
    __tablename__ = u'my_cashbook'

    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(80), default=u'', nullable=False)
    amount = db.Column(db.Float, default=0.0)
    method = db.Column(db.String(20), default=u'现金')
    date = db.Column(db.DATE, default=date.today)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_json(self):
        json_type = {
            u'id': self.id,
            u'comment': self.comment,
            u'amount': self.amount,
            u'method': self.method,
            u'date': self.date,
            u'timestamp': self.timestamp
        }
        return json_type
