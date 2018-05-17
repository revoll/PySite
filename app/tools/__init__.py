# -*- coding: utf-8 -*-
import os
from PIL import Image


def save_post_image(instance, path, name, limit=True, max_x=800, max_y=1200, save_raw=True):
    """
    根据要求将图片分别保存为原图,以及最大分辨率不超过规定值(水平800px，垂直1200px)的裁剪图
    :param instance: 文件流句柄
    :param path: 图片在文件系统中的存储路径
    :param name: 图片存储的名称（不包括“.jpg”后缀）
    :param limit: 是否保存为限制大小的图片
    :param max_x: 最大宽度（limit=True时有效）
    :param max_y: 最大高度（limit=True时有效）
    :param save_raw: 选择是否保存一份原图（limit=True时有效）
    :return: None
    """
    if not os.path.exists(path):
        os.makedirs(path)
    img = Image.open(instance)
    if limit:
        if img.size[0] > max_x or img.size[1] > max_y:
            if img.size[0] / img.size[1] > max_x / max_y:
                resize = img.resize((max_x, int(float(max_x) * img.size[1] / img.size[0])), Image.ANTIALIAS)
            else:
                resize = img.resize((int(float(max_y) * img.size[0] / img.size[1]), max_y), Image.ANTIALIAS)
            resize.save(os.path.join(path, name + u'.jpg'), u'JPEG')
        else:
            img.save(os.path.join(path, name + u'.jpg'), u'JPEG')
        if save_raw:
            img.save(os.path.join(path, name + u'_raw.jpg'), u'JPEG')
    else:
        img.save(os.path.join(path, name + u'.jpg'), u'JPEG')
