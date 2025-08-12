import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the 'create_app' factory from your 'shop' package
from shop import create_app

# Create the application object that Passenger will use
application = create_app()