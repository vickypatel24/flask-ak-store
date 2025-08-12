from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


# Initialize extensions so they can be used by other modules
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    """Construct the core application."""
    app = Flask(__name__)

    # --- Application Configuration ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-hard-to-guess-default-secret-key-for-dev')

    
    ### local development database
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin@localhost/flask_shop_db'

    # --- Production database configuration ---

    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')
    db_host = os.environ.get('DB_HOST')
    db_name = os.environ.get('DB_NAME')

    if all([db_user, db_pass, db_host, db_name]):
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin@localhost/flask_shop_db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app instance
    db.init_app(app)
    login_manager.init_app(app)
    
    # --- Flask-Login Configuration ---
    # The name of the view to redirect to when the user needs to log in.
    # We use 'routes.login' because 'login' is inside the 'routes' blueprint.
    login_manager.login_view = 'routes.login'
    login_manager.login_message_category = 'info' # Bootstrap category for flashed message

    with app.app_context():
        # Import parts of our application
        from . import routes  # Import routes
        from . import models  # Import models to ensure they are registered with SQLAlchemy
        
        # Register Blueprints
        app.register_blueprint(routes.bp)

        # Create database tables for our models, if they don't exist
        db.create_all()

        return app