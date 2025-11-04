FROM python:3.11-slim

LABEL maintainer="Arancia XDR Platform"
LABEL description="Sigma Rule Validator Service using pySigma"

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY validator.py .

# Make validator executable
RUN chmod +x validator.py

# Expose service port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run as non-root user for security
RUN useradd -m -u 1000 validator && \
    chown -R validator:validator /app
USER validator

# Start the service
CMD ["python3", "validator.py"]
