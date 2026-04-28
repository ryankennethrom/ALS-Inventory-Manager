import os
import sys
import shutil
import subprocess
import platform
import time

class Application:
    @staticmethod
    def run_on_startup(enable=True):
        """
        Creates or removes a shortcut in the user's Startup folder.
        This ensures the EXE runs at login with the correct working directory.
        """

        app_name = "ALSInventoryManager"

        # Determine path to the executable
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(sys.argv[0])

        # Path to user's Startup folder
        startup_dir = os.path.join(
            os.environ["APPDATA"],
            r"Microsoft\Windows\Start Menu\Programs\Startup"
        )

        shortcut_path = os.path.join(startup_dir, f"{app_name}.lnk")

        if enable:
            try:
                from win32com.client import Dispatch

                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.IconLocation = exe_path
                shortcut.save()

            except Exception as e:
                print("Failed to create startup shortcut:", e)

        else:
            try:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
            except Exception as e:
                print("Failed to remove startup shortcut:", e)

    @staticmethod
    def save(save_folder, folder_name):
        # Build full path: save_folder/folder_name
        target_dir = os.path.join(save_folder, folder_name)

        # Create directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Path to the running executable or script
        if getattr(sys, 'frozen', False):
            # Running as a compiled EXE
            exe_path = sys.executable
        else:
            # Running as a .py script
            exe_path = os.path.abspath(sys.argv[0])

        # Copy the EXE (or script)
        exe_name = os.path.basename(exe_path)
        shutil.copy2(exe_path, os.path.join(target_dir, exe_name))

        # Copy data.db (must be in same directory as the exe/script)
        base_dir = os.path.dirname(exe_path)
        db_path = os.path.join(base_dir, "data.db")

        if os.path.exists(db_path):
            shutil.copy2(db_path, os.path.join(target_dir, "data.db"))
        else:
            raise FileNotFoundError("data.db not found next to the executable")

        return target_dir

    @staticmethod
    def openfile(filepath):
        system = platform.system()

        if system == "Windows":
            # Open the file
            os.startfile(filepath)

            # Give the app a moment to launch
            time.sleep(0.5)

            # Bring the most recently opened window to the front
            try:
                import win32gui
                import win32con

                # Get the foreground window
                hwnd = win32gui.GetForegroundWindow()

                # Force it to the front
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)

            except ImportError:
                print("pywin32 not installed; focusing skipped")

        elif system == "Darwin":  # macOS
            subprocess.call(["open", filepath])
            time.sleep(0.5)
            subprocess.call([
                "osascript", "-e",
                'tell application "System Events" to set frontmost of the first process whose unix id is (do shell script "pgrep -n -f \\"{}\\"") to true'.format(filepath)
            ])

        else:  # Linux
            subprocess.call(["xdg-open", filepath])
