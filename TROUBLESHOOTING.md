# Troubleshooting Home Assistant Add-on

## Restart Supervisor on Raspberry Pi

### Method 1: Via Home Assistant UI

1. Go to **Settings** → **System**
2. Look for **Hardware** or **Supervisor** section
3. Click the three dots (⋮) menu
4. Select **Restart Supervisor** or **Reload Supervisor**

**Alternative paths:**
- **Settings** → **Add-ons** → **Supervisor** → **System** → **Restart**
- **Developer Tools** → **YAML** → Check for supervisor commands

### Method 2: Via SSH/Terminal

If you have SSH access to your Home Assistant:

```bash
# Connect via SSH
ssh root@homeassistant.local
# Or use your Home Assistant IP address

# Restart supervisor
ha supervisor reload

# Or restart the entire system
ha core restart
```

### Method 3: Via Home Assistant Terminal Add-on

1. Install **SSH & Web Terminal** add-on if not already installed
2. Open the terminal
3. Run:
   ```bash
   ha supervisor reload
   ```

## Architecture-Specific Issues (Raspberry Pi 4 - aarch64)

### Check Your Architecture

```bash
# Via SSH or Terminal add-on
uname -m
# Should show: aarch64
```

### Verify Add-on Compatibility

The add-on supports these architectures:
- ✅ aarch64 (Raspberry Pi 4 - 64-bit)
- ✅ amd64
- ✅ armhf
- ✅ armv7
- ✅ i386

Your Raspberry Pi 4 should be compatible.

## Common Installation Issues

### Issue: "Can't install base image" (403 error)

**Solution:**
1. The add-on has been updated to fix this
2. Make sure you have the latest version from the repository
3. Try uninstalling and reinstalling the add-on

### Issue: "Docker image pull failed"

**Possible causes:**
1. Network connectivity issues
2. Docker not running
3. Insufficient disk space

**Check:**
```bash
# Check Docker status
ha docker ps

# Check disk space
df -h

# Check network
ping -c 3 8.8.8.8
```

### Issue: "Add-on won't start"

**Check logs:**
1. Go to **Settings** → **Add-ons** → **MaraX Controller** → **Logs**
2. Look for error messages
3. Common issues:
   - MQTT broker not configured
   - Port conflicts
   - Missing dependencies

### Issue: "Web interface not accessible"

**Check:**
1. Add-on status should be "Running"
2. Check ingress is enabled in config.json
3. Try accessing via: `http://homeassistant.local:8080`
4. Check firewall settings

## Getting System Information

To help diagnose issues, provide:

1. **Home Assistant Version:**
   - Go to **Settings** → **System** → **About**
   - Note the version number

2. **Supervisor Version:**
   - Go to **Settings** → **System** → **About**
   - Look for "Supervisor" version

3. **Architecture:**
   ```bash
   uname -m
   ```

4. **Add-on Logs:**
   - **Settings** → **Add-ons** → **MaraX Controller** → **Logs**
   - Copy the last 50-100 lines

5. **System Logs:**
   - **Settings** → **System** → **Logs**
   - Filter for "supervisor" or "marax"

## Quick Diagnostic Commands

Run these via SSH or Terminal add-on:

```bash
# Check supervisor status
ha supervisor info

# Check add-on status
ha addons info local_marax_controller

# Check Docker
ha docker ps

# Check disk space
df -h

# Check network
ha network info
```

## Still Having Issues?

1. **Check the logs** (most important):
   - Add-on logs
   - Supervisor logs
   - System logs

2. **Verify repository is up to date:**
   - Remove and re-add the repository
   - Make sure you're using: `https://github.com/Appphan/marax-homeassistant-addon`

3. **Try manual installation:**
   - See [MANUAL_INSTALL.md](MANUAL_INSTALL.md)

4. **Check Home Assistant version:**
   - Minimum required: 2023.1.0
   - Update if needed

