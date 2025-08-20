#
# FILE: shop/models.py
#

from shop import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app # <-- Add this import
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from datetime import datetime
from sqlalchemy import Index



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
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    
    def get_reset_token(self, salt='password-reset-salt'):
        """Generates a password reset token."""
        s = Serializer(current_app.config['SECRET_KEY'], salt=salt)
        return s.dumps(self.id)

    # --- UPDATED TOKEN VERIFICATION METHOD ---
    @staticmethod
    def verify_reset_token(token, salt='password-reset-salt', max_age=1800): # max_age is in seconds (30 minutes)
        """Verifies the reset token and returns the user if valid."""
        s = Serializer(current_app.config['SECRET_KEY'], salt=salt)
        try:
            user_id = s.loads(token, max_age=max_age)
        except:
            return None # If token is invalid or expired
        return User.query.get(user_id)

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
    

class MailingList(db.Model):
    """Stores the emails for the marketing campaigns."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='Pending', index=True)
    sent_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<MailingList {self.email} - {self.status}>'


class Settings(db.Model):
    """A key-value store for application settings."""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Settings {self.key}>'
    


class ShortURL(db.Model):
    __tablename__ = 'short_url'
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(2048), nullable=False, index=True, info={'mysql_length': 255}) 
    short_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    created_for_email = db.Column(db.String(150), nullable=True, index=True)
    click_count = db.Column(db.Integer, default=0, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    clicks = db.relationship('ClickLog', back_populates='short_url', lazy='dynamic')

    def __repr__(self):
        return f'<ShortURL {self.short_code}>'


class ClickLog(db.Model):
    __tablename__ = 'click_log'
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('short_url.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(45))
    country = db.Column(db.String(100), index=True)
    city = db.Column(db.String(100))
    browser = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    device_type = db.Column(db.String(50), index=True)
    referrer = db.Column(db.Text)
    utm_source = db.Column(db.String(100), index=True)
    utm_medium = db.Column(db.String(100))
    utm_campaign = db.Column(db.String(100), index=True)
    short_url = db.relationship('ShortURL', back_populates='clicks')

    __table_args__ = (
        Index('ix_click_log_url_id_timestamp', 'url_id', 'timestamp'),
    )