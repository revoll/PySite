# encoding: utf-8
from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, SelectField, \
    SubmitField, FileField
from wtforms.validators import DataRequired, Length

from ..models.movie import str_movie_type


def make_types_options():
    types_list = str_movie_type.split(u',')
    return [(types_list[i], i) for i in range(0, len(types_list))]


class PosterForm(Form):
    poster = FileField()
    name = StringField(u'电影名', validators=[DataRequired(), Length(0, 100)])
    alisa = StringField(u'翻译', validators=[Length(0, 160)])
    director = StringField(u'导演', validators=[Length(0, 20)])
    performers = StringField(u'主演', validators=[Length(0, 180)])
    type = SelectField(u'类型', choices=make_types_options())
    country = StringField(u'地区', validators=[Length(0, 120)])
    length = StringField(u'片长', validators=[Length(0, 60)])
    release_date = StringField(u'上映日期', validators=[Length(0, 60)])
    douban_link = StringField(u'豆瓣链接', validators=[Length(0, 80)])
    introduction = TextAreaField()
    submit = SubmitField(u'Submit')


class StillForm(Form):
    images = FileField()
    submit = SubmitField('上传图片')
