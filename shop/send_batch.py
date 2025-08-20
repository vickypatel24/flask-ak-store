# FILE: send_batch.py

from datetime import datetime
from shop import create_app, db, mail
from shop.models import MailingList
from flask_mail import Message

# Create an app instance and push an application context
app = create_app()
app.app_context().push()

def send_promotional_email(recipient_email):
    """Composes and sends the actual promotional email."""
    try:
        msg = Message(
            subject="A Special Offer from Genric Store!",
            sender=app.config.get('MAIL_USERNAME', 'noreply@yourdomain.com'),
            recipients=[recipient_email]
        )
        msg.html = "<h1>Hello!</h1><p>Thank you for being on our mailing list. Check out our latest products and offers!</p>"
        mail.send(msg)
        print(f"Successfully sent email to {recipient_email}")
        return True
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {e}")
        return False

def process_single_email():
    """Finds one pending email, sends it, and updates its status."""
    print(f"--- {datetime.utcnow()}: Running scheduled email task. ---")
    
    # Find the first email that is still 'Pending'
    email_to_send = MailingList.query.filter_by(status='Pending').order_by(MailingList.id).first()
    
    if not email_to_send:
        print("No pending emails found. Exiting.")
        return

    print(f"Found pending email: {email_to_send.email}. Attempting to send...")
    
    if send_promotional_email(email_to_send.email):
        # If sending was successful, update the database
        email_to_send.status = 'Sent'
        email_to_send.sent_date = datetime.utcnow()
        db.session.commit()
        print(f"Updated status for {email_to_send.email} to 'Sent'.")
    else:
        # Optional: If sending failed, you could mark it as 'Failed'
        email_to_send.status = 'Failed'
        db.session.commit()
        print(f"Updated status for {email_to_send.email} to 'Failed'.")

if __name__ == '__main__':
    process_single_email()