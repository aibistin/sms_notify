# from app import create_app, cli, db
from app import create_app, db, cli
from app.models import User, Message, PrivateMessage, Notification, Task


app = create_app()
# Use some functions from app/cli.py
cli.register(app)

# For using the flask_shell
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Message': Message, 'PrivateMessage': PrivateMessage,
            'Notification': Notification, 'Task': Task}
