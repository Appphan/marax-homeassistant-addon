ARG BUILD_FROM
FROM ${BUILD_FROM}

# Set working directory
WORKDIR /app

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    wget \
    curl

# Copy application files
COPY . /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir --break-system-packages \
    paho-mqtt==1.6.1 \
    flask==2.3.3 \
    flask-cors==4.0.0 \
    python-dotenv==1.0.0

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run application
CMD ["python3", "/app/app.py"]

