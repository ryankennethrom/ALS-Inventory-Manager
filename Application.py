import os
import sys
import shutil
import subprocess
import platform
import time
import psutil
import win32event
import win32api
import win32con
import requests
import constants
import certifi
from datetime import date, timedelta
import DB

class Application:
    EXE_NAME = "ALS Inventory Manager.exe"
    DatabasePath = "Resources/Database/data.db"
    HELPER_NAME = "ALS Inventory Helper.exe"
    HELPER_PATH = os.path.join("Resources", "Helper", HELPER_NAME)

    class Settings:

        @staticmethod
        def GetLastMonthlyEmail():
            return DB.get_monthly_email_last_sent(None)
        
        @staticmethod
        def SetMonthlyEmailAsToday():
            DB.set_monthly_email_last_sent(
                None,
                date.today()
            )

        @staticmethod
        def clear_monthly_email_last_sent():
            DB.clear_monthly_email_last_sent()
    
    @staticmethod
    def get_monthly_report_html() -> str:

        emergency = DB.get_on_emergency()
        low = DB.get_on_low()
        out_of_stock = DB.get_out_of_stock()

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h1>ALS Inventory Monthly Report</h1>
            <p>Generated: {date.today()}</p>
        """

        def product_table(title, products):
            if not products:
                return f"<h2>{title}</h2><p>None</p>"

            table = f"""
                <h2>{title}</h2>
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr>
                        <th>Product</th>
                        <th>Quantity</th>
                    </tr>
            """

            for product in products:
                table += f"""
                    <tr>
                        <td>{product["ProductName"]}</td>
                        <td>{product["TotalQuantityAvailable"]}</td>
                    </tr>
                """

            table += "</table>"
            return table

        html += product_table(
            "Emergency Stock",
            emergency
        )

        html += product_table(
            "Low Stock",
            low
        )

        html += product_table(
            "Out Of Stock",
            out_of_stock
        )

        html += """
        </body>
        </html>
        """

        return html
        
    @staticmethod
    def should_send_monthly_email():
        def third_monday(year: int, month: int) -> date:
            first_day = date(year, month, 1)

            # Monday = 0
            days_until_monday = (0 - first_day.weekday()) % 7

            first_monday = first_day + timedelta(days=days_until_monday)

            # Third Monday = first Monday + 14 days
            return first_monday + timedelta(days=14)

        last_sent = DB.get_monthly_email_last_sent()

        today = date.today()

        target_date = third_monday(today.year, today.month)

        return True

        # Not yet reached the third Monday
        if today < target_date:
            return False

        # Never sent before
        if last_sent is None:
            return True

        # Already sent after the trigger date
        if last_sent >= target_date:
            return False

        return True

    @staticmethod
    def delete_task_if_exists():
        """
        Deletes a Windows Scheduled Task with the same name as the EXE.
        Safe to call even if the task does not exist.
        """
        task_name = "ALS_Inventory_Manager_5min"

        # Check if task exists
        check_cmd = ["schtasks", "/Query", "/TN", task_name]
        result = subprocess.run(check_cmd, capture_output=True, text=True)

        if "ERROR:" not in result.stdout:
            print(f"Scheduled task '{task_name}' found. Deleting...")
            subprocess.run(["schtasks", "/Delete", "/TN", task_name, "/F"])
        else:
            print(f"No scheduled task named '{task_name}' found.")
    
    @staticmethod
    def run_helper_if_not_running():
        """
        Starts ALS Inventory Helper if it is not already running.
        """
        # Check if helper is running
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == Application.HELPER_NAME:
                print("Helper already running.")
                return

        # Launch helper
        if os.path.exists(Application.HELPER_PATH):
            print("Starting ALS Inventory Helper...")
            subprocess.Popen([Application.HELPER_PATH])
        else:
            print(f"Helper not found at: {Application.HELPER_PATH}")

    @staticmethod
    def run_every_five_minutes():
        exe_path = os.path.abspath(Application.EXE_NAME)
        exe_dir = os.path.dirname(exe_path)
        task_name = "ALS_Inventory_Manager_5min"

        vbs_path = os.path.join(exe_dir, "Resources/AppRunners/run_app.vbs")

        def register_task(vbs_path):
            task_name = "ALS_Inventory_Manager_5min"
            
            CREATE_NO_WINDOW = 0x08000000

            # Delete old task if it exists
            subprocess.run(
                ["schtasks", "/Delete", "/TN", task_name, "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW,
                shell=False
            )

            # Create new task
            subprocess.run([
                "schtasks",
                "/Create",
                "/SC", "MINUTE",
                "/MO", "30",
                "/ST", "00:00",
                "/TN", task_name,
                "/TR", f'wscript.exe "{vbs_path}"',
                "/RL", "LIMITED",
                "/RU", os.environ["USERNAME"],
                "/F"
            ],
            creationflags=CREATE_NO_WINDOW
            )

        def create_vbs_launcher(exe_name, exe_dir, vbs_path):
                vbs_content = f'''
            Set WshShell = CreateObject("Wscript.Shell")
            WshShell.Run "powershell.exe -WindowStyle Hidden -Command ""Start-Process '{exe_name}' -WorkingDirectory '{exe_dir}' -WindowStyle Hidden""", 0, False
            '''

                with open(vbs_path, "w", encoding="utf-8") as f:
                    f.write(vbs_content)

        create_vbs_launcher(Application.EXE_NAME, exe_dir, vbs_path)
        register_task(vbs_path)


    @staticmethod
    def test_send_email() -> bool:
        try:
            response = requests.get(
                "https://api.brevo.com/v3/account",
                headers={
                    "accept": "application/json",
                    "api-key": constants.BREVO_API_KEY
                },
                verify=False,  # Match your current implementation
                timeout=30
            )

            return response.status_code == 200

        except Exception:
            return False

    @staticmethod
    def send_email(subject: str, body: str, recipient: str) -> bool:
        url = "https://api.brevo.com/v3/smtp/email"

        headers = {
            "accept": "application/json",
            "api-key": constants.BREVO_API_KEY,
            "content-type": "application/json",
        }

        payload = {
            "sender": {
                "name": "ALS Inventory Manager",
                "email": constants.EMAIL_SENDER,
            },
            "to": [
                {
                    "email": recipient,
                }
            ],
            "subject": subject,
            "htmlContent": body,
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            return True

        except requests.RequestException as e:
            print(f"Failed to send email: {e}")
            return False

    @staticmethod
    def is_allowed_to_run():
        maintenance_flag = os.path.join(os.getcwd(), "AppInMaintenance.txt")
        return not os.path.exists(maintenance_flag)
    
    @staticmethod
    def kill_all_instance():
        subprocess.Popen(
            ["cmd", "/c", "start", "/B", "taskkill", "/F", "/T","/IM", f"{Application.EXE_NAME}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000  # CREATE_NO_WINDOW
        )
        

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
        target_dir = os.path.join(f"Resources/{save_folder}", folder_name)

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

        base_dir = os.path.dirname(exe_path)
        db_path = os.path.join(base_dir, Application.DatabasePath)

        if os.path.exists(db_path):
            shutil.copy2(db_path, os.path.join(target_dir, "data.db"))
        else:
            raise FileNotFoundError("data.db not found")

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
