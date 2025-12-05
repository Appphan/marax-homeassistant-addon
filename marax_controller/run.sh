#!/bin/sh
set -e

# Load configuration
CONFIG_PATH=/data/options.json

echo "=========================================="
echo "MaraX Controller Add-on Starting"
echo "=========================================="
echo "Checking for configuration file: $CONFIG_PATH"

if [ -f "$CONFIG_PATH" ]; then
    echo "✓ Configuration file found"
    echo "Loading configuration..."
    
    # Check if jq is available
    if ! command -v jq >/dev/null 2>&1; then
        echo "ERROR: jq is not installed. Installing..."
        apk add --no-cache jq >/dev/null 2>&1 || echo "WARNING: Could not install jq"
    fi
    
    export MQTT_BROKER=$(jq -r '.mqtt_broker // "core-mosquitto"' "$CONFIG_PATH" 2>/dev/null || echo "core-mosquitto")
    export MQTT_PORT=$(jq -r '.mqtt_port // 1883' "$CONFIG_PATH" 2>/dev/null || echo "1883")
    export MQTT_USER=$(jq -r '.mqtt_user // ""' "$CONFIG_PATH" 2>/dev/null || echo "")
    export MQTT_PASSWORD=$(jq -r '.mqtt_password // ""' "$CONFIG_PATH" 2>/dev/null || echo "")
    export MQTT_BASE_TOPIC=$(jq -r '.mqtt_base_topic // "marax"' "$CONFIG_PATH" 2>/dev/null || echo "marax")
    export UPDATE_INTERVAL=$(jq -r '.update_interval // 1' "$CONFIG_PATH" 2>/dev/null || echo "1")
    export LOG_LEVEL=$(jq -r '.log_level // "info"' "$CONFIG_PATH" 2>/dev/null || echo "info")
    
    echo "Configuration loaded successfully:"
    echo "  MQTT_BROKER=$MQTT_BROKER"
    echo "  MQTT_PORT=$MQTT_PORT"
    echo "  MQTT_USER=${MQTT_USER:-'(empty)'}"
    echo "  MQTT_PASSWORD=${MQTT_PASSWORD:+'(set)'}"
    echo "  MQTT_BASE_TOPIC=$MQTT_BASE_TOPIC"
    echo "=========================================="
else
    echo "✗ WARNING: Configuration file $CONFIG_PATH not found!"
    echo "Using default configuration:"
    echo "  MQTT_BROKER=core-mosquitto"
    echo "  MQTT_PORT=1883"
    echo "  MQTT_USER=(empty)"
    echo "  MQTT_PASSWORD=(empty)"
    echo "=========================================="
    echo "Please configure the add-on in Home Assistant:"
    echo "Settings → Add-ons → MaraX Controller → Configuration"
fi

# Set Python logging level
export PYTHONUNBUFFERED=1

# Run the application
exec python3 /app/app.py

