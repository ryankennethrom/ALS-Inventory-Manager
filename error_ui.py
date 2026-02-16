import tkinter as tk
from tkinter import ttk

def show_error_ui(short: str, error_details: str = None, root: tk.Tk = None):
    """
    Shows a modal error popup with a short message and optional toggleable details.
    Centers relative to `root` if provided.
    """
    popup = tk.Toplevel(root)
    popup.title("Error")
    popup.resizable(False, False)
    popup.attributes("-topmost", True)

    # ---------- Frame ----------
    frame = ttk.Frame(popup, padding=20)
    frame.grid(sticky="nsew")
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    # ---------- Short message ----------
    label = ttk.Label(frame, text=short, font=("TkDefaultFont", 11), wraplength=400)
    label.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 10))

    # ---------- Details ----------
    detail_text = tk.Text(frame, wrap="word", height=10, bg="#f9f9f9", relief="solid", bd=1)
    detail_text.insert("1.0", error_details or "")
    detail_text.configure(state="disabled")
    detail_text.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
    detail_text.grid_remove()  # hide initially

    # ---------- Buttons ----------
    toggle_btn = ttk.Button(frame, text="Show Details")
    close_btn = ttk.Button(frame, text="Close", command=popup.destroy)
    toggle_btn.grid(row=2, column=0, sticky="w", pady=(5, 0))
    close_btn.grid(row=2, column=1, sticky="e", pady=(5, 0))

    def center_popup():
        """Recalculate popup size and center it over the root window."""
        popup.update_idletasks()
        w = popup.winfo_reqwidth()
        h = popup.winfo_reqheight()

        if root.winfo_ismapped():
            # Center over root
            x = root.winfo_rootx() + (root.winfo_width() // 2) - (w // 2)
            y = root.winfo_rooty() + (root.winfo_height() // 2) - (h // 2)
        else:
            # Center on screen
            x = (popup.winfo_screenwidth() // 2) - (w // 2)
            y = (popup.winfo_screenheight() // 2) - (h // 2)

        popup.geometry(f"{w}x{h}+{x}+{y}")

    def toggle_details():
        if detail_text.winfo_viewable():
            detail_text.grid_remove()
            toggle_btn.config(text="Show Details")
        else:
            detail_text.grid()
            toggle_btn.config(text="Hide Details")
        center_popup()  # recalc size/position

    toggle_btn.config(command=toggle_details)

    # ---------- Initial center ----------
    center_popup()

    # ---------- Block until closed ----------
    popup.wait_window()
