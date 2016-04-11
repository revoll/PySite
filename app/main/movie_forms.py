# encoding: utf-8
from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, SelectField, \
    SubmitField, DateField, IntegerField, FileField
from wtforms.validators import DataRequired, Length
from ..models.movie import str_country, str_movie_type


def make_country_options():
    country_list = str_country.split(u',')
    return [(country_list[i], i) for i in range(0, len(country_list))]


def make_types_options():
    types_list = str_movie_type.split(u',')
    return [(types_list[i], i) for i in range(0, len(types_list))]


class PosterForm(Form):
    name = StringField(u'电影名', validators=[DataRequired(), Length(0, 100)])
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
