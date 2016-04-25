# encoding: utf-8
from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask.ext.login import login_required, current_user

from . import blog
from .blog_forms import PostForm, CommentForm
from .. import db
from ..models.blog import Post, Comment
from ..tools.decorators import admin_required


@blog.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.is_admin() and form.validate_on_submit():
        the_post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(the_post)
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('blog/index.html', form=form, posts=posts,
                           show_followed=show_followed, pagination=pagination)


@blog.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@blog.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


@blog.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if current_user.is_authenticated and form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post, author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('blog/post.html', posts=[post], form=form, comments=comments, pagination=pagination)


@blog.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.is_admin():
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('blog/edit_post.html', form=form)


@blog.route('/delete/<int:id>')
@login_required
def delete(id):
    post = Post.query.get_or_404(id)
    user = current_user._get_current_object()
    redirect_url = request.args.get('redirect', url_for('main.profile', username=user.username))
    if user.id == post.author_id or user.is_admin():
        db.session.delete(post)
        flash('Post ({0}) is deleted.'.format(str(id)))
    return redirect(redirect_url)


@blog.route('/delete-comment/<int:id>')
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    redirect_url = request.args.get('redirect', url_for('.post', id=comment.post_id))
    post_author_id = comment.post.author_id
    user = current_user._get_current_object()
    if user.id == comment.author_id or user.id == post_author_id or user.is_admin():
        db.session.delete(comment)
        flash('Comment ({0}) is deleted.'.format(str(id)))
    return redirect(redirect_url)


@blog.route('/moderate')
@admin_required
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('blog/moderate.html', comments=comments, pagination=pagination, page=page)


@blog.route('/moderate/enable/<int:id>')
@admin_required
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@blog.route('/moderate/disable/<int:id>')
@admin_required
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))
