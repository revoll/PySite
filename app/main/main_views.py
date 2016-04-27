# encoding: utf-8
import os

from flask import render_template, redirect, url_for, send_file, abort, flash, request, current_app, jsonify
from flask.ext.sqlalchemy import get_debug_queries

from . import main
from ..models.user import Permission


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.app_errorhandler(403)
def forbidden(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    return render_template('common/403.html'), 403


@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('common/404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('common/500.html'), 500


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/crossdomain.xml')
def get_crossdomain():
    return send_file(os.path.join(current_app.static_folder, 'crossdomain.xml'))


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/init-db')
def init_db():
    from .. import db
    from ..models.movie import MovieType

    # db.drop_all()
    db.create_all()
    MovieType.insert_types()
    # User.generate_fake()
    # Post.generate_fake()
    # Poster.generate_fake()
    flash('init db with success.')

    return redirect(url_for('.index'))
