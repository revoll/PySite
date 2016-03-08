# encoding: utf-8
from PIL import Image
from StringIO import StringIO
import time

t_counter = 0


@staticmethod
def generate_uuid():
    """ Generates a uuid which combines timestamp and global counter.
    :return: 16 bytes long uuid.
    """
    global t_counter
    t_counter += 1
    t_str = ('%011.2f' % time.time()).split('.')
    return '%s%s%03d' % (t_str[0], t_str[1], t_counter % 1000)


@staticmethod
def quadrating_image(img, size=150):
    if not isinstance(img, Image.Image) or size <= 0:
        return img  # None
    if img.size[0] != img.size[1]:
        if img.size[0] > img.size[1]:
            i_size = img.size[1]
            i_diff = (img.size[0] - img.size[1]) / 2
            box = (i_diff, 0, i_size + i_diff, i_size)
        else:
            i_size = img.size[0]
            i_diff = (img.size[1] - img.size[0]) / 2
            box = (0, i_diff, i_size, i_size + i_diff)
        img = img.crop(box)
    return img.resize((size, size), Image.ANTIALIAS)


@staticmethod
def thumbnail_image(image_path, size=150, fmt='PNG'):
    img_sio = StringIO()
    img = Image.open(image_path)
    # img.thumbnail((th_size, th_size), Image.ANTIALIAS)
    img = quadrating_image(img, size)
    img.save(img_sio, fmt)  # quality=70
    img_sio.seek(0)
    return img_sio
