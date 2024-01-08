# Use the official Python image as the base image
FROM python:3.11.6

# Set the working directory inside the container
WORKDIR /app

# Copy the application code and requirements file into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that your Flask app will listen on
EXPOSE 5000

# Define the command to run your Flask app with Gunicorn
CMD ["gunicorn", "--workers=4", "--bind", "0.0.0.0:5000", "app:app"]
