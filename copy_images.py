import shutil
import os

def main():
    src_dir = r"C:\Users\shaik\.gemini\antigravity-ide\brain\6951887d-ba89-4b87-b433-0ad1c078da4a"
    dest_dir = r"e:\weatherBOT\document\images"
    
    mapping = {
        "dashboard_page_1784176071188.png": "bot_dashboard.png",
        "dataset_list_1784176089132.png": "bot_datasets.png",
        "history_list_1784176108786.png": "bot_history.png",
        "settings_page_1784176124645.png": "bot_settings.png",
        "media__1784177654708.png": "bot_chat.png",
    }
    
    for src_name, dest_name in mapping.items():
        src_path = os.path.join(src_dir, src_name)
        dest_path = os.path.join(dest_dir, dest_name)
        if os.path.exists(src_path):
            shutil.copy(src_path, dest_path)
            print(f"Copied {src_name} to {dest_name}")
        else:
            print(f"Source not found: {src_path}")

if __name__ == "__main__":
    main()
