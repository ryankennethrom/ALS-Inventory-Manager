import os
import subprocess
import psutil
import time

MAINTENANCE_FILE = "AppInMaintenance.txt"
APP_NAME = "ALS Inventory Manager.exe"
APP_PATH = f"{APP_NAME}"   # fixed path

def is_app_running(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return proc
    return None

def main():
    while True:
        maintenance_exists = os.path.exists(MAINTENANCE_FILE)
        proc = is_app_running(APP_NAME)

        # If maintenance file exists → kill the app
        if maintenance_exists:
            if proc:
                print("Maintenance file exists. Killing application...")
                proc.terminate()
            else:
                print("Maintenance file exists. App already stopped.")

        # If maintenance file does NOT exist → start the app if not running
        else:
            if not proc:
                print("Maintenance file missing and app not running. Starting application...")
                subprocess.Popen([APP_PATH])
            else:
                print("App already running. No action needed.")

        time.sleep(10)

if __name__ == "__main__":
    main()
