# encoding: utf-8
from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, SelectField, \
    SubmitField, DateField, IntegerField, FileField
from wtforms.validators import Required, Length

from ..models.movie import MovieType, Country


def make_country_options():
    country_list = Country.get_country_list()
    options = []
    for item in country_list:
        options.append((country_list[item], item))
    return options


def make_types_options():
    types_list = MovieType.get_types_list()
    options = []
    for item in types_list:
        options.append((types_list[item], item))
    return options


class PosterForm(Form):
    name = StringField(u'电影名', validators=[Required(), Length(0, 100)])
    alisa = StringField(u'翻译', validators=[Length(0, 100)])
    director = StringField(u'导演', validators=[Length(0, 20)])
    performers = StringField(u'主演', validators=[Length(0, 180)])
    type = SelectField(u'类型', choices=make_types_options())
    country = StringField(u'地区', choices=make_country_options())
    length = IntegerField(u'片长', 0)
    release_date = DateField(u'上映日期')
    douban_link = StringField(u'豆瓣链接', validators=[Length(0, 20)])
    introduction = TextAreaField()
    submit = SubmitField(u'Submit')

class StillForm(Form):
    images = FileField()
    submit = SubmitField('上传图片')
