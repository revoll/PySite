# encoding: utf-8
from flask import render_template
from flask.ext.login import login_required

from . import files
from ..models.user import Permission
from ..tools.decorators import permission_required


@files.route('/')
@login_required
def index():
    return render_template('files/index.html')


@files.route('/upload/')
@login_required
def upload():
    return 'files - upload()'


@files.route('/rename/')
@permission_required(Permission.ADMIN_FILES)
def rename():
    return 'files - rename()'


@files.route('/move/')
@permission_required(Permission.ADMIN_FILES)
def move():
    return 'files - move()'


@files.route('/delete/')
@permission_required(Permission.ADMIN_FILES)
def delete():
    return 'files - delete()'
