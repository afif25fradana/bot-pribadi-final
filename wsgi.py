# wsgi.py
"""
WSGI entry point for the application.

This file is used by Gunicorn to run the application in production.
It imports the fully initialized app object from app.py.
"""

# Import the app object and get_main function
from app import app, get_main

# Get the main function and run it to initialize everything
main = get_main()
initialization_success = main()

# Check if initialization was successful
if not initialization_success:
    import sys
    print("FATAL ERROR: Application failed to initialize properly. Exiting.")
    sys.exit(1)

# The app object is now fully initialized and ready for Gunicorn