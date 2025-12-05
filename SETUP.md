# Setting Up the Public Home Assistant Add-on Repository

This guide explains how to create and publish the public Home Assistant add-on repository.

## Step 1: Create New GitHub Repository

1. Go to GitHub and create a new repository:
   - Name: `marax-homeassistant-addon`
   - Description: "Home Assistant add-on for MaraX ESP32 Controller"
   - **Make it Public** ✅
   - **Do NOT** initialize with README, .gitignore, or license (we already have these)

2. Copy the repository URL (you'll need it for the next steps)

## Step 2: Initialize Git Repository

```bash
cd home_assistant_repo
git init
git add .
git commit -m "Initial commit: MaraX Controller Home Assistant add-on"
```

## Step 3: Connect to GitHub

```bash
# Add remote (replace with your actual repository URL)
git remote add origin https://github.com/Appphan/marax-homeassistant-addon.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 4: Verify Repository Structure

Your repository should have this structure:

```
marax-homeassistant-addon/
├── repository.json
├── README.md
├── .gitignore
├── SETUP.md
└── marax_controller/
    ├── config.json
    ├── Dockerfile
    ├── app.py
    ├── run.sh
    └── README.md
```

## Step 5: Test in Home Assistant

1. Add the repository to Home Assistant:
   ```
   https://github.com/Appphan/marax-homeassistant-addon
   ```

2. Verify the add-on appears in the store

3. Install and test

## Updating the Add-on

When you make changes to the add-on:

1. Update files in `home_assistant_repo/marax_controller/`
2. Commit changes:
   ```bash
   cd home_assistant_repo
   git add .
   git commit -m "Update: description of changes"
   git push origin main
   ```
3. Home Assistant will automatically detect updates

## Keeping in Sync with Main Repository

To keep the add-on updated with changes from the main repository:

```bash
# From the main repository directory
cd /path/to/maraxcontroller_V2

# Copy updated add-on files
cp -r home_assistant/addon/* home_assistant_repo/marax_controller/

# Commit and push to public repo
cd home_assistant_repo
git add .
git commit -m "Sync with main repository"
git push origin main
```

## Automation Script

You can create a script to automate syncing:

```bash
#!/bin/bash
# sync_addon.sh

MAIN_REPO="/path/to/maraxcontroller_V2"
PUBLIC_REPO="/path/to/home_assistant_repo"

# Copy files
cp -r "$MAIN_REPO/home_assistant/addon/"* "$PUBLIC_REPO/marax_controller/"

# Commit and push
cd "$PUBLIC_REPO"
git add .
git commit -m "Sync with main repository - $(date +%Y-%m-%d)"
git push origin main

echo "Add-on synced successfully!"
```

## Notes

- The public repository only contains Home Assistant-specific files
- No sensitive information (tokens, credentials) should be in the public repo
- The main repository can remain private
- Users can install directly from the public repository URL

