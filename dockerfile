# Use a Python 3.9 image as a base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy only requirements.txt first for caching purposes
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application code
COPY . .

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Make port 8080 available to the world outside this container
EXPOSE 5000

# Define environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Run the Flask app directly without Gunicorn
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
