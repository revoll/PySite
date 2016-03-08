from flask import Blueprint

user = Blueprint('user', __name__)
user_np = Blueprint('user_np', __name__)

from . import views
