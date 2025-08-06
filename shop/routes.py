#
# FILE: shop/routes.py
#

from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from shop import db
from shop.models import User, Product
from shop.forms import RegistrationForm, LoginForm

# Create a Blueprint object
bp = Blueprint('routes', __name__)

@bp.route('/')
@bp.route('/home')
def home():
    products = Product.query.all()
    return render_template('home.html', title='Home', products=products)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, email=form.email.data)
        print(f"Creating new user: {new_user.username}, Email: {new_user.email}")
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        print(f"New user created: {new_user}")
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('routes.login'))
        
    return render_template('register.html', title='Register', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.home'))
        
    form = LoginForm()
    if form.validate_on_submit():
        print(f"Attempting login with email: {form.email.data}")
        user = User.query.filter_by(email=form.email.data).first()
        print(f"User found: {user}")
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('routes.home'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.home'))

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard')


@bp.route('/product/<int:product_id>')
def product(product_id):
    # Fetch the product from the database by its ID.
    # .first_or_404() is a handy shortcut: it gets the first result or
    # automatically sends a 404 "Not Found" error if no product with that ID exists.
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', title=product.name, product=product)