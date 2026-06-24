import random
import tkinter as tk
from tkinter import simpledialog, messagebox
import DB
import date

class StockVerifyAction:
    def __init__(self, db_path, product_name, non_consumable_logs_widget, consumable_logs_widget, available_buttons, frequency=1.0):
        self.frequency = frequency
        self.product_name = product_name
        self.db_path = db_path
        self.non_consumable_logs_widget = non_consumable_logs_widget
        self.consumable_logs_widget = consumable_logs_widget
        self.available_buttons = available_buttons

    def action(self):
        pass

    def ask_to_verify(self):
        quantity = DB.get_product_quantity(self.db_path, self.product_name)

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        # First popup
        answer = messagebox.askyesnocancel(
            title="Stock Verification",
            message=(
                f"Can you confirm there are {quantity} in stock for the product "
                f"'{self.product_name}' ?\n\n(Press 'Cancel' to skip verification)"
            ),
            parent=root
        )

        # User clicked "Yes"
        if answer is True:

            # Ask for initials (must be exactly 2 chars)
            while True:
                initials = simpledialog.askstring(
                    title="Stock Verification",
                    prompt="Please enter your initials (2 characters).\n(Press Cancel to skip)",
                    parent=root
                )

                if initials is None:
                    return {"status": "skipped"}

                initials = initials.strip()

                if len(initials) != 2:
                    messagebox.showerror(
                        "Invalid Input",
                        "Initials must be exactly 2 characters."
                    )
                    continue

                break

            return {
                "status": "confirmed",
                "quantity": quantity,
                "initials": initials
            }

        # User clicked "Cancel"
        if answer is None:
            return {"status": "skipped"}

        # User clicked "No" → ask for actual quantity (non-negative only)
        while True:
            new_qty = simpledialog.askinteger(
                title="Stock Verification",
                prompt=f"How many {self.product_name} are there currently?\n(Press Cancel to skip)",
                parent=root
            )

            if new_qty is None:
                return {"status": "skipped"}

            if new_qty < 0:
                messagebox.showerror(
                    "Invalid Input",
                    "Negative numbers are not allowed."
                )
                continue

            break  # valid number

        # Ask for initials (must be exactly 2 chars)
        while True:
            initials = simpledialog.askstring(
                title="Stock Verification",
                prompt="Please enter your initials (2 characters).\n(Press Cancel to skip)",
                parent=root
            )

            if initials is None:
                return {"status": "skipped"}

            initials = initials.strip()

            if len(initials) != 2:
                messagebox.showerror(
                    "Invalid Input",
                    "Initials must be exactly 2 characters."
                )
                continue

            break

        return {
            "status": "updated",
            "quantity": new_qty,
            "initials": initials
        }

    def verify_product_quantity(self):
        response = self.ask_to_verify()

        # If skipped, do nothing and exit early
        if response["status"] == "skipped":
            messagebox.showinfo("Stock Verification", "Stock Verification Skipped.")
            return

        if response["status"] == "confirmed":
            # Nothing special to do here yet
            pass

        elif response["status"] == "updated":
            difference = DB.get_product_quantity(self.db_path, self.product_name) - response["quantity"]

            if DB.is_product_consumable(self.db_path, self.product_name):
                widget = self.consumable_logs_widget
                if difference > 0:
                    # fill in open and finish with "Offset"
                    finish_count = 0
                    while difference > finish_count:
                        oldest_date_opened_not_filled_row = widget.get_first_row_from_bottom(field="DateOpened", value="")
                        oldest_date_finished_not_filled_row = widget.get_first_row_from_bottom(field="DateFinished", value="")
                        o = oldest_date_opened_not_filled_row
                        f = oldest_date_finished_not_filled_row
                        if (f is not None and o is None) or oldest_date_opened_not_filled_row < oldest_date_finished_not_filled_row:
                            finish_count += 1
                            widget.double_click("DateFinished", "")
                            widget.enter_update_entry_value("FinishedInitials", f"OFF{response["initials"]}")
                            widget.enter_update_entry_value("DateFinished", date.get_today_date_str())
                            widget.click_update_item()
                        elif (o is not None and f is None) or oldest_date_opened_not_filled_row >= oldest_date_finished_not_filled_row:
                            widget.double_click("DateOpened", "")
                            widget.enter_update_entry_value("OpenedInitials", f"OFF{response["initials"]}")
                            widget.enter_update_entry_value("DateOpened", date.get_today_date_str())
                            widget.click_update_item()

                else:
                    # Copy previous log and add "Offset"
                    pass

            else:
                if difference > 0:
                    # Open items until quantity is the same and add "Offset" as comment
                    widget = self.non_consumable_logs_widget
                    widget.add_button.invoke()
                    widget.enter_add_entry_value("ActionType", "Opened")
                    widget.enter_add_entry_value("ProductName", self.product_name)
                    widget.enter_add_entry_value("Initials", response["initials"])
                    widget.enter_add_entry_value("Quantity", difference)
                    widget.enter_add_entry_value("PONumber", "Offset")
                    widget.enter_add_entry_value("Comments", "Offset")
                    widget.click_add_new_item()
                else:
                    # Receive items until quantity is the same and add "Offset" as comment
                    widget = self.non_consumable_logs_widget
                    widget.add_button.invoke()
                    widget.enter_add_entry_value("ActionType", "Received")
                    widget.enter_add_entry_value("ProductName", self.product_name)
                    widget.enter_add_entry_value("Initials", response["initials"])
                    widget.enter_add_entry_value("Quantity", abs(difference))
                    widget.enter_add_entry_value("Comments", "Offset")
                    widget.enter_add_entry_value("PONumber", "Offset")
                    widget.click_add_new_item()
                    pass

        # ⭐ Final confirmation popup
        messagebox.showinfo(
            title="Stock Verification",
            message="Stock Verification Done. You may now proceed."
        )
    
    def execute(self):
        if random.random() <= self.frequency:
            self.verify_product_quantity()
        # self.action()

