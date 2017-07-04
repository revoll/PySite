# -*- coding: utf-8 -*-
from flask import Blueprint


main_blueprint = Blueprint(u'main', __name__)
auth_blueprint = Blueprint(u'auth', __name__, url_prefix=u'/auth')
blog_blueprint = Blueprint(u'blog', __name__, url_prefix=u'/blog')
music_blueprint = Blueprint(u'music', __name__, url_prefix=u'/music')
movie_blueprint = Blueprint(u'movie', __name__, url_prefix=u'/movie')
photo_blueprint = Blueprint(u'photo', __name__, url_prefix=u'/photo')
files_blueprint = Blueprint(u'files', __name__, url_prefix=u'/files')

from . import main_views, auth_views, blog_views, movie_views, music_views, photo_views, files_views
