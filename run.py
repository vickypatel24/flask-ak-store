import click
from shop import create_app
from shop.models import User
from shop import db


app = create_app()

# FLASK_APP=run.py

from shop.commands import send_email_batch_command
app.cli.add_command(send_email_batch_command)

if __name__ == '__main__':
    app.run(debug=True)