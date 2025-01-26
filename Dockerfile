# Use a base image with Python 3.9 or later
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the required files to the container
COPY . /app

# Install the necessary Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 5678

# Command to run the Flask app
CMD ["python", "app.py"]
