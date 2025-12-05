#!/bin/sh
set -e

# Load configuration
CONFIG_PATH=/data/options.json

if [ -f "$CONFIG_PATH" ]; then
    echo "Loading configuration from $CONFIG_PATH"
    export MQTT_BROKER=$(jq -r '.mqtt_broker // "core-mosquitto"' "$CONFIG_PATH")
    export MQTT_PORT=$(jq -r '.mqtt_port // 1883' "$CONFIG_PATH")
    export MQTT_USER=$(jq -r '.mqtt_user // ""' "$CONFIG_PATH")
    export MQTT_PASSWORD=$(jq -r '.mqtt_password // ""' "$CONFIG_PATH")
    export MQTT_BASE_TOPIC=$(jq -r '.mqtt_base_topic // "marax"' "$CONFIG_PATH")
    export UPDATE_INTERVAL=$(jq -r '.update_interval // 1' "$CONFIG_PATH")
    export LOG_LEVEL=$(jq -r '.log_level // "info"' "$CONFIG_PATH")
    
    echo "Configuration loaded:"
    echo "  MQTT_BROKER=$MQTT_BROKER"
    echo "  MQTT_PORT=$MQTT_PORT"
    echo "  MQTT_USER=$MQTT_USER"
    echo "  MQTT_BASE_TOPIC=$MQTT_BASE_TOPIC"
else
    echo "WARNING: Configuration file $CONFIG_PATH not found, using defaults"
fi

# Set Python logging level
export PYTHONUNBUFFERED=1

# Run the application
exec python3 /app/app.py

