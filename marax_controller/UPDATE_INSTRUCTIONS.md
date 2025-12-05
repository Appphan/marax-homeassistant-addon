# How to See the macOS UI Redesign Update

## Quick Steps

1. **Refresh the Repository** (to detect the new version):
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Click the three dots (⋮) → **Repositories**
   - Find your repository and click **Reload** (or remove and re-add it)

2. **Update the Add-on**:
   - Go to **Settings** → **Add-ons** → **MaraX Controller**
   - If you see an **"Update"** button, click it
   - Wait for the update to complete

3. **Restart the Add-on**:
   - Click **Restart** (or Stop then Start)
   - Wait for it to fully start

4. **Clear Browser Cache** (Important!):
   - **Chrome/Edge**: Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
   - Select "Cached images and files"
   - Click "Clear data"
   - **OR** Hard refresh: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)

5. **Reload the Web Interface**:
   - Close and reopen the web interface
   - Or press `F5` to refresh

## If Update Button Doesn't Appear

### Method 1: Force Repository Refresh
1. **Settings** → **Add-ons** → **Add-on Store** → **Repositories**
2. Remove your repository
3. Re-add it with the same URL
4. Wait a few seconds
5. Check for updates again

### Method 2: Restart Supervisor
1. **Settings** → **System** → **Hardware**
2. Click three dots (⋮) → **Restart Supervisor**
3. Wait for restart
4. Check for updates again

### Method 3: Manual Restart (Quick Fix)
If you just want to see the changes without updating:
1. **Settings** → **Add-ons** → **MaraX Controller**
2. Click **Stop**
3. Wait 5 seconds
4. Click **Start**
5. **Clear browser cache** (very important!)
6. Reload the web interface

## What Changed

The UI has been completely redesigned to follow Apple's Human Interface Guidelines for macOS:

- ✅ macOS system colors (light/dark mode)
- ✅ Proper spacing and typography
- ✅ Modern card designs with shadows
- ✅ macOS-style buttons and forms
- ✅ Smooth animations and transitions
- ✅ Better visual hierarchy

## Troubleshooting

### Still seeing old design?
1. **Clear browser cache** - This is the most common issue!
2. Try **incognito/private mode** to bypass cache
3. Check add-on logs for errors
4. Verify the version shows **2.5.3** in add-on info

### Update fails?
1. Check logs: **Settings** → **Add-ons** → **MaraX Controller** → **Logs**
2. Check disk space
3. Try stopping, then updating, then starting

### Need help?
Check the logs in the add-on page for any error messages.

