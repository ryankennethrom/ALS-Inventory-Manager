import DB
import tkinter as tk
from tkinter import ttk, messagebox
from Application import Application

class Settings(ttk.Frame):
    def __init__(self, notebook):
        super().__init__(notebook)

        self.notebook = notebook
        notebook.add(self, text="Settings")

        self.create()
    
    def create(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ==================================================
        # Monthly Reports
        # ==================================================

        reports_frame = ttk.LabelFrame(
            self,
            text="Monthly Reports",
            padding=10
        )

        reports_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=10
        )

        ttk.Label(
            reports_frame,
            text="Monthly inventory reports are sent after the third Monday of each month."
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 10)
        )

        self.send_test_email_button = ttk.Button(
            reports_frame,
            text="Send Test Report",
            command=self.send_test_report
        )

        self.send_test_email_button.grid(
            row=1,
            column=0,
            sticky="w"
        )

        ttk.Button(
            reports_frame,
            text="Reset Last Sent Date",
            command=self.reset_last_sent_date
        ).grid(
            row=1,
            column=1,
            padx=(10, 0),
            sticky="w"
        )

        self.email_status_label = ttk.Label(
            reports_frame,
            text=""
        )

        self.email_status_label.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(10, 0)
        )

        self.refresh_email_status()

        # ==================================================
        # Email Recipients
        # ==================================================

        recipients_frame = ttk.LabelFrame(
            self,
            text="Monthly Report Recipients",
            padding=10
        )

        recipients_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(0, 10)
        )

        recipients_frame.columnconfigure(0, weight=1)
        recipients_frame.rowconfigure(1, weight=1)

        ttk.Label(
            recipients_frame,
            text="Recipients"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.recipients_listbox = tk.Listbox(
            recipients_frame,
            height=10
        )

        self.recipients_listbox.grid(
            row=1,
            column=0,
            sticky="nsew",
            pady=(5, 0)
        )

        scrollbar = ttk.Scrollbar(
            recipients_frame,
            orient="vertical",
            command=self.recipients_listbox.yview
        )

        scrollbar.grid(
            row=1,
            column=1,
            sticky="ns",
            pady=(5, 0)
        )

        self.recipients_listbox.configure(
            yscrollcommand=scrollbar.set
        )

        controls = ttk.Frame(recipients_frame)

        controls.grid(
            row=1,
            column=2,
            sticky="ns",
            padx=(10, 0)
        )

        ttk.Button(
            controls,
            text="Add",
            width=14,
            command=self.add_recipient
        ).pack(fill="x", pady=(0, 5))

        ttk.Button(
            controls,
            text="Modify",
            width=14,
            command=self.modify_recipient
        ).pack(fill="x", pady=(0, 5))

        ttk.Button(
            controls,
            text="Delete",
            width=14,
            command=self.delete_recipient
        ).pack(fill="x")

        self.load_recipients()


    def refresh_email_status(self):
        if Application.test_send_email():
            self.send_test_email_button.configure(
                state="normal"
            )

            self.email_status_label.configure(
                text="✓ You can send the report from this computer",
                foreground="green"
            )

        else:
            self.send_test_email_button.configure(
                state="disabled"
            )

            self.email_status_label.configure(
                text="✗ You cannot send the report from this computer",
                foreground="red"
            )

    # ======================================================
    # Recipient Actions
    # ======================================================

    def load_recipients(self):
        self.recipients_listbox.delete(0, tk.END)

        recipients = DB.get_monthly_email_recipients()

        for recipient in recipients:
            self.recipients_listbox.insert(
                tk.END,
                recipient
            )

    
    def add_recipient(self):
        dialog = RecipientDialog(
            self,
            "Add Recipient"
        )

        self.wait_window(dialog)

        if dialog.result:
            DB.add_monthly_email_recipient(dialog.result)
            self.load_recipients()
    
    def modify_recipient(self):
        selection = self.recipients_listbox.curselection()

        if not selection:
            return

        current_email = self.recipients_listbox.get(
            selection[0]
        )

        dialog = RecipientDialog(
            self,
            "Modify Recipient",
            current_email
        )

        if dialog.result:
            DB.update_monthly_email_recipient(
                current_email,
                dialog.result
            )
            self.load_recipients()

    def delete_recipient(self):
        selection = self.recipients_listbox.curselection()

        if not selection:
            return

        email = self.recipients_listbox.get(
            selection[0]
        )

        if messagebox.askyesno(
            "Delete Recipient",
            f"Delete '{email}'?"
        ):
            DB.delete_monthly_email_recipient(email)
            self.load_recipients()

    # ======================================================
    # Monthly Report Actions
    # ======================================================

    def send_test_report(self):
        messagebox.showinfo(
            "Test Report",
            "Test report sent."
        )

    def reset_last_sent_date(self):
        if messagebox.askyesno(
            "Reset Date",
            "Reset MonthlyEmailLastSent?"
        ):
            Application.Settings.clear_monthly_email_last_sent()

            messagebox.showinfo(
                "Success",
                "Monthly email date reset."
            )


class RecipientDialog(tk.Toplevel):
    def __init__(self, parent, title, initial_value=""):
        super().__init__(parent)

        self.result = None

        self.title(title)
        self.resizable(False, False)

        ttk.Label(
            self,
            text="Email Address:"
        ).grid(
            row=0,
            column=0,
            padx=10,
            pady=10
        )

        self.entry = ttk.Entry(
            self,
            width=40
        )

        self.entry.grid(
            row=0,
            column=1,
            padx=(0, 10),
            pady=10
        )

        self.entry.insert(
            0,
            initial_value
        )

        ttk.Button(
            self,
            text="Save",
            command=self.save
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            pady=(0, 10)
        )

        self.transient(parent)
        self.grab_set()

    def save(self):
        self.result = self.entry.get().strip()
        self.destroy()

