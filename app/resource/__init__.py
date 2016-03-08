from flask import Blueprint

# resource = Blueprint('resource', __name__)
upload = Blueprint('upload', __name__)
image = Blueprint('image', __name__)

from . import views
