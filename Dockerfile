# Dockerfile for Flask on Fly.io via GitHub
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1     PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Start gunicorn on the PORT provided by Fly (default 8080)
# Change 'app:app' if your module/variable differ (e.g., main:server)
CMD ["sh", "-c", "gunicorn -w ${WEB_CONCURRENCY:-2} -b 0.0.0.0:${PORT:-8080} 'app:app'"]
