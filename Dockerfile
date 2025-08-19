# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the local tar.gz library into the container
COPY ./data/cords_semantics-0.2.3.tar.gz /app/

COPY ./policies /app/policies

# Install the local tar.gz library
RUN pip install /app/cords_semantics-0.2.3.tar.gz

# Copy the rest of the application code into the container
COPY . /app/


# Ensure the database folder exists
# RUN mkdir -p /app/db

# Set the PYTHONPATH environment variable to include the src directory
ENV PYTHONPATH=/app/src

# Expose the port the app runs on
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py

# Run the Flask app
CMD ["python", "app.py"]
