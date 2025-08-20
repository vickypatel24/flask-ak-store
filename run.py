import click
from shop import create_app
from shop.models import User
from shop import db


app = create_app()

# FLASK_APP=run.py

if __name__ == '__main__':
    app.run(debug=True)