# -*- coding: utf-8 -*-
from flask import render_template, abort, request, current_app, make_response, redirect, url_for, jsonify
from flask_login import current_user, login_required
from flask_sqlalchemy import get_debug_queries
from . import main_blueprint as main
from .. import db
from ..tools.decoraters import admin_required
from ..tools.restful import Result, bad_request, unauthorized, forbidden, not_found, method_not_allowed, internal_server_error


@main.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and \
                request.endpoint and request.endpoint[:5] != u'auth.' and request.endpoint != u'static':
            return redirect(url_for(u'auth.unconfirmed'))


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config[u'SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                u'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration, query.context))
    return response


########################################################################################################################
# Error handlers: 内容协商 404 & 500 需要特别定制，其它可以选择性定制。
########################################################################################################################

@main.app_errorhandler(400)
def bad_request(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return bad_request()
    return render_template(u'common/error_page.html', code=400, name=u'Bad Request', description=u''), 400


@main.app_errorhandler(401)
def unauthorized(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return unauthorized()
    return render_template(u'common/error_page.html', code=401, name=u'Unauthorized', description=u''), 401


@main.app_errorhandler(403)
def forbidden(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return forbidden()
    return render_template(u'common/error_page.html', code=403, name=u'Forbidden', description=u''), 403


@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return not_found()
    return render_template(u'common/error_page.html', code=404, name=u'Not Found', description=u''), 404


@main.app_errorhandler(405)
def method_not_allowed(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return method_not_allowed()
    return render_template(u'common/error_page.html', code=405, name=u'Method Not Allowed', description=u''), 405


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return internal_server_error()
    return render_template(u'common/error_page.html', code=500, name=u'Internal Server Error', description=u''), 500


########################################################################################################################
# Categories and tags management (ctm)
########################################################################################################################
from app.models.blog import BlogCategory, BlogTag, BlogPost
from app.models.movie import MovieCategory, MovieTag, MoviePost
from app.models.photo import PhotoCategory, PhotoTag, PhotoPost


ctm_mapper = {
    u'blog': {u'category': BlogCategory, u'tag': BlogTag, u'object': BlogPost},
    u'movie': {u'category': MovieCategory, u'tag': MovieTag, u'object': MoviePost},
    u'photo': {u'category': PhotoCategory, u'tag': PhotoTag, u'object': PhotoPost},
}


@main.route(u'/ctm/', methods=[u'GET'])
@admin_required
def ctm_index():
    """
    分类与标签管理首页，直接跳转到CTM处理。
    :return:
    """
    return redirect(url_for(u'.ctm', module=u'blog'))


@main.route(u'/ctm/<module>/available-categories/', methods=[u'GET'])
@admin_required
def show_available(module):
    """
    显示所有可用的分类及对应的标签。
    :param module:
    :return:
    """
    module = module.lower()
    resp = make_response(redirect(url_for(u'.ctm', module=module)))
    resp.set_cookie(u'show_deleted', u'', max_age=30*24*60*60)
    return resp


@main.route(u'/ctm/<module>/deleted-categories/', methods=[u'GET'])
@admin_required
def show_deleted(module):
    """
    显示所有已经弃用的分类及对应的标签。
    已经弃用的分类不能被指派为新的POST使用，也不能被编辑，但是可以重新恢复为正常分类。
    :param module:
    :return:
    """
    module = module.lower()
    resp = make_response(redirect(url_for(u'.ctm', module=module)))
    resp.set_cookie(u'show_deleted', u'1', max_age=30*24*60*60)
    return resp


@main.route(u'/ctm/<module>/', methods=[u'GET'])
@admin_required
def ctm(module):
    """
    标签管理视图：根据Session中的'show_deleted'字段进行分类显示。
    :param module:
    :return:
    """
    module = module.lower()
    show_hide = bool(request.cookies.get(u'show_deleted', u''))

    if module not in ctm_mapper.keys():
        return redirect(url_for(u'.ctm', module=u'blog'))

    ctm_c = ctm_mapper[module][u'category']
    categories = ctm_c.query.filter_by(disabled=show_hide).order_by(ctm_c.id).all()

    return render_template(u'common/tagging.html', module=module, categories=categories, show_disabled=show_hide)


@main.route(u'/ctm/<module>/category-all/', methods=[u'GET'])
def all_categories(module):
    """
    获取当前模块的所有分类信息。
    :param module:
    :return: JSON
    """
    module = module.lower()
    result = Result()

    if module not in ctm_mapper.keys():
        return not_found()

    ctm_c = ctm_mapper[module][u'category']
    if current_user.is_authenticated:
        query = ctm_c.query
    else:
        query = ctm_c.query.filter_by(private=False)
    categories = query.all()
    result.status = Result.Status.SUCCESS
    result.detail = Result.Detail.SUCCESS
    result.data = [c.to_json() for c in categories]

    return jsonify(result.to_json())


@main.route(u'/ctm/<module>/category/<int:category_id>/', methods=[u'GET'])
def query_category(module, category_id):
    """
    获取指定模块下指定分类的信息。
    :param module:
    :param category_id:
    :return: JSON
    """
    module = module.lower()
    result = Result()

    if module not in ctm_mapper.keys():
        return not_found()

    ctm_c = ctm_mapper[module][u'category']
    c = ctm_c.query.get(category_id)
    if c is None:
        return not_found()
    if current_user.is_anonymous and c.private:
        return forbidden()
    result.status = Result.Status.SUCCESS
    result.detail = Result.Detail.SUCCESS
    result.data = c.to_json()

    return jsonify(result.to_json())


@main.route(u'/ctm/<module>/add-category/', methods=[u'POST'])
@admin_required
def add_category(module):
    """
    在指定模块下添加一个分类。
    :param module:
    :return: JSON
    """
    module = module.lower()
    result = Result()
    name = request.json.get(u'name')

    if module not in ctm_mapper.keys():
        return not_found()
    if not name:
        return bad_request()

    ctm_c = ctm_mapper[module][u'category']
    try:
        c = ctm_c(name=name)
        db.session.add(c)  # 分类名称查重在SQLAlchemy中完成
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
        result.data = c.to_json()
    finally:
        return jsonify(result.to_json())


@main.route(u'/ctm/<module>/edit-category/<int:category_id>/', methods=[u'POST'])
@admin_required
def edit_category(module, category_id):
    """
    编辑指定模块下的某个分类的信息。
    :param module:
    :param category_id:
    :return: JSON
    """
    module = module.lower()
    result = Result()
    name = request.json.get(u'name')
    private = request.json.get(u'private')

    if module not in ctm_mapper.keys():
        return not_found()
    if not name or private is None:
        return bad_request()

    ctm_c = ctm_mapper[module][u'category']
    c = ctm_c.query.get(category_id)
    if c is None:
        return not_found()
    try:
        c.name = name
        c.private = private
        db.session.merge(c)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
        result.data = c.to_json()
    finally:
        return jsonify(result.to_json())


@main.route(u'/ctm/<module>/delete-category/<int:category_id>/', methods=[u'GET'])
@admin_required
def delete_category(module, category_id):
    """
    删除指定模块下的指定分类（冻结）。
    :param module:
    :param category_id:
    :return: JSON
    """
    module = module.lower()
    ctm_c = ctm_mapper[module][u'category']
    result = Result()
    c = ctm_c.query.get(category_id)
    if c is None:
        return not_found()
    try:
        # delete this `category` if no post references it, and not tags belongs to it, or mark it as disabled else.
        if c.posts.first() or c.tags.first():
            c.disabled = True
            db.session.merge(c)
        else:
            db.session.delete(c)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
        result.data = c.to_json()
    finally:
        return jsonify(result.to_json())


@main.route(u'/ctm/<module>/recycle-category/<int:category_id>/', methods=[u'GET'])
@admin_required
def recycle_category(module, category_id):
    """
    恢复使用指定模块下的指定分类（解冻）。
    :param module:
    :param category_id:
    :return: JSON
    """
    module = module.lower()
    ctm_c = ctm_mapper[module][u'category']
    result = Result()
    c = ctm_c.query.get(category_id)
    if c is None:
        return not_found()
    try:
        c.disabled = False
        db.session.merge(c)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
        result.data = c.to_json()
    finally:
        return jsonify(result.to_json())


@main.route(u'/ctm/<module>/tag/<int:tag_id>/', methods=[u'GET'])
def query_tag(module, tag_id):
    """
    查询指定模块指定分类下的某个标签信息。
    :param module:
    :param tag_id:
    :return: JSON
    """
    module = module.lower()
    ctm_t = ctm_mapper[module][u'tag']
    result = Result()
    t = ctm_t.query.get(tag_id)
    if t is None:
        return not_found()
    if current_user.is_anonymous and t.category.private:
        return forbidden()
    result.status = Result.Status.SUCCESS
    result.detail = Result.Detail.SUCCESS
    result.data = t.to_json()
    return jsonify(result.to_json())


@main.route(u'/ctm/<module>/add-tag/<int:category_id>/', methods=[u'POST'])
@admin_required
def add_tag(module, category_id):
    """
    在指定模块指定分类下添加一个标签。
    :param module:
    :param category_id:
    :return: JSON
    """
    module = module.lower()
    ctm_c = ctm_mapper[module][u'category']
    ctm_t = ctm_mapper[module][u'tag']
    result = Result()
    try:
        c = ctm_c.query.get(category_id)
        name = request.json.get(u'name')
        assert c and name
        if name in [t.name for t in c.tags]:
            raise AttributeError(u'指定的分类下已经存在相同名称的标签')
    except Exception, e:
        return bad_request(e.message)
    try:
        t = ctm_t(name=name, category_id=category_id)
        db.session.add(t)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
        result.data = t.to_json()
    finally:
        return jsonify(result.to_json())


@main.route(u'/ctm/<module>/edit-tag/<int:tag_id>/', methods=[u'POST'])
@admin_required
def edit_tag(module, tag_id):
    """
    编辑指定模块指定分类下的特定标签。
    :param module:
    :param tag_id:
    :return: JSON
    """
    module = module.lower()
    ctm_c = ctm_mapper[module][u'category']
    ctm_t = ctm_mapper[module][u'tag']
    result = Result()
    t = ctm_t.query.get(tag_id)
    if t is None:
        return not_found()
    try:
        name = request.json.get(u'name')
        assert name
        if name != t.name and name in [_t.name for _t in t.category.tags]:
            raise AttributeError(u'指定的分类下已经存在相同名称的标签')
    except Exception, e:
        return bad_request(e.message)
    try:
        t.name = name
        db.session.merge(t)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
        result.data = t.to_json()
    finally:
        return jsonify(result.to_json())


@main.route(u'/ctm/<module>/delete-tag/<int:tag_id>/', methods=[u'GET'])
@admin_required
def delete_tag(module, tag_id):
    """
    删除指定模块指定分类下的特定标签。
    :param module:
    :param tag_id:
    :return: JSON
    """
    module = module.lower()
    ctm_t = ctm_mapper[module][u'tag']
    result = Result()
    t = ctm_t.query.get(tag_id)
    if t is None:
        return not_found()
    try:
        db.session.delete(t)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
        result.data = t.to_json()
    finally:
        return jsonify(result.to_json())


########################################################################################################################
# Views & Controls
########################################################################################################################

@main.route(u'/', methods=[u'GET', u'POST'])
def index():
    return render_template(u'index.html')


@main.route(u'/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get(u'werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return u'Shutting down...'


@main.route(u'/user/detail/')
@login_required
def user():
    return render_template(u'common/user.html')
