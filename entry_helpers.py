from tkcalendar import DateEntry, Calendar
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pyautogui
from rapidfuzz import fuzz, process
import DB
import subprocess
import os
import win32com.client
import pythoncom
import time
from PIL import Image

def scan_document_and_save(connect_timeout=10):
    """
    Scans a document and returns the saved file path.
    Returns None if:
      - User cancels
      - Cannot connect to scanner within connect_timeout seconds
    """

    root = tk.Tk()
    root.withdraw()  # Hide main window
    scan_result = {"image": None}

    def choose_scanner_gui(devices):
        """Scanner selection GUI with horizontally aligned buttons."""
        win = tk.Toplevel()
        win.title("Select Scanner")
        win.geometry("400x300")

        selected_index = {"value": None}

        # Title
        tk.Label(win, text="Select a scanner", font=("Arial", 14, "bold")).pack(pady=(10, 5))

        # Listbox + Scrollbar
        list_frame = tk.Frame(win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        listbox = tk.Listbox(list_frame, font=("Arial", 11), yscrollcommand=scrollbar.set, activestyle='dotbox')
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for idx, name in devices:
            listbox.insert(tk.END, name)

        # Instructions
        tk.Label(win, text="Double-click or click 'Select' to pick a scanner", font=("Arial", 10), fg="gray").pack(pady=(0, 5))

        # Double-click selects scanner
        def on_double_click(event):
            sel = listbox.curselection()
            if sel:
                selected_index["value"] = devices[sel[0]][0]
                win.destroy()

        listbox.bind("<Double-Button-1>", on_double_click)

        # Buttons frame at bottom (horizontal)
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)

        select_btn = tk.Button(
            btn_frame,
            text="Select",
            width=12,
            command=lambda: (selected_index.update({"value": devices[listbox.curselection()[0]][0]}), win.destroy())
        )
        cancel_btn = tk.Button(btn_frame, text="Cancel", width=12, command=win.destroy)

        # Pack buttons horizontally
        select_btn.pack(side=tk.LEFT, padx=5, ipadx=5, ipady=5)
        cancel_btn.pack(side=tk.LEFT, padx=5, ipadx=5, ipady=5)

        win.grab_set()
        win.wait_window()
        return selected_index["value"]

    try:
        pythoncom.CoInitialize()
        wia = win32com.client.Dispatch("WIA.DeviceManager")

        # Enumerate scanners
        devices = [
            (i + 1, wia.DeviceInfos[i + 1].Properties("Name").Value)
            for i in range(wia.DeviceInfos.Count)
            if wia.DeviceInfos[i + 1].Type == 1
        ]

        if not devices:
            messagebox.showerror("Error", "No scanners found.")
            return None

        selected = choose_scanner_gui(devices)
        if selected is None:
            return None

        # Timeout while connecting
        start_time = time.time()
        device = None
        scan_win = tk.Toplevel()
        scan_win.title("Connecting to Scanner")
        scan_win.geometry("300x80")
        tk.Label(scan_win, text="Connecting to scanner...", font=("Arial", 11)).pack(pady=20)
        scan_win.update()

        while time.time() - start_time < connect_timeout:
            try:
                device = wia.DeviceInfos[selected].Connect()
                break
            except Exception:
                scan_win.update()
                time.sleep(0.1)

        scan_win.destroy()

        if device is None:
            messagebox.showerror("Timeout", f"Could not connect to scanner within {connect_timeout} seconds. Please make sure no other program is using the scanner.")
            return None

        # Scan window
        scan_win = tk.Toplevel()
        scan_win.title("Scanning")
        scan_win.geometry("300x80")
        tk.Label(scan_win, text="Scanning, please wait...", font=("Arial", 11)).pack(pady=20)
        scan_win.update()

        item = device.Items[1]
        scan_result["image"] = item.Transfer()
        scan_win.destroy()

        # after your scan:
        file_path = filedialog.asksaveasfilename(
            title="Save Scanned Document as PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")]
        )
        if not file_path:
            return None

        # Save temporary PNG (WIA image)
        temp_png = file_path.replace(".pdf", "_temp.png")
        scan_result["image"].SaveFile(temp_png)

        # Convert PNG to PDF
        img = Image.open(temp_png)
        img.convert("RGB").save(file_path, "PDF")

        messagebox.showinfo("Success", f"Saved to:\n{file_path}")
        return file_path
        
    except Exception as e:
        messagebox.showerror("Scan Error", str(e))
        return None

    finally:
        pythoncom.CoUninitialize()
        root.destroy()

def open_file(path):
    subprocess.Popen(["start", "", path], shell=True)

def attach_datepicker(entry):    
    calendar_window = None
    focus_in_id = None
    button_down_id = None
    entry.focused_entry = False
    entry.focused_calendar = False

    def show_calendar(event=None):
        nonlocal button_down_id
        nonlocal focus_in_id
        nonlocal calendar_window

        def hide_calendar(event=None):
            if calendar_window:
                calendar_window.destroy()

        # Prevent multiple popups
        if calendar_window and calendar_window.winfo_exists():
            return

        parent = entry.winfo_toplevel()

        calendar_window = tk.Toplevel(parent)
        calendar_window.overrideredirect(True)  # remove title bar
        calendar_window.attributes("-topmost", True)

        # Position under entry
        parent.update_idletasks()
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()

        calendar_window.geometry(f"+{x}+{y}")
        
        def reposition_calendar(event=None):
            if calendar_window and calendar_window.winfo_exists():
                x = entry.winfo_rootx()
                y = entry.winfo_rooty() + entry.winfo_height()
                calendar_window.geometry(f"+{x}+{y}")

        parent.bind("<Configure>", reposition_calendar)

        cal = Calendar(calendar_window, selectmode="day", date_pattern="yyyy-mm-dd")
        cal.pack()
 
        def select_date(event=None):
            entry.delete(0, tk.END)
            entry.insert(0, cal.get_date())
            entry.tk_focusNext().focus()
            calendar_window.destroy()

        def close_if_out_of_focus(e):
            try:
                x = int(event.x_root)
                y = int(event.y_root)
                
                popup = calendar_window
                px = int(popup.winfo_rootx())
                py = int(popup.winfo_rooty())
                pw = int(popup.winfo_width())
                ph = int(popup.winfo_height())

            except Exception:
                parent.unbind("<Button-1>", button_down_id)
                calendar_window.destroy()
                return

            if ( px <= x <= px + pw and py <= y <= py + ph ) :
                return
            else:
                parent.unbind("<Button-1>", button_down_id)
                calendar_window.destroy()

        cal.bind("<<CalendarSelected>>", select_date)

        button_down_id = parent.bind("<Button-1>", close_if_out_of_focus)
        parent.bind("<Tab>", lambda e: calendar_window.destroy()) 
        parent.bind("<Unmap>", lambda e: calendar_window.destroy())
    focus_in_id = entry.bind("<Button-1>", show_calendar)


def attach_listpicker(entry, options_list):
    """
    Attach a dropdown list picker to a Tkinter Entry widget.
    Dropdown follows the entry if the window moves/resizes.

    :param entry: tk.Entry widget
    :param options_list: list of strings to choose from
    """
    dropdown = None

    def show_dropdown(event=None):
        nonlocal dropdown

        # Prevent multiple popups
        if dropdown and dropdown.winfo_exists():
            return

        parent = entry.winfo_toplevel()

        dropdown = tk.Toplevel(parent)
        dropdown.overrideredirect(True)
        dropdown.attributes("-topmost", True)

        # Position under entry
        def reposition_dropdown(event=None):
            if dropdown and dropdown.winfo_exists():
                x = entry.winfo_rootx()
                y = entry.winfo_rooty() + entry.winfo_height()
                dropdown.geometry(f"+{x}+{y}")

        reposition_dropdown()
        parent.bind("<Configure>", reposition_dropdown)

        # ---------------- ADDED: frame + scrollbar ----------------
        frame = tk.Frame(dropdown)
        frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        

        listbox = tk.Listbox(
            frame,
            height=8,  # LIMIT VISIBLE ROWS
            yscrollcommand=scrollbar.set
        )
        listbox.pack(side="left", fill="both", expand=True)

        scrollbar.config(command=listbox.yview)
        # ----------------------------------------------------------
        MAX_VISIBLE = 8
        MIN_VISIBLE = 1 
        def update_list(filter_text=""):
            listbox.delete(0, tk.END)

            matches = [
                item for item in options_list
                if filter_text.lower() in item.lower()
            ]

            for item in matches:
                listbox.insert(tk.END, item)

            # 🔽 ADJUST HEIGHT TO CONTENTS
            visible_rows = max(MIN_VISIBLE, min(len(matches), MAX_VISIBLE))
            listbox.config(height=visible_rows)

        update_list()

        # Handle selection
        def on_button_down(event=None):
            if listbox.curselection():
                value = listbox.get(listbox.curselection()[0])  # fixed tuple usage
                entry.delete(0, tk.END)
                entry.insert(0, value)
                entry.tk_focusNext().focus()
                dropdown.destroy()

        def destroy_dropdown(event):
            dropdown.destroy()

        parent.bind("<Button-1>", destroy_dropdown)
        parent.bind("<Key>", destroy_dropdown)

        listbox.bind("<Button-1>", on_button_down)
        listbox.bind("<Key>", on_button_down)

    return entry.bind("<FocusIn>", show_dropdown)

def unattach_all(entry):
    entry.unbind("<FocusIn>")

def attach_fuzzy_list(entry, data):
    """
    Attach a dropdown list picker to a Tkinter Entry widget.
    Dropdown follows the entry if the window moves/resizes.

    :param entry: tk.Entry widget
    :param options_list: list of strings to choose from
    """
    dropdown = None

    def show_dropdown(event=None):
        nonlocal dropdown
        # Prevent multiple popups
        if dropdown and dropdown.winfo_exists():
            return

        parent = entry.winfo_toplevel()

        dropdown = tk.Toplevel(parent)
        dropdown.overrideredirect(True)
        dropdown.lift()

        # Position under entry
        def reposition_dropdown(event=None):
            if dropdown and dropdown.winfo_exists():
                x = entry.winfo_rootx()
                y = entry.winfo_rooty() + entry.winfo_height()
                dropdown.geometry(f"+{x}+{y}")

        reposition_dropdown()
        parent.bind("<Configure>", reposition_dropdown)

        # ---------------- ADDED: frame + scrollbar ----------------
        frame = tk.Frame(dropdown)

        scrollbar = tk.Scrollbar(frame)
        

        listbox = tk.Listbox(
            frame,
            height=8,  # LIMIT VISIBLE ROWS
            yscrollcommand=scrollbar.set
        )

        scrollbar.config(command=listbox.yview)
        # ----------------------------------------------------------
        MAX_VISIBLE = 8
        MIN_VISIBLE = 1 
        def update_list(event=None):
            if not dropdown or not dropdown.winfo_exists():
                return
            dropdown.lift()
            listbox.delete(0, tk.END)

            query = entry.get()

            matches = sorted(data, key=lambda x: fuzz.ratio(query, x), reverse=True)
            matches = matches
            for item in matches:
                listbox.insert(tk.END, item)

            visible_rows = max(MIN_VISIBLE, min(len(matches), MAX_VISIBLE))
            listbox.config(height=visible_rows)

        update_list()
        frame.pack(fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        listbox.pack(side="left", fill="both", expand=True)
        

        def on_button_down(event=None):
            if listbox.curselection():
                value = listbox.get(listbox.curselection()[0])  # fixed tuple usage
                dropdown.destroy()
                entry.delete(0, tk.END)
                entry.insert(0, value)
                entry.focus_set()
                pyautogui.press("enter")

        def close_if_out_of_focus(e):
            try:
                x = int(event.x_root)
                y = int(event.y_root)

                popup = dropdown
                px = int(popup.winfo_rootx())
                py = int(popup.winfo_rooty())
                pw = int(popup.winfo_width())
                ph = int(popup.winfo_height())

            except Exception:
                dropdown.destroy()
                return

            if px <= x <= px + pw and py <= y <= py + ph:
                return
            else:
                dropdown.destroy()
        
        def focus_listbox(e):
            if dropdown.focus_get() != listbox:
                listbox.focus_set()
                listbox.selection_clear(0, tk.END)
                listbox.activate(0)
                listbox.selection_set(0)
                listbox.see(0)

        def unfocus_listbox(e):
            entry.focus_set()
            return "break"

        parent.bind("<Button-1>", close_if_out_of_focus)
        parent.bind("<Down>", focus_listbox)
        listbox.bind("<Up>", unfocus_listbox)
        listbox.bind("<Button-1>", on_button_down)
        listbox.bind("<Return>", on_button_down)
        parent.bind("<Tab>", lambda e: dropdown.destroy()) 
        parent.bind("<Unmap>", lambda e: dropdown.destroy())
        entry.bind("<Return>", lambda e: dropdown.destroy(), add='+')
        entry.bind("<KeyRelease>", update_list)
    return entry.bind("<FocusIn>", show_dropdown)

def attach_filepath_manager(entry):
    dropdown = None

    def show_dropdown(event=None):
        nonlocal dropdown
        # Prevent multiple popups
        if dropdown and dropdown.winfo_exists():
            return

        parent = entry.winfo_toplevel()

        dropdown = tk.Toplevel(parent)
        dropdown.overrideredirect(True)
        dropdown.lift()

        # Position under entry
        def reposition_dropdown(event=None):
            if dropdown and dropdown.winfo_exists():
                x = entry.winfo_rootx()
                y = entry.winfo_rooty() + entry.winfo_height()
                dropdown.geometry(f"+{x}+{y}")

        reposition_dropdown()
        parent.bind("<Configure>", reposition_dropdown)

        # ---------------- ADDED: frame + scrollbar ----------------
        frame = tk.Frame(dropdown)

        scrollbar = tk.Scrollbar(frame)


        listbox = tk.Listbox(
            frame,
            height=8,  # LIMIT VISIBLE ROWS
            yscrollcommand=scrollbar.set
        )

        scrollbar.config(command=listbox.yview)
        # ----------------------------------------------------------
        MAX_VISIBLE = 3
        MIN_VISIBLE = 3
        def update_list(event=None):
            if not dropdown or not dropdown.winfo_exists():
                return
            dropdown.lift()
            listbox.delete(0, tk.END)

            items = ["Select a file", "Open file", "Scan file"]
            for item in items:
                listbox.insert(tk.END, item)

            visible_rows = max(MIN_VISIBLE, min(len(items), MAX_VISIBLE))
            listbox.config(height=visible_rows)

        update_list()
        frame.pack(fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        listbox.pack(side="left", fill="both", expand=True)
        
        # Handle selection
        def on_button_down(event=None):
            if listbox.curselection():
                value = listbox.get(listbox.curselection()[0])
                if value == "Select a file":
                    file_path = filedialog.askopenfilename(
                        title="Select a file"
                    )
                    entry.delete(0, tk.END)
                    entry.insert(0, file_path)
                elif value == "Open file":
                    open_file(str(entry.get()))
                elif value == "Scan file":
                    file_path = scan_document_and_save()
                    entry.delete(0, tk.END)
                    entry.insert(0, file_path)
                else:
                    raise Exception("File Path entry helper doesn't recognize a user's input")
                entry.focus_set()
                dropdown.destroy()
                pyautogui.press("enter")

        def close_if_out_of_focus(e):
            try:
                x = int(event.x_root)
                y = int(event.y_root)

                popup = dropdown
                px = int(popup.winfo_rootx())
                py = int(popup.winfo_rooty())
                pw = int(popup.winfo_width())
                ph = int(popup.winfo_height())

            except Exception:
                dropdown.destroy()
                return

            if px <= x <= px + pw and py <= y <= py + ph:
                return
            else:
                dropdown.destroy()
 
        def focus_listbox(e):
            if dropdown.focus_get() != listbox:
                listbox.focus_set()
                listbox.selection_clear(0, tk.END)
                listbox.activate(0)
                listbox.selection_set(0)
                listbox.see(0)

        def unfocus_listbox(e):
            entry.focus_set()
            return "break"

        parent.bind("<Button-1>", close_if_out_of_focus)
        parent.bind("<Down>", focus_listbox)
        listbox.bind("<Up>", unfocus_listbox)
        listbox.bind("<Button-1>", on_button_down)
        listbox.bind("<Return>", on_button_down)
        parent.bind("<Tab>", lambda e: dropdown.destroy())
        parent.bind("<Unmap>", lambda e: dropdown.destroy())
        entry.bind("<Return>", lambda e: dropdown.destroy(), add='+')
    return entry.bind("<FocusIn>", show_dropdown)



def attach_helper(root, entry_name, entry, db_path, relation_name, all_columns, all_column_types):
    col = entry_name
    if all_column_types[col] == "date":
        attach_datepicker(entry)
    if col == "ProductName":
        attach_fuzzy_list(entry, DB.get_productnames(db_path, relation_name))
    elif col == "Station":
        attach_fuzzy_list(entry, DB.get_stations(db_path))
    elif col == "IsConsumable":
        attach_fuzzy_list(entry, ["y", "n"])
    elif col == "ActionType":
        attach_fuzzy_list(entry, ["Received", "Opened"])
    elif col == "CoaFilePath":
        attach_filepath_manager(entry)
