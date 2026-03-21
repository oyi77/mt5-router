# Backend
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Copy gunicorn config
COPY gunicorn.conf.py ./

# Create data and logs directories
RUN mkdir -p data logs

# Expose port
EXPOSE 8080

# Run the application with gunicorn (production) or uvicorn (development)
CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
