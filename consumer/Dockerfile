FROM python:3.9-slim-buster

WORKDIR /app

# Install websockets and other dependencies
RUN pip install websockets

# Copy your Python script into the container
COPY server.py .

# Expose the port the server will listen on
EXPOSE 8765

# Command to run the server when the container starts
CMD ["python", "server.py"]
