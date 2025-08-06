#
# FILE: shop/models.py
#

from shop import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# This function is required by Flask-Login to load a user from the session.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# UserMixin adds required attributes for Flask-Login
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_file = db.Column(db.String(100), nullable=False, default='default.jpg')
    stock = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Product {self.name}>'