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
TOPIC_LEARNING_CONTROL = f"{MQTT_BASE_TOPIC}/learning/control"
TOPIC_LEARNING_STATUS = f"{MQTT_BASE_TOPIC}/learning/status"
TOPIC_LEARNING_PROGRESS = f"{MQTT_BASE_TOPIC}/learning/progress"
TOPIC_LEARNING_KP = f"{MQTT_BASE_TOPIC}/learning/kp"
TOPIC_LEARNING_KI = f"{MQTT_BASE_TOPIC}/learning/ki"
TOPIC_LEARNING_KD = f"{MQTT_BASE_TOPIC}/learning/kd"
TOPIC_LEARNING_OVERSHOOT = f"{MQTT_BASE_TOPIC}/learning/overshoot"
TOPIC_LEARNING_SETTLING_TIME = f"{MQTT_BASE_TOPIC}/learning/settling_time"
TOPIC_LEARNING_STEADY_STATE_ERROR = f"{MQTT_BASE_TOPIC}/learning/steady_state_error"
TOPIC_LEARNING_SHOT_COUNT = f"{MQTT_BASE_TOPIC}/learning/shot_count"
TOPIC_LEARNING_PID_PARAMETERS = f"{MQTT_BASE_TOPIC}/learning/pid_parameters"
TOPIC_CONTROL_SYSTEM = f"{MQTT_BASE_TOPIC}/control/system"
TOPIC_CONTROL_STATUS = f"{MQTT_BASE_TOPIC}/control/status"
TOPIC_SCALE_WEIGHT = f"{MQTT_BASE_TOPIC}/scale/weight"
TOPIC_SCALE_TARGET_WEIGHT = f"{MQTT_BASE_TOPIC}/scale/weight/target"
TOPIC_SCALE_TARE = f"{MQTT_BASE_TOPIC}/scale/tare"
TOPIC_SCALE_BATTERY = f"{MQTT_BASE_TOPIC}/scale/battery"
TOPIC_SHOT_NUMBER = f"{MQTT_BASE_TOPIC}/shot/shotnumber"
TOPIC_SHOT_SET_COUNT = f"{MQTT_BASE_TOPIC}/shot/setcount"
TOPIC_SHOT_DATA = f"{MQTT_BASE_TOPIC}/shot/data"
TOPIC_SHOT_EVENT = f"{MQTT_BASE_TOPIC}/shot/event"
TOPIC_SET_LEVER = f"{MQTT_BASE_TOPIC}/setlever"
TOPIC_SET_TARGET_WEIGHT = f"{MQTT_BASE_TOPIC}/settargetweight"
TOPIC_TIMER_RESET = f"{MQTT_BASE_TOPIC}/timer/reset"
TOPIC_DEVICE_TELEMETRY = f"{MQTT_BASE_TOPIC}/device/telemetry"

# Data storage
device_data = {
    'status': 'offline',
    'info': {},
    'brew_state': {},
    'machine_state': {},
    'scale_state': {},
    'current_phase': {},
    'profiles': [],
    'learning': {
        'status': 'disabled',
        'kp': 0.0,
        'ki': 0.0,
        'kd': 0.0,
        'overshoot': 0.0,
        'settling_time': 0.0,
        'steady_state_error': 0.0,
        'shot_count': 0
    },
    'control_system': 'pid',
    'scale': {
        'weight': 0.0,
        'target_weight': 0.0,
        'battery': 0,
        'connected': False
    },
    'shot': {
        'number': 0,
        'time': 0,
        'weight': 0.0,
        'data': None,
        'events': []
    },
    'settings': {
        'lever_mode': False,
        'weight_profiling': False
    },
    'telemetry': {
        'wifi_rssi': 0,
        'free_heap': 0,
        'min_free_heap': 0
    }
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
        
        # Only log profile-related topics in detail to reduce noise
        is_profile_topic = "profile" in topic.lower()
        
        if is_profile_topic:
            payload_preview = payload[:200] + "..." if len(payload) > 200 else payload
            logger.info(f"📨 PROFILE MQTT: {topic}")
            logger.info(f"   Payload length: {len(payload)} bytes")
            logger.info(f"   Preview: {payload_preview}")
        else:
            # Other topics: only log at debug level
            logger.debug(f"📨 MQTT: {topic}")
        
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
                # Only log at debug level (not profile-related)
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
            # Log profile debug messages
            try:
                debug_data = json.loads(payload)
                logger.info(f"🔍 PROFILE DEBUG [{topic}]: {debug_data.get('message', payload)}")
            except:
                logger.info(f"🔍 PROFILE DEBUG [{topic}]: {payload}")
        elif topic == TOPIC_LEARNING_STATUS:
            device_data['learning']['status'] = payload
            # Only log at debug level (not profile-related)
        elif topic == TOPIC_LEARNING_KP:
            try:
                device_data['learning']['kp'] = float(payload)
            except:
                pass
        elif topic == TOPIC_LEARNING_KI:
            try:
                device_data['learning']['ki'] = float(payload)
            except:
                pass
        elif topic == TOPIC_LEARNING_KD:
            try:
                device_data['learning']['kd'] = float(payload)
            except:
                pass
        elif topic == TOPIC_LEARNING_OVERSHOOT:
            try:
                device_data['learning']['overshoot'] = float(payload)
            except:
                pass
        elif topic == TOPIC_LEARNING_SETTLING_TIME:
            try:
                device_data['learning']['settling_time'] = float(payload)
            except:
                pass
        elif topic == TOPIC_LEARNING_STEADY_STATE_ERROR:
            try:
                device_data['learning']['steady_state_error'] = float(payload)
            except:
                pass
        elif topic == TOPIC_LEARNING_SHOT_COUNT:
            try:
                device_data['learning']['shot_count'] = int(payload)
            except:
                pass
        elif topic == TOPIC_LEARNING_PROGRESS:
            try:
                progress_data = json.loads(payload)
                device_data['learning'].update(progress_data)
            except:
                pass
        elif topic == TOPIC_LEARNING_PID_PARAMETERS:
            try:
                pid_data = json.loads(payload)
                if 'Kp' in pid_data:
                    device_data['learning']['kp'] = pid_data['Kp']
                if 'Ki' in pid_data:
                    device_data['learning']['ki'] = pid_data['Ki']
                if 'Kd' in pid_data:
                    device_data['learning']['kd'] = pid_data['Kd']
                if 'shot_count' in pid_data:
                    device_data['learning']['shot_count'] = pid_data['shot_count']
            except:
                pass
        elif topic == TOPIC_CONTROL_STATUS:
            device_data['control_system'] = payload
            logger.debug(f"Updated control system: {payload}")
        elif topic == TOPIC_SCALE_WEIGHT:
            try:
                device_data['scale']['weight'] = float(payload)
            except:
                pass
        elif topic == TOPIC_SCALE_TARGET_WEIGHT:
            try:
                device_data['scale']['target_weight'] = float(payload)
            except:
                pass
        elif topic == TOPIC_SCALE_BATTERY:
            try:
                device_data['scale']['battery'] = int(payload)
            except:
                pass
        elif topic == TOPIC_SHOT_NUMBER:
            try:
                device_data['shot']['number'] = int(payload)
            except:
                pass
        elif topic == TOPIC_SHOT_DATA:
            try:
                device_data['shot']['data'] = json.loads(payload)
            except:
                pass
        elif topic == TOPIC_SHOT_EVENT:
            try:
                event_data = json.loads(payload)
                # Keep last 10 events
                device_data['shot']['events'].append(event_data)
                if len(device_data['shot']['events']) > 10:
                    device_data['shot']['events'].pop(0)
            except:
                pass
        elif topic == TOPIC_DEVICE_TELEMETRY:
            try:
                telemetry_data = json.loads(payload)
                device_data['telemetry'].update(telemetry_data)
            except:
                pass
        elif topic == TOPIC_PROFILE_LIST:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔔 PROFILE LIST MESSAGE RECEIVED")
            logger.info(f"{'='*60}")
            logger.info(f"Topic: {topic}")
            logger.info(f"Payload length: {len(payload)} bytes")
            
            try:
                # Ignore our own "get" request message
                if payload == "get" or payload.strip() == "get":
                    logger.info("⚠️ Ignoring our own profile list request")
                    logger.info(f"{'='*60}\n")
                    return
                
                # Check if payload is JSON
                if not payload.strip().startswith('{') and not payload.strip().startswith('['):
                    logger.warning(f"⚠️ Profile list payload doesn't look like JSON")
                    logger.warning(f"Payload preview: {payload[:100]}")
                    logger.info(f"{'='*60}\n")
                    return
                
                data = json.loads(payload)
                logger.info(f"✅ JSON parsed successfully")
                logger.info(f"JSON keys: {list(data.keys())}")
                
                if 'profiles' in data:
                    profiles = data['profiles']
                    logger.info(f"✅ Found {len(profiles)} profiles in response")
                    
                    # Normalize field names for frontend compatibility
                    # ESP32 sends snake_case (phase_count), frontend expects camelCase (phaseCount)
                    normalized_profiles = []
                    for p in profiles:
                        normalized = dict(p)  # Copy the profile
                        # Convert phase_count to phaseCount for frontend
                        if 'phase_count' in normalized:
                            normalized['phaseCount'] = normalized.pop('phase_count')
                        # Ensure all expected fields exist
                        if 'id' not in normalized:
                            logger.warning(f"⚠️ Profile missing 'id' field: {normalized}")
                        if 'name' not in normalized:
                            normalized['name'] = normalized.get('profileName', 'Unnamed Profile')
                        normalized_profiles.append(normalized)
                        logger.info(f"  ✅ Profile {normalized.get('id')}: '{normalized.get('name', 'unnamed')}' ({normalized.get('phaseCount', 0)} phases)")
                    
                    device_data['profiles'] = normalized_profiles
                    logger.info(f"✅ Stored {len(normalized_profiles)} profiles in device_data")
                    
                    if 'active_profile' in data:
                        device_data['active_profile'] = data['active_profile']
                        logger.info(f"✅ Active profile: {data['active_profile']}")
                    
                    logger.info(f"{'='*60}\n")
                else:
                    logger.warning(f"⚠️ Profile list response missing 'profiles' key")
                    logger.warning(f"Available keys: {list(data.keys())}")
                    logger.warning(f"Full data preview: {json.dumps(data, indent=2)[:500]}")
                    logger.info(f"{'='*60}\n")
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON decode error: {e}")
                logger.error(f"Payload preview (first 500 chars): {payload[:500]}")
                logger.info(f"{'='*60}\n")
            except Exception as e:
                logger.error(f"❌ Error parsing profile list: {e}")
                logger.error(f"Payload preview (first 500 chars): {payload[:500]}")
                import traceback
                logger.error(traceback.format_exc())
                logger.info(f"{'='*60}\n")
        else:
            # Check if it's a profile-related topic but didn't match handler
            if "profile" in topic.lower():
                logger.warning(f"⚠️ PROFILE topic received but didn't match handler: {topic}")
                logger.warning(f"Expected topics: {TOPIC_PROFILE_LIST}, {TOPIC_PROFILE_SELECT}, {TOPIC_PROFILE_SET}")
                logger.warning(f"Payload preview: {payload[:200]}")
            # Other topics: only log at debug level
    except json.JSONDecodeError as e:
        # Only log JSON errors for profile topics in detail
        if "profile" in topic.lower():
            logger.warning(f"⚠️ Failed to parse JSON from profile topic {topic}: {e}")
            logger.warning(f"Payload (first 200 chars): {payload[:200]}")
        else:
            logger.debug(f"Failed to parse JSON from {topic}: {e}")
    except Exception as e:
        # Only log errors for profile topics in detail
        if "profile" in topic.lower():
            logger.error("=" * 60)
            logger.error(f"❌ ERROR processing PROFILE MQTT message from {topic}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error("=" * 60)
        else:
            logger.debug(f"Error processing {topic}: {e}")

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
    logger.info(f"🔍 request_profile_list() called")
    logger.info(f"   mqtt_client exists: {mqtt_client is not None}")
    logger.info(f"   mqtt_connected: {mqtt_connected}")
    
    if mqtt_client and mqtt_connected:
        logger.info(f"\n{'='*60}")
        logger.info(f"📤 REQUESTING PROFILE LIST")
        logger.info(f"{'='*60}")
        logger.info(f"Topic: {TOPIC_PROFILE_LIST}")
        logger.info(f"Message: 'get'")
        result = mqtt_client.publish(TOPIC_PROFILE_LIST, "get", qos=0)
        logger.info(f"Publish result: rc={result.rc}, mid={result.mid if hasattr(result, 'mid') else 'N/A'}")
        if result.rc == 0:
            logger.info("✅ Request published successfully")
            logger.info(f"{'='*60}\n")
        else:
            logger.error(f"❌ Failed to publish request: MQTT error code {result.rc}")
            logger.info(f"{'='*60}\n")
    else:
        logger.error("❌ Cannot request profile list: MQTT not connected")
        logger.error(f"   mqtt_client: {mqtt_client}")
        logger.error(f"   mqtt_connected: {mqtt_connected}")

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
    # Only request fresh profile list if 'refresh' parameter is set
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    if refresh:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 API /profiles - REFRESH REQUESTED")
        logger.info(f"{'='*60}")
        logger.info(f"Current profiles in cache: {len(device_data.get('profiles', []))}")
        request_profile_list()
        # Wait longer for response (ESP32 needs time to process and publish)
        logger.info(f"⏳ Waiting 2 seconds for ESP32 response...")
        time.sleep(2.0)
        logger.info(f"✅ Wait complete, checking for new profiles...")
        logger.info(f"Profiles in cache after wait: {len(device_data.get('profiles', []))}")
    else:
        logger.info("📋 API /profiles - Using cached data (no refresh)")
    
    profiles = device_data.get('profiles', [])
    active_profile = device_data.get('active_profile', None)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"📋 API /profiles RESPONSE")
    logger.info(f"{'='*60}")
    logger.info(f"Returning {len(profiles)} profiles")
    
    if profiles:
        logger.info(f"Profile names: {[p.get('name', 'unnamed') for p in profiles]}")
        # Log first profile structure for debugging
        if len(profiles) > 0:
            first_profile = profiles[0]
            logger.info(f"First profile structure:")
            logger.info(f"  Keys: {list(first_profile.keys())}")
            logger.info(f"  ID: {first_profile.get('id', 'N/A')}")
            logger.info(f"  Name: {first_profile.get('name', 'N/A')}")
            logger.info(f"  phaseCount: {first_profile.get('phaseCount', 'NOT FOUND')}")
            logger.info(f"  phase_count: {first_profile.get('phase_count', 'NOT FOUND')}")
    else:
        logger.warning("⚠️ No profiles in device_data")
        logger.warning("Possible reasons:")
        logger.warning("  1. ESP32 hasn't responded to profile list request yet")
        logger.warning("  2. MQTT message wasn't received by add-on")
        logger.warning("  3. Profile list was empty on ESP32")
    
    # Add active_profile to response if available
    response = {
        'profiles': profiles,
        'active_profile': active_profile,
        'count': len(profiles)
    }
    
    logger.info(f"Response structure: {list(response.keys())}")
    logger.info(f"{'='*60}\n")
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
        return jsonify({'success': False, 'error': 'Profile data required'}), 400
    
    profile_name = profile.get('profileName', 'Unknown')
    phase_count = profile.get('phaseCount', 0)
    logger.info(f"Received profile: {profile_name} with {phase_count} phases")
    
    if not mqtt_client or not mqtt_connected:
        logger.error("MQTT not connected - cannot send profile")
        return jsonify({'success': False, 'error': 'MQTT not connected. Check add-on configuration and ensure MQTT broker is running.'}), 503
    
    try:
        payload = json.dumps(profile)
        result = mqtt_client.publish(TOPIC_PROFILE_SET, payload, qos=1)
        
        if result.rc == 0:
            logger.info(f"✅ Successfully sent profile to device: {profile_name}")
            # Wait a moment for ESP32 to process and save
            import time
            time.sleep(0.5)
            return jsonify({
                'success': True, 
                'message': f'Profile "{profile_name}" sent to ESP32 and saved to EEPROM',
                'profile_name': profile_name,
                'phase_count': phase_count
            })
        else:
            error_msg = f"MQTT publish failed with code {result.rc}"
            logger.error(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        error_msg = f"Error sending profile: {str(e)}"
        logger.error(f"❌ {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': error_msg}), 500

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

@app.route('/api/learning/control', methods=['POST'])
def api_learning_control():
    """Control learning system"""
    data = request.json
    command = data.get('command')
    
    if not command:
        return jsonify({'error': 'command required'}), 400
    
    valid_commands = ['enable', 'disable', 'reset', 'clear', 'status', 'info', 'pid', 'test']
    if command not in valid_commands:
        return jsonify({'error': f'Invalid command. Valid: {valid_commands}'}), 400
    
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(TOPIC_LEARNING_CONTROL, command, qos=1)
        return jsonify({'success': True, 'command': command})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

@app.route('/api/learning/status', methods=['GET'])
def api_learning_status():
    """Get learning system status"""
    return jsonify(device_data.get('learning', {}))

@app.route('/api/control/system', methods=['POST'])
def api_control_system():
    """Set control system"""
    data = request.json
    system = data.get('system')
    
    if not system:
        return jsonify({'error': 'system required'}), 400
    
    valid_systems = ['pid', 'fuzzy', 'adaptive']
    if system not in valid_systems:
        return jsonify({'error': f'Invalid system. Valid: {valid_systems}'}), 400
    
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(TOPIC_CONTROL_SYSTEM, system, qos=1)
        return jsonify({'success': True, 'system': system})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

@app.route('/api/control/status', methods=['GET'])
def api_control_status():
    """Get control system status"""
    return jsonify({'system': device_data.get('control_system', 'pid')})

@app.route('/api/scale/tare', methods=['POST'])
def api_scale_tare():
    """Tare the scale"""
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(TOPIC_SCALE_TARE, "", qos=1)
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

@app.route('/api/scale/status', methods=['GET'])
def api_scale_status():
    """Get scale status"""
    return jsonify(device_data.get('scale', {}))

@app.route('/api/shot/number', methods=['GET'])
def api_shot_number():
    """Get shot number"""
    return jsonify({'number': device_data.get('shot', {}).get('number', 0)})

@app.route('/api/shot/setcount', methods=['POST'])
def api_shot_setcount():
    """Set shot count"""
    data = request.json
    count = data.get('count')
    
    if count is None or count < 0:
        return jsonify({'error': 'count required and must be >= 0'}), 400
    
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(TOPIC_SHOT_SET_COUNT, str(count), qos=1)
        return jsonify({'success': True, 'count': count})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

@app.route('/api/shot/data', methods=['GET'])
def api_shot_data():
    """Get shot data"""
    return jsonify(device_data.get('shot', {}))

@app.route('/api/settings/lever', methods=['POST'])
def api_settings_lever():
    """Set lever mode"""
    data = request.json
    enabled = data.get('enabled', False)
    
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(TOPIC_SET_LEVER, "1" if enabled else "0", qos=1)
        return jsonify({'success': True, 'enabled': enabled})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

@app.route('/api/timer/reset', methods=['POST'])
def api_timer_reset():
    """Reset brew timer"""
    if mqtt_client and mqtt_connected:
        mqtt_client.publish(TOPIC_TIMER_RESET, "", qos=0)
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'MQTT not connected'}), 503

@app.route('/api/telemetry', methods=['GET'])
def api_telemetry():
    """Get device telemetry"""
    return jsonify(device_data.get('telemetry', {}))

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

