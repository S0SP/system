import os
import shutil

WORKSPACE_DIR = "d:\\wa\\neokim"
ARCHIVE_DIR = os.path.join(WORKSPACE_DIR, "archive")
ZIP_OUTPUT = os.path.join(WORKSPACE_DIR, "system_design_academy_archive")

def zip_archive():
    if not os.path.exists(ARCHIVE_DIR):
        print(f"Error: Archive directory {ARCHIVE_DIR} does not exist. Run crawling first.")
        return
        
    print("Compressing archive folder...")
    try:
        shutil.make_archive(ZIP_OUTPUT, 'zip', ARCHIVE_DIR)
        print(f"✅ Successfully compiled offline archive ZIP at: {ZIP_OUTPUT}.zip")
    except Exception as e:
        print(f"Error compiling ZIP: {e}")

if __name__ == '__main__':
    zip_archive()
