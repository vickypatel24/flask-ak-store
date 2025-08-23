import click
from flask.cli import with_appcontext
from datetime import datetime
from flask import render_template
from . import db, mail
from .models import MailingList, Settings
from flask_mail import Message

def send_promo_email_logic(email_to_send, app):
    """The core logic for sending one email."""
    print(f"Found pending email: {email_to_send.email}. Attempting to send...")
    
    # Your email content and sending logic
    product_names = [
        "Ivermectin 3mg/6mg/12mg", "mebendazole 100mg", "Hydroxychloroquin 200mg/400mg",
        "Doxycycline 100mg", "Azithromycin 250mg/500mg", "Cephalexin 250mg/500mg",
        "Fluvoxamine 50mg", "Amoxicillin 250mg/500mg", "Zycolchin 0.5mg",
        "Febendazole 500mg"
    ]
    products_with_links = [{'name': name, 'url': "https://ziverdokit.us/"} for name in product_names]
    template_data = {
        'subject': 'Important Information from Ziverdokit', 'greeting': 'Hello Sir/Madam,',
        'company_name': 'Ziverdokit', 'company_url': 'https://www.ziverdokit.us',
        'company_url_display': 'www.ziverdokit.us', 'products': products_with_links,
        'closing_message': 'Thanks again'
    }

    try:
        html_body = render_template('email_template.html', **template_data)
        msg = Message(
            subject=template_data['subject'],
            sender=app.config['MAIL_USERNAME'],
            recipients=[email_to_send.email],
            html=html_body
        )

        ##### ================= lolulalit =============================
        # mail.send(msg)
        
        email_to_send.status = 'Sent'
        email_to_send.sent_date = datetime.utcnow()
        db.session.commit()
        print(f"Successfully sent and updated status for {email_to_send.email}")
    except Exception as e:
        email_to_send.status = 'Failed'
        db.session.commit()
        print(f"FAILED to send promo email to {email_to_send.email}. Error: {e}")

@click.command('send-email-batch')
@with_appcontext
def send_email_batch_command():
    """Finds and sends one pending email from the mailing list."""
    print(f"--- {datetime.utcnow()}: Running send-email-batch command. ---")
    
    # Check if the process is "paused" in the database
    status_setting = Settings.query.filter_by(key='scheduler_status').first()
    if status_setting and status_setting.value == 'Paused':
        print("Scheduler is paused in database. Exiting.")
        return

    email_to_send = MailingList.query.filter_by(status='Pending').order_by(MailingList.id).first()
    
    if not email_to_send:
        print("No pending emails found. Nothing to do.")
        return
    
    # We need the app object to get the mail configuration
    from flask import current_app
    send_promo_email_logic(email_to_send, current_app)