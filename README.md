# MaraX Controller Home Assistant Add-on Repository

This repository contains the Home Assistant add-on for the MaraX ESP32 Controller.

## Installation

### Add Repository to Home Assistant

1. Go to **Settings** → **Add-ons** → **Add-on Store**
2. Click the three dots (⋮) in the top right
3. Select **Repositories**
4. Add this URL:
   ```
   https://github.com/Appphan/marax-homeassistant-addon
   ```
5. Click **Add**

### Install the Add-on

1. Find **MaraX Controller** in the add-on store
2. Click **Install**
3. Configure the add-on (see below)
4. Start the add-on

## Configuration

After installation, configure the add-on:

1. Go to **Settings** → **Add-ons** → **MaraX Controller** → **Configuration**
2. Set your MQTT broker settings:
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
3. Click **Save**
4. Click **Start**

## Features

- 🎨 Beautiful web interface
- 📊 Real-time monitoring (pressure, flow, weight, temperature)
- ☕ Profile management with visual editor
- 📈 Shot analytics and history
- 🎛️ Brew control (start/stop, adjust targets)
- 📱 Mobile-friendly design
- 🔄 Auto-discovery via MQTT

## Requirements

- Home Assistant with Supervisor
- MQTT broker (Home Assistant's built-in Mosquitto works)
- MaraX ESP32 Controller connected to the same MQTT broker

## Usage

1. **Access the Web Interface**:
   - Click **Open Web UI** in the add-on page
   - Or access via: `http://homeassistant.local:8080`

2. **Monitor Your Machine**:
   - View real-time metrics on the dashboard
   - Check machine status and temperatures
   - Monitor current brew progress

3. **Manage Profiles**:
   - Create custom brewing profiles
   - Edit existing profiles
   - Send profiles to your MaraX device

4. **Control Brewing**:
   - Start/stop brewing remotely
   - Set target weight
   - Monitor shot progress

## Documentation

For detailed documentation, see:
- [Home Assistant Integration Guide](https://github.com/Appphan/maraxcontroller_V2/blob/main/HOME_ASSISTANT.md)
- [MQTT API Documentation](https://github.com/Appphan/maraxcontroller_V2/blob/main/MQTT_API.md)

## Support

- **Issues**: Open an issue on the [main repository](https://github.com/Appphan/maraxcontroller_V2)
- **Questions**: Check the documentation or open a discussion

## License

Same as the main project - see [LICENSE](https://github.com/Appphan/maraxcontroller_V2/blob/main/LICENSE)

## Repository Structure

```
.
├── repository.json          # Repository metadata
├── README.md               # This file
└── marax_controller/       # Add-on directory
    ├── config.json         # Add-on configuration
    ├── Dockerfile          # Container build file
    ├── app.py             # Application code
    ├── run.sh             # Startup script
    └── README.md          # Add-on documentation
```

## Changelog

See the [main repository's CHANGELOG](https://github.com/Appphan/maraxcontroller_V2/blob/main/CHANGELOG.md) for version history.

