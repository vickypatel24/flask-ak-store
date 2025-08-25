# FILE: shop/tasks.py
# This file contains the "pure" logic for our background tasks.

from datetime import datetime
from . import db, mail
from .models import MailingList, Settings
from .tracker import generate_trackable_link
from flask import render_template
from flask_mail import Message

def execute_send_email_batch():
    """
    The core logic for sending one email from the mailing list.
    This is a 'pure' function that can be called from anywhere.
    """
    print(f"--- {datetime.utcnow()}: Executing email sending task. ---")
    
    # Check the database to see if the campaign is running
    status_setting = Settings.query.filter_by(key='scheduler_status').first()
    if not status_setting or status_setting.value != 'Running':
        print("Scheduler is paused in database. Exiting.")
        return

    # Find the first email that is still 'Pending'
    email_to_send = MailingList.query.filter_by(status='Pending').order_by(MailingList.id).first()
    
    if not email_to_send:
        print("No pending emails found. Pausing scheduler.")
        status_setting.value = 'Paused'
        db.session.commit()
        return

    print(f"Found pending email: {email_to_send.email}. Attempting to send...")
    
    # (The rest of the email sending logic is the same)
    target_url = "https://www.ziverdokit.us/"
    short_code = generate_trackable_link(long_url=target_url, recipient_email=email_to_send.email)
    base_url = "https://generic-cures.com/" 
    trackable_link = base_url + short_code

    product_names = [
        "Ivermectin 3mg/6mg/12mg", "mebendazole 100mg", "Hydroxychloroquin 200mg/400mg",
        "Doxycycline 100mg", "Azithromycin 250mg/500mg", "Cephalexin 250mg/500mg",
        "Fluvoxamine 50mg", "Amoxicillin 250mg/500mg", "Zycolchin 0.5mg",
        "Febendazole 500mg"
    ]
    products_with_links = [{'name': name, 'url': trackable_link} for name in product_names]
    template_data = {
        'subject': 'Important Information from Ziverdokit', 'greeting': 'Hello Sir/Madam,',
        'company_name': 'Ziverdokit', 'company_url': trackable_link,
        'company_url_display': 'www.ziverdokit.us', 'products': products_with_links,
        'closing_message': 'Thanks again'
    }

    try:
        html_body = render_template('email_template.html', **template_data)
        msg = Message(
            subject=template_data['subject'],
            recipients=[email_to_send.email],
            html=html_body,
            sender='your-sender-email@gmail.com' # It's good practice to set sender here
        )
        mail.send(msg)
        
        email_to_send.status = 'Sent'
        email_to_send.sent_date = datetime.utcnow()
        db.session.commit()
        print(f"Successfully sent and updated status for {email_to_send.email}")

    except Exception as e:
        email_to_send.status = 'Failed'
        db.session.commit()
        print(f"FAILED to send promo email to {email_to_send.email}. Error: {e}")