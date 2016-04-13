# encoding: utf-8
from datetime import datetime

from flask import url_for

from .. import db
from ..models.user import User

str_country = u'中国大陆,香港,台湾,' \
              u'美国,日本,英国,法国,韩国,德国,意大利,印度,泰国,西班牙,欧洲,加拿大,澳大利亚,俄罗斯,伊朗,爱尔兰,' \
              u'瑞典,巴西,波兰,丹麦,捷克,阿根廷,比利时,墨西哥,奥地利,荷兰,新西兰,土耳其,匈牙利,以色列,新加坡'

str_movie_type = u'动作与历险,儿童与家庭,喜剧,剧情,爱情,恐怖与惊悚,科幻与奇幻,记录与传记,动画,情色,其他'


class Poster(db.Model):
    __tablename__ = 'posters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    alias = db.Column(db.String(100))
    director = db.Column(db.String(20))
    performers = db.Column(db.String(180))
    length = db.Column(db.Integer)
    release_date = db.Column(db.Date)
    douban_link = db.Column(db.String(80))
    type_id = db.Column(db.Integer, db.ForeignKey('movie_type.id'))
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    introduction = db.Column(db.Text)
    stills = db.relationship('Still', backref='poster', lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import forgery_py
        seed()
        num_country = Country.query.count()
        num_type = MovieType.query.count()
        num_author = User.query.count()
        for i in range(count):
            p = Poster()
            p.name = forgery_py.lorem_ipsum.title()
            p.alias = u'(Empty)'
            p.director = forgery_py.name.full_name()
            p.performers = forgery_py.name.full_name() + u'/' + forgery_py.name.full_name() + u'/' + forgery_py.name.full_name()
            p.length = randint(90, 180)
            p.release_date = forgery_py.date.date()
            p.douban_link = u'http://movie.douban.com/' + forgery_py.internet.domain_name()
            p.type_id = randint(0, num_type)
            p.country_id = randint(0, num_country)
            p.author_id = randint(0, num_author)
            p.timestamp = forgery_py.date.date(True)
            p.introduction = forgery_py.lorem_ipsum.sentences(randint(1, 5))
            db.session.add(p)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    def to_json(self):
        json_post = {
            # 'url': url_for('api.get_poster', id=self.id, _external=True),
            'name': self.name,
            'alias': self.alias,
            'director': self.director,
            'performers': self.performers,
            'length': self.length,
            'release_date': self.release_date,
            'douban_link': self.douban_link,
            'type': MovieType.query.filter_by(id=self.type_id).first().name,
            'country': Country.query.filter_by(id=self.country_id).first().name,
            'author': url_for('api.get_user', id=self.author_id, _external=True),
            'introduction': self.introduction,
            'timestamp': self.timestamp
        }
        return json_post


class Country(db.Model):
    __tablename__ = 'country'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True)
    posters = db.relationship('Poster', backref='country', lazy='dynamic')

    @staticmethod
    def insert_countries():
        countries = str_country.split(u',')
        for c in countries:
            country = Country.query.filter_by(name=c).first()
            if country is None:
                country = Country(name=c)
            db.session.add(country)
        db.session.commit()


class MovieType(db.Model):
    __tablename__ = 'movie_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True)
    posters = db.relationship('Poster', backref='type', lazy='dynamic')

    @staticmethod
    def insert_types():
        types = str_movie_type.split(u',')
        for t in types:
            type = MovieType.query.filter_by(name=t).first()
            if type is None:
                type = MovieType(name=t)
            db.session.add(type)
        db.session.commit()


class Still(db.Model):
    __tablename__ = 'stills'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    poster_id = db.Column(db.Integer, db.ForeignKey('posters.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
