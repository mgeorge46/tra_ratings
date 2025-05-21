# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /code

# Install dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /code/

# Collect static files
RUN mkdir -p /code/staticfiles

# Run the application
CMD ["gunicorn", "tra_ratings.wsgi:application", "--bind", "0.0.0.0:8000"]
