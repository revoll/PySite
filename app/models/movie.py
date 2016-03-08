# encoding: utf-8
from datetime import datetime

from .. import db


class Poster(db.Model):
    __tablename__ = 'posters'
    id = db.Column(db.Integer, primary_key=True)
    introduction = db.Column(db.text)
    performer = db.Column(db.text)
    release = db.Column(db.Date)
    cover = db.Column(db.Integer, db.ForeignKey('stills.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    film_stills = db.relationship('Stills', backref='Poster', lazy='dynamic')


class Stills(db.Model):
    __tablename__ = 'stills'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.CHAR(10))
    comment = db.Column(db.text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    poster_id = db.Column(db.Integer, db.ForeignKey('posters.id'))
