from flask import Blueprint


main = Blueprint('main', __name__)

auth = Blueprint('auth', __name__)

blog = Blueprint('blog', __name__)

movie = Blueprint('movie', __name__)

from . import main_views, auth_views, blog_views, movie_views, misc_views
