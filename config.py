# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """ Application Configurations """
    SECRET_KEY = os.environ.get(u'SECRET_KEY') or os.urandom(24)
    SSL_DISABLE = True

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    SLOW_DB_QUERY_TIME = 0.5

    MAIL_SERVER = os.environ.get(u'MAIL_SERVER')
    MAIL_PORT = int(os.environ.get(u'MAIL_PORT') or u'25')
    MAIL_USERNAME = os.environ.get(u'MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get(u'MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = u'[PySite]'
    MAIL_SENDER = u'PySite Admin <%s>' % os.environ.get(u'MAIL_USERNAME')
    MAIL_NOTIFICATION = u'MAIL NOTIFICATION BOYD HERE....'

    @staticmethod
    def init_app(app):
        app.data_path = os.path.join(basedir, u'data')


#
# Config example for 'SQLALCHEMY_DATABASE_URI':
#
# MYSQL  : u'mysql://flasky:654321@localhost/pysite'
# SQLite : u'sqlite:///' + os.path.join(basedir, u'data/data.sqlite')
#


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = u'sqlite:///' + os.path.join(basedir, u'data/data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = u'sqlite:///' + os.path.join(basedir, u'data/data-test.sqlite')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = u'sqlite:///' + os.path.join(basedir, u'data/data.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, u'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, u'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=[cls.MAIL_NOTIFICATION],
            subject=cls.MAIL_SUBJECT_PREFIX + u'Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    u'development': DevelopmentConfig,
    u'testing': TestingConfig,
    u'production': ProductionConfig,
    u'unix': UnixConfig,
    u'default': DevelopmentConfig
}
