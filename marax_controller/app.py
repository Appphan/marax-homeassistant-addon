#!/usr/bin/env python3
"""
MaraX Controller Home Assistant Add-on
Web interface for managing MaraX ESP32 Controller
"""

import os
import json
import logging
import paho.mqtt.client as mqtt
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Handle ingress path if present
INGRESS_PATH = os.getenv('SUPERVISOR_TOKEN', '')

# Configuration from Home Assistant options
MQTT_BROKER = os.getenv('MQTT_BROKER', 'core-mosquitto')

# For Home Assistant add-ons, MQTT broker is accessible via supervisor network
# Try multiple hostnames in order of preference
MQTT_BROKER_OPTIONS = ['core-mosquitto', 'supervisor', 'localhost', '127.0.0.1']

# If default broker doesn't work, try alternatives
if MQTT_BROKER == 'core-mosquitto':
    import socket
    resolved = False
    for broker_option in MQTT_BROKER_OPTIONS:
        try:
            socket.gethostbyname(broker_option)
            logger.info(f"Hostname {broker_option} resolves correctly")
            resolved = True
            break
        except socket.gaierror:
            continue
    
    if not resolved:
        # Use supervisor as default (most reliable in Home Assistant)
        MQTT_BROKER = 'supervisor'
        logger.warning(f"Could not resolve hostnames, using {MQTT_BROKER} as fallback")

MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
MQTT_BASE_TOPIC = os.getenv('MQTT_BASE_TOPIC', 'marax')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 1))

# MQTT Topics
TOPIC_DEVICE_STATUS = f"{MQTT_BASE_TOPIC}/device/status"
TOPIC_DEVICE_INFO = f"{MQTT_BASE_TOPIC}/device/info"
TOPIC_BREW_STATE = f"{MQTT_BASE_TOPIC}/brew/state"
TOPIC_MACHINE_STATE = f"{MQTT_BASE_TOPIC}/machine/state"
TOPIC_SCALE_STATE = f"{MQTT_BASE_TOPIC}/scale/state"
TOPIC_BREW_PHASE = f"{MQTT_BASE_TOPIC}/brew/phase"
TOPIC_BREW_PHASE_STATUS = f"{MQTT_BASE_TOPIC}/brew/phase_status"
TOPIC_PROFILE_LIST = f"{MQTT_BASE_TOPIC}/brew/profile/list"
TOPIC_PROFILE_SELECT = f"{MQTT_BASE_TOPIC}/brew/profile/select"
TOPIC_PROFILE_SET = f"{MQTT_BASE_TOPIC}/brew/profile/set"
TOPIC_PROFILE_STATUS = f"{MQTT_BASE_TOPIC}/profile/status"

# Data storage
device_data = {
    'status': 'offline',
    'info': {},
    'brew_state': {},
    'machine_state': {},
    'scale_state': {},
    'current_phase': {},
    'profiles': []
}

# MQTT Client
mqtt_client = None
mqtt_connected = False

def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        logger.info("✅ Connected to MQTT broker successfully")
        
        # Subscribe to all topics
        topics = [
            (TOPIC_DEVICE_STATUS, 1),
            (TOPIC_DEVICE_INFO, 1),
            (TOPIC_BREW_STATE, 1),
            (TOPIC_MACHINE_STATE, 1),
            (TOPIC_SCALE_STATE, 1),
            (TOPIC_BREW_PHASE, 0),
            (TOPIC_BREW_PHASE_STATUS, 0),
            (TOPIC_PROFILE_STATUS, 0)
        ]
        
        for topic, qos in topics:
            client.subscribe(topic, qos)
            logger.info(f"Subscribed to {topic}")
    else:
        mqtt_connected = False
        error_messages = {
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorized"
        }
        error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
        logger.error(f"❌ Failed to connect to MQTT broker: {error_msg} (code: {rc})")

def on_disconnect(client, userdata, rc):
    """MQTT disconnection callback"""
    global mqtt_connected
    mqtt_connected = False
    logger.warning("Disconnected from MQTT broker")

def on_message(client, userdata, msg):
    """MQTT message callback"""
    topic = msg.topic
    payload = msg.payload.decode()
    
    try:
        if topic == TOPIC_DEVICE_STATUS:
            device_data['status'] = payload
        elif topic == TOPIC_DEVICE_INFO:
            device_data['info'] = json.loads(payload)
        elif topic == TOPIC_BREW_STATE:
            device_data['brew_state'] = json.loads(payload)
        elif topic == TOPIC_MACHINE_STATE:
            device_data['machine_state'] = json.loads(payload)
        elif topic == TOPIC_SCALE_STATE:
            device_data['scale_state'] = json.loads(payload)
        elif topic == TOPIC_BREW_PHASE_STATUS:
            device_data['current_phase'] = json.loads(payload)
        elif topic == TOPIC_PROFILE_LIST:
            data = json.loads(payload)
            if 'profiles' in data:
                device_data['profiles'] = data['profiles']
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {topic}: {e}")
    except Exception as e:
        logger.error(f"Error processing message from {topic}: {e}")

def init_mqtt():
    """Initialize MQTT client with retry logic"""
    global mqtt_client
    
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    
    if MQTT_USER and MQTT_PASSWORD:
        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        logger.info(f"Using MQTT authentication: user={MQTT_USER}")
    else:
        logger.info("No MQTT authentication configured")
    
    # Try connecting with retry logic
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            mqtt_client.loop_start()
            logger.info(f"MQTT connection initiated to {MQTT_BROKER}:{MQTT_PORT}")
            
            # Wait for connection to establish
            time.sleep(3)
            if mqtt_connected:
                logger.info("✅ MQTT connection established successfully")
                return
            else:
                logger.warning(f"Connection attempt {attempt + 1} failed - not connected after 3 seconds")
                mqtt_client.loop_stop()
                mqtt_client.disconnect()
                
                # Try alternative broker hostname if this was core-mosquitto
                if attempt < max_retries - 1 and MQTT_BROKER == 'core-mosquitto':
                    global MQTT_BROKER
                    if attempt == 0:
                        MQTT_BROKER = 'supervisor'
                        logger.info(f"Trying alternative broker: {MQTT_BROKER}")
                    elif attempt == 1:
                        MQTT_BROKER = 'localhost'
                        logger.info(f"Trying alternative broker: {MQTT_BROKER}")
                
                time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Connection attempt {attempt + 1} failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            
            if attempt < max_retries - 1:
                # Try alternative broker hostname
                if MQTT_BROKER == 'core-mosquitto':
                    global MQTT_BROKER
                    if attempt == 0:
                        MQTT_BROKER = 'supervisor'
                        logger.info(f"Trying alternative broker: {MQTT_BROKER}")
                    elif attempt == 1:
                        MQTT_BROKER = 'localhost'
                        logger.info(f"Trying alternative broker: {MQTT_BROKER}")
                time.sleep(retry_delay)
            else:
                import traceback
                logger.error("Final connection attempt failed. Traceback:")
                logger.error(traceback.format_exc())
                logger.error("⚠️ MQTT connection failed. The add-on will continue but won't receive data.")
                logger.error("Please check:")
                logger.error("  1. MQTT broker is running (Mosquitto add-on)")
                logger.error("  2. MQTT broker hostname in configuration")
                logger.error("  3. Network connectivity between add-on and broker")

def request_profile_list():
    """Request profile list from device"""
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(TOPIC_PROFILE_LIST, "get", qos=0)
        logger.info("Requested profile list")

# Flask Routes
@app.route('/')
def index():
    """Main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        # Fallback HTML if template doesn't exist
        return """
        <!DOCTYPE html>
        <html>
        <head><title>MaraX Controller</title></head>
        <body>
            <h1>MaraX Controller</h1>
            <p>Web interface is loading...</p>
            <p>API Status: <a href="/api/status">/api/status</a></p>
            <p>Health: <a href="/health">/health</a></p>
        </body>
        </html>
        """

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'mqtt_connected': mqtt_connected,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status')
def api_status():
    """Get device status"""
    status = device_data.copy()
    status['mqtt_connected'] = mqtt_connected
    status['mqtt_broker'] = MQTT_BROKER
    status['mqtt_port'] = MQTT_PORT
    return jsonify(status)

@app.route('/api/brew/state')
def api_brew_state():
    """Get brew state"""
    return jsonify(device_data.get('brew_state', {}))

@app.route('/api/machine/state')
def api_machine_state():
    """Get machine state"""
    return jsonify(device_data.get('machine_state', {}))

@app.route('/api/profiles')
def api_profiles():
    """Get profiles list"""
    if not device_data.get('profiles'):
        request_profile_list()
        time.sleep(0.5)  # Wait for response
    return jsonify(device_data.get('profiles', []))

@app.route('/api/profiles/select', methods=['POST'])
def api_profile_select():
    """Select a profile"""
    data = request.json
    profile_id = data.get('profile_id')
    
    if profile_id is None:
        return jsonify({'error': 'profile_id required'}), 400
    
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(TOPIC_PROFILE_SELECT, str(profile_id), qos=1)
        return jsonify({'success': True, 'profile_id': profile_id})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

@app.route('/api/profiles/send', methods=['POST'])
def api_profile_send():
    """Send a profile to device"""
    profile = request.json
    
    if not profile:
        return jsonify({'error': 'Profile data required'}), 400
    
    if mqtt_client and mqtt_connected:
        payload = json.dumps(profile)
        mqtt_client.publish(TOPIC_PROFILE_SET, payload, qos=1)
        logger.info(f"Sent profile: {profile.get('name', 'Unknown')}")
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

@app.route('/api/brew/stop', methods=['POST'])
def api_brew_stop():
    """Stop brewing"""
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(f"{MQTT_BASE_TOPIC}/remotestate", "1", qos=1)
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

@app.route('/api/target/weight', methods=['POST'])
def api_target_weight():
    """Set target weight"""
    data = request.json
    weight = data.get('weight')
    
    if weight is None:
        return jsonify({'error': 'weight required'}), 400
    
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(f"{MQTT_BASE_TOPIC}/settargetweight", str(weight), qos=1)
        return jsonify({'success': True, 'weight': weight})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

# Static files
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Initialize MQTT
    init_mqtt()
    
    # Request initial data
    time.sleep(2)
    request_profile_list()
    
    # Start Flask app
    logger.info("Starting MaraX Controller add-on")
    app.run(host='0.0.0.0', port=8080, debug=False)

