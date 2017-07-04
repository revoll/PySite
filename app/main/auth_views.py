# -*- coding: utf-8 -*-
from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, login_required
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length
from . import auth_blueprint as auth
from ..models import User


########################################################################################################################
# Auth Forms
########################################################################################################################

class LoginForm(Form):
    username = StringField(u'用户名', validators=[Required(), Length(1, 64)])
    password = PasswordField(u'密码', validators=[Required()])
    remember = BooleanField(u'记住我')
    submit = SubmitField(u'登录')


########################################################################################################################
# Auth Views
########################################################################################################################

@auth.route(u'/login', methods=[u'GET', u'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == u'admin' and form.password.data == u'0':
            login_user(User(), form.remember.data)
            return redirect(request.args.get(u'next') or url_for(u'main.index'))
        flash(u'用户名或密码错误，登录失败！')
    return render_template(u'auth/login.html', form=form)


@auth.route(u'/logout')
@login_required
def logout():
    logout_user()
    flash(u'您已登出，谢谢！')
    return redirect(url_for(u'main.index'))
