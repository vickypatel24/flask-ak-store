import random
from flask import render_template, url_for, flash, redirect, request, Blueprint, jsonify, session
from flask_login import login_user, current_user, logout_user, login_required
from shop import db
from shop.models import User, Product, MailingList
import smtplib
from sqlalchemy.exc import IntegrityError
import os
from wtforms.validators import Length
from werkzeug.security import generate_password_hash
from flask_mail import Message
from shop import mail
from shop.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, OTPForm, EmailImportForm, IntervalUpdateForm
from functools import wraps
from flask import current_app
from .scheduler import scheduler
from .models import Settings


# Create a Blueprint object
bp = Blueprint('routes', __name__)


# SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
# SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
# EMAIL_USER = os.getenv("EMAIL_USER", "your_email@gmail.com")
# EMAIL_PASS = os.getenv("EMAIL_PASS", "your_app_password")



def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('routes.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@bp.route('/home')
def index():
    # products = Product.query.all()
    # return render_template('home.html', title='Home', products=products)
    return render_template('index.html', title='Home')

@bp.route('/about')
def about():
    return render_template('about.html', title='About Us')

@bp.route('/products')
def products():
    # Later we will fetch products from the database here
    # For now, just show the page
    all_products = Product.query.all()
    return render_template('products.html', title='Our Products', products=all_products)

@bp.route('/contact')
def contact():
    return render_template('contact.html', title='Contact Us')

@bp.route('/faq')
def faq():
    return render_template('faq.html', title='FAQs')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Instead of creating the user, generate OTP and store data in session
        otp = generate_otp()
        
        # We need to hash the password here before storing it
        hashed_password = generate_password_hash(form.password.data)

        # Store form data and OTP in the session
        session['registration_data'] = {
            'username': form.username.data,
            'email': form.email.data,
            'password_hash': hashed_password
        }
        session['otp'] = otp
        session.permanent = True # The session will expire after a set time

        # Send the OTP email
        send_otp_email(form.email.data, otp)
        
        flash('A verification code has been sent to your email.', 'info')
        return redirect(url_for('routes.verify_otp'))
        
    return render_template('register.html', title='Register', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        print(f"Attempting login with email: {form.email.data}")
        user = User.query.filter_by(email=form.email.data).first()
        print(f"User found: {user}")
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('routes.index'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.index'))


@bp.route('/dashboard', methods=['GET'])
@login_required
@admin_required
def dashboard():
    import_form = EmailImportForm()
    interval_form = IntervalUpdateForm()
    
    # Get status and interval directly from the database
    status_setting = Settings.query.filter_by(key='scheduler_status').first()
    interval_setting = Settings.query.filter_by(key='email_interval').first()
    
    # Provide default values if they don't exist in the DB yet
    job_status = status_setting.value if status_setting else "Paused"
    current_interval = interval_setting.value if interval_setting else 10

    # Pre-populate the form with the current interval
    interval_form.interval.data = int(current_interval)

    mailing_list_entries = MailingList.query.order_by(MailingList.id).all()
    
    return render_template('dashboard.html', 
                           title='Admin Dashboard',
                           import_form=import_form,
                           interval_form=interval_form,
                           mailing_list=mailing_list_entries,
                           job_status=job_status,
                           current_interval=current_interval)


@bp.route('/product/<int:product_id>')
def product(product_id):
    # Fetch the product from the database by its ID.
    # .first_or_404() is a handy shortcut: it gets the first result or
    # automatically sends a 404 "Not Found" error if no product with that ID exists.
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', title=product.name, product=product)


@bp.route('/vitrag')
def vitrag():
    return render_template('mail-home.html', title='mail-home')


# @bp.route("/send_email", methods=["POST"])
# def send_email():
#     data = request.get_json()
#     email = data.get("email")

#     try:
#         # SMTP setup (Example: Gmail SMTP)
#         server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
#         server.starttls()
#         server.login(EMAIL_USER, EMAIL_PASS)

#         subject = "Test Email"
#         body = "This is a test email."
#         msg = f"Subject: {subject}\n\n{body}"
#         print(f"Sending email to {email}... commented code ==================================")
#         # server.sendmail(EMAIL_USER, email, msg)
#         server.quit()

#         return jsonify({"success": True})
#     except Exception as e:
#         print("Error sending to", email, ":", e)
#         return jsonify({"success": False})
    

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', 
                  sender='noreply@demo.com',  # Can be a generic sender
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('routes.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('routes.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('routes.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('routes.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


def generate_otp():
    """Generates a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    """Sends an email with the OTP for verification."""
    msg = Message('Your Account Verification Code',
                  sender='noreply@demo.com', # Or your configured MAIL_USERNAME
                  recipients=[email])
    msg.body = f'Your verification code is: {otp}\n\nThis code will expire in 10 minutes.'
    mail.send(msg)


@bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    # If the user isn't in the middle of registration, send them back
    if 'registration_data' not in session or 'otp' not in session:
        flash('Please register first.', 'warning')
        return redirect(url_for('routes.register'))

    form = OTPForm()
    if form.validate_on_submit():
        user_otp = form.otp.data
        if user_otp == session['otp']:
            # OTP is correct, create the user
            reg_data = session['registration_data']
            
            new_user = User(
                username=reg_data['username'],
                email=reg_data['email'],
                password_hash=reg_data['password_hash']
                # If you have is_admin, it will default to False
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            # Clear the temporary data from the session
            session.pop('registration_data', None)
            session.pop('otp', None)
            
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('routes.login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('verify_otp.html', title='Verify Account', form=form)



@bp.route('/import-emails', methods=['POST'])
@login_required
@admin_required
def import_emails():
    import_form = EmailImportForm()
    
    if import_form.validate_on_submit():
        # Get the raw text from the form's text area
        raw_emails = import_form.emails.data.splitlines()
        
        # Initialize counters for the summary message
        new_emails_count = 0
        duplicate_count = 0
        invalid_count = 0

        # Loop through each line pasted by the admin
        for email_str in raw_emails:
            # Clean up whitespace from the beginning and end of the line
            clean_email = email_str.strip()
            
            # Basic check to see if it's a non-empty line that looks like an email
            if clean_email and '@' in clean_email and '.' in clean_email.split('@')[1]:
                # Create a new MailingList object for the database
                new_entry = MailingList(email=clean_email)
                db.session.add(new_entry)
                
                try:
                    # Try to save it to the database
                    db.session.commit()
                    new_emails_count += 1
                except IntegrityError:
                    # This error happens if the email already exists (because of the 'unique' constraint)
                    # We "rollback" the failed 'add' operation and increment the duplicate counter
                    db.session.rollback()
                    duplicate_count += 1
            elif clean_email:
                # If the line wasn't empty but didn't look like an email, count it as invalid
                invalid_count += 1
        
        # Create a detailed success message for the admin
        flash_message = f"Import complete! Added: {new_emails_count}, Duplicates ignored: {duplicate_count}, Invalid lines ignored: {invalid_count}."
        flash(flash_message, "success")

        # --- INTELLIGENT SCHEDULER RESUME ---
        # After successfully adding new emails, check if the scheduler is paused.
        # If it is, resume it so it can start sending to the new addresses.
        if new_emails_count > 0:
            status_setting = Settings.query.filter_by(key='scheduler_status').first()
            if not status_setting:
                status_setting = Settings(key='scheduler_status', value='Running')
                db.session.add(status_setting)
            else:
                status_setting.value = 'Running'
            db.session.commit()
            flash("New emails imported. Scheduler will resume on its next run.", "info")
    else:
        flash("Form submission failed.", "danger")
    return redirect(url_for('routes.dashboard'))



@bp.route('/pause-scheduler', methods=['POST'])
@login_required
@admin_required
def pause_scheduler():
    """Sets the scheduler status to 'Paused' in the database."""
    status_setting = Settings.query.filter_by(key='scheduler_status').first()
    if not status_setting:
        status_setting = Settings(key='scheduler_status', value='Paused')
        db.session.add(status_setting)
    else:
        status_setting.value = 'Paused'
    db.session.commit()
    flash("Email campaign has been paused.", "info")
    return redirect(url_for('routes.dashboard'))


@bp.route('/resume-scheduler', methods=['POST'])
@login_required
@admin_required
def resume_scheduler():
    """Sets the scheduler status to 'Running' in the database."""
    status_setting = Settings.query.filter_by(key='scheduler_status').first()
    if not status_setting:
        status_setting = Settings(key='scheduler_status', value='Running')
        db.session.add(status_setting)
    else:
        status_setting.value = 'Running'
    db.session.commit()
    flash("Email campaign has been resumed.", "success")
    return redirect(url_for('routes.dashboard'))

# ; Your Hosting SMTP (cPanel, etc.)
# ; If your hosting provider gives you email accounts (like noreply@yourdomain.com),
# ; you’ll have SMTP details in cPanel → Email Accounts → Connect Devices.

# ; SMTP_SERVER = "mail.yourdomain.com"
# ; SMTP_PORT = 587
# ; EMAIL_USER = "noreply@yourdomain.com"
# ; EMAIL_PASS = "your_email_password"

# DB_USER = generic_vitrag
# DB_PASS = vitragkrisha7
# DB_HOST = 
# DB_NAME = generic_ak-storedb01