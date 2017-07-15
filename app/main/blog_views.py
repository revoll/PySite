# -*- coding: utf-8 -*-
import os
import uuid
from bs4 import BeautifulSoup
from markdown import markdown
from datetime import date
from flask import request, current_app, render_template, redirect, abort, url_for, make_response, flash, send_from_directory, jsonify
from flask_login import login_required, current_user
from flask_wtf import Form
from flask_pagedown.fields import PageDownField
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from . import blog_blueprint as blog
from .. import db
from ..models.blog import BlogPost as Post, BlogCategory as Category, BlogTag as Tag
from ..tools.restful import Result, bad_request, not_found


########################################################################################################################
# Blog Forms
########################################################################################################################

class PostForm(Form):
    title = StringField(u'标题', validators=[DataRequired()])
    category = SelectField(u'分类', coerce=int)
    # tags = SelectMultipleField(u'标签', coerce=int)
    private = SelectField(u'是否公开', choices=[(0, u'所有人可见'), (1, u'仅自己可见')], coerce=int)
    body = PageDownField(u'内容', validators=[DataRequired()])
    submit = SubmitField(u'下一步')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(c.id, c.name) for c in Category.query.filter_by(disabled=False).all()]


########################################################################################################################
# Blog Views
########################################################################################################################

@blog.route(u'/category/<int:c_id>/', methods=[u'GET'])
def switch_category(c_id):
    resp = make_response(redirect(url_for(u'.index')))
    resp.set_cookie(u'blog_category', str(c_id), max_age=60*60)
    return resp


@blog.route(u'/category/all/', methods=[u'GET'])
def switch_category_all():
    resp = make_response(redirect(url_for(u'.index')))
    resp.set_cookie(u'blog_category', u'', max_age=60*60)
    return resp


@blog.route(u'/', methods=[u'GET'])
def index():
    page = request.args.get(u'page', 1, type=int)
    c_id = request.cookies.get(u'blog_category', u'')
    c_id = int(c_id) if c_id else None
    query = Post.query
    if c_id:
        query = query.filter_by(category_id=c_id)
    if current_user.is_anonymous:
        query = query.filter(Category.private==False, Category.disabled==False).filter_by(private=False)
    pagination = query.order_by(Post.timestamp.desc()).paginate(page, per_page=10, error_out=False)
    posts = pagination.items
    for i in range(0, len(posts)):
        soup = BeautifulSoup(markdown(posts[i].body, output_format=u'html'), u'html.parser')
        posts[i].body_text = soup.get_text()[:200]
        posts[i].cover_url = soup.img[u'src'] if soup.img else None
    return render_template(u'blog/blog_index.html', posts=posts, pagination=pagination,
                           categories=Category.query.all(), c_sel=c_id)


@blog.route(u'/post/<int:post_id>/', methods=[u'GET'])
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user.is_anonymous:
        if post.category.disabled:
            abort(404)  # abort 410 exactly
        if post.private or post.category.private:
            abort(403)
    return render_template(u'blog/blog_post.html', post=post)


@blog.route(u'/add/', methods=[u'GET', u'POST'])
@login_required
def add_post():
    try:
        post = Post(title=U'新建文章')
        db.session.add(post)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        flash(u'添加失败: %s' % e.message)
        abort(500)
    else:
        return redirect(url_for(u'.edit_post', post_id=post.id))


@blog.route(u'/edit/<int:post_id>/', methods=[u'GET', u'POST'])
@login_required
def edit_post(post_id):
    if request.method == u'POST':
        result = Result()
        post = Post.query.get(post_id)
        if post is None:
            return not_found()
        try:
            category = request.json.get(u'category')
            private = request.json.get(u'private')
            title = request.json.get(u'title')
            assert category and private is not None and title
            body = request.json.get(u'body')
            body_html = request.json.get(u'body_html')
            assert body is not None and body_html is not None
        except Exception, e:
            return bad_request(e.message)
        try:
            post.category_id = int(category)
            post.private = True if private == u'1' else False
            post.title = title
            post.body = body
            post.body_html = body_html
            db.session.merge(post)
            db.session.commit()
        except Exception, e:
            db.session.rollback()
            result.status = Result.Status.ERROR
            result.detail = e.message
        else:
            result.status = Result.Status.SUCCESS
            result.detail = u'所有修改已妥善保存！'
        finally:
            return jsonify(result.to_json())
    else:
        post = Post.query.get_or_404(post_id)
        form = PostForm()
        form.category.data = post.category_id
        form.title.data = post.title
        form.body.data = post.body
        form.private.data = 1 if post.private else 0
        return render_template(u'blog/edit_post.html', form=form, post=post)


@blog.route(u'/delete/<int:post_id>/', methods=[u'GET'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    redirect_url = request.args.get(u'redirect', url_for(u'.index'))
    db.session.delete(post)
    flash(u'Post ({0}) is deleted.'.format(str(post_id)))
    return redirect(redirect_url)


@blog.route(u'/edit_tags/<int:post_id>/', methods=[u'POST'])
@login_required
def edit_tags(post_id):
    """
    编辑标签
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)

    try:
        post.tags = []
        for t_n in request.form:
            tag = Tag.query.get(request.form[t_n])
            if tag:
                post.tags.append(tag)
            else:
                abort(400)
        db.session.merge(post)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        flash(u'ERROR: %s' % e.message)

    return redirect(url_for(u'.get_post', post_id=post_id))


@blog.route(u'/upload-image/', methods=[u'POST'])
@login_required
def upload_image():
    img = request.files[u'editormd-image-file']
    filename = uuid.uuid1().hex[:20] + os.path.splitext(img.filename)[1]
    folder = date.today().strftime(u'%Y-%m')
    path = os.path.join(current_app.data_path, u'blog', folder)
    if not os.path.exists(path):
        os.makedirs(path)
    img.save(os.path.join(path, filename))
    return jsonify({u'success': 1,
                    u'message': u'ok',
                    u'url': url_for(u'.serve_image', folder=folder, filename=filename, _external=True)})


@blog.route(u'/image/<folder>/<filename>', methods=[u'GET'])
def serve_image(folder, filename):
    return send_from_directory(os.path.join(current_app.data_path, u'blog', folder), filename)
