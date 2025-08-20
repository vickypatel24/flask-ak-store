from apscheduler.schedulers.background import BackgroundScheduler

# Create a single, shared scheduler instance
scheduler = BackgroundScheduler(daemon=True)