# Use the official Python image as the base image with Python 3.8
FROM python:3.8-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP app.py

# Create and set the working directory in the container
WORKDIR /app

# Install pipenv globally using pip from the base image
RUN pip install pipenv

# Copy the Pipfile and Pipfile.lock into the container
COPY Pipfile Pipfile.lock /app/

# Explicitly specify the Python version (3.8) for pipenv
RUN pipenv --python 3.8

# Install project dependencies using Pipenv
RUN pipenv install --deploy --ignore-pipfile

# Copy the rest of the application code into the container
COPY . /app/

# Expose the port on which the Flask app will run (if needed)
# EXPOSE 5000

# Command to run the Flask app using Pipenv
ENTRYPOINT ["pipenv", "run", "python", "app.py"]
