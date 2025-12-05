# How to Update the MaraX Controller Add-on

## Method 1: Update via Home Assistant UI (Recommended)

1. **Go to the Add-on Store**:
   - **Settings** → **Add-ons** → **Add-on Store**
   - Find **MaraX Controller** in your installed add-ons

2. **Check for Updates**:
   - If there's an update available, you'll see an **"Update"** button
   - Click **Update**
   - Wait for the update to complete

3. **If Update Button Doesn't Appear**:
   - Home Assistant might not detect updates automatically
   - Try refreshing the repository (see Method 2)

## Method 2: Refresh Repository

1. **Remove and Re-add Repository**:
   - **Settings** → **Add-ons** → **Add-on Store** → **Repositories**
   - Find `https://github.com/Appphan/marax-homeassistant-addon`
   - Click the three dots (⋮) → **Remove**
   - Click **Add** → Enter: `https://github.com/Appphan/marax-homeassistant-addon`
   - Click **Add**

2. **Check for Updates**:
   - Go back to **Add-on Store**
   - Find **MaraX Controller**
   - If update is available, click **Update**

## Method 3: Force Update via Restart Supervisor

1. **Restart Supervisor** (this refreshes add-on information):
   - **Settings** → **System** → **Hardware**
   - Click the three dots (⋮) → **Restart Supervisor**
   - Wait for restart to complete

2. **Check Add-on Store Again**:
   - Go to **Add-ons** → **Add-on Store**
   - Look for **MaraX Controller**
   - Click **Update** if available

## Method 4: Manual Update (If Auto-Update Doesn't Work)

1. **Stop the Add-on**:
   - **Settings** → **Add-ons** → **MaraX Controller**
   - Click **Stop**

2. **Uninstall the Add-on**:
   - Click **Uninstall**
   - Confirm

3. **Reinstall**:
   - Go to **Add-on Store**
   - Find **MaraX Controller**
   - Click **Install**
   - **Configure** (your settings will be lost, so note them down first!)
   - Click **Start**

## Method 5: Update via SSH/Terminal

If you have SSH access:

```bash
# Connect via SSH
ssh root@homeassistant.local

# Reload supervisor (refreshes add-on info)
ha supervisor reload

# Check add-on info
ha addons info local_marax_controller

# Update if available
ha addons update local_marax_controller
ha addons rebuild local_marax_controller
ha addons restart local_marax_controller
```

## Why Updates Might Not Show

1. **Home Assistant caches add-on information** - Try refreshing the repository
2. **Version number hasn't changed** - The add-on version in `config.json` needs to increment
3. **Repository not refreshed** - Remove and re-add the repository

## Check Current Version

1. **Settings** → **Add-ons** → **MaraX Controller**
2. Look at the version number shown
3. Compare with the latest version in the repository

## After Updating

1. **Restart the add-on**:
   - Click **Restart** (or Stop then Start)

2. **Check logs**:
   - **Settings** → **Add-ons** → **MaraX Controller** → **Logs**
   - Verify it's running correctly

3. **Verify configuration**:
   - Your configuration should be preserved
   - Double-check MQTT settings if needed

## Troubleshooting

### "No update available" but repository has new version

1. Remove and re-add the repository
2. Restart Supervisor
3. Check again

### Update fails

1. Check logs: **Settings** → **Add-ons** → **MaraX Controller** → **Logs**
2. Check disk space: **Settings** → **System** → **Hardware**
3. Try manual uninstall/reinstall

### Configuration lost after update

- Configuration should be preserved, but always note down your settings before updating
- Settings are stored in `/data/options.json` in the add-on

