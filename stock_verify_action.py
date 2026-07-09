import random
import tkinter as tk
from tkinter import simpledialog, messagebox
import DB
import date

class StockVerifyAction:
    def __init__(self, db_path, product_name, non_consumable_logs_widget, consumable_logs_widget, available_buttons, callbacks_on_verify=[], frequency=1.0):
        self.frequency = frequency
        self.product_name = product_name
        self.db_path = db_path
        self.non_consumable_logs_widget = non_consumable_logs_widget
        self.consumable_logs_widget = consumable_logs_widget
        self.available_buttons = available_buttons
        self.callbacks_on_verify = callbacks_on_verify

    def action(self):
        pass

    def ask_to_verify(self, prefix=None):
        quantity = DB.get_product_quantity(self.db_path, self.product_name)

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        # User clicked "No" → ask for actual quantity (non-negative only)
        while True:
            new_qty = simpledialog.askinteger(
                title="Stock Verification",
                prompt=f"{f"{prefix} " if prefix is not None else ""}How many {self.product_name} are in stock currently ? (System Answer: {quantity})\n(Press Cancel to skip)",
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

    def verify_product_quantity(self, prefix=""):
        response = self.ask_to_verify(prefix)

        # If skipped, do nothing and exit early
        if response["status"] == "skipped":
            messagebox.showinfo("Stock Verification", "Stock Verification Skipped.")
            return

        if response["status"] == "confirmed":
            # Nothing special to do here yet
            pass

        elif response["status"] == "updated":
            difference = DB.get_product_quantity(self.db_path, self.product_name) - response["quantity"]
            is_overestimation = difference > 0
            if difference == 0:
                pass
            elif DB.is_product_consumable(self.db_path, self.product_name):
                widget = self.consumable_logs_widget
                if is_overestimation:
                    finish_count = 0
                    
                    # Delete empty offset rows
                    curr_row = 0
                    while difference > finish_count and len(widget.relation.curr_results) > curr_row: 
                        if "offset" in widget.relation.curr_results[curr_row]["Comments"].lower() and widget.relation.curr_results[curr_row]["OpenedInitials"] == "" and widget.relation.curr_results[curr_row]["FinishedInitials"] == "":
                            widget.delete_item(curr_row)
                            finish_count += 1
                        elif widget.relation.curr_results[curr_row]["OpenedInitials"] == "" and widget.relation.curr_results[curr_row]["FinishedInitials"] == "":
                            curr_row += 1
                        else:
                            break

                    # fill in open and finish with "Offset"
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
                    widget.update_table()
                    
                    freed_count = 0

                    i = 0
                    while widget.relation.curr_results[i]["FinishedInitials"] == "" and widget.relation.curr_results[i]["OpenedInitials"] =="":
                        i += 1
                    
                    widget.double_click_row(row=i)
                    if not widget.relation.curr_results[i]["FinishedInitials"].startswith("OFF") and widget.relation.curr_results[i]["OpenedInitials"].startswith("OFF"):
                        widget.enter_update_entry_value("DateOpened", "")
                        widget.enter_update_entry_value("OpenedInitials", "")
                        i += 1
                    widget.click_update_item()
                            
                    # Delete offsets if they exist
                    while i < len(widget.relation.curr_results) and abs(difference) > freed_count:
                        if widget.relation.curr_results[i]["FinishedInitials"].startswith("OFF"):                            
                            widget.double_click_row(row=i)
                            if widget.relation.curr_results[i]["OpenedInitials"].startswith("OFF"):
                                widget.enter_update_entry_value("DateOpened", "")
                                widget.enter_update_entry_value("OpenedInitials", "")
                            widget.enter_update_entry_value("DateFinished", "")
                            widget.enter_update_entry_value("FinishedInitials", "")
                            widget.click_update_item()
                            i += 1
                            freed_count += 1
                        else:
                            break

                    if abs(difference) > freed_count:
                        # Add "Offset" logs
                        widget.add_button.invoke()
                        widget.enter_add_entry_value("ProductName", self.product_name)
                        widget.enter_add_entry_value("Quantity", abs(difference)-freed_count)
                        widget.enter_add_entry_value("ReceivedInitials", f"Missing")
                        widget.enter_add_entry_value("DateReceived", "Unknown")
                        widget.enter_add_entry_value("CertifiedValue", "Missing")
                        widget.enter_add_entry_value("CertificationDate", "Missing")
                        widget.enter_add_entry_value("CoaFilePath", "Missing")
                        widget.enter_add_entry_value("LOT", "Missing")
                        widget.enter_add_entry_value("PONumber", "Missing")
                        widget.enter_add_entry_value("ExpiryDate", "Missing")
                        widget.enter_add_entry_value("Comments", f"This is OFFSET by {response["initials"]}")
                        widget.click_add_new_item()

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

        #⭐ Final confirmation popup
        messagebox.showinfo(
            title="Stock Verification",
            message="Stock Verification Done. You may now proceed."
        )
    
    def execute(self):
        if random.random() <= self.frequency:
            self.verify_product_quantity(prefix="Before you proceed, ")
            for callback in self.callbacks_on_verify:
                callback()
        else:
            self.action()

