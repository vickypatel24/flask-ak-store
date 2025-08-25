from flask import Blueprint, request, redirect, abort, render_template
from . import db
from .models import ShortURL, ClickLog
import string
import random
import geoip2.database
from geoip2.errors import AddressNotFoundError
import user_agents

# --- Blueprint Setup ---
tracker_bp = Blueprint('tracker', __name__)


#### need to make this change 

# import os

# --- Load GeoIP Database (More Robustly) ---
# try:
#     # Build a path to the file relative to this script's location
#     # This finds the 'shop' folder, goes up one level to the project root,
#     # and then looks for the file.
#     db_path = os.path.join(os.path.dirname(__file__), '..', 'GeoLite2-City.mmdb')
#     geoip_reader = geoip2.database.Reader(db_path)
# except FileNotFoundError:
#     print("WARNING: GeoLite2-City.mmdb not found. Geolocation tracking will be disabled.")
#     geoip_reader = None

# --- Load GeoIP Database ---
try:
    # Assumes the file is in the root directory of the project
    geoip_reader = geoip2.database.Reader('GeoLite2-City.mmdb')
except FileNotFoundError:
    print("WARNING: GeoLite2-City.mmdb not found. Geolocation tracking will be disabled.")
    geoip_reader = None


# --- Helper Function (for use by the scheduler) ---
def generate_trackable_link(long_url, recipient_email):
    """
    Creates a new unique short URL for a specific recipient.
    This is the main function our email scheduler will call.
    """
    characters = string.ascii_letters + string.digits
    while True:
        short_code = ''.join(random.choices(characters, k=7)) # 7 characters for more combinations
        if not ShortURL.query.filter_by(short_code=short_code).first():
            break

    new_url = ShortURL(
        long_url=long_url, 
        short_code=short_code,
        created_for_email=recipient_email
    )
    db.session.add(new_url)
    db.session.commit()
    
    # Construct the full URL using the request context's host URL
    # We will pass the request's base URL from the scheduler
    # For now, let's assume a placeholder
    return short_code


# --- The Main Redirect and Tracking Route ---
@tracker_bp.route('/<short_code>')
def redirect_short_url(short_code):
    url_entry = ShortURL.query.filter_by(short_code=short_code, is_deleted=False).first_or_404()
    
    # --- Data Collection ---
    visitor_ip = request.remote_addr
    ua_string = request.user_agent.string
    referrer = request.referrer
    parsed_ua = user_agents.parse(ua_string)

    country, city = None, None
    if geoip_reader and visitor_ip not in ('127.0.0.1', 'localhost'):
        try:
            response = geoip_reader.city(visitor_ip)
            country = response.country.name
            city = response.city.name
        except AddressNotFoundError:
            country, city = "Unknown", "Unknown"
        except Exception as e:
            print(f"GeoIP Error: {e}")
            pass

    # --- Database Logging ---
    new_click = ClickLog(
        url_id=url_entry.id,
        ip_address=visitor_ip,
        country=country,
        city=city,
        browser=parsed_ua.browser.family,
        platform=parsed_ua.os.family,
        device_type='mobile' if parsed_ua.is_mobile else 'tablet' if parsed_ua.is_tablet else 'pc' if parsed_ua.is_pc else 'other',
        referrer=referrer,
        utm_source=request.args.get('utm_source'),
        utm_medium=request.args.get('utm_medium'),
        utm_campaign=request.args.get('utm_campaign')
    )
    
    db.session.add(new_click)
    url_entry.click_count += 1
    db.session.commit()

    # --- Render the Interstitial Redirect Page ---
    return render_template('redirecting.html', target_url=url_entry.long_url)