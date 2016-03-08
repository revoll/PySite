# encoding: utf-8
from flask import redirect, url_for, abort, request, render_template, \
    current_app, jsonify
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
    return render_template('403.html'), 403


@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500


@main.route('/', methods=['GET', 'POST'])
def index():
    return redirect(url_for('blog.index'))


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


""" Test WTForm """
from flask.ext.wtf import Form
from wtforms import fields, validators


class TestForm(Form):
    # ul_widgets = widgets.ListWidget()
    # tb_widgets = widgets.TableWidget()
    str_field = fields.StringField(u'Simple String Field', [validators.required(), validators.length(max=10)],
                                   default='Input ...')
    smt_field = fields.SubmitField(u'提交所有')


@main.route('/test-form', methods=['GET', 'POST'])
def test_form():
    form = TestForm()
    if request.method == 'POST':
        redirect(url_for('main.test_form'))
    else:
        return render_template('test_form.html', form=form)
