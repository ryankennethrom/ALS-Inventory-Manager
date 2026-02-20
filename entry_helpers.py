from tkcalendar import DateEntry, Calendar
import tkinter as tk
from tkinter import ttk
import pyautogui
from rapidfuzz import fuzz, process


def attach_datepicker(entry):
    
    calendar_window = None
    focus_in_id = None
    focus_out_id = None
    entry.focused_entry = False
    entry.focused_calendar = False

    def show_calendar(event=None):
        nonlocal focus_out_id
        nonlocal focus_in_id
        nonlocal calendar_window

        entry.delete(0, tk.END)
 
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

            except ValueError:
                calendar_window.destroy()
                return

            if px <= x <= px + pw and py <= y <= py + ph:
                return
            else:
                calendar_window.destroy()

        cal.bind("<<CalendarSelected>>", select_date)

        parent.bind("<Button-1>", close_if_out_of_focus)
        parent.bind("<Tab>", lambda e: calendar_window.destroy()) 

    focus_in_id = entry.bind("<FocusIn>", show_calendar)


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
        def update_list(event=None):
            if not dropdown or not dropdown.winfo_exists():
                return

            listbox.delete(0, tk.END)

            query = entry.get()

            matches = sorted(data, key=lambda x: fuzz.ratio(query, x), reverse=True)
            matches = ["", query] + matches
            for item in matches:
                listbox.insert(tk.END, item)

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

        def close_if_out_of_focus(e):
            try:
                x = int(event.x_root)
                y = int(event.y_root)

                popup = dropdown
                px = int(popup.winfo_rootx())
                py = int(popup.winfo_rooty())
                pw = int(popup.winfo_width())
                ph = int(popup.winfo_height())

            except ValueError:
                dropdown.destroy()
                return

            if px <= x <= px + pw and py <= y <= py + ph:
                return
            else:
                dropdown.destroy()
        listbox.start=-1
        def move_down(e):
            if not dropdown or not dropdown.winfo_exists():
                return
            listbox.focus_set()
            listbox.start += 1
            listbox.start = listbox.start%listbox.size() 
            listbox.selection_clear(0, tk.END)
            listbox.activate(listbox.start)
            listbox.selection_set(listbox.start)
            listbox.see(listbox.start)
            return "break"

        def move_up(e):
            listbox.start -= 1
            if listbox.start < 0:
                entry.focus_set()
            else:
                listbox.start = listbox.start%listbox.size()
                listbox.selection_clear(0, tk.END)
                listbox.activate(listbox.start)
                listbox.selection_set(listbox.start)
                listbox.see(listbox.start)
            return "break"

        parent.bind("<Button-1>", close_if_out_of_focus)
        parent.bind("<Tab>", move_down)
        listbox.bind("<Button-1>", on_button_down)
        listbox.bind("<Return>", on_button_down)
        listbox.bind("<Tab>", move_down)
        listbox.bind("<Shift-Tab>", move_up)

        entry.bind("<KeyRelease>", update_list)
    return entry.bind("<FocusIn>", show_dropdown)

