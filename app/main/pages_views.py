# encoding: utf-8
from flask import render_template

from . import pages


@pages.route('/')
def index():
    return render_template('pages/index.html')
