# encoding: utf-8
from flask.ext.wtf import Form
from wtforms import FileField


class PosterForm(Form):
    pass


class StillForm(Form):
    images = FileField()
