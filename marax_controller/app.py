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

# Add request logging
@app.before_request
def log_request_info():
    """Log all incoming requests"""
    logger.debug(f"🌐 {request.method} {request.path} - From: {request.remote_addr}")

@app.after_request
def log_response_info(response):
    """Log all outgoing responses"""
    logger.debug(f"📤 {request.method} {request.path} - Status: {response.status_code}")
    return response

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
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        
        # Log received messages for debugging (truncate long payloads)
        payload_preview = payload[:100] + "..." if len(payload) > 100 else payload
        logger.debug(f"📨 MQTT message received: {topic} = {payload_preview}")
        
        try:
        if topic == TOPIC_DEVICE_STATUS:
            device_data['status'] = payload
            logger.debug(f"Updated device status: {payload}")
        elif topic == TOPIC_DEVICE_INFO:
            device_data['info'] = json.loads(payload)
            logger.debug(f"Updated device info: {device_data['info']}")
        elif topic == TOPIC_BREW_STATE:
            try:
                brew_state_data = json.loads(payload)
                device_data['brew_state'] = brew_state_data
                is_active = brew_state_data.get('isActive', False)
                pressure = brew_state_data.get('pressure', 0)
                flow = brew_state_data.get('flow', 0)
                logger.info(f"✅ Updated brew state: isActive={is_active}, pressure={pressure:.2f}, flow={flow:.2f}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse brew state JSON: {e}, payload: {payload[:100]}")
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
                logger.info(f"🔍 ESP32 Debug [{topic}]: {debug_data.get('message', payload)}")
            except:
                logger.info(f"🔍 ESP32 Debug [{topic}]: {payload}")
        elif topic == TOPIC_PROFILE_LIST:
            try:
                # Ignore our own "get" request message
                if payload == "get":
                    logger.debug("Ignoring our own profile list request")
                    return
                
                data = json.loads(payload)
                logger.info(f"✅ Received profile list response with {len(data.get('profiles', []))} profiles")
                if 'profiles' in data:
                    device_data['profiles'] = data['profiles']
                    logger.info(f"✅ Updated profiles: {len(data['profiles'])} profiles found")
                    # Log profile names for debugging
                    for p in data['profiles']:
                        logger.info(f"  - Profile {p.get('id')}: {p.get('name', 'unnamed')} ({p.get('phase_count', 0)} phases)")
                    if 'active_profile' in data:
                        device_data['active_profile'] = data['active_profile']
                        logger.info(f"Active profile: {data['active_profile']}")
                else:
                    logger.warning(f"Profile list response missing 'profiles' key: {data}")
            except Exception as e:
                logger.error(f"Error parsing profile list: {e}")
                logger.error(f"Payload (first 500 chars): {payload[:500]}")
        else:
            logger.debug(f"⚠️ Unhandled topic: {topic}")
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ Failed to parse JSON from {topic}: {e}")
        logger.debug(f"Payload (first 200 chars): {payload[:200]}")
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ ERROR processing MQTT message from {topic}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 60)

def init_mqtt():
    """Initialize MQTT client with retry logic"""
    global mqtt_client, MQTT_BROKER
    
    logger.info("=" * 60)
    logger.info("Initializing MQTT Connection")
    logger.info("=" * 60)
    
    # Request profile list on startup
    def request_profiles_after_connect():
        logger.debug("Requesting profile list after MQTT connection...")
        time.sleep(2)  # Wait for subscriptions to be established
        request_profile_list()
        logger.info("✓ Requested profile list on startup")
    
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
        logger.info("GET / - Serving index page")
        template_path = os.path.join(app.template_folder, 'index.html')
        logger.debug(f"Template path: {template_path}")
        logger.debug(f"Template exists: {os.path.exists(template_path)}")
        html = render_template('index.html')
        logger.debug(f"Template rendered successfully, size: {len(html)} bytes")
        return html
    except Exception as e:
        logger.error("=" * 60)
        logger.error("ERROR: Failed to render index page")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 60)
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
    try:
        logger.debug("GET /api/status - Request received")
        status = device_data.copy()
        status['mqtt_connected'] = mqtt_connected
        status['mqtt_broker'] = MQTT_BROKER
        status['mqtt_port'] = MQTT_PORT
        status['last_update'] = datetime.now().isoformat()
        # Log what we're returning for debugging
        logger.debug(f"API /status returning: status={status.get('status')}, has_info={bool(status.get('info'))}, has_brew_state={bool(status.get('brew_state'))}, has_machine_state={bool(status.get('machine_state'))}")
        response = jsonify(status)
        logger.debug(f"API /status - Response sent successfully")
        return response
    except Exception as e:
        logger.error(f"ERROR in /api/status: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/brew/state')
def api_brew_state():
    """Get brew state"""
    try:
        logger.debug("GET /api/brew/state - Request received")
        brew_state = device_data.get('brew_state', {})
        if brew_state:
            logger.debug(f"API /brew/state returning: isActive={brew_state.get('isActive')}, pressure={brew_state.get('pressure')}, flow={brew_state.get('flow')}")
        else:
            logger.debug("API /brew/state - No brew state data available")
        return jsonify(brew_state)
    except Exception as e:
        logger.error(f"ERROR in /api/brew/state: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

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
        # Wait longer for response (ESP32 needs time to process and publish)
        time.sleep(2.0)
    else:
        logger.info("Using cached profile data (no refresh requested)")
    
    profiles = device_data.get('profiles', [])
    active_profile = device_data.get('active_profile', None)
    
    logger.info(f"API /profiles returning {len(profiles)} profiles")
    if profiles:
        logger.info(f"Profile names: {[p.get('name', 'unnamed') for p in profiles]}")
    else:
        logger.warning("No profiles in device_data - ESP32 may not have responded yet")
    
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
        # Update active profile in device_data
        device_data['active_profile'] = profile_id
        return jsonify({'success': True, 'profile_id': profile_id})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

@app.route('/api/phase')
def api_phase():
    """Get current phase information"""
    try:
        logger.debug("GET /api/phase - Request received")
        phase_data = device_data.get('current_phase', {})
        if phase_data:
            logger.debug(f"API /phase returning: phase={phase_data.get('phase')}, phase_time={phase_data.get('phase_time')}")
        else:
            logger.debug("API /phase - No phase data available")
        return jsonify(phase_data)
    except Exception as e:
        logger.error(f"ERROR in /api/phase: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

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
    logger.info("=" * 60)
    logger.info("MaraX Controller Add-on Starting")
    logger.info("=" * 60)
    
    try:
        # Initialize MQTT
        logger.info("Step 1/4: Initializing MQTT connection...")
        init_mqtt()
        logger.info("✓ MQTT initialization complete")
        
        # Request initial data
        logger.info("Step 2/4: Waiting for MQTT connection to stabilize...")
        time.sleep(2)
        logger.info("Step 3/4: Requesting initial profile list...")
        request_profile_list()
        logger.info("✓ Initial data request sent")
        
        # Start Flask app
        logger.info("Step 4/4: Starting Flask web server...")
        logger.info("=" * 60)
        logger.info("Flask server will start on: http://0.0.0.0:8080")
        logger.info("Ingress URL will be available via Home Assistant")
        logger.info("=" * 60)
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    except Exception as e:
        logger.error("=" * 60)
        logger.error("FATAL ERROR: Failed to start add-on")
        logger.error("=" * 60)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 60)
        raise

