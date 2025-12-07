# How to Use the Diagnostic System

## Quick Start Guide

### 1. Install the Home Assistant Add-on

1. **Add the Repository**:
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Click the three dots (⋮) in the top right
   - Select **Repositories**
   - Add: `https://github.com/Appphan/marax-homeassistant-addon`
   - Click **Add**

2. **Install the Add-on**:
   - Find **MaraX Controller** in the add-on store
   - Click **Install**
   - Wait for installation to complete

3. **Configure MQTT**:
   - Click **Configuration**
   - Set your MQTT settings:
     ```json
     {
       "mqtt_broker": "core-mosquitto",
       "mqtt_port": 1883,
       "mqtt_user": "",
       "mqtt_password": "",
       "mqtt_base_topic": "marax",
       "update_interval": 1,
       "log_level": "info"
     }
     ```
   - Click **Save**

4. **Start the Add-on**:
   - Click **Start**
   - Wait for it to start (check logs if needed)

### 2. Access the Diagnostic Dashboard

**Option A: Via Home Assistant Ingress (Recommended)**
- Click **Open Web UI** in the add-on page
- Navigate to: `http://your-home-assistant:port/diagnostic`

**Option B: Direct URL**
- Access: `http://YOUR_HA_IP:8080/diagnostic`
- Replace `YOUR_HA_IP` with your Home Assistant IP address

**Option C: Via Main Dashboard**
- Open the main dashboard: `http://YOUR_HA_IP:8080/`
- Add a link to `/diagnostic` in your navigation

### 3. Understanding the Diagnostic Dashboard

The diagnostic dashboard shows comprehensive system information:

#### 📊 Overall Health Score
- **90-100 (Green)**: Excellent - All systems operational
- **70-89 (Blue)**: Good - Minor issues, system functional
- **50-69 (Orange)**: Warning - Some systems degraded
- **0-49 (Red)**: Error - Critical issues detected

#### 💻 System Information
- **Uptime**: How long the ESP32 has been running
- **Firmware Version**: Current firmware version
- **Chip Model**: ESP32 model information
- **CPU Frequency**: Processor speed
- **Free Heap**: Available memory
- **Heap Fragmentation**: Memory fragmentation percentage

#### 🌐 Network Status
- **WiFi Status**: Connected/Disconnected
- **SSID**: WiFi network name
- **RSSI**: Signal strength (dBm)
- **IP Address**: Device IP address
- **MQTT Status**: Connected/Disconnected
- **MQTT Broker**: Broker address

#### 📡 Sensor Status

**Pressure Sensor:**
- Current pressure (bar)
- Target pressure (bar)
- Pressure error (difference)
- Status (ok/error)

**Temperature Sensors:**
- Coffee temperature (°C)
- Steam temperature (°C)
- Target temperature (°C)
- Status (ok/invalid)

**Scale (BLE):**
- Connection status
- Current weight (g)
- Battery level (%)
- Status (ok/timeout/disconnected)

#### ☕ Brew System
- **Brew Active**: Whether brewing is currently active
- **Pressure**: Current brew pressure
- **Flow Rate**: Current flow rate (ml/s)
- **Weight**: Current weight (g)
- **Pump Power**: Pump power percentage
- **Control System**: PID/Fuzzy/Adaptive

#### 🧠 Learning System
- **Enabled**: Whether learning is active
- **Shot Count**: Number of shots used for learning
- **Kp, Ki, Kd**: Current PID parameters
- **Avg Overshoot**: Average pressure overshoot
- **Avg Settling Time**: Average time to reach target

#### ⚠️ Error History
- Last 5 errors with:
  - Error code
  - Severity (Info/Warning/Critical/Fatal)
  - Error message
  - Timestamp

### 4. Using Diagnostic Features

#### Auto-Refresh
- Dashboard automatically refreshes every 30 seconds
- Shows "Last updated" timestamp at the bottom

#### Manual Refresh
- Click the **🔄 Refresh** button to request fresh data
- This sends a request to the ESP32 to publish diagnostic data immediately

#### Collapsible Sections
- Click on any section header to collapse/expand it
- Useful for focusing on specific areas

#### Raw JSON View
- Click "📄 Raw Diagnostic Data (JSON)" to see the complete JSON
- Useful for debugging or integration with other tools

### 5. Requesting Diagnostic Data via MQTT

You can also request diagnostic data directly via MQTT:

```bash
# Request diagnostic data
mosquitto_pub -h YOUR_MQTT_BROKER -t "marax/diagnostic/request" -m "get"

# Subscribe to diagnostic data
mosquitto_sub -h YOUR_MQTT_BROKER -t "marax/diagnostic"
```

### 6. Using the REST API

The add-on also provides a REST API endpoint:

```bash
# Get diagnostic data
curl http://YOUR_HA_IP:8080/api/diagnostic

# Request fresh data
curl http://YOUR_HA_IP:8080/api/diagnostic?refresh=true
```

### 7. Integration with Home Assistant

You can create sensors in Home Assistant to monitor diagnostic data:

```yaml
# configuration.yaml
mqtt:
  sensor:
    - name: "MaraX Health Score"
      state_topic: "marax/diagnostic"
      value_template: "{{ value_json.health.overall_score }}"
      unit_of_measurement: "%"
      
    - name: "MaraX Free Heap"
      state_topic: "marax/diagnostic"
      value_template: "{{ value_json.system.free_heap }}"
      unit_of_measurement: "bytes"
      
    - name: "MaraX WiFi RSSI"
      state_topic: "marax/diagnostic"
      value_template: "{{ value_json.network.wifi_rssi }}"
      unit_of_measurement: "dBm"
      
    - name: "MaraX Health Status"
      state_topic: "marax/diagnostic"
      value_template: "{{ value_json.health.status }}"
```

### 8. Troubleshooting

#### No Diagnostic Data Available
- **Check ESP32 is connected**: Ensure your ESP32 is powered and connected to WiFi
- **Check MQTT connection**: Verify ESP32 is connected to the same MQTT broker
- **Check topic**: Ensure MQTT base topic matches (default: `marax`)
- **Wait for auto-publish**: ESP32 publishes diagnostic data every 30 seconds

#### Dashboard Shows "Loading..."
- **Check add-on is running**: Go to Settings → Add-ons → MaraX Controller
- **Check logs**: Look for errors in the add-on logs
- **Check MQTT connection**: Verify add-on can connect to MQTT broker

#### Health Score is Low
- **Check error history**: Look at the Error History section
- **Check network status**: Verify WiFi and MQTT connections
- **Check memory**: Low free heap can indicate issues
- **Check sensors**: Verify all sensors are reporting correctly

### 9. Best Practices

1. **Regular Monitoring**: Check the diagnostic dashboard periodically to catch issues early
2. **Watch Health Score**: A declining health score indicates potential problems
3. **Monitor Memory**: Heap fragmentation > 30% may indicate memory leaks
4. **Check Error History**: Review errors regularly to identify patterns
5. **Network Monitoring**: Poor WiFi signal (RSSI < -70 dBm) can cause issues

### 10. Advanced Usage

#### Custom Alerts
Create Home Assistant automations based on diagnostic data:

```yaml
automation:
  - alias: "MaraX Low Memory Alert"
    trigger:
      - platform: mqtt
        topic: "marax/diagnostic"
    condition:
      condition: template
      value_template: "{{ trigger.payload_json.system.free_heap < 50000 }}"
    action:
      - service: notify.mobile_app
        data:
          message: "MaraX low memory: {{ trigger.payload_json.system.free_heap }} bytes"
          
  - alias: "MaraX Health Degraded"
    trigger:
      - platform: mqtt
        topic: "marax/diagnostic"
    condition:
      condition: template
      value_template: "{{ trigger.payload_json.health.overall_score < 70 }}"
    action:
      - service: notify.mobile_app
        data:
          message: "MaraX health degraded: {{ trigger.payload_json.health.message }}"
```

#### Historical Tracking
Store diagnostic data for historical analysis:

```yaml
recorder:
  include:
    entities:
      - sensor.marax_health_score
      - sensor.marax_free_heap
      - sensor.marax_wifi_rssi
```

## Summary

The diagnostic system provides comprehensive monitoring of your MaraX ESP32 controller:

✅ **System Health**: Monitor uptime, memory, CPU  
✅ **Network Status**: Track WiFi and MQTT connections  
✅ **Sensor Status**: Verify all sensors are working  
✅ **Brew System**: Monitor active brews and control system  
✅ **Learning System**: Track PID tuning progress  
✅ **Error Tracking**: View error history and severity  
✅ **Real-time Updates**: Auto-refresh every 30 seconds  

Access it at: `http://YOUR_HA_IP:8080/diagnostic`

