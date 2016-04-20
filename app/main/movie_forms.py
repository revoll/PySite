# encoding: utf-8
from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, SelectField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, URL, Regexp

from ..models.movie import str_movie_type


def make_types_options():
    types_list = str_movie_type.split(u',')
    return [(str(i).decode('utf-8'), types_list[i]) for i in range(0, len(types_list))]


class PosterForm(Form):
    name = StringField(u'电影名', validators=[DataRequired(), Length(0, 50)])
    o_name = StringField(u'原名', validators=[Length(0, 50)])
    alias = StringField(u'别名', validators=[Length(0, 160)])
    director = StringField(u'导演', validators=[Length(0, 40)])
    screenwriter = StringField(u'编剧', validators=[Length(0, 40)])
    performers = StringField(u'主演', validators=[Length(0, 200)])
    type = SelectField(u'类型', choices=make_types_options(), validators=[Regexp(u'^\d+$')])
    country = StringField(u'地区', validators=[Length(0, 100)])
    length = StringField(u'片长', validators=[Length(0, 60)])
    release_date = StringField(u'上映日期', validators=[Length(0, 60)])
    douban_link = StringField(u'豆瓣链接', validators=[Length(0, 80), URL()])
    method = SelectField(u'上传方式', choices=[(u'file', u'本地图片'), (u'url', u'网络图片')], validators=[Regexp(u'^file|url$')])
    img_file = FileField(u'海报图片')
    img_url = StringField(u'海报URL', validators=[])
    introduction = TextAreaField(u'电影简介')
    submit = SubmitField(u'提交')


class StillForm(Form):
    time_min = StringField(u'时间（分）', validators=[Regexp(u'^\d{0,3}$')])
    time_sec = StringField(u'时间（秒）', validators=[Regexp(u'^\d{0,2}$')])
    method = SelectField(u'上传方式', choices=[(u'file', u'本地图片'), (u'url', u'网络图片')], validators=[Regexp(u'^file|url$')])
    img_file = FileField(u'剧照图片')
    img_url = StringField(u'剧照URL', validators=[])
    comment = StringField(u'我想说')
    submit = SubmitField(u'提交')


class StillForm2(Form):
    time_min = StringField(u'时间（分）', validators=[Regexp(u'^\d{1,3}$')])
    time_sec = StringField(u'时间（秒）', validators=[Regexp(u'^\d{1,2}$')])
    comment = StringField(u'我想说')
    submit = SubmitField(u'更新')
