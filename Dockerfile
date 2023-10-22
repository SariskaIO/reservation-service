# Use the Python 3.9-slim image as the base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app
RUN apt update
RUN  apt -y install libpq-dev python3-dev
RUN  apt -y install build-essential

# Install the required packages and modules
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc && \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install Flask setuptools flask-cors flask-restx Flask-API gunicorn Werkzeug==2.2.2 flasgger requests datetime python-dateutil sqlalchemy psycopg2 psycopg2-binary  Flask-Bootstrap4 python-dotenv pytz pyjwt[crypto]


# Copy your application files
COPY /app/ .

# Expose the port your application will run on
EXPOSE 8080

# Start the application using Gunicorn
CMD ["/opt/venv/bin/gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--access-logfile", "-"]