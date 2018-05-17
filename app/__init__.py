# -*- coding: utf-8 -*-
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_pagedown import PageDown
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()
login_manager = LoginManager()
login_manager.session_protection = u'strong'
login_manager.login_view = u'auth.login'


def create_app(config_name):
    from config import config
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    # 添加全局模板变量，使得在模板中可以直接使用该变量
    # app.add_template_global(moment, 'moment')

    if not app.debug and not app.testing and not app.config[u'SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    from .main import main_blueprint, auth_blueprint, \
        blog_blueprint, music_blueprint, movie_blueprint, photo_blueprint, utils_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(blog_blueprint)
    app.register_blueprint(photo_blueprint)
    app.register_blueprint(movie_blueprint)
    app.register_blueprint(music_blueprint)
    app.register_blueprint(utils_blueprint)

    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api_v1.0')

    return app
