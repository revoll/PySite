# -*- coding: utf-8 -*-
import os
import datetime
import time
import shutil
from flask import request, current_app, render_template, flash, jsonify, abort, redirect, url_for, send_file
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp
from . import utils_blueprint as utils
from ..models import db, Passbook, Cashbook
from ..models.user import Permission
from ..tools.decoraters import root_required
from ..tools.restful import Result, not_found, unauthorized


########################################################################################################################
#
# Section: Files
#
########################################################################################################################

@utils.route(u'/files/', methods=[u'GET'])
def files():
    return redirect(url_for(u'.files_explorer', path=u'' if current_user.can(Permission.ADMIN) else u'public/'))


def _generate_urls(path):
    path = path.strip(u'/')
    nav_list = []
    while path:
        pl = path.rsplit(u'/', 1)
        if len(pl) < 2:
            break
        nav_list.append({u'name': pl[1], u'url': url_for(u'.files_explorer', path=path)})
        path = pl[0]
    if path:
        nav_list.append({u'name': path, u'url': url_for(u'.files_explorer', path=path)})
    if current_user.can(Permission.ADMIN):
        nav_list.append({u'name': None, u'url': url_for(u'.files_explorer', path=u'')})  # 'root'
    else:
        nav_list[-1][u'name'] = None  # 'public'. 匿名情况下传入空字符串非法，此情况已在主函数中排除。
    nav_list[0][u'url'] = None
    return nav_list[::-1]


@utils.route(u'/files/root/', methods=[u'GET'])
@utils.route(u'/files/root/<path:path>', methods=[u'GET'])
def files_explorer(path=u''):
    """
    Explore files and directories under the given path directory.
    Authenticated user can fully access the 'ROOT' directory, while anonymous user can only access 'public' directory.
    :param path:
    :return:
    """
    if not current_user.can(Permission.ADMIN) and cmp(path[:6], u'public'):
        abort(403)
    path = path.rstrip(u'/')
    abs_path = os.path.join(current_app.data_path, u'files', path).rstrip(u'/')
    if os.path.isdir(abs_path):
        folders = {}
        objects = {}
        parent_url = (url_for(u'.files_explorer', path=path).rsplit(u'/', 1)[0] + u'/') \
            if (path != (u'' if current_user.can(Permission.ADMIN) else u'public')) else None
        nav_tabs = _generate_urls(path)
        for name in os.listdir(abs_path):
            path_name = os.path.join(abs_path, name)
            if os.path.isdir(path_name):
                folders[name] = {
                    u'link': url_for(u'.files_explorer', path=os.path.join(path, name)+u'/'),
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
                    u'link': url_for(u'.files_explorer', path=os.path.join(path, name)),
                    u'type': type_c[1] if len(type_c) == 2 else None,
                    u'size': u'%.3f %s' % (size, [u'B', u'KB', u'MB', u'GB', u'TB'][size_l]) if size_l else u'%.0f B' % size,
                    u'last_modify': time.strftime(u'%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(path_name))),
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
        return render_template(u'utils/file_explorer.html', folders=folders, files=objects,
                               path=path, nav_tabs=nav_tabs, back_link=parent_url)
    elif os.path.isfile(abs_path):
        return send_file(abs_path)
    else:
        abort(404)


@utils.route(u'/files/mkdir/', methods=[u'POST'])
@utils.route(u'/files/mkdir/<path:path>/', methods=[u'POST'])
def files_mkdir(path=u''):
    """
    e.g. POST /mkdir/dir/to/path/?name=dir_to_create
    :param path:
    :return:
    """
    result = Result()
    if not current_user.can(Permission.ADMIN) and cmp(path[:6], u'public'):
        return unauthorized()
    abs_path = os.path.join(current_app.data_path, u'files', path).rstrip(u'/')
    dir_name = request.json.get(u'name')
    try:
        if not dir_name:
            raise AttributeError(u'参数错误')
        if not os.path.exists(abs_path):
            raise AttributeError(u'路径错误')
        if os.path.exists(os.path.join(abs_path, dir_name)):
            raise AttributeError(u'已经存在该文件夹')
        os.mkdir(os.path.join(abs_path, dir_name))
    except OSError and AttributeError, e:
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
    finally:
        return jsonify(result.to_json())


''' AJAX版本
@utils.route(u'/files/upload/', methods=[u'POST'])
@utils.route(u'/files/upload/<path:path>/', methods=[u'POST'])
def files_upload(path=u''):
    """
    e.g. POST /upload/dir/to/path/
              and those files to be uploaded can be find in 'request.files'
    :param path:
    :return:
    """
    result = Result()
    if not current_user.can(Permission.ADMIN) and cmp(path[:6], u'public'):
        return unauthorized()
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
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
    finally:
        return jsonify(result.to_json())
'''


@utils.route(u'/files/upload/', methods=[u'POST'])
@utils.route(u'/files/upload/<path:path>/', methods=[u'POST'])
def files_upload(path=u''):
    """
    e.g. POST /upload/dir/to/path/
              and those files to be uploaded can be find in 'request.files'
    :param path:
    :return:
    """
    if not current_user.can(Permission.ADMIN) and cmp(path[:6], u'public'):
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
        flash(u'上传成功！')
    finally:
        return redirect(url_for(u'.files_explorer', path=path))


@utils.route(u'/files/delete/', methods=[u'GET', u'POST'])
@utils.route(u'/files/delete/<path:path>/', methods=[u'GET', u'POST'])
def files_delete(path=u''):
    """
    e.g. GET /delete/dir/to/path/?name=object_to_delete
    :param path:
    :return:
    """
    result = Result()
    if not current_user.can(Permission.ADMIN) and cmp(path[:6], u'public'):
        return unauthorized()
    dir_path = os.path.join(current_app.data_path, u'files', path).rstrip(u'/')
    obj_name = request.json.get(u'name')
    try:
        if not obj_name or len(obj_name.split(u'/')) > 1:
            raise AttributeError(u'参数错误')
        if (path == u'' and obj_name == u'public') or (not current_user.can(Permission.ADMIN) and path[:6] != u'public'):
            raise AttributeError(u'路径错误或不允许')
        abs_path = os.path.join(dir_path, obj_name)
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        elif os.path.isfile(abs_path):
            os.remove(abs_path)
        else:
            raise AttributeError(u'路径错误')
    except OSError and AttributeError, e:
        result.status = Result.Status.ERROR
        result.detail = e.message
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
    finally:
        return jsonify(result.to_json())


########################################################################################################################
#
# Section: Passbook
#
########################################################################################################################

class PassbookRecordForm(FlaskForm):
    keyword = StringField(u'关键字', validators=[Regexp(u'^[a-zA-Z\d]{0,20}$')])
    name = StringField(u'名称', validators=[DataRequired()])
    host = StringField(u'域名')
    username = StringField(u'用户名')
    password = StringField(u'密码')
    comments = StringField(u'备注信息')
    submit = SubmitField(u'提交')


@utils.route(u'/passbook/', methods=[u'GET'])
@root_required
def passbook():
    """
    密码簿工具
    +----------+---------+------+------+----------+----------+----------+
    | ID(None) | Keyword | Name | HOST | Username | Password | Comments |
    +----------+---------+------+------+----------+----------+----------+
    :return:
    """
    records = Passbook.query.order_by(Passbook.keyword.asc()).all()
    return render_template(u'utils/passbook.html', records=records, form=PassbookRecordForm())


@utils.route(u'/passbook/create', methods=[u'POST'])
@root_required
def passbook_create_record():
    form = PassbookRecordForm()
    if form.validate_on_submit():
        record = Passbook()
        record.name = form.name.data
        record.host = form.host.data
        record.keyword = form.keyword.data.upper()
        record.username = form.username.data
        record.password = form.password.data
        record.comments = form.comments.data
        try:
            db.session.add(record)
            db.session.commit()
        except IOError:
            db.session.rollback()
            abort(500)
    else:
        flash(u'插入失败，可能包含非法的输入！')
    return redirect(url_for(u'.passbook'))


@utils.route(u'/passbook/update/<int:record_id>', methods=[u'POST'])
@root_required
def passbook_update_record(record_id):
    form = PassbookRecordForm()
    if form.validate_on_submit():
        record = Passbook.query.get_or_404(record_id)
        record.name = form.name.data
        record.host = form.host.data
        record.keyword = form.keyword.data
        record.username = form.username.data
        record.password = form.password.data
        record.comments = form.comments.data
        try:
            db.session.merge(record)
            db.session.commit()
        except IOError:
            db.session.rollback()
            abort(500)
    else:
        flash(u'修改失败，可能包含非法的输入！')
    return redirect(url_for(u'.passbook'))


@utils.route(u'/passbook/delete/<int:record_id>', methods=[u'GET', u'POST'])
@root_required
def passbook_delete_record(record_id):
    record = Passbook.query.get_or_404(record_id)
    try:
        db.session.delete(record)
        db.session.commit()
    except IOError:
        db.session.rollback()
        flash(u'删除失败！')
    return redirect(url_for(u'.passbook'))


########################################################################################################################
#
# Section: Cashbook
#
########################################################################################################################

'''
class CashbookRecordForm(FlaskForm):
    date = DateField(u'交易日期')
    comment = StringField(u'记账名目', validators=[DataRequired])
    method = StringField(u'支付方式')
    amount = FloatField(u'金额')
    submit = SubmitField(u'提交')
'''


@utils.route(u'/cashbook/', methods=[u'GET'])
@root_required
def cashbook():
    """
    记账本（人情簿）工具
    +----------+------+---------+--------+--------+-----------+
    | ID(None) | Date | Comment | Method | Amount | Timestamp |
    +----------+------+---------+--------+--------+-----------+
    :return:
    """
    records = Cashbook.query.order_by(Cashbook.date.desc(), Cashbook.timestamp.desc()).all()
    return render_template(u'utils/cashbook.html', records=records, form=FlaskForm())


@utils.route(u'/cashbook/create', methods=[u'POST'])
@root_required
def cashbook_create_record():
    result = Result()
    record = Cashbook()
    try:
        record.comment = request.json.get(u'comment')
        record.method = request.json.get(u'method')
        record.amount = float(request.json.get(u'amount'))
        record.date = datetime.datetime.strptime(request.json.get(u'date'), u'%Y-%m-%d').date()
        record.timestamp = datetime.datetime.utcnow()
        db.session.add(record)
        db.session.commit()
    except IOError:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = Result.Detail.ERROR
    except:
        result.status = Result.Status.ERROR
        result.detail = Result.Detail.ERROR
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
    finally:
        return jsonify(result.to_json())


@utils.route(u'/cashbook/update/<int:record_id>', methods=[u'POST'])
@root_required
def cashbook_update_record(record_id):
    result = Result()
    record = Cashbook.query.get(record_id)
    if record is None:
        return not_found()
    try:
        record.comment = request.json.get(u'comment')
        record.method = request.json.get(u'method')
        record.amount = float(request.json.get(u'amount'))
        record.date = datetime.datetime.strptime(request.json.get(u'date'), u'%Y-%m-%d').date()
        record.timestamp = datetime.datetime.utcnow()
        db.session.merge(record)
        db.session.commit()
    except IOError:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = Result.Detail.ERROR
    except:
        result.status = Result.Status.ERROR
        result.detail = Result.Detail.ERROR
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
    finally:
        return jsonify(result.to_json())


@utils.route(u'/cashbook/delete/<int:record_id>', methods=[u'GET', u'POST'])
@root_required
def cashbook_delete_record(record_id):
    result = Result()
    record = Cashbook.query.get(record_id)
    if record is None:
        return not_found()
    try:
        db.session.delete(record)
        db.session.commit()
    except IOError:
        db.session.rollback()
        result.status = Result.Status.ERROR
        result.detail = Result.Detail.ERROR
    else:
        result.status = Result.Status.SUCCESS
        result.detail = Result.Detail.SUCCESS
    finally:
        return jsonify(result.to_json())
