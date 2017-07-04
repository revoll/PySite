# -*- coding: utf-8 -*-
from flask.ext.login import UserMixin
from .. import login_manager


########################################################################################################################
# 登录模块初始化配置
########################################################################################################################

class User(UserMixin):

    id = 0

    def __init__(self):
        pass


@login_manager.user_loader
def load_user(user_id):
    return User()
