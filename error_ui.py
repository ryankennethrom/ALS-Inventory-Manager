import tkinter as tk
from tkinter import ttk

def show_error_ui_old(short: str, error_details: str = None, root=None):
    owns_root = False
    if root is None:
        root = tk.Tk()
        root.withdraw()
        owns_root = True

    popup = tk.Toplevel(root)
    popup.title("Error")
    popup.resizable(False, False)
    popup.transient(root)

    # ONLY grab if nothing else has it
    try:
        current_grab = popup.tk.call("grab", "current")
        if not current_grab:
            popup.grab_set()
    except tk.TclError:
        pass  # fail silently — error UI must never crash the app

    frame = ttk.Frame(popup, padding=20)
    frame.grid(sticky="nsew")

    ttk.Label(
        frame,
        text=short,
        font=("TkDefaultFont", 11, "bold"),
        foreground="#b00020",
        wraplength=420
    ).grid(row=0, column=0, sticky="w", pady=(0, 10))

    detail_text = tk.Text(
        frame,
        height=10,
        wrap="word",
        bg="#f7f7f7",
        relief="solid",
        bd=1
    )
    detail_text.insert("1.0", error_details or "")
    detail_text.configure(state="disabled")
    detail_text.grid(row=1, column=0, sticky="nsew")
    detail_text.grid_remove()

    def toggle_details():
        if detail_text.winfo_viewable():
            detail_text.grid_remove()
            toggle_btn.config(text="Show Details")
        else:
            detail_text.grid()
            toggle_btn.config(text="Hide Details")
        center_popup()

    btn_frame = ttk.Frame(frame)
    btn_frame.grid(row=2, column=0, sticky="e", pady=(10, 0))

    toggle_btn = ttk.Button(btn_frame, text="Show Details", command=toggle_details)
    toggle_btn.pack(side="left", padx=(0, 5))

    ttk.Button(btn_frame, text="Close", command=popup.destroy).pack(side="left")

    def center_popup():
        popup.update_idletasks()
        w = popup.winfo_reqwidth()
        h = popup.winfo_reqheight()

        if root.winfo_ismapped():
            x = root.winfo_rootx() + (root.winfo_width() // 2) - (w // 2)
            y = root.winfo_rooty() + (root.winfo_height() // 2) - (h // 2)
        else:
            x = (popup.winfo_screenwidth() - w) // 2
            y = (popup.winfo_screenheight() - h) // 2

        popup.geometry(f"{w}x{h}+{x}+{y}")

    center_popup()
    popup.wait_window()

    if owns_root:
        root.destroy()

def show_error_ui(short: str, error_details: str = None, root: tk.Tk = None):
    """
    Shows a modal error popup with a short message and optional toggleable details.
    Centers relative to `root` if provided.
    """
    owns_root = False
    if root is None:
        root = tk.Tk()
        root.withdraw()
        owns_root = True

    popup = tk.Toplevel(root)
    popup.title("Error")
    popup.resizable(False, False)
    popup.transient(root)
    popup.grab_set()

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

    # Clean up hidden root if we created it
    if owns_root:
        root.destroy()

