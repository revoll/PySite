# encoding: utf-8
from flask import render_template, redirect, url_for, flash, request, current_app
from flask.ext.login import login_required, current_user

from . import user
from .user_forms import EditProfileForm, EditProfileAdminForm
from .. import db
from ..models.user import User
from ..models.blog import Post
from ..tools.decorators import admin_required


def index_to_value(index):
    if (index >= 0) and (index < 64):
        return 1 << index
    else:
        raise ValueError


def value_to_index(value):
    index = 0
    while value > 1:
        index += 1
        value >>= 1
    return index


def index_array_to_value(index_array):
    value = 0
    for index in index_array:
        value |= index_to_value(index)
    return value


def value_to_index_array(value):
    index_array = []
    counter = 0
    while value > 0:
        if value & 1:
            index_array.append(counter)
        value >>= 1
        counter += 1
    return index_array


@user.route('/')
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.member_since.desc()).paginate(
        page, per_page=current_app.config['FLASKY_USERS_PER_PAGE'], error_out=False)
    return render_template('user/users.html', users=pagination.items, pagination=pagination)


@user.route('/p/<username>/')
@login_required
def profile(username):
    the_user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = the_user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    return render_template('user/profile.html', user=the_user, posts=pagination.items, pagination=pagination)


@user.route('/edit-profile/', methods=['GET', 'POST'])
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


@user.route('/edit-profile/<int:user_id>/', methods=['GET', 'POST'])
@admin_required
def edit_profile_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.permission = index_array_to_value(form.permission.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('main.profile', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.permission.data = value_to_index_array(user.permission)
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('user/edit_profile.html', form=form, user=user)
