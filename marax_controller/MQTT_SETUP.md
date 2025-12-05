# MQTT Configuration Guide

## Error Code 5: Connection Refused - Not Authorized

If you see error code 5, it means the MQTT broker is refusing the connection. This is usually due to:

1. **Authentication required but not provided**
2. **Wrong username/password**
3. **Broker not allowing connections from this network**

## Solution Steps

### Step 1: Check Mosquitto Broker Configuration

1. Go to **Settings** → **Add-ons** → **Mosquitto broker**
2. Check if authentication is enabled:
   - If **"Allow anonymous connections"** is **OFF**, you need credentials
   - If it's **ON**, you can leave username/password empty

### Step 2: Configure Add-on MQTT Settings

1. Go to **Settings** → **Add-ons** → **MaraX Controller** → **Configuration**
2. Set the correct values:

**If Mosquitto has authentication enabled:**
```json
{
  "mqtt_broker": "core-mosquitto",
  "mqtt_port": 1883,
  "mqtt_user": "YOUR_MQTT_USERNAME",
  "mqtt_password": "YOUR_MQTT_PASSWORD",
  "mqtt_base_topic": "marax",
  "update_interval": 1,
  "log_level": "info"
}
```

**If Mosquitto allows anonymous connections:**
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

### Step 3: Alternative Broker Hostnames

If `core-mosquitto` doesn't work, try these in order:

1. `supervisor` - Most reliable in Home Assistant
2. `localhost` - If broker is on same container
3. Your Home Assistant IP address (e.g., `192.168.1.100`)

### Step 4: Verify Mosquitto is Running

1. Go to **Settings** → **Add-ons** → **Mosquitto broker**
2. Ensure it's **Installed** and **Running**
3. Check the logs for any errors

### Step 5: Test MQTT Connection

You can test the connection from Home Assistant:

1. Install **MQTT Explorer** or use **Developer Tools** → **MQTT**
2. Try subscribing to: `marax/#`
3. If you see messages, MQTT is working

## Common Issues

### Issue: "Connection refused - not authorized" (Error 5)

**Causes:**
- Wrong username/password
- Authentication required but not provided
- User doesn't have permission

**Solution:**
1. Check Mosquitto broker settings
2. Verify username/password in add-on configuration
3. Try creating a new MQTT user in Mosquitto

### Issue: "Connection refused - server unavailable" (Error 3)

**Causes:**
- Broker not running
- Wrong hostname/IP
- Network issue

**Solution:**
1. Ensure Mosquitto broker is running
2. Try alternative hostnames (supervisor, localhost)
3. Check network connectivity

### Issue: "Connection refused - bad username or password" (Error 4)

**Causes:**
- Incorrect credentials

**Solution:**
1. Double-check username and password
2. Create new MQTT user in Mosquitto
3. Update add-on configuration

## Getting MQTT Credentials

### If Using Home Assistant's Built-in Mosquitto:

1. Go to **Settings** → **Devices & Services** → **MQTT**
2. If you set up a user, use those credentials
3. If not, you can:
   - Enable "Allow anonymous connections" in Mosquitto settings
   - Or create a new user in Mosquitto configuration

### Creating MQTT User in Mosquitto:

1. Go to **Settings** → **Add-ons** → **Mosquitto broker** → **Configuration**
2. Add user to `logins` section:
   ```yaml
   logins:
     - username: marax_user
       password: your_secure_password
   ```
3. Restart Mosquitto
4. Use these credentials in MaraX Controller add-on

## Testing Connection

After configuring, check the add-on logs:

1. **Settings** → **Add-ons** → **MaraX Controller** → **Logs**
2. Look for: `✅ Connected to MQTT broker successfully`
3. If you see errors, check the error code and refer to solutions above

## Still Not Working?

1. **Check Mosquitto logs**: Settings → Add-ons → Mosquitto broker → Logs
2. **Verify network**: Ensure both add-ons are on the same network
3. **Try IP address**: Use your Home Assistant IP instead of hostname
4. **Check firewall**: Ensure port 1883 is not blocked

