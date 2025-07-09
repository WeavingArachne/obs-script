import os
import sys
import time
import subprocess
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import obswebsocket
from obswebsocket import obsws, requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload


class OBSRecordingAutomator:
    def __init__(self, config_file="config.json"):
        self.config = self.load_config(config_file)
        self.obs_ws = None
        self.observer = None
        self.drive_services = {}
        self.recording_file = None
        self.current_group = None

    def load_config(self, config_file):
        default_config = {
            "obs": {
                "host": "localhost",
                "port": 4455,
                "password": "",
                "obs_executable": "obs64.exe"
            },
            "groups": {
                "Group1": {
                    "scene_name": "Scene 1",
                    "record_folder": "C:/Users/001/Videos/Group1",
                    "google_drive": {
                        "credentials_file": "credentials_group1.json",
                        "token_file": "token_group1.json",
                        "upload_folder_id": "root",
                        "scopes": ["https://www.googleapis.com/auth/drive.file"]
                    }
                },
                "Group2": {
                    "scene_name": "Scene 2",
                    "record_folder": "C:/Users/001/Videos/Group2",
                    "google_drive": {
                        "credentials_file": "credentials_group2.json",
                        "token_file": "token_group2.json",
                        "upload_folder_id": "root",
                        "scopes": ["https://www.googleapis.com/auth/drive.file"]
                    }
                }
            }
        }

        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                if "obs" not in config:
                    config["obs"] = default_config["obs"]
                if "groups" not in config:
                    config["groups"] = default_config["groups"]
        else:
            config = default_config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Created default config file: {config_file}")
            print("Please edit the config file with your groups and settings!")

        return config

    def list_groups(self):
        return list(self.config["groups"].keys())

    def select_group(self):
        groups = self.list_groups()
        print("\n=== Available Groups ===")
        for i, group in enumerate(groups, 1):
            scene = self.config["groups"][group]["scene_name"]
            print(f"{i}. {group} (Scene: {scene})")

        while True:
            try:
                choice = input(f"\nSelect group (1-{len(groups)}): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(groups):
                        self.current_group = groups[idx]
                        print(f"Selected group: {self.current_group}")
                        return True
                    else:
                        print("Invalid selection. Please try again.")
                else:
                    print("Please enter a number.")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return False

    def get_current_group_config(self):
        if not self.current_group:
            return None
        return self.config["groups"][self.current_group]

    def wait_for_obs_to_be_ready(self, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                test_ws = obsws(
                    self.config["obs"]["host"],
                    self.config["obs"]["port"],
                    self.config["obs"]["password"]
                )
                test_ws.connect()
                test_ws.disconnect()
                return True
            except:
                time.sleep(0.5)
        return False

    def launch_obs(self):
        try:
            obs_path = self.config["obs"]["obs_executable"]
            print(f"Launching OBS: {obs_path}")
            if not os.path.exists(obs_path):
                common_paths = [
                    "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
                    "C:\\Program Files (x86)\\obs-studio\\bin\\64bit\\obs64.exe",
                    "/Applications/OBS.app/Contents/MacOS/OBS",
                    "/usr/bin/obs",
                    "/usr/local/bin/obs"
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        obs_path = path
                        break
                else:
                    print("OBS executable not found. Please update the config file.")
                    return False
            working_dir = os.path.dirname(obs_path)
            subprocess.Popen([obs_path], cwd=working_dir)
            time.sleep(3)
            print("OBS launched, waiting for WebSocket to be ready...")
            if not self.wait_for_obs_to_be_ready():
                print("OBS did not become ready in time.")
                return False
            print("OBS launched and ready")
            return True
        except Exception as e:
            print(f"Failed to launch OBS: {e}")
            return False

    def connect_to_obs(self):
        try:
            self.obs_ws = obsws(
                self.config["obs"]["host"],
                self.config["obs"]["port"],
                self.config["obs"]["password"]
            )
            self.obs_ws.connect()
            print("Connected to OBS WebSocket")
            return True
        except Exception as e:
            print(f"Failed to connect to OBS WebSocket: {e}")
            return False

    def set_scene(self, scene_name):
        try:
            self.obs_ws.call(
                requests.SetCurrentProgramScene(sceneName=scene_name))
            print(f"Set scene to: {scene_name}")
            return True
        except Exception as e:
            print(f"Failed to set scene: {e}")
            return False

    def set_recording_folder(self, folder_path):
        try:
            self.obs_ws.call(requests.SetRecordDirectory(
                recordDirectory=folder_path))
            print(f"Set OBS recording directory to: {folder_path}")
            return True
        except Exception as e:
            print(f"Failed to set recording directory: {e}")
            return False

    def start_recording(self):
        try:
            self.obs_ws.call(requests.StartRecord())
            print("Recording started")
            return True
        except Exception as e:
            print(f"Failed to start recording: {e}")
            return False

    def get_recording_status(self):
        try:
            response = self.obs_ws.call(requests.GetRecordStatus())
            return response.datain['outputActive']
        except Exception as e:
            print(f"Failed to get recording status: {e}")
            return False

    def get_recording_path(self):
        group_config = self.get_current_group_config()
        return group_config.get("record_folder")

    def setup_google_drive_auth(self, group_name):
        try:
            group_config = self.config["groups"][group_name]
            drive_config = group_config["google_drive"]
            creds = None
            token_file = drive_config["token_file"]
            credentials_file = drive_config["credentials_file"]
            scopes = drive_config["scopes"]
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(
                    token_file, scopes)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("🔄 Token expired. Attempting to refresh...")
                    creds.refresh(Request())
                    print("✅ Token refreshed.")
                else:
                    print("🔐 No valid token or refresh token. Starting new flow...")
                    if not os.path.exists(credentials_file):
                        print(
                            f"Google Drive credentials file not found: {credentials_file}")
                        return False
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, scopes)
                    creds = flow.run_local_server(port=0)
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            self.drive_services[group_name] = build(
                'drive', 'v3', credentials=creds)
            print(f"Google Drive authentication successful for {group_name}")
            return True
        except Exception as e:
            print(
                f"Failed to setup Google Drive authentication for {group_name}: {e}")
            return False

    def upload_to_drive(self, file_path, group_name, max_retries=10):
        """Upload file to Google Drive for a specific group with true resumable retry logic"""
        wait_time = 8  # seconds between chunk retries

        def print_progress_bar(progress, total, bar_length=40):
            percent = progress / total if total > 0 else 0
            arrow_count = int(round(percent * bar_length))
            arrow = '=' * (arrow_count - 1) + '>' if arrow_count > 0 else ''
            spaces = ' ' * (bar_length - arrow_count)
            sys.stdout.write(
                f"\rUploading: [{arrow + spaces}] {int(percent * 100)}%")
            sys.stdout.flush()

        if group_name not in self.drive_services:
            print(f"No Drive service available for {group_name}")
            return False

        drive_service = self.drive_services[group_name]
        group_config = self.config["groups"][group_name]
        drive_config = group_config["google_drive"]

        file_name = os.path.basename(file_path)
        file_name_with_group = f"[{group_name}] {file_name}"
        file_size = os.path.getsize(file_path)

        file_metadata = {
            'name': file_name_with_group,
            'parents': [drive_config["upload_folder_id"]]
        }

        media = MediaFileUpload(file_path, resumable=True,
                                chunksize=1 * 1024 * 1024)  # 1MB chunks

        print(f"\nUploading {file_name} to Google Drive for {group_name}...")

        try:
            request = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            )

            response = None
            last_progress = 0
            retries = 0

            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        current_progress = int(status.progress() * file_size)
                        print_progress_bar(current_progress, file_size)
                        last_progress = current_progress
                        retries = 0  # reset retries on success
                    else:
                        print_progress_bar(last_progress, file_size)

                except Exception as e:
                    retries += 1
                    print(
                        f"\n⚠️ Chunk upload failed (Retry {retries} of {max_retries}): {e}")
                    if "storageQuotaExceeded" in str(e):
                        print(
                            "🚫 Upload failed: Google Drive storage quota exceeded (15GB limit reached).")
                        return False
                    # if retries >= max_retries:
                    #     print("❌ Max chunk retries reached. Upload failed.")
                    #     return False
                    print(f"⏳ Retrying chunk in {wait_time} seconds...")
                    time.sleep(wait_time)

            print_progress_bar(file_size, file_size)
            print(f"\n✅ Upload completed! File ID: {response.get('id')}")
            return True

        except Exception as e:
            print(f"❌ Upload initialization failed: {e}")
            return False

    class RecordingHandler(FileSystemEventHandler):
        def __init__(self, automator):
            self.automator = automator

        def on_created(self, event):
            if not event.is_directory and event.src_path.endswith(('.mp4', '.mkv', '.flv')):
                recording_dir = Path(
                    self.automator.get_recording_path()).resolve()
                created_file_path = Path(event.src_path).resolve()
                if recording_dir in created_file_path.parents or recording_dir == created_file_path.parent:
                    print(f"New recording detected: {event.src_path}")
                    self.automator.recording_file = event.src_path

    # def monitor_recording_completion(self):
    #     recording_path = self.get_recording_path()
    #     if not recording_path:
    #         print("Could not determine recording path")
    #         return
    #     event_handler = self.RecordingHandler(self)
    #     self.observer = Observer()
    #     self.observer.schedule(event_handler, recording_path, recursive=False)
    #     self.observer.start()
    #     print(f"Monitoring recording status for group: {self.current_group}")
    #     print("Press Ctrl+C to stop monitoring")
    #     try:
    #         was_recording = False
    #         while True:
    #             is_recording = self.get_recording_status()
    #             if is_recording and not was_recording:
    #                 print(f"Recording started for {self.current_group}")
    #                 was_recording = True
    #             elif not is_recording and was_recording:
    #                 print(f"Recording stopped for {self.current_group}")
    #                 was_recording = False
    #                 time.sleep(10)
    #                 if self.recording_file and os.path.exists(self.recording_file):
    #                     print(
    #                         f"Uploading recorded file to {self.current_group}'s Drive: {self.recording_file}")
    #                     if self.upload_to_drive(self.recording_file, self.current_group):
    #                         print(
    #                             f"Upload successful to {self.current_group}'s Google Drive!")
    #                     else:
    #                         print(f"Upload failed for {self.current_group}!")
    #                     self.recording_file = None
    #                 else:
    #                     print("No recording file found")
    #             time.sleep(1)
    #     except KeyboardInterrupt:
    #         print("\nMonitoring stopped")
    #     finally:
    #         if self.observer:
    #             self.observer.stop()
    #             self.observer.join()

    def monitor_recording_completion(self):
        recording_path = self.get_recording_path()
        if not recording_path:
            print("Could not determine recording path")
            return
        event_handler = self.RecordingHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, recording_path, recursive=False)
        self.observer.start()
        print(f"Monitoring recording status for group: {self.current_group}")
        print("Press Ctrl+C to stop monitoring")
        try:
            was_recording = False
            while True:
                is_recording = self.get_recording_status()
                if is_recording and not was_recording:
                    print(f"Recording started for {self.current_group}")
                    was_recording = True
                elif not is_recording and was_recording:
                    print(f"Recording stopped for {self.current_group}")
                    was_recording = False

                    # 🔄 Wait for file to appear
                    print("⏳ Waiting for recording file to appear...")
                    wait_time = 0
                    max_wait = 60
                    while wait_time < max_wait:
                        if self.recording_file and os.path.exists(self.recording_file):
                            print(
                                f"✅ Recording file detected: {self.recording_file}")
                            break
                        time.sleep(8)
                        wait_time += 8
                    else:
                        print("🚫 Recording file not found after waiting.")
                        # 🧍 Ask user to manually provide path
                        while True:
                            manual_path = input(
                                "📂 Please enter the full path to the recording file (or press Enter to skip): ").strip()
                            if manual_path == "":
                                print("⚠️ Skipping upload.")
                                self.recording_file = None
                                break
                            elif os.path.exists(manual_path):
                                self.recording_file = manual_path
                                print(
                                    f"✅ Using manually provided file: {self.recording_file}")
                                break
                            else:
                                print(
                                    "❌ File not found. Try again or press Enter to skip.")

                    if self.recording_file and os.path.exists(self.recording_file):
                        print(
                            f"Uploading recorded file to {self.current_group}'s Drive: {self.recording_file}")
                        if self.upload_to_drive(self.recording_file, self.current_group):
                            print(
                                f"✅ Upload successful to {self.current_group}'s Google Drive!")
                        else:
                            print(f"❌ Upload failed for {self.current_group}!")
                        self.recording_file = None

                time.sleep(1)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()

    def run(self):
        print("=== OBS Multi-Group Recording Automator ===")
        if not self.select_group():
            return
        group_config = self.get_current_group_config()
        if not group_config:
            print("Invalid group configuration")
            return
        if not self.launch_obs():
            return
        if not self.connect_to_obs():
            return
        scene_name = group_config["scene_name"]
        if not self.set_scene(scene_name):
            return
        record_folder = group_config.get("record_folder")
        if record_folder:
            os.makedirs(record_folder, exist_ok=True)
            if not self.set_recording_folder(record_folder):
                return
        if not self.setup_google_drive_auth(self.current_group):
            return
        if not self.start_recording():
            return
        self.monitor_recording_completion()
        if self.obs_ws:
            self.obs_ws.disconnect()
            print("Disconnected from OBS")


def main():
    automator = OBSRecordingAutomator()
    automator.run()


if __name__ == "__main__":
    main()
