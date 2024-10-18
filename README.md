# My Flask App with AWS, Docker, and Kubernetes

## Project Overview

In this project, I created a simple Flask web application that integrates with several AWS services, utilizes Docker for containerization, and is deployed using Kubernetes (EKS). This project has been a fun journey into serverless architectures, container orchestration, and cloud-native development. Below is a breakdown of what I built and the steps I followed:

---

### 1. Flask App Features

The basic functionality of the Flask app includes:
- **Login**: Fetches user credentials from **DynamoDB** for authentication.
- **Create Post**: Allows authenticated users to create posts.
- **Delete Post**: Users can delete their posts.
- **View Post**: Anyone can view posts.
- **Update Post**: Authenticated users can update their posts.

---

### 2. AWS API Gateway Endpoints

I set up **AWS API Gateway** to expose several endpoints for the Flask app:
- **/** - Base endpoint for the app
- **/post**:
  - OPTIONS
  - POST
- **/posts**:
  - GET
  - OPTIONS
- **/{id}**:
  - DELETE
  - GET
  - OPTIONS
  - PUT

---

### 3. AWS Lambda Functions

I used **AWS Lambda** to handle specific serverless functions, particularly for managing API requests and interacting with **DynamoDB**. This allowed for efficient serverless operations without managing infrastructure directly.

---

### 4. DynamoDB for Data Storage

For data storage, I used **DynamoDB**:
- **User credentials**: Stored user login information.
- **Posts**: Stored post data for the application.

The Flask app was integrated with DynamoDB to seamlessly fetch, create, update, and delete data.

---

### 5. API Testing with Postman

I used **Postman** for testing all APIs. To authorize requests, I included AWS Signature for authorization. API testing included verifying all routes (GET, POST, PUT, DELETE) for functionality.

---

### 6. Docker for Containerization

To ensure consistency across different environments, I containerized the Flask app using Docker.

#### Steps to Dockerize:
1. **Install Docker**:
   Follow [Docker installation guide](https://docs.docker.com/get-docker/) for your operating system.

2. **Dockerfile**:
   Below is the `Dockerfile` used to build the Flask app container:

   ```dockerfile
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

   # Make port 5000 available to the world outside this container
   EXPOSE 5000

   # Define environment variables for Flask
   ENV FLASK_APP=app.py
   ENV FLASK_RUN_HOST=0.0.0.0
   ENV FLASK_RUN_PORT=5000

   # Run the Flask app directly without Gunicorn
   CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
