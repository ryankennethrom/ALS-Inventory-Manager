import tkinter as tk
from tkinter import ttk

class ConfirmDialog:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.auto_confirm = False

    def show(
    self,
    question: str,
    root: tk.Tk = None,
    confirm_text: str = None
    ) -> bool:

        # Automatically approve without showing UI
        if self.auto_confirm:
            return True
        
        result = {"value": False}
        
        popup = tk.Toplevel(root)
        popup.title("Confirm")
        popup.resizable(False, False)
        popup.focus_set()
        popup.attributes("-topmost", True)
        popup.grab_set()
        
        frame = ttk.Frame(popup, padding=20)
        frame.grid(sticky="nsew")

        ttk.Label(
        frame,
        text=question,
        wraplength=400
        ).grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 10))
        
        entry_var = tk.StringVar()
        error_var = tk.StringVar()
        
        row = 1
        entry = None
        
        if confirm_text:
            ttk.Label(
            frame,
            text=f'Type "{confirm_text}" to confirm:'
            ).grid(row=row, column=0, columnspan=2, sticky="we", pady=(0, 5))
            row += 1
        
            entry = ttk.Entry(frame, textvariable=entry_var)
            entry.grid(row=row, column=0, columnspan=2, sticky="we", pady=(0, 5))
            row += 1
        
            ttk.Label(
            frame,
            textvariable=error_var,
            foreground="red"
            ).grid(row=row, column=0, columnspan=2, sticky="we", pady=(0, 5))
            row += 1
        
            entry.focus_set()

        def choose_yes():
            if confirm_text:
                if entry.get().strip() != confirm_text:
                    error_var.set("Confirmation text does not match.")
                    return
        
            result["value"] = True
            popup.destroy()
        
        def choose_no():
            result["value"] = False
            popup.destroy()
        
        popup.protocol("WM_DELETE_WINDOW", choose_no)
        
        ttk.Button(
            frame,
            text="Yes",
            command=choose_yes
        ).grid(row=row, column=0, sticky="w", pady=(5, 0))
        
        ttk.Button(
            frame,
            text="No",
            command=choose_no
        ).grid(row=row, column=1, sticky="e", pady=(5, 0))
        
        popup.update_idletasks()
        
        w = popup.winfo_reqwidth()
        h = popup.winfo_reqheight()
        
        if root and root.winfo_ismapped():
            x = root.winfo_rootx() + (root.winfo_width() // 2) - (w // 2)
            y = root.winfo_rooty() + (root.winfo_height() // 2) - (h // 2)
        else:
            x = (popup.winfo_screenwidth() // 2) - (w // 2)
            y = (popup.winfo_screenheight() // 2) - (h // 2)
        
        popup.geometry(f"{w}x{h}+{x}+{y}")
        
        popup.wait_window()
        
        return result["value"]
