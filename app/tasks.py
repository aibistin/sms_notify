# tasks.py
import json
import sys
import time
from rq import get_current_job
from flask import render_template
from app import create_app, db
from app.email import send_email
from app.models import User, Message, Task

app = create_app()
# Make this app the current app instance
app.app_context().push()


# Starting Redis tasks on Ubuntu
# sudo service redis-server start
# rq worker sms-notify-tasks

def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(), 'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()


def export_messages(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_msgs = user.messages.count()
        for msg in user.messages.order_by(Message.timestamp.asc()):
            data.append({'body': msg.body, 'timestamp': msg.timestamp.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(round(100 * i / total_msgs,2))

        send_email('[SMS-Notify] Your sms messages',
                sender=app.config['ADMINS'][0], recipients=[user.email],
                text_body=render_template('email/export_messages.txt', user=user),
                html_body=render_template('email/export_messages.html',user=user),
                attachments=[('messages.json', 'application/json',json.dumps({'messages': data}, indent=4))],sync=True)
    except:
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
