# FILE: shop/commands.py

import click
from .tasks import execute_send_email_batch # <-- Import the logic

@click.command('send-email-batch')
def send_email_batch_command():
    """
    Runs the email sending task once.
    This is a command-line wrapper for the core logic.
    """
    print("--- Running send-email-batch command via CLI. ---")
    execute_send_email_batch()