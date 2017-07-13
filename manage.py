#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from flask import current_app
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
from app import create_app, db
from app.models.blog import BlogPost, BlogCategory, BlogTag
from app.models.movie import MoviePost, MovieStill, MovieCategory, MovieTag
from app.models.photo import PhotoPost, PhotoImage, PhotoCategory, PhotoTag


"""
Development Usage:
----------------------------------------------------------------
manage.py runserver  --passthrough-errors --no-reload
manage.py test/profile/deploy
"""


"""
Import Environment Variables from '.pysite_env'
----------------------------------------------------------------
"""
environment_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), u'.pysite_env')
if os.path.exists(environment_file):
    print u'Importing environment variables from \'%s\' ...' % environment_file
    for line in open(environment_file):
        if line[0] == u'#':  # comments
            continue
        kv = line.split(u'=', 1)
        if len(kv) == 2:
            os.environ[kv[0].strip()] = kv[1].split(u'#')[0].strip()
else:
    print u'Can not find environment file (%s)!' % environment_file
    exit()


COV = None
if os.environ.get(u'FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include=u'app/*')
    COV.start()


app = create_app(u'unix' or os.getenv(u'FLASK_CONFIG') or u'default')  # use 'unix' config
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db,
                BlogPost=BlogPost, BlogCategory=BlogCategory, BlogTag=BlogTag,
                MoviePost=MoviePost, MovieStill=MovieStill, MovieCategory=MovieCategory, MovieTag=MovieTag,
                PhotoPost=PhotoPost, PhotoImage=PhotoImage, PhotoCategory=PhotoCategory, PhotoTag=PhotoTag)
manager.add_command(u"shell", Shell(make_context=make_shell_context))
manager.add_command(u'db', MigrateCommand)


@manager.command
def test(coverage=False):
    """
    Runs the unit tests.
    """
    if coverage and not os.environ.get(u'FLASK_COVERAGE'):
        import sys
        os.environ[u'FLASK_COVERAGE'] = u'1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover(u'tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print(u'Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, u'tmp/coverage')
        COV.html_report(directory=covdir)
        print(u'HTML version: file://%s/index.html' % covdir)
        COV.erase()


@manager.command
def profile(length=25, profile_dir=None):
    """
    Starts the application under the code profiler.
    """
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length], profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    """
    Runs deployment tasks.
    """
    data_root = current_app.data_path
    if os.path.exists(data_root):
        print u'FAILED: Target directory \'%s\' already exists.' % data_root
        return

    print u'DEPLOY: Creating necessary directories for application data storage ...'
    data_dirs = [u'', u'blog', u'music', u'movie', u'photo', u'files', u'files/public']
    for dd in data_dirs:
        dir_new = os.path.join(data_root, dd)
        os.mkdir(dir_new)
        print u'    * Creating %s' % dir_new

    print u'DEPLOY: Preparing database ...'
    db.create_all()
    from app.models import blog, movie, photo
    db.session.add(blog.BlogCategory(id=0, name=u'未分类'))
    db.session.add(movie.MovieCategory(id=0, name=u'未分类'))
    db.session.add(photo.PhotoCategory(id=0, name=u'未分类'))

    print u'DEPLOY: Successfully finished!'
    print u'(Now you can start this project by running \'./manage.py runserver -t HOST -p PORT\')'


if __name__ == u'__main__':
    manager.run()
