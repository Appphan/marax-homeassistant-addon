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
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info').upper()
log_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR
}
logging.basicConfig(
    level=log_level_map.get(LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f"Log level set to: {LOG_LEVEL}")

# Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Handle ingress path if present
INGRESS_PATH = os.getenv('SUPERVISOR_TOKEN', '')

# Configuration from Home Assistant options
# Note: You can use:
# - IP address (e.g., '192.168.178.2') - Most reliable
# - 'core-mosquitto' (if Mosquitto add-on is installed)
# - 'supervisor' (alternative hostname)
# - 'localhost' (if on same container)
MQTT_BROKER = os.getenv('MQTT_BROKER', 'core-mosquitto')
logger.info(f"Loading MQTT configuration from environment:")
logger.info(f"  MQTT_BROKER={MQTT_BROKER}")
logger.info(f"  MQTT_PORT={os.getenv('MQTT_PORT', '1883')}")
logger.info(f"  MQTT_USER={'***' if os.getenv('MQTT_USER') else '(empty)'}")
logger.info(f"  MQTT_PASSWORD={'***' if os.getenv('MQTT_PASSWORD') else '(empty)'}")

# If broker is set to default and it's not an IP, try to resolve it
# IP addresses don't need resolution
import re
is_ip_address = re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', MQTT_BROKER)

if not is_ip_address and MQTT_BROKER == 'core-mosquitto':
    # For hostnames, try multiple options in order of preference
    MQTT_BROKER_OPTIONS = ['core-mosquitto', 'supervisor', 'localhost', '127.0.0.1']
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
else:
    logger.info(f"Using MQTT broker: {MQTT_BROKER} (IP address or custom hostname)")

MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_USER = os.getenv('MQTT_USER', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
MQTT_BASE_TOPIC = os.getenv('MQTT_BASE_TOPIC', 'marax')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '1'))

# Log configuration (after loading)
logger.info(f"MQTT Configuration loaded:")
logger.info(f"  Broker: {MQTT_BROKER}:{MQTT_PORT}")
logger.info(f"  User: {MQTT_USER if MQTT_USER else '(none)'}")
logger.info(f"  Password: {'***' if MQTT_PASSWORD else '(none)'}")
logger.info(f"  Base Topic: {MQTT_BASE_TOPIC}")

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
            (TOPIC_PROFILE_STATUS, 0),
            (TOPIC_PROFILE_LIST, 0)  # Subscribe to profile list responses
        ]
        
        # Also subscribe to wildcard to catch any messages we might have missed
        wildcard_topic = f"{MQTT_BASE_TOPIC}/#"
        client.subscribe(wildcard_topic, 0)
        logger.info(f"Subscribed to wildcard: {wildcard_topic}")
        
        for topic, qos in topics:
            client.subscribe(topic, qos)
            logger.info(f"Subscribed to {topic} (QoS {qos})")
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
    
    # Log received messages for debugging
    logger.debug(f"Received MQTT message: {topic} = {payload[:100]}...")
    
    try:
        if topic == TOPIC_DEVICE_STATUS:
            device_data['status'] = payload
            logger.debug(f"Updated device status: {payload}")
        elif topic == TOPIC_DEVICE_INFO:
            device_data['info'] = json.loads(payload)
            logger.debug(f"Updated device info: {device_data['info']}")
        elif topic == TOPIC_BREW_STATE:
            device_data['brew_state'] = json.loads(payload)
            logger.debug(f"Updated brew state: {device_data['brew_state']}")
        elif topic == TOPIC_MACHINE_STATE:
            device_data['machine_state'] = json.loads(payload)
            logger.debug(f"Updated machine state: {device_data['machine_state']}")
        elif topic == TOPIC_SCALE_STATE:
            device_data['scale_state'] = json.loads(payload)
            logger.debug(f"Updated scale state: {device_data['scale_state']}")
        elif topic == TOPIC_BREW_PHASE_STATUS:
            device_data['current_phase'] = json.loads(payload)
            logger.debug(f"Updated current phase: {device_data['current_phase']}")
        elif topic == "marax/debug/profile" or topic == "marax/debug/mqtt":
            # Log debug messages for troubleshooting
            try:
                debug_data = json.loads(payload)
                logger.info(f"ESP32 Debug [{topic}]: {debug_data.get('message', payload)}")
            except:
                logger.info(f"ESP32 Debug [{topic}]: {payload}")
        elif topic == TOPIC_PROFILE_LIST:
            try:
                data = json.loads(payload)
                logger.info(f"Received profile list response: {json.dumps(data)}")
                if 'profiles' in data:
                    device_data['profiles'] = data['profiles']
                    logger.info(f"✅ Updated profiles: {len(data['profiles'])} profiles found")
                    if 'active_profile' in data:
                        device_data['active_profile'] = data['active_profile']
                        logger.info(f"Active profile: {data['active_profile']}")
                else:
                    logger.warning(f"Profile list response missing 'profiles' key: {data}")
            except Exception as e:
                logger.error(f"Error parsing profile list: {e}, payload: {payload[:200]}")
        else:
            logger.debug(f"Unhandled topic: {topic}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {topic}: {e}")
        logger.error(f"Payload was: {payload}")
    except Exception as e:
        logger.error(f"Error processing message from {topic}: {e}")
        import traceback
        logger.error(traceback.format_exc())

def init_mqtt():
    """Initialize MQTT client with retry logic"""
    global mqtt_client, MQTT_BROKER
    
    # Use a local variable for broker attempts to avoid modifying global during retries
    current_broker = MQTT_BROKER
    
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
    
    # Alternative broker options if default fails
    broker_options = [current_broker]
    if current_broker == 'core-mosquitto':
        broker_options.extend(['supervisor', 'localhost'])
    
    for attempt in range(max_retries):
        # Select broker for this attempt
        if attempt < len(broker_options):
            current_broker = broker_options[attempt]
        else:
            current_broker = broker_options[-1]  # Use last option
        
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Connecting to MQTT broker at {current_broker}:{MQTT_PORT}")
            mqtt_client.connect(current_broker, MQTT_PORT, 60)
            mqtt_client.loop_start()
            logger.info(f"MQTT connection initiated to {current_broker}:{MQTT_PORT}")
            
            # Wait for connection to establish
            time.sleep(3)
            if mqtt_connected:
                logger.info("✅ MQTT connection established successfully")
                # Update global if we used an alternative
                if current_broker != MQTT_BROKER:
                    MQTT_BROKER = current_broker
                    logger.info(f"Updated MQTT_BROKER to {current_broker}")
                return
            else:
                logger.warning(f"Connection attempt {attempt + 1} failed - not connected after 3 seconds")
                mqtt_client.loop_stop()
                mqtt_client.disconnect()
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Connection attempt {attempt + 1} failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                import traceback
                logger.error("Final connection attempt failed. Traceback:")
                logger.error(traceback.format_exc())
                logger.error("⚠️ MQTT connection failed. The add-on will continue but won't receive data.")
                logger.error("Please check:")
                logger.error("  1. MQTT broker is running (Mosquitto add-on)")
                logger.error("  2. MQTT broker hostname/IP in configuration")
                logger.error("  3. Network connectivity between add-on and broker")
                logger.error(f"  4. Tried brokers: {', '.join(broker_options)}")

def request_profile_list():
    """Request profile list from device"""
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(TOPIC_PROFILE_LIST, "get", qos=0)
        logger.info("Requested profile list")

# Flask Routes
@app.before_request
def log_request():
    """Log all incoming requests"""
    # Log all requests at INFO level so we can see them
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.route('/')
def index():
    """Main page"""
    try:
        logger.info("Serving index page")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
    logger.info("API /status endpoint called")
    status = device_data.copy()
    status['mqtt_connected'] = mqtt_connected
    status['mqtt_broker'] = MQTT_BROKER
    status['mqtt_port'] = MQTT_PORT
    status['last_update'] = datetime.now().isoformat()
    # Log what we're returning for debugging
    logger.info(f"API /status returning data: status={status.get('status')}, has_info={bool(status.get('info'))}, has_brew_state={bool(status.get('brew_state'))}, has_machine_state={bool(status.get('machine_state'))}")
    return jsonify(status)

@app.route('/api/brew/state')
def api_brew_state():
    """Get brew state"""
    logger.info("API /brew/state endpoint called")
    brew_state = device_data.get('brew_state', {})
    logger.info(f"API /brew/state returning: {brew_state}")
    if not brew_state:
        logger.warning("No brew state data available")
    return jsonify(brew_state)

@app.route('/api/machine/state')
def api_machine_state():
    """Get machine state"""
    logger.info("API /machine/state endpoint called")
    machine_state = device_data.get('machine_state', {})
    logger.info(f"API /machine/state returning: {machine_state}")
    if not machine_state:
        logger.warning("No machine state data available")
    return jsonify(machine_state)

@app.route('/api/profiles')
def api_profiles():
    """Get profiles list"""
    logger.info("API /profiles endpoint called")
    
    # Only request fresh profile list if 'refresh' parameter is set
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    if refresh:
        logger.info("Refresh requested, requesting profile list from device")
        request_profile_list()
        # Wait a bit longer for response
        time.sleep(1.0)
    else:
        logger.info("Using cached profile data (no refresh requested)")
    
    profiles = device_data.get('profiles', [])
    active_profile = device_data.get('active_profile', None)
    
    logger.info(f"API /profiles returning {len(profiles)} profiles")
    logger.info(f"Profiles data: {json.dumps(profiles)}")
    
    # Add active_profile to response if available
    response = {
        'profiles': profiles,
        'active_profile': active_profile,
        'count': len(profiles)
    }
    
    return jsonify(response)

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
    logger.info("API /profiles/send endpoint called")
    profile = request.json
    
    if not profile:
        return jsonify({'error': 'Profile data required'}), 400
    
    logger.info(f"Received profile: {profile.get('profileName', 'Unknown')} with {profile.get('phaseCount', 0)} phases")
    
    if mqtt_client and mqtt_connected:
        payload = json.dumps(profile)
        mqtt_client.publish(TOPIC_PROFILE_SET, payload, qos=1)
        logger.info(f"Sent profile to device: {profile.get('profileName', 'Unknown')}")
        return jsonify({'success': True, 'message': 'Profile sent to device'})
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

