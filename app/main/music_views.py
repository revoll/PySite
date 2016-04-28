# encoding: utf-8
from flask import render_template

from . import music


@music.route('/')
def index():
    return render_template('music/index.html')
