# -*- coding: utf-8 -*-
import os
import uuid
from bs4 import BeautifulSoup
from datetime import date, datetime
from flask import request, current_app, render_template, redirect, abort, url_for, send_from_directory, jsonify
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from . import blog_blueprint as blog
from .. import db
from ..models.user import Permission
from ..models.blog import BlogPost as Post, BlogCategory as Category, BlogTag as Tag
from ..tools.decoraters import permission_required
from ..tools.restful import Result, bad_request, not_found


########################################################################################################################
# Blog Forms
########################################################################################################################

class PostAttributesForm(FlaskForm):
    title = StringField(u'标题', validators=[DataRequired()])
    category = SelectField(u'分类', coerce=int)
    # tags = SelectMultipleField(u'标签', coerce=int)
    private = SelectField(u'是否公开', choices=[(0, u'所有人可见'), (1, u'仅自己可见')], coerce=int)
    # body = PageDownField(u'内容', validators=[DataRequired()])
    submit = SubmitField(u'下一步')

    def __init__(self, *args, **kwargs):
        super(PostAttributesForm, self).__init__(*args, **kwargs)
        self.category.choices = [(c.id, c.name) for c in Category.query.filter_by(disabled=False).all()]


########################################################################################################################
# Blog Views
########################################################################################################################
'''
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
'''


@blog.route(u'/', methods=[u'GET'])
def index():
    """
    首页导航
    args: 分页页码(page)，分类(c_id)
    :return:
    """
    page = request.args.get(u'page', 1, type=int)
    c_id = request.args.get(u'c_id', None, type=int)
    query = Post.query.filter(Category.disabled==False)
    if not current_user.can(Permission.VIEW_PRIVATE_BLOG):
        query = query.filter(Category.private==False, Post.private==False)
    if c_id:
        query = query.filter_by(category_id=c_id)
    pagination = query.order_by(Post.timestamp.desc()).paginate(page, per_page=10, error_out=False)
    posts = pagination.items
    for i in range(0, len(posts)):
        soup = BeautifulSoup(posts[i].body_html, u'html.parser')  # markdown(posts[i].body, output_format=u'html')
        posts[i].body_text = soup.get_text()[:400]
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
    if post.category.disabled:
        abort(404)  # abort 410 exactly
    if not current_user.can(Permission.VIEW_PRIVATE_BLOG):
        if post.private or post.category.private:
            abort(403)
    template_name = {
        u'category01': u'blog_post_category01.html',
    }.get(post.category.name, u'blog_post.html')
    post.ping()
    return render_template(u'blog/' + template_name, post=post)


@blog.route(u'/add/', methods=[u'GET', u'POST'])
@permission_required(Permission.CURD_BLOG)
def add_post():
    """
    添加博客
    :return:
    """
    form = PostAttributesForm()
    if request.method == u'POST':
        try:
            assert form.validate_on_submit()
            post = Post()
            post.title = form.title.data
            post.category_id = form.category.data
            post.private = True if form.private.data == u'1' else False
            post.body = u''
            post.body_html = u''
            db.session.add(post)
            db.session.commit()
        except AssertionError:
            abort(400)  # parameter error
        except IOError:
            db.session.rollback()
            abort(500)  # internal server error
        else:
            return redirect(url_for(u'.edit_post', post_id=post.id))
    return render_template(u'blog/_add_post_form.html', form=form)


@blog.route(u'/edit/<int:post_id>/', methods=[u'GET'])
@permission_required(Permission.CURD_BLOG)
def edit_post(post_id):
    """
    编辑博客: 编辑时调阅MARKDOWN版本的文本,保存时同时保存MARKDOWN和HTML版本的文本,查看时调阅HTML版本的文本.
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    return render_template(u'blog/edit_post.html', post=post)


@blog.route(u'/edit/<int:post_id>/edit-post-attributes', methods=[u'GET'])
@permission_required(Permission.CURD_BLOG)
def edit_post_attributes(post_id):
    """
    获取文章属性信息（在博客编辑页面中有使用）
    :param post_id:
    :return:
    """
    post = Post.query.get(post_id)
    if post is None:
        return u'<h3>ERROR_404</h3><p>Can not read target post\'s attributes. (POST_ID: %d)</p>' % post_id
    form = PostAttributesForm()
    form.category.data = post.category_id
    form.private.data = 1 if post.private else 0
    form.title.data = post.title
    return render_template(u'blog/_post_attributes_form.html', form=form)


@blog.route(u'/save-attributes/<int:post_id>/', methods=[u'POST'])
@permission_required(Permission.CURD_BLOG)
def save_post_attributes(post_id):
    """
    保存博客属性信息
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
@permission_required(Permission.CURD_BLOG)
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
        post.last_modify = datetime.utcnow()
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
@permission_required(Permission.CURD_BLOG)
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
@permission_required(Permission.CURD_BLOG)
def edit_tags(post_id):
    """
    编辑博客标签
    :param post_id:
    :return:
    """
    post = Post.query.get_or_404(post_id)
    id_array = request.json[u'check']
    result = Result()
    try:
        post.tags = []
        for tag_id in id_array:
            tag = Tag.query.get(tag_id)
            if tag:
                post.tags.append(tag)
            else:
                abort(400)
        db.session.merge(post)
        db.session.commit()
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
    except IOError, e:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = u'保持标签时发生错误，可能是传入了非法的数据。'
    return jsonify(result.to_json())


@blog.route(u'/upload-image/', methods=[u'POST'])
@permission_required(Permission.CURD_BLOG)
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
