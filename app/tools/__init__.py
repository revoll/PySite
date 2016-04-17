# encoding: utf-8
import time
from emails import send_email

t_counter = 0


def generate_uuid():
    """ Generates a uuid which combines timestamp and global counter.
    :return: 16 bytes long uuid.
    """
    global t_counter
    t_counter += 1
    t_str = ('%011.2f' % time.time()).split('.')
    return '%s%s%03d' % (t_str[0], t_str[1], t_counter % 1000)
