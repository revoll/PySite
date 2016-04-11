# coding:utf-8
from threading import Thread
import smtplib
from email.mime.text import MIMEText

from flask import current_app, render_template

'''
from flask.ext.mail import Message
from . import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
'''


def send_async_email(app, msg, to):
    try:
        s = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        s.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        s.sendmail(app.config['FLASKY_MAIL_SENDER'], to, msg.as_string())
        s.quit()
    except Exception, e:
        print str(e)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = MIMEText(render_template(template + '.html', **kwargs), 'html')
    msg['subject'] = subject
    msg['from'] = app.config['FLASKY_MAIL_SENDER']
    msg['to'] = to
    thr = Thread(target=send_async_email, args=[app, msg, to])
    thr.start()
    return thr
