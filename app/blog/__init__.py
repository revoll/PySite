from flask import Blueprint

blog = Blueprint('blog', __name__)

from . import views
