# FILE: cron_runner.py

from shop import create_app
from shop.tasks import execute_send_email_batch # <-- Import the pure logic function

def run_task():
    """
    Creates a Flask app context and executes our desired task.
    """
    app = create_app()
    with app.app_context():
        # Directly call the pure Python logic function.
        # This does NOT require a click context.
        execute_send_email_batch()

if __name__ == '__main__':
    print("--- Cron Runner Script Started ---")
    run_task()
    print("--- Cron Runner Script Finished ---")