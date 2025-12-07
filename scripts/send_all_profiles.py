#!/usr/bin/env python3
"""
Send all sample brewing profiles to MaraX ESP32 via MQTT
"""

import json
import sys
import os
import time
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', '192.168.178.2')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER', 'mqtt-user')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'smart123')
MQTT_BASE_TOPIC = os.getenv('MQTT_BASE_TOPIC', 'marax')

PROFILE_SET_TOPIC = f"{MQTT_BASE_TOPIC}/brew/profile/set"
PROFILE_ACK_TOPIC = f"{MQTT_BASE_TOPIC}/brew/profile/ack"

# Profile files
PROFILES_DIR = os.path.join(os.path.dirname(__file__), 'profiles')
PROFILE_FILES = [
    'traditional_italian_espresso.json',
    'blooming_espresso.json',
    'turbo_shot.json'
]

# Global variables
profiles_sent = {}
profiles_acknowledged = {}

def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    if rc == 0:
        print(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        # Subscribe to acknowledgment topic
        client.subscribe(PROFILE_ACK_TOPIC)
        print(f"📡 Subscribed to {PROFILE_ACK_TOPIC}")
    else:
        print(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    """MQTT message callback"""
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    if topic == PROFILE_ACK_TOPIC:
        try:
            ack = json.loads(payload)
            if ack.get('status') == 'success':
                profile_id = ack.get('profile_id', 'unknown')
                profile_name = ack.get('profile_name', 'unknown')
                phase_count = ack.get('phase_count', 0)
                print(f"✅ Profile '{profile_name}' (ID: {profile_id}) saved successfully with {phase_count} phases")
                profiles_acknowledged[profile_name] = True
            else:
                print(f"⚠️ Profile acknowledgment: {payload}")
        except json.JSONDecodeError:
            print(f"📨 Acknowledgment received: {payload}")

def load_profile(filepath):
    """Load profile from JSON file"""
    try:
        with open(filepath, 'r') as f:
            profile = json.load(f)
        return profile
    except FileNotFoundError:
        print(f"❌ Profile file not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filepath}: {e}")
        return None

def send_profile(client, profile, profile_name):
    """Send a single profile via MQTT"""
    print(f"\n📤 Sending profile: {profile_name}")
    print(f"   Technique: {profile.get('technique', 'unknown')}")
    print(f"   Phases: {len(profile.get('phases', []))}")
    print(f"   Dose: {profile.get('defaultDose', 0)}g")
    print(f"   Yield: {profile.get('defaultYield', 0)}g")
    
    payload = json.dumps(profile)
    result = client.publish(PROFILE_SET_TOPIC, payload, qos=1)
    
    if result.rc == 0:
        print(f"   ✅ Published to {PROFILE_SET_TOPIC}")
        profiles_sent[profile_name] = True
        return True
    else:
        print(f"   ❌ Failed to publish. Return code: {result.rc}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("MaraX Profile Sender")
    print("=" * 60)
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"MQTT User: {MQTT_USER}")
    print(f"Profile Topic: {PROFILE_SET_TOPIC}")
    print(f"Profiles Directory: {PROFILES_DIR}")
    print("=" * 60)
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Set credentials if provided
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    # Connect to broker
    print(f"\n🔌 Connecting to MQTT broker...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)
    
    # Start network loop
    client.loop_start()
    
    # Wait for connection
    time.sleep(2)
    
    # Send all profiles
    success_count = 0
    for profile_file in PROFILE_FILES:
        profile_path = os.path.join(PROFILES_DIR, profile_file)
        
        if not os.path.exists(profile_path):
            print(f"\n⚠️ Profile file not found: {profile_path}")
            continue
        
        profile = load_profile(profile_path)
        if profile is None:
            continue
        
        profile_name = profile.get('profileName', profile_file)
        
        if send_profile(client, profile, profile_name):
            success_count += 1
            # Wait for acknowledgment (with timeout)
            timeout = 5
            start_time = time.time()
            while profile_name not in profiles_acknowledged and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if profile_name not in profiles_acknowledged:
                print(f"   ⚠️ No acknowledgment received for {profile_name} (timeout: {timeout}s)")
            
            # Small delay between profiles
            time.sleep(1)
    
    # Wait a bit more for any remaining acknowledgments
    time.sleep(2)
    
    # Stop network loop
    client.loop_stop()
    client.disconnect()
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Profiles sent: {success_count}/{len(PROFILE_FILES)}")
    print(f"Profiles acknowledged: {len(profiles_acknowledged)}/{success_count}")
    
    if len(profiles_acknowledged) == success_count:
        print("\n✅ All profiles sent and saved successfully!")
    else:
        print("\n⚠️ Some profiles may not have been saved. Check ESP32 logs.")
    
    print("=" * 60)

if __name__ == '__main__':
    main()

