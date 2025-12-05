# MaraX Controller Home Assistant Add-on

A beautiful web-based interface for managing your MaraX ESP32 Controller, including profile management, real-time monitoring, and brew control.

## Features

- 🎨 **Beautiful Web Interface**: Modern, responsive design
- 📊 **Real-time Monitoring**: Live pressure, flow, weight, and temperature graphs
- ☕ **Profile Management**: Visual profile editor with drag-and-drop interface
- 📈 **Shot Analytics**: Historical shot data and statistics
- 🎛️ **Brew Control**: Start/stop brewing, adjust targets
- 📱 **Mobile Friendly**: Works on all devices
- 🔄 **Auto-discovery**: Automatically connects to your MaraX device via MQTT

## Installation

### Option 1: Install from Repository (Recommended)

**Important**: For private repositories, you have two options:

#### Option A: Make Repository Public (Easiest)
1. Go to your GitHub repository settings
2. Scroll down to "Danger Zone"
3. Click "Change visibility" → "Make public"
4. Then follow the steps below

#### Option B: Use Personal Access Token (For Private Repos)
1. Create a GitHub Personal Access Token:
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` scope
   - Copy the token
2. Use this URL format in Home Assistant:
   ```
   https://YOUR_TOKEN@github.com/Appphan/maraxcontroller_V2
   ```
   Replace `YOUR_TOKEN` with your actual token

#### Installation Steps:

1. **Add Repository**:
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Click the three dots (⋮) in the top right
   - Select **Repositories**
   - Add: `https://github.com/Appphan/maraxcontroller_V2` (or with token for private)
   - **Important**: Make sure there are no spaces before or after the URL
   - Click **Add**

2. **Install the add-on**:
   - Find **MaraX Controller** in the add-on store
   - Click **Install**
   - Wait for installation to complete

3. Configure the add-on:
   - Click **Configuration**
   - Set your MQTT broker settings:
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

4. Start the add-on:
   - Click **Start**
   - Wait for it to start (check logs if needed)

5. Access the interface:
   - Click **Open Web UI** or go to **http://homeassistant.local:8080**
   - The interface will automatically connect to your MaraX device

### Option 2: Manual Installation

1. Copy the `addon` directory to your Home Assistant:
   ```bash
   cp -r home_assistant/addon /config/addons/marax_controller
   ```

2. Restart Home Assistant Supervisor

3. The add-on should appear in **Settings** → **Add-ons** → **Local add-ons**

## Configuration

### MQTT Settings

- **mqtt_broker**: MQTT broker address (use `core-mosquitto` for Home Assistant's built-in broker)
- **mqtt_port**: MQTT broker port (usually 1883)
- **mqtt_user**: MQTT username (leave empty if not required)
- **mqtt_password**: MQTT password (leave empty if not required)
- **mqtt_base_topic**: Base MQTT topic (default: `marax`)
- **update_interval**: Update interval in seconds (default: 1)
- **log_level**: Logging level (`debug`, `info`, `warning`, `error`)

### Using Home Assistant's Built-in MQTT Broker

If you're using Home Assistant's built-in Mosquitto broker:

1. Install the **Mosquitto broker** add-on if not already installed
2. Set `mqtt_broker` to `core-mosquitto`
3. Leave `mqtt_user` and `mqtt_password` empty (or use your MQTT credentials)

## Usage

### Web Interface

1. Open the web interface by clicking **Open Web UI** in the add-on page
2. The interface will automatically connect to your MaraX device
3. You'll see:
   - **Dashboard**: Real-time metrics and controls
   - **Profiles**: Manage and edit brewing profiles
   - **History**: View shot history and analytics
   - **Settings**: Configure device settings

### Profile Management

1. Go to the **Profiles** section
2. Click **New Profile** to create a custom profile
3. Configure phases:
   - Add phases (preinfusion, extraction, etc.)
   - Set target pressure/flow for each phase
   - Configure breakout criteria
4. Click **Save** to save the profile
5. Click **Send to Device** to upload to your MaraX

### Brew Control

1. Select a profile from the dropdown
2. Set target weight (if using weight-based stopping)
3. Click **Start Brew** to begin
4. Monitor real-time metrics on the dashboard
5. Click **Stop Brew** to stop manually

## Integration with Home Assistant

The add-on provides a web interface, but you can also integrate it with Home Assistant:

### Using the REST API

The add-on exposes a REST API that Home Assistant can use:

```yaml
# Example: Get device status
rest:
  - resource: http://localhost:8080/api/status
    scan_interval: 5
    sensor:
      - name: "MaraX Status"
        value_template: "{{ value_json.status }}"
```

### Using MQTT Directly

The add-on subscribes to MQTT topics, so you can still use MQTT sensors in Home Assistant as described in `HOME_ASSISTANT.md`.

## Troubleshooting

### Add-on Won't Start

1. Check the logs: **Settings** → **Add-ons** → **MaraX Controller** → **Logs**
2. Verify MQTT broker is running
3. Check MQTT credentials are correct
4. Ensure port 8080 is not in use

### Can't Connect to Device

1. Verify your MaraX ESP32 is connected to the same MQTT broker
2. Check MQTT base topic matches (default: `marax`)
3. Test MQTT connection using `mosquitto_pub`/`mosquitto_sub`
4. Check device logs for MQTT connection status

### Web Interface Not Loading

1. Check add-on is running
2. Try accessing via IP: `http://YOUR_HA_IP:8080`
3. Check browser console for errors
4. Verify ingress is enabled (should be automatic)

## Development

### Building the Add-on

```bash
cd home_assistant/addon
docker build -t marax-controller-addon .
```

### Running Locally

```bash
python3 app.py
```

### File Structure

```
addon/
├── config.json          # Add-on configuration
├── Dockerfile           # Docker build file
├── app.py              # Main application
├── README.md           # This file
├── templates/          # HTML templates
│   └── index.html
└── static/             # Static files (CSS, JS)
    ├── css/
    └── js/
```

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the main [README.md](../../README.md)
- Review [MQTT_API.md](../../MQTT_API.md) for API details
- See [HOME_ASSISTANT.md](../../HOME_ASSISTANT.md) for integration options

## License

Same as the main project - see [LICENSE](../../LICENSE)

