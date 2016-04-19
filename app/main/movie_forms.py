# encoding: utf-8
from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, SelectField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, URL

from ..models.movie import str_movie_type


def make_types_options():
    types_list = str_movie_type.split(u',')
    return [(str(i).decode('utf-8'), types_list[i]) for i in range(0, len(types_list))]


class PosterForm(Form):
    poster = FileField(u'电影海报')
    name = StringField(u'电影名', validators=[DataRequired(), Length(0, 50)])
    o_name = StringField(u'原名', validators=[Length(0, 50)])
    alias = StringField(u'别名', validators=[Length(0, 160)])
    director = StringField(u'导演', validators=[Length(0, 40)])
    screenwriter = StringField(u'编剧', validators=[Length(0, 40)])
    performers = StringField(u'主演', validators=[Length(0, 200)])
    type = SelectField(u'类型', choices=make_types_options(), validators=[])
    country = StringField(u'地区', validators=[Length(0, 100)])
    length = StringField(u'片长', validators=[Length(0, 60)])
    release_date = StringField(u'上映日期', validators=[Length(0, 60)])
    douban_link = StringField(u'豆瓣链接', validators=[Length(0, 80), URL()])
    introduction = TextAreaField(u'电影简介')
    submit = SubmitField(u'提交')


class StillForm(Form):
    snapshot = FileField(u'电影剧照')
    timeline = StringField(u'时间点', validators=[Length(1, 8)])  # 格式：%M:%S
    comment = StringField(u'我想说')
    submit = SubmitField(u'提交')


class StillForm2(Form):
    timeline = StringField(u'时间点', validators=[Length(1, 8)])
    comment = StringField(u'我想说')
    submit = SubmitField(u'更新')
