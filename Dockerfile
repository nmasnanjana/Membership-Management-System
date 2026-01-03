# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        default-mysql-client \
        pkg-config \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create directories for media and static files
RUN mkdir -p /app/media /app/staticfiles /app/logs

# Collect static files (will be run during container startup)
# Expose port (will be overridden by docker-compose or env variable)
EXPOSE 8000

# Run gunicorn server
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn mms.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3"]

