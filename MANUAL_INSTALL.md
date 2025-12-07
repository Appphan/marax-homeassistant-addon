# Manual Installation Guide for Private Repository

Since Home Assistant's add-on store has issues with private repositories using token authentication, here's how to manually install the add-on.

## Quick Installation Steps

### Option A: Using Samba/Network Share (Easiest)

1. **Enable Samba in Home Assistant**:
   - Go to **Settings** → **Add-ons** → **Samba share**
   - Install and start it if not already running
   - Note the network path (usually `\\homeassistant.local\config`)

2. **Copy Files**:
   - Download or clone your repository
   - Navigate to `home_assistant/addon/` folder
   - Copy all files to: `\\homeassistant.local\config\addons\marax_controller\`
   - Or via SSH: `/config/addons/marax_controller/`

3. **Restart Home Assistant Supervisor**:
   - Go to **Settings** → **System** → **Hardware**
   - Click the three dots (⋮) → **Restart Supervisor**

4. **Install Add-on**:
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - The add-on should appear under **Local add-ons**
   - Click **MaraX Controller** → **Install**

### Option B: Using SSH

1. **Enable SSH in Home Assistant**:
   - Go to **Settings** → **Add-ons** → **SSH & Web Terminal**
   - Install and start if not already running

2. **Connect via SSH**:
   ```bash
   ssh root@homeassistant.local
   # Or use your Home Assistant IP
   ```

3. **Create Directory and Copy Files**:
   ```bash
   mkdir -p /config/addons/marax_controller
   cd /config/addons/marax_controller
   ```

4. **Download Files** (choose one method):

   **Method 1: Using wget with token**:
   ```bash
   # Download repository as ZIP
   wget --header="Authorization: token YOUR_TOKEN" \
        https://github.com/Appphan/maraxcontroller_V2/archive/refs/heads/main.zip
   unzip main.zip
   cp -r maraxcontroller_V2-main/home_assistant/addon/* /config/addons/marax_controller/
   rm -rf maraxcontroller_V2-main main.zip
   ```

   **Method 2: Using git with token**:
   ```bash
   git clone https://YOUR_TOKEN@github.com/Appphan/maraxcontroller_V2.git /tmp/marax
   cp -r /tmp/marax/home_assistant/addon/* /config/addons/marax_controller/
   rm -rf /tmp/marax
   ```

   **Method 3: Manual file creation**:
   ```bash
   # Create files manually or copy from your local machine
   # Use SCP to copy files:
   scp -r /path/to/maraxcontroller_V2/home_assistant/addon/* root@homeassistant.local:/config/addons/marax_controller/
   ```

5. **Set Permissions**:
   ```bash
   chmod +x /config/addons/marax_controller/run.sh
   ```

6. **Restart Supervisor**:
   ```bash
   # Via SSH
   ha supervisor reload
   # Or via Home Assistant UI: Settings → System → Hardware → Restart Supervisor
   ```

7. **Install Add-on**:
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Find **MaraX Controller** under **Local add-ons**
   - Click **Install**

### Option C: Using Home Assistant File Editor

1. **Install File Editor Add-on** (if not installed):
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Search for "File editor" and install

2. **Create Directory Structure**:
   - Open File Editor
   - Navigate to `/config/addons/`
   - Create folder `marax_controller`

3. **Create Files**:
   - Copy files from `home_assistant/addon/` to `/config/addons/marax_controller/`
   - Required files:
     - `config.json`
     - `Dockerfile`
     - `app.py`
     - `run.sh`
     - `README.md`

4. **Set Permissions**:
   - Make sure `run.sh` is executable (chmod +x)

5. **Restart Supervisor** and install as above

## File Structure

After copying, your `/config/addons/marax_controller/` should contain:

```
marax_controller/
├── config.json
├── Dockerfile
├── app.py
├── run.sh
├── README.md
├── templates/          (if you have HTML templates)
│   └── index.html
└── static/             (if you have static files)
    ├── css/
    └── js/
```

## Verification

1. Check files exist:
   ```bash
   ls -la /config/addons/marax_controller/
   ```

2. Check config.json is valid:
   ```bash
   cat /config/addons/marax_controller/config.json | python3 -m json.tool
   ```

3. Restart Supervisor and check logs:
   - **Settings** → **Add-ons** → **MaraX Controller** → **Logs**

## Troubleshooting

### Add-on doesn't appear

1. Check file permissions:
   ```bash
   chmod +x /config/addons/marax_controller/run.sh
   chmod 644 /config/addons/marax_controller/*.json
   ```

2. Verify config.json syntax:
   ```bash
   python3 -m json.tool /config/addons/marax_controller/config.json
   ```

3. Check Supervisor logs:
   - **Settings** → **System** → **Logs**
   - Look for errors related to add-ons

4. Restart Supervisor:
   - **Settings** → **System** → **Hardware** → **Restart Supervisor**

### Installation fails

1. Check Docker is running:
   ```bash
   ha docker ps
   ```

2. Check disk space:
   ```bash
   df -h
   ```

3. Check add-on logs:
   - **Settings** → **Add-ons** → **MaraX Controller** → **Logs**

### Can't access web interface

1. Check add-on is running:
   - **Settings** → **Add-ons** → **MaraX Controller** → Status should be "Running"

2. Check ingress is enabled in config.json

3. Try accessing directly:
   - `http://homeassistant.local:8080` (if port is exposed)

## Next Steps

After successful installation:

1. **Configure the add-on**:
   - Go to **Settings** → **Add-ons** → **MaraX Controller** → **Configuration**
   - Set MQTT broker settings
   - Click **Save**

2. **Start the add-on**:
   - Click **Start**
   - Wait for it to start

3. **Access the interface**:
   - Click **Open Web UI**
   - Or go to the add-on page and click the web interface link

## Updating the Add-on

To update manually:

1. Download latest files from repository
2. Copy to `/config/addons/marax_controller/` (overwrite existing)
3. Restart the add-on:
   - **Settings** → **Add-ons** → **MaraX Controller** → **Restart**

