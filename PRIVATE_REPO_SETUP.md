# Setting Up Home Assistant Add-on with Private Repository

If your GitHub repository is private, you need to use authentication to add it to Home Assistant's add-on store.

## Method 1: Manual Installation (Recommended for Private Repos)

**Note**: Home Assistant's add-on store has issues with token-based HTTPS URLs for private repositories. Use manual installation instead.

### Step 1: Download Add-on Files

1. Clone or download your repository:
   ```bash
   git clone https://github.com/Appphan/maraxcontroller_V2.git
   # Or download as ZIP from GitHub
   ```

2. Copy the add-on directory to Home Assistant:
   ```bash
   # On your Home Assistant machine (via SSH or Samba)
   mkdir -p /config/addons/marax_controller
   cp -r maraxcontroller_V2/home_assistant/addon/* /config/addons/marax_controller/
   ```

### Step 2: Install in Home Assistant

1. Go to **Settings** → **Add-ons** → **Add-on Store**
2. Click the three dots (⋮) → **Repositories**
3. The add-on should appear under **Local add-ons** (if not, restart Home Assistant Supervisor)
4. Find **MaraX Controller** and click **Install**

---

## Method 2: Use SSH URL (Alternative)

If you have SSH keys set up with GitHub:

1. Go to **Settings** → **Add-ons** → **Add-on Store** → **Repositories**
2. Add repository using SSH format:
   ```
   git@github.com:Appphan/maraxcontroller_V2.git
   ```
3. **Note**: This requires SSH keys to be configured on your Home Assistant system

---

## Method 3: Personal Access Token (✅ Works!)

### Step 1: Create GitHub Personal Access Token

1. Go to GitHub → **Settings** → **Developer settings**
2. Click **Personal access tokens** → **Tokens (classic)**
3. Click **Generate new token (classic)**
4. Give it a name: `Home Assistant Add-on`
5. Select scope: **`repo`** (Full control of private repositories)
6. Click **Generate token**
7. **Copy the token immediately** (you won't see it again!)

### Step 2: Add Repository to Home Assistant

1. Go to **Settings** → **Add-ons** → **Add-on Store**
2. Click the three dots (⋮) in the top right
3. Select **Repositories**
4. **Use this format** (includes username before token):
   ```
   https://USERNAME:PERSONALACCESSTOKEN@github.com/USERNAME/REPONAME.git
   ```
   
   **For your repository, it would be:**
   ```
   https://Appphan:YOUR_TOKEN@github.com/Appphan/maraxcontroller_V2.git
   ```
   
   Replace:
   - `Appphan` with your GitHub username
   - `YOUR_TOKEN` with your Personal Access Token
   
5. **Important**: 
   - Include `.git` at the end
   - Format is: `USERNAME:TOKEN@github.com/USERNAME/REPO.git`
   - No spaces before or after the URL
   - Click **Add**

### Step 3: Install Add-on

1. The repository should now appear in the add-on store
2. Find **MaraX Controller** and click **Install**
3. Configure and start as normal

### Step 3: Install Add-on

1. The repository should now appear in the add-on store
2. Find **MaraX Controller** and click **Install**
3. Configure and start as normal

## Method 2: Make Repository Public (Simplest)

If you're okay with making the repository public:

1. Go to your GitHub repository
2. Click **Settings**
3. Scroll down to **Danger Zone**
4. Click **Change visibility**
5. Select **Make public**
6. Confirm
7. Then add the repository normally: `https://github.com/Appphan/maraxcontroller_V2`

## Method 3: Manual Installation (No Repository)

If you prefer not to use a repository:

1. **Copy add-on files to Home Assistant**:
   ```bash
   # On your Home Assistant machine
   mkdir -p /config/addons/marax_controller
   ```
   
2. **Copy files from this repository**:
   - Copy `home_assistant/addon/` directory contents to `/config/addons/marax_controller/`
   
3. **Restart Home Assistant Supervisor**:
   - The add-on should appear in **Settings** → **Add-ons** → **Local add-ons**

4. **Install and configure** as normal

## Troubleshooting

### Error: "protocol ' https' is not supported"

This means there's a space in the URL. Fix:
- Remove any spaces before or after the URL
- Make sure it starts with `https://` (no space before)

### Error: "Repository not found" or "Authentication failed"

- Check your Personal Access Token is correct
- Verify token has `repo` scope
- Make sure the repository URL is correct
- Try regenerating the token

### Add-on doesn't appear after adding repository

1. Refresh the add-on store page
2. Check Home Assistant logs: **Settings** → **System** → **Logs**
3. Verify `repository.json` exists in the repository root
4. Check repository is accessible (try opening the URL in a browser)

### For Private Repos: Token Security

- **Never commit tokens to git**
- Tokens are stored securely in Home Assistant
- You can revoke tokens anytime from GitHub settings
- Consider using a token with minimal permissions

## Alternative: Use Home Assistant Community Add-ons

If you want to share your add-on publicly, consider:
1. Making the repository public
2. Submitting to [Home Assistant Community Add-ons](https://github.com/hassio-addons/repository)
3. Or creating your own public add-on repository

## File Structure Required

For the repository to work as an add-on store, you need:

```
repository/
├── repository.json          # Repository metadata (already created)
└── home_assistant/
    └── addon/
        ├── config.json      # Add-on configuration
        ├── Dockerfile       # Container build file
        ├── app.py          # Application code
        ├── run.sh          # Startup script
        └── README.md       # Add-on documentation
```

The `repository.json` file has been created in the repository root.

