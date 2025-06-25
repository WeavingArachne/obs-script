import json
import os
from pathlib import Path


class GroupManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "obs": {
                    "host": "localhost",
                    "port": 4455,
                    "password": "",
                    "obs_executable": "obs64.exe"
                },
                "groups": {}
            }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
        print(f"Configuration saved to {self.config_file}")

    def add_group(self, group_name, scene_name, record_folder="", folder_id="root"):
        if group_name in self.config["groups"]:
            print(f"Group '{group_name}' already exists!")
            return False

        safe_name = group_name.lower().replace(' ', '_').replace('-', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')

        self.config["groups"][group_name] = {
            "scene_name": scene_name,
            "record_folder": record_folder,
            "google_drive": {
                "credentials_file": f"credentials_{safe_name}.json",
                "token_file": f"token_{safe_name}.json",
                "upload_folder_id": folder_id,
                "scopes": ["https://www.googleapis.com/auth/drive.file"]
            }
        }

        print(f"Added group: {group_name}")
        print(f"Scene: {scene_name}")
        print(f"Record folder: {record_folder}")
        print(f"Credentials file: credentials_{safe_name}.json")
        print(f"Token file: token_{safe_name}.json")
        return True

    def remove_group(self, group_name):
        if group_name not in self.config["groups"]:
            print(f"Group '{group_name}' not found!")
            return False
        del self.config["groups"][group_name]
        print(f"Removed group: {group_name}")
        return True

    def list_groups(self):
        if not self.config["groups"]:
            print("No groups configured.")
            return
        print("\n=== Configured Groups ===")
        for group_name, group_config in self.config["groups"].items():
            scene = group_config["scene_name"]
            folder = group_config.get("record_folder", "")
            creds_file = group_config["google_drive"]["credentials_file"]
            folder_id = group_config["google_drive"]["upload_folder_id"]
            print(f"\nGroup: {group_name}")
            print(f"  Scene: {scene}")
            print(f"  Record Folder: {folder}")
            print(f"  Credentials: {creds_file}")
            print(f"  Drive Folder: {folder_id}")
            print(f"  Credentials exists: {os.path.exists(creds_file)}")

    def update_group_scene(self, group_name, new_scene_name):
        if group_name not in self.config["groups"]:
            print(f"Group '{group_name}' not found!")
            return False
        old_scene = self.config["groups"][group_name]["scene_name"]
        self.config["groups"][group_name]["scene_name"] = new_scene_name
        print(
            f"Updated {group_name} scene: '{old_scene}' -> '{new_scene_name}'")
        return True

    def update_group_folder(self, group_name, new_folder_id):
        if group_name not in self.config["groups"]:
            print(f"Group '{group_name}' not found!")
            return False
        old_folder = self.config["groups"][group_name]["google_drive"]["upload_folder_id"]
        self.config["groups"][group_name]["google_drive"]["upload_folder_id"] = new_folder_id
        print(
            f"Updated {group_name} Drive folder: '{old_folder}' -> '{new_folder_id}'")
        return True

    def update_group_record_folder(self, group_name, new_record_folder):
        if group_name not in self.config["groups"]:
            print(f"Group '{group_name}' not found!")
            return False
        old_path = self.config["groups"][group_name].get("record_folder", "")
        self.config["groups"][group_name]["record_folder"] = new_record_folder
        print(
            f"Updated {group_name} record folder: '{old_path}' -> '{new_record_folder}'")
        return True

    def interactive_menu(self):
        while True:
            print("\n=== Group Management Menu ===")
            print("1. List all groups")
            print("2. Add new group")
            print("3. Remove group")
            print("4. Update group scene")
            print("5. Update group Drive folder")
            print("6. Update group Record folder")
            print("7. Save and exit")
            print("8. Exit without saving")

            choice = input("\nSelect option (1-8): ").strip()

            if choice == "1":
                self.list_groups()
            elif choice == "2":
                group_name = input("Enter group name: ").strip()
                scene_name = input("Enter OBS scene name: ").strip()
                record_folder = input(
                    "Enter recording folder (leave blank if not needed): ").strip()
                folder_id = input(
                    "Enter Google Drive folder ID (or press Enter for root): ").strip()
                if not folder_id:
                    folder_id = "root"
                self.add_group(group_name, scene_name,
                               record_folder, folder_id)
            elif choice == "3":
                self.list_groups()
                group_name = input("\nEnter group name to remove: ").strip()
                if input(f"Are you sure you want to remove '{group_name}'? (y/N): ").lower() == 'y':
                    self.remove_group(group_name)
            elif choice == "4":
                self.list_groups()
                group_name = input("\nEnter group name: ").strip()
                new_scene = input("Enter new scene name: ").strip()
                self.update_group_scene(group_name, new_scene)
            elif choice == "5":
                self.list_groups()
                group_name = input("\nEnter group name: ").strip()
                new_folder = input(
                    "Enter new Google Drive folder ID: ").strip()
                self.update_group_folder(group_name, new_folder)
            elif choice == "6":
                self.list_groups()
                group_name = input("\nEnter group name: ").strip()
                new_record_path = input(
                    "Enter new record folder path: ").strip()
                self.update_group_record_folder(group_name, new_record_path)
            elif choice == "7":
                self.save_config()
                print("Configuration saved. Goodbye!")
                break
            elif choice == "8":
                print("Exiting without saving. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")


def main():
    print("=== OBS Group Manager ===")
    manager = GroupManager()
    manager.interactive_menu()


if __name__ == "__main__":
    main()
