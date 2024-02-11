# gunicorn_config.py

# Define the host and port for Gunicorn to listen on
bind = "0.0.0.0:5000"

# Number of worker processes to run (adjust as needed)
workers = 4

# Set the application module or script
# Replace "your_app" with the name of your Flask application module or script
app_module = "app:app"

# Logging configuration (optional)
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stdout
