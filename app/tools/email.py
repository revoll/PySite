from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from .. import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config[u'MAIL_SUBJECT_PREFIX'] + u' ' + subject,
                  sender=app.config[u'MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + u'.txt', **kwargs)
    msg.html = render_template(template + u'.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
