# Popular Coffee Brewing Profiles

This directory contains sample brewing profiles for popular coffee styles. These profiles can be imported into the MaraX Controller via the Home Assistant add-on or sent directly via MQTT.

## Available Profiles

### 1. Traditional Italian Espresso
**File:** `traditional_italian_espresso.json`

Classic Italian-style espresso shot:
- **Pre-Infusion:** 2 bar for up to 5 seconds or until 2g weight
- **Extraction:** 9 bar constant pressure until 36g yield or 30 seconds
- **Best for:** Dark roasts, traditional espresso blends
- **Dose:** 18g
- **Yield:** 36g (1:2 ratio)

### 2. Blooming Espresso
**File:** `blooming_espresso.json`

Modern blooming technique for light roasts:
- **Pre-Infusion:** 2 bar until 3g weight or 8 seconds
- **Bloom:** Pump off for 25 seconds (allows coffee to bloom)
- **Ramp Up:** Gradual pressure increase from 2 to 9 bar over 4 seconds
- **Extraction:** 9 bar until 40g yield or 35 seconds
- **Best for:** Light roasts, single origins, fruity coffees
- **Dose:** 18g
- **Yield:** 40g (1:2.2 ratio)

### 3. Turbo Shot
**File:** `turbo_shot.json`

High-flow, lower-pressure modern technique:
- **Quick Pre-Infusion:** 1.5 bar for up to 3 seconds or until 1.5g weight
- **High Flow Extraction:** 6 bar constant pressure until 60g yield or 20 seconds
- **Best for:** Light roasts, high-extraction shots, modern espresso
- **Dose:** 20g
- **Yield:** 60g (1:3 ratio)

## How to Use

### Via Home Assistant Add-on:
1. Open the MaraX Controller add-on
2. Go to the "Profiles" tab
3. Click "Add New Profile"
4. Copy the JSON content from one of the profile files
5. Paste it into the profile editor (or use the UI to configure)
6. Click "Save Profile"

### Via MQTT:
Use the `send_profile.py` script:
```bash
python3 send_profile.py traditional_italian_espresso.json
```

### Via Python Script:
```python
import json
import paho.mqtt.client as mqtt

# Load profile
with open('traditional_italian_espresso.json', 'r') as f:
    profile = json.load(f)

# Send via MQTT
client = mqtt.Client()
client.connect("your_mqtt_broker", 1883)
client.publish("marax/brew/profile/set", json.dumps(profile))
```

## Profile Structure

Each profile contains:
- **profileName:** Display name
- **technique:** Technique type (traditional, blooming, turbo, etc.)
- **defaultDose:** Default coffee dose in grams
- **defaultYield:** Default yield in grams
- **defaultRatio:** Default brew ratio
- **phases:** Array of brewing phases with:
  - Control mode (pressure, flow, ramp, etc.)
  - Target values (pressure, flow)
  - Breakout criteria (time, weight, flow, pressure)
  - Duration limits

## Customization

Feel free to modify these profiles to suit your taste:
- Adjust pressure values for different extraction characteristics
- Change yield targets for different ratios
- Modify breakout criteria thresholds
- Add or remove phases for more complex profiles

## Notes

- All profiles use weight-based breakout criteria as primary, with time as fallback
- Pressure values are in bar
- Weight values are in grams
- Time values are in seconds
- Control mode 0 = Pressure control
- Control mode 3 = Pause (pump off)
- Control mode 4 = Ramp pressure
- Breakout type 1 = Time
- Breakout type 2 = Weight
- Breakout type 4 = Pressure (as percentage)

