# FILE: shop/scheduler_jobs.py

from datetime import datetime
from flask import render_template
from . import create_app, db, mail
from .models import MailingList
from .scheduler import scheduler
from .tracker import generate_trackable_link # <-- 1. IMPORT our link generator
from flask_mail import Message

def send_single_email():
    """
    Finds one pending email, creates a unique trackable link,
    sends the promotional template with the link, and updates its status.
    """
    app = create_app()
    with app.app_context():
        print(f"--- {datetime.utcnow()}: Scheduler job running. ---")
        
        email_to_send = MailingList.query.filter_by(status='Pending').order_by(MailingList.id).first()
        
        if not email_to_send:
            print("No pending emails found. Pausing scheduler job.")
            scheduler.pause_job('email_sending_job')
            return

        print(f"Found pending email: {email_to_send.email}. Generating trackable link...")

        # --- 2. GENERATE THE UNIQUE TRACKABLE LINK ---
        # Define the target URL and generate a short code for this specific email recipient
        target_url = "https://www.ziverdokit.us/"
        short_code = generate_trackable_link(long_url=target_url, recipient_email=email_to_send.email)
        
        # Build the full clickable short URL
        # IMPORTANT: Replace 'generic-cures.com' with your actual domain name.
        # For local testing, you might use 'http://127.0.0.1:5000/'
        base_url = "http://127.0.0.1:5000/"
        # base_url = "https://generic-cures.com/"
        trackable_link = base_url + short_code

        print(f"Generated link: {trackable_link}")
        
        # 3. Define the content for the promotional email template
        product_names = [
            "Ivermectin 3mg/6mg/12mg", "mebendazole 100mg", "Hydroxychloroquin 200mg/400mg",
            "Doxycycline 100mg", "Azithromycin 250mg/500mg", "Cephalexin 250mg/500mg",
            "Fluvoxamine 50mg", "Amoxicillin 250mg/500mg", "Zycolchin 0.5mg",
            "Febendazole 500mg"
        ]

        # --- 4. CREATE PRODUCT LINKS USING THE TRACKABLE URL ---
        # Now every product link in the email is the same unique, trackable link.
        products_with_links = [
            {'name': name, 'url': trackable_link} for name in product_names
        ]

        template_data = {
            'subject': 'Important Information from Ziverdokit',
            'greeting': 'Hello Sir/Madam,',
            'company_name': 'Ziverdokit',
            'company_url': trackable_link, # <-- Use the trackable link
            'company_url_display': 'www.ziverdokit.us', # <-- Display text can be different
            'products': products_with_links,
            'closing_message': 'Thanks again'
        }

        # 5. Try to build and send the email
        try:
            html_body = render_template('email_template.html', **template_data)
            msg = Message(
                subject=template_data['subject'],
                sender=app.config['MAIL_USERNAME'],
                recipients=[email_to_send.email],
                html=html_body
            )
            # mail.send(msg)
            
            email_to_send.status = 'Sent'
            email_to_send.sent_date = datetime.utcnow()
            db.session.commit()
            print(f"Successfully sent and updated status for {email_to_send.email}")

        except Exception as e:
            email_to_send.status = 'Failed'
            db.session.commit()
            print(f"FAILED to send promo email to {email_to_send.email}. Error: {e}")