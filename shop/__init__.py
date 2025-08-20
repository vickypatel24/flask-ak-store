# FILE: shop/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate, upgrade  # <-- 1. ADD 'upgrade' TO THIS IMPORT
import os
from dotenv import load_dotenv
load_dotenv()

from flask_mail import Mail
from .scheduler import scheduler

mail = Mail()
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def _ensure_default_admins():
    """Checks for and creates default admin users if they don't exist."""
    from .models import User  # Import here to avoid circular import errors

    # --- DEFINE YOUR ADMINS HERE ---
    default_admins = [
        {
            'username': 'vitrag',
            'email': 'vitragpatel2408@gmail.com',
            'password': 'vklodulalit!'
        },
        {
            'username': 'akshay',
            'email': 'vitragharkhani1606@gmail.com',
            'password': 'aklodulalit'
        }
    ]

    print("Ensuring default admin users exist...")
    for admin_details in default_admins:
        user = User.query.filter_by(email=admin_details['email']).first()
        if not user:
            print(f"Creating default admin user: {admin_details['username']}")
            new_admin = User(
                username=admin_details['username'],
                email=admin_details['email'],
                is_admin=True
            )
            new_admin.set_password(admin_details['password'])
            db.session.add(new_admin)
        elif not user.is_admin:
            user.is_admin = True
            print(f"User {user.username} exists, promoting to admin.")
    
    db.session.commit()
    print("Admin user check complete.")


def get_email_interval(app):
    """Helper function to get the email interval from the DB."""
    with app.app_context():
        from .models import Settings
        setting = Settings.query.filter_by(key='email_interval').first()
        if not setting:
            default_setting = Settings(key='email_interval', value='10')
            db.session.add(default_setting)
            db.session.commit()
            return 10
        return int(setting.value)


def create_app():
    """Construct the core application."""
    app = Flask(__name__)

    # --- Application Configuration ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-hard-to-guess-default-secret-key-for-dev')
    
    # --- Database Configuration (you can uncomment the production block later) ---


    # ### =========================== for production =====================================
    # db_user = os.environ.get('DB_USER')
    # db_pass = os.environ.get('DB_PASS')
    # db_host = os.environ.get('DB_HOST')
    # db_name = os.environ.get('DB_NAME')
    # app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'

    ### ========================== for local development ==========================
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin@localhost/flask_shop_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Mail Configuration ---
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

    # Initialize extensions with the app instance
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # --- Flask-Login Configuration ---
    login_manager.login_view = 'routes.login'
    login_manager.login_message_category = 'info'

    with app.app_context():
        # --- 2. AUTOMATIC DATABASE SETUP AND ADMIN CREATION ---
        print("Applying database migrations on startup...")
        upgrade()
        print("Migrations complete.")
        _ensure_default_admins()
        
        # --- Register Blueprints and Start Scheduler ---
        from . import routes, models
        from .scheduler_jobs import send_single_email
        from .tracker import tracker_bp
        
        app.register_blueprint(routes.bp)
        app.register_blueprint(tracker_bp)
        
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
            if not scheduler.running:
                status_setting = models.Settings.query.filter_by(key='scheduler_status').first()
                start_paused = (status_setting and status_setting.value == 'Paused')
                job_interval = get_email_interval(app)
                
                scheduler.add_job(
                    id='email_sending_job',
                    func=send_single_email,
                    trigger='interval',
                    minutes=job_interval
                )
                scheduler.start(paused=start_paused)

                if start_paused:
                    print("Scheduler started in a PAUSED state.")
                else:
                    print(f"Scheduler started with interval: {job_interval} minutes.")
            
    return app
    

# set FLASK_APP=run.py
# flask db migrate -m "Add MailingList and EmailJob tables"
# flask db upgrade
