# -*- coding: utf-8 -*-
import os
import time
import shutil
from flask import request, render_template, url_for, redirect, current_app, send_file, abort, flash
from flask_login import current_user
from . import files_blueprint as files


########################################################################################################################
# Files Forms
########################################################################################################################


########################################################################################################################
# Files Views
########################################################################################################################

@files.route(u'/', methods=[u'GET'])
def index():
    return redirect(url_for(u'.explorer', path=u'' if current_user.is_authenticated else u'public/'))


def _generate_urls(path):
    path = path.strip(u'/')
    nav_list = []
    while path:
        pl = path.rsplit(u'/', 1)
        if len(pl) < 2:
            break
        nav_list.append({u'name': pl[1], u'url': url_for(u'.explorer', path=path)})
        path = pl[0]
    if path:
        nav_list.append({u'name': path, u'url': url_for(u'.explorer', path=path)})
    if current_user.is_authenticated:
        nav_list.append({u'name': None, u'url': url_for(u'.explorer', path=u'')})  # 'root'
    else:
        nav_list[-1][u'name'] = None  # 'public'. 匿名情况下传入空字符串非法，此情况已在主函数中排除。
    nav_list[0][u'url'] = None
    return nav_list[::-1]


@files.route(u'/root/', methods=[u'GET'])
@files.route(u'/root/<path:path>', methods=[u'GET'])
def explorer(path=u''):
    """
    Explore files and directories under the given path directory.
    Authenticated user can fully access the 'ROOT' directory, while anonymous user can only access 'public' directory.
    :param path:
    :return:
    """
    if current_user.is_anonymous and cmp(path[:6], u'public'):
        abort(403)
    path = path.rstrip(u'/')
    abs_path = os.path.join(current_app.data_path, u'files', path).rstrip(u'/')
    if os.path.isdir(abs_path):
        folders = {}
        objects = {}
        parent_url = (url_for(u'.explorer', path=path).rsplit(u'/', 1)[0] + u'/') \
            if (path != (u'' if current_user.is_authenticated else u'public')) else None
        nav_tabs = _generate_urls(path)
        for name in os.listdir(abs_path):
            path_name = os.path.join(abs_path, name)
            if os.path.isdir(path_name):
                folders[name] = {
                    u'link': url_for(u'.explorer', path=os.path.join(path, name)+u'/'),
                    u'last_modify': time.strftime(u'%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(path_name))),
                }
            elif os.path.isfile(path_name):
                type_c = name.rsplit(u'.', 1)
                size = float(os.path.getsize(path_name))
                size_l = 0
                while size > 1000.0 and size_l < 4:
                    size /= 1000.0
                    size_l += 1
                objects[name] = {
                    u'link': url_for(u'.explorer', path=os.path.join(path, name)),
                    u'type': type_c[1] if len(type_c) == 2 else None,
                    u'size': u'%.3f %s' % (size, [u'B', u'KB', u'MB', u'GB', u'TB'][size_l]) if size_l else u'%.0f B' % size,
                    u'last_modify': time.strftime(u'%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(abs_path))),
                }
        # folders = sorted(folders.iteritems(), key=lambda k: k, reverse=False)
        # objects = sorted(objects.iteritems(), key=lambda k: k, reverse=False)
        #######################################################################
        #      path : 相对于文件夹根目录的路径（根目录为空字符串）
        #  nav_tabs : 当前路径对应的每一级路径名级链接
        # back_link : 上一级目录的链接（根目录的上一级为None）
        #   folders : 文件夹列表
        #     files : 文件列表
        #######################################################################
        return render_template(u'files/files_index.html', folders=folders, files=objects,
                               path=path, nav_tabs=nav_tabs, back_link=parent_url)
    elif os.path.isfile(abs_path):
        return send_file(abs_path)
    else:
        abort(404)


@files.route(u'/mkdir/', methods=[u'POST'])
@files.route(u'/mkdir/<path:path>/', methods=[u'POST'])
def mkdir(path=u''):
    """
    e.g. POST /mkdir/dir/to/path/?name=dir_to_create
    :param path:
    :return:
    """
    if current_user.is_anonymous and cmp(path[:6], u'public'):
        abort(403)
    abs_path = os.path.join(current_app.data_path, u'files', path).rstrip(u'/')
    dir_name = request.form.get(u'name', None)
    try:
        if dir_name is None:
            raise AttributeError(u'参数错误')
        if not os.path.exists(abs_path):
            raise AttributeError(u'路径错误')
        if os.path.exists(os.path.join(abs_path, dir_name)):
            raise AttributeError(u'已经存在该文件夹')
        os.mkdir(os.path.join(abs_path, dir_name))
    except OSError and AttributeError, e:
        flash(e.message, category=u'error')
    return redirect(url_for(u'.explorer', path=path))


@files.route(u'/upload/', methods=[u'POST'])
@files.route(u'/upload/<path:path>/', methods=[u'POST'])
def upload(path=u''):
    """
    e.g. POST /upload/dir/to/path/
              and those files to be uploaded can be find in 'request.files'
    :param path:
    :return:
    """
    if current_user.is_anonymous and cmp(path[:6], u'public'):
        abort(403)
    try:
        base_dir = os.path.join(current_app.data_path, u'files', path)
        for fn in request.files:
            f = request.files[fn]
            if len(f.filename.split(u'/')) > 1:
                raise AttributeError(u'上传的文件中包含非法的文件名')
            if os.path.exists(os.path.join(base_dir, f.filename)):
                raise AttributeError(u'上传的文件中包含与当前目录相同文件名的文件')
        for fn in request.files:
            f = request.files[fn]
            f.save(os.path.join(base_dir, f.filename))
    except OSError and AttributeError, e:
        flash(e.message, category=u'error')
    else:
        flash(u'文件上传完成！')
    return redirect(url_for(u'.explorer', path=path))


@files.route(u'/delete/', methods=[u'GET'])
@files.route(u'/delete/<path:path>/', methods=[u'GET'])
def delete(path=''):
    """
    e.g. GET /delete/dir/to/path/?name=object_to_delete
    :param path:
    :return:
    """
    if current_user.is_anonymous and cmp(path[:6], u'public'):
        abort(403)
    dir_path = os.path.join(current_app.data_path, u'files', path).rstrip(u'/')
    obj_name = request.args.get(u'name', None)
    try:
        if not obj_name or len(obj_name.split(u'/')) > 1:
            raise AttributeError(u'参数错误')
        if (path == u'' and obj_name == u'public') or (current_user.is_anonymous and path[:6] != u'public'):
            raise AttributeError(u'路径错误或不允许')
        abs_path = os.path.join(dir_path, obj_name)
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        elif os.path.isfile(abs_path):
            os.remove(abs_path)
        else:
            raise AttributeError(u'路径错误')
    except OSError and AttributeError, e:
        flash(e.message, category=u'error')
    return redirect(url_for(u'.explorer', path=path+u'/') if path else url_for(u'.explorer'))
