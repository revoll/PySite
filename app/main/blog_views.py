# -*- coding: utf-8 -*-
import os
import uuid
from bs4 import BeautifulSoup
from markdown import markdown
from datetime import date
from flask import request, current_app, render_template, redirect, abort, url_for, make_response, flash, send_from_directory, jsonify
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from . import blog_blueprint as blog
from .. import db
from ..models.blog import BlogPost as Post, BlogCategory as Category, BlogTag as Tag
from ..tools.decoraters import admin_required
from ..tools.restful import Result, bad_request, not_found


########################################################################################################################
# Blog Forms
########################################################################################################################

class PostMetasForm(FlaskForm):
    title = StringField(u'标题', validators=[DataRequired()])
    category = SelectField(u'分类', coerce=int)
    # tags = SelectMultipleField(u'标签', coerce=int)
    private = SelectField(u'是否公开', choices=[(0, u'所有人可见'), (1, u'仅自己可见')], coerce=int)
    # body = PageDownField(u'内容', validators=[DataRequired()])
    submit = SubmitField(u'下一步')

    def __init__(self, *args, **kwargs):
        super(PostMetasForm, self).__init__(*args, **kwargs)
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
    """
    首页
    :return:
    """
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
    """
    博客详情
    某些情况下，作者会把Markdown文本第一行作为标题，此时在渲染‘blog_post.html’页面时，应对把HTML对应的<h1>XXX</h1>标题剔除。
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    if current_user.is_anonymous:
        if post.category.disabled:
            abort(404)  # abort 410 exactly
        if post.private or post.category.private:
            abort(403)
    try:
        post.content = post.body_html if post.body_html[:3] != u'<h1' \
            else post.body_html[post.body_html.index(u'</h1>')+len(u'</h1>'):]
    except ValueError:
        post.content = post.body_html
    return render_template(u'blog/blog_post.html', post=post)


@blog.route(u'/add/', methods=[u'GET', u'POST'])
@admin_required
def add_post():
    """
    添加博客
    :return:
    """
    form = PostMetasForm()
    if request.method == u'POST':
        try:
            assert form.validate_on_submit()
            post = Post()
            post.title = form.title.data
            post.category_id = form.category.data
            post.private = True if form.private.data == u'1' else False
            post.body = u'# ' + post.title + u'\r\n\r\n\r\n'
            post.body_html = u'<h1>%s</h1>' % post.title
            db.session.add(post)
            db.session.commit()
        except AssertionError:
            abort(400)  # bad request
        except IOError:
            db.session.rollback()
            abort(500)  # internal server error
        else:
            return redirect(url_for(u'.edit_post', post_id=post.id))
    return render_template(u'blog/_add_post_form.html', form=form)


@blog.route(u'/edit/<int:post_id>/', methods=[u'GET'])
@admin_required
def edit_post(post_id):
    """
    编辑博客: 编辑时调阅MARKDOWN版本的文本,保存时同时保存MARKDOWN和HTML版本的文本,查看时调阅HTML版本的文本.
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    return render_template(u'blog/edit_post.html', post=post)


@blog.route(u'/form-edit-metas/<int:post_id>', methods=[u'GET'])
def _get_edit_metas_form(post_id):
    """
    获取文章元信息
    :param post_id:
    :return:
    """
    post = Post.query.get(post_id)
    if post is None:
        return u'<h3>ERROR_404</h3><p>Can not read target post\'s metas. (POST_ID: %d)</p>' % post_id
    form = PostMetasForm()
    form.category.data = post.category_id
    form.private.data = 1 if post.private else 0
    form.title.data = post.title
    return render_template(u'blog/_post_metas_form.html', form=form)


@blog.route(u'/save-metas/<int:post_id>/', methods=[u'POST'])
@admin_required
def save_post_metas(post_id):
    """
    编辑博客元信息
    :param post_id:
    :return:
    """
    result = Result()
    post = Post.query.get(post_id)
    if post is None:
        return not_found()
    try:
        category = request.json.get(u'category')
        private = request.json.get(u'private')
        title = request.json.get(u'title')
        assert category and private is not None and title
        post.category_id = int(category)
        post.private = True if private == u'1' else False
        post.title = title
        db.session.merge(post)
        db.session.commit()
    except AssertionError, e:
        return bad_request(e.message)
    except IOError, e:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = u'修改成功！'
    finally:
        return jsonify(result.to_json())


@blog.route(u'/save-content/<int:post_id>/', methods=[u'POST'])
@admin_required
def save_post_content(post_id):
    """
    编辑博客内容(标题在MarkDown文本的首行).
    :param post_id:
    :return:
    """
    result = Result()
    post = Post.query.get(post_id)
    if post is None:
        return not_found()
    try:
        body = request.json.get(u'body')
        body_html = request.json.get(u'body_html')
        assert body is not None and body_html is not None
        post.body = body
        post.body_html = body_html
        db.session.merge(post)
        db.session.commit()
    except AssertionError, e:
        return bad_request(e.message)
    except IOError, e:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = u'保存成功！'
    finally:
        return jsonify(result.to_json())


@blog.route(u'/delete/<int:post_id>/', methods=[u'GET'])
@admin_required
def delete_post(post_id):
    """
    删除博客
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    redirect_url = request.args.get(u'redirect', url_for(u'.index'))
    db.session.delete(post)
    return redirect(redirect_url)


@blog.route(u'/edit_tags/<int:post_id>/', methods=[u'POST'])
@admin_required
def edit_tags(post_id):
    """
    编辑博客标签
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
    except IOError, e:
        db.session.rollback()
        flash(u'ERROR: %s' % e.message)
    return redirect(url_for(u'.get_post', post_id=post_id))


@blog.route(u'/upload-image/', methods=[u'POST'])
@admin_required
def upload_image():
    """
    上传图片接口(AJAX API)
    :return:
    """
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
    """
    图片获取接口(部署时实际使用WEB容器完成)
    :param folder:
    :param filename:
    :return:
    """
    return send_from_directory(os.path.join(current_app.data_path, u'blog', folder), filename)
