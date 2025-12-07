#!/usr/bin/env python3
"""
MaraX Profile Sender Script
Sends a brewing profile to the MaraX controller via MQTT

Usage:
    python send_profile.py profile.json
    
    Or use as a Home Assistant script:
    python send_profile.py --home-assistant --profile-id 3
"""

import json
import sys
import argparse
import paho.mqtt.client as mqtt
from typing import Dict, List, Any

# MQTT Configuration (adjust to your setup)
MQTT_BROKER = "localhost"  # or your MQTT broker IP
MQTT_PORT = 1883
MQTT_USER = "mqtt-user"
MQTT_PASSWORD = "smart123"
PROFILE_TOPIC = "marax/brew/profile/set"
STATUS_TOPIC = "marax/profile/status"

def create_profile_template() -> Dict[str, Any]:
    """Create a template profile structure"""
    return {
        "profile_id": 3,
        "name": "Custom Profile",
        "technique": "custom",
        "default_dose": 18.0,
        "default_yield": 36.0,
        "default_ratio": 2.0,
        "phases": [
            {
                "name": "preinfusion",
                "phase_index": 0,
                "control_mode": 0,  # MODE_PRESSURE
                "target_pressure_start": 2.5,
                "target_pressure_end": 2.5,
                "target_flow_start": 0.0,
                "target_flow_end": 0.0,
                "max_duration": 15.0,
                "min_duration": 0.0,
                "ramp_duration": 0.0,
                "use_ramp": False,
                "allow_manual_stop": True,
                "publish_events": True,
                "criteria_count": 1,
                "criteria_logic": 0,  # BREAKOUT_NONE
                "breakout_criteria": [
                    {
                        "type": 1,  # BREAKOUT_TIME
                        "threshold": 15.0,
                        "enabled": True,
                        "min_duration": 0.0
                    }
                ]
            },
            {
                "name": "extraction",
                "phase_index": 1,
                "control_mode": 0,  # MODE_PRESSURE
                "target_pressure_start": 9.0,
                "target_pressure_end": 9.0,
                "target_flow_start": 0.0,
                "target_flow_end": 0.0,
                "max_duration": 30.0,
                "min_duration": 0.0,
                "ramp_duration": 0.0,
                "use_ramp": False,
                "allow_manual_stop": True,
                "publish_events": True,
                "criteria_count": 1,
                "criteria_logic": 0,
                "breakout_criteria": [
                    {
                        "type": 2,  # BREAKOUT_WEIGHT
                        "threshold": 36.0,
                        "enabled": True,
                        "min_duration": 0.0
                    }
                ]
            }
        ]
    }

def load_profile_from_file(filename: str) -> Dict[str, Any]:
    """Load profile from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)

def send_profile(client: mqtt.Client, profile: Dict[str, Any]) -> bool:
    """Send profile to MQTT broker"""
    payload = json.dumps(profile)
    result = client.publish(PROFILE_TOPIC, payload, qos=1)
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"✓ Profile sent successfully")
        print(f"  Topic: {PROFILE_TOPIC}")
        print(f"  Profile: {profile['name']}")
        print(f"  Phases: {len(profile['phases'])}")
        return True
    else:
        print(f"✗ Failed to send profile: {result.rc}")
        return False

def on_connect(client, userdata, flags, rc):
    """Callback for when client connects"""
    if rc == 0:
        print("✓ Connected to MQTT broker")
        client.subscribe(STATUS_TOPIC)
    else:
        print(f"✗ Connection failed: {rc}")

def on_message(client, userdata, msg):
    """Callback for when message is received"""
    payload = msg.payload.decode()
    print(f"Status: {payload}")
    
    if "success" in payload.lower() or "ready" in payload.lower():
        print("✓ Profile accepted by device")
        client.disconnect()
    elif "error" in payload.lower():
        print(f"✗ Error from device: {payload}")
        client.disconnect()

def main():
    parser = argparse.ArgumentParser(description='Send MaraX brewing profile via MQTT')
    parser.add_argument('profile_file', nargs='?', help='JSON profile file')
    parser.add_argument('--broker', default=MQTT_BROKER, help='MQTT broker address')
    parser.add_argument('--port', type=int, default=MQTT_PORT, help='MQTT broker port')
    parser.add_argument('--user', default=MQTT_USER, help='MQTT username')
    parser.add_argument('--password', default=MQTT_PASSWORD, help='MQTT password')
    parser.add_argument('--template', action='store_true', help='Generate template profile')
    
    args = parser.parse_args()
    
    if args.template:
        template = create_profile_template()
        print(json.dumps(template, indent=2))
        return
    
    if not args.profile_file:
        print("Error: Profile file required")
        print("Usage: python send_profile.py profile.json")
        print("       python send_profile.py --template  # Generate template")
        sys.exit(1)
    
    # Load profile
    try:
        profile = load_profile_from_file(args.profile_file)
    except FileNotFoundError:
        print(f"Error: File not found: {args.profile_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        sys.exit(1)
    
    # Connect to MQTT
    client = mqtt.Client()
    client.username_pw_set(args.user, args.password)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(args.broker, args.port, 60)
        client.loop_start()
        
        # Wait a bit for connection
        import time
        time.sleep(1)
        
        # Send profile
        if send_profile(client, profile):
            # Wait for response
            time.sleep(5)
        
        client.loop_stop()
        client.disconnect()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

