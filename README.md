# OBS Auto Recording & Google Drive Upload

This Python script automates OBS Studio recording and uploads the recorded videos to Google Drive.

## Prerequisites

1. **OBS Studio** installed with WebSocket plugin enabled
2. **Python 3.7+** installed
3. **Google Cloud Console** project with Drive API enabled

## Installation

### 1. Install Required Python Packages

Navigate to this directory in terminal/command prompt:
```bash
cd "C:\Users\001\Desktop\All Projects\ah\obs-script"
```

Install the required packages:
```bash
pip install -r requirements.txt
```

### 2. Configure OBS Studio

1. **Enable WebSocket Server:**
   - Open OBS Studio
   - Go to `Tools` > `WebSocket Server Settings`
   - Check "Enable WebSocket server"
   - Set port to `4455` (or note your custom port)
   - Set a password if desired (recommended)

2. **Create/Note Your Scene:**
   - Create or identify the scene you want to use for recording
   - Note the exact scene name

3. **Check Recording Settings:**
   - Go to `Settings` > `Output` > `Recording`
   - Note the recording path
   - Ensure format is MP4, MKV, or FLV

### 3. Setup Google Drive API

1. **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Drive API:**
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file
   - Rename it to `credentials.json`
   - Place it in this directory (`C:\Users\001\Desktop\All Projects\ah\obs-script\`)

4. **Get Folder ID (Optional):**
   - If you want to upload to a specific folder, get its ID from the URL
   - Example: `https://drive.google.com/drive/folders/1ABC123DEF456` → ID is `1ABC123DEF456`

## Configuration

The script will create a `config.json` file on first run. Edit it with your settings:

```json
{
    "obs": {
        "host": "localhost",
        "port": 4455,
        "password": "your_obs_websocket_password",
        "scene_name": "Your Scene Name",
        "recording_path": "",
        "obs_executable": "obs64.exe"
    },
    "google_drive": {
        "credentials_file": "credentials.json",
        "token_file": "token.json",
        "upload_folder_id": "root",
        "scopes": ["https://www.googleapis.com/auth/drive.file"]
    }
}
```

### Configuration Options:

- **obs.host**: OBS WebSocket host (usually "localhost")
- **obs.port**: OBS WebSocket port (usually 4455)
- **obs.password**: WebSocket password (if set in OBS)
- **obs.scene_name**: Name of the scene to activate
- **obs.obs_executable**: Path to OBS executable (auto-detected if not specified)
- **google_drive.upload_folder_id**: Google Drive folder ID ("root" for root folder)

## Usage

1. **Navigate to the project directory:**
   ```bash
   cd "C:\Users\001\Desktop\All Projects\ah\obs-script"
   ```

2. **Run the script:**
   ```bash
   python obs_auto_recorder.py
   ```

3. **First run:**
   - Script will open browser for Google Drive authentication
   - Grant necessary permissions
   - Authentication token will be saved for future use

4. **Script will:**
   - Launch OBS Studio
   - Connect to WebSocket
   - Set the specified scene
   - Start recording automatically
   - Monitor recording status
   - Upload video to Google Drive when recording stops

5. **To stop recording:**
   - Use OBS interface (Stop Recording button)
   - Or use OBS hotkey for stop recording
   - **Note:** Pause recording won't trigger upload - must fully stop

6. **To exit script:**
   - Press `Ctrl+C` in terminal

## Troubleshooting

### Common Issues:

1. **OBS WebSocket connection failed:**
   - Ensure OBS is running
   - Check WebSocket is enabled in OBS
   - Verify host, port, and password in config

2. **Google Drive authentication failed:**
   - Check `credentials.json` file exists and is valid
   - Delete `token.json` to re-authenticate
   - Ensure Drive API is enabled in Google Cloud Console

3. **Recording file not found:**
   - Check OBS recording path is accessible
   - Ensure recording format is MP4, MKV, or FLV
   - Verify file system permissions

4. **Upload fails:**
   - Check internet connection
   - Verify Google Drive folder ID
   - Ensure sufficient Google Drive storage space

### File Structure:
```
C:\Users\001\Desktop\All Projects\ah\obs-script\
├── obs_auto_recorder.py
├── config.json (created on first run)
├── credentials.json (you need to add this)
├── token.json (created after first auth)
├── requirements.txt
└── README.md
```

## Features

- ✅ Auto-launch OBS Studio
- ✅ Set specific scene
- ✅ Start recording automatically
- ✅ Monitor recording status
- ✅ Auto-upload to Google Drive when recording stops
- ✅ Progress indication during upload
- ✅ Configurable settings
- ✅ Error handling and logging

## Notes

- The script monitors file system changes to detect new recordings
- Only supports stop recording (not pause) for upload trigger
- Supports MP4, MKV, and FLV recording formats
- Requires continuous internet connection for Google Drive upload
- OBS must have WebSocket plugin enabled (included in recent versions)

## Quick Start Checklist

- [ ] Install Python packages: `pip install -r requirements.txt`
- [ ] Enable OBS WebSocket in Tools > WebSocket Server Settings
- [ ] Create Google Cloud project and enable Drive API
- [ ] Download OAuth credentials as `credentials.json`
- [ ] Run script: `python obs_auto_recorder.py`
- [ ] Edit `config.json` with your settings
- [ ] Run script again to start automation
