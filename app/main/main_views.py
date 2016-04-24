# encoding: utf-8
import os

from flask import render_template, redirect, send_file, abort, url_for, flash, request, current_app, jsonify
from flask.ext.sqlalchemy import get_debug_queries
from flask.ext.login import login_required, current_user

from . import main
from .main_forms import EditProfileForm, EditProfileAdminForm
from .. import db
from ..models.user import User, Permission
from ..models.blog import Post
from ..tools.decorators import permission_required, admin_required


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


@main.route('/users/')
@login_required
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.member_since.desc()).paginate(
        page, per_page=current_app.config['FLASKY_USERS_PER_PAGE'], error_out=False)
    return render_template('user/users.html', users=pagination.items, pagination=pagination)


@main.route('/user/<username>/')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    return render_template('user/profile.html', user=user, posts=pagination.items, pagination=pagination)


@main.route('/edit-profile/', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('main.profile', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('user/edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>/', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.permission = Permission.index_array_to_value(form.permission.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('main.profile', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.permission.data = Permission.value_to_index_array(user.permission)
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('user/edit_profile.html', form=form, user=user)


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
