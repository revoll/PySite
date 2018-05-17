# -*- coding: utf-8 -*-
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Email, Regexp
from wtforms import ValidationError
from . import auth_blueprint as auth
from .. import db
from ..models.user import User
from ..tools.decoraters import admin_required
from ..tools.email import send_email


########################################################################################################################
# Auth Forms
########################################################################################################################

class LoginForm(FlaskForm):
    email = StringField(u'账号', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField(u'密码', validators=[DataRequired()])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField(u'登录')


class RegistrationForm(FlaskForm):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(u'用户名', validators=[
        DataRequired(), Length(1, 64), Regexp(u'^[A-Za-z][A-Za-z0-9_.]*$', 0, u'用户名只能包含字母,数字或下划线')])
    password = PasswordField(u'密码', validators=[DataRequired(), EqualTo(u'password2', message=u'两次输入的密码不一致')])
    password2 = PasswordField(u'再输入一次密码', validators=[DataRequired()])
    submit = SubmitField(u'注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'此邮箱已经被注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'用户名已经被占用')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(u'原密码', validators=[DataRequired()])
    password = PasswordField(u'新的密码', validators=[
        DataRequired(), EqualTo(u'password2', message=u'两次输入的密码不一致')])
    password2 = PasswordField(u'再次输入新密码', validators=[DataRequired()])
    submit = SubmitField(u'确认修改')


class PasswordResetRequestForm(FlaskForm):
    email = StringField(u'请输入您的邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField(u'重置')


class PasswordResetForm(FlaskForm):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField(u'新的密码', validators=[
        DataRequired(), EqualTo(u'password2', message=u'两次输入的密码不一致')])
    password2 = PasswordField(u'再次输入新密码', validators=[DataRequired()])
    submit = SubmitField(u'Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'Unknown email address.')


class ChangeEmailForm(FlaskForm):
    email = StringField(u'New Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField(u'Password', validators=[DataRequired()])
    submit = SubmitField(u'Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'Email already registered.')


########################################################################################################################
# Auth Views
########################################################################################################################

@auth.route(u'/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for(u'main.index'))
    return render_template(u'auth/unconfirmed.html')


@auth.route(u'/login', methods=[u'GET', u'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get(u'next') or url_for(u'main.index'))
        flash(u'Invalid username or password.')
    return render_template(u'auth/login.html', form=form)


@auth.route(u'/logout')
@login_required
def logout():
    logout_user()
    flash(u'You have been logged out.')
    return redirect(url_for(u'main.index'))


@auth.route(u'/register', methods=[u'GET', u'POST'])
@admin_required  # 只有与管理员才可以注册会员,发送确认邮件后由用户自己确认注册,并完成注册流程
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, u'Confirm Your Account', u'auth/email/confirm', user=user, token=token)
        flash(u'A confirmation email has been sent to %s by email.' % user.email)
        # return redirect(url_for(u'auth.login'))
    return render_template(u'auth/register.html', form=form)


@auth.route(u'/confirm/<token>')
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for(u'main.index'))
    if current_user.confirm(token):
        flash(u'You have confirmed your account. Thanks!')
    else:
        flash(u'The confirmation link is invalid or has expired.')
    return redirect(url_for(u'main.index'))


@auth.route(u'/confirm')
@admin_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, u'Confirm Your Account', u'auth/email/confirm', user=current_user, token=token)
    flash(u'A new confirmation email has been sent to you by email.')
    return redirect(url_for(u'main.index'))


@auth.route(u'/change-password', methods=[u'GET', u'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash(u'Your password has been updated.')
            return redirect(url_for(u'main.index'))
        else:
            flash(u'Invalid password.')
    return render_template(u'auth/change_password.html', form=form)


@auth.route(u'/reset', methods=[u'GET', u'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for(u'main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, u'Reset Your Password', u'auth/email/reset_password',
                       user=user, token=token, next=request.args.get(u'next'))
            flash(u'An email with instructions to reset your password has been sent to you.')
            return redirect(url_for(u'auth.login'))
        else:
            flash(u'This email has not registered yet.')
    return render_template(u'auth/reset_password.html', form=form)


@auth.route(u'/reset/<token>', methods=[u'GET', u'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for(u'main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for(u'main.index'))
        if user.reset_password(token, form.password.data):
            flash(u'Your password has been updated.')
            return redirect(url_for(u'auth.login'))
        else:
            return redirect(url_for(u'main.index'))
    return render_template(u'auth/reset_password.html', form=form)


@auth.route(u'/change-email', methods=[u'GET', u'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, u'Confirm your email address', u'auth/email/change_email',
                       user=current_user, token=token)
            flash(u'An email with instructions to confirm your new email address has been sent to you.')
            return redirect(url_for(u'main.index'))
        else:
            flash(u'Invalid email or password.')
    return render_template(u'auth/change_email.html', form=form)


@auth.route(u'/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash(u'Your email address has been updated.')
    else:
        flash(u'Invalid request.')
    return redirect(url_for(u'main.index'))
