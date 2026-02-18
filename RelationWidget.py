import tkinter as tk
from tkinter import ttk, font
import tkinter.font as tkfont
import DB
from RelationInterface import RelationInterface
import random
import string
from error_ui import show_error_ui
from error_handler import run_with_error_handling
from tkinter import messagebox
import time
import types

def generate_random_name(length=6):
    letters = string.ascii_uppercase
    digits = string.digits
    random_part = ''.join(random.choices(letters + digits, k=length))
    return f"PROD-{random_part}"

class RelationWidget(ttk.LabelFrame):
    def __init__(self, master, relation_interface, min_width=400, min_height=200, is_view=False, exclude_fields_on_update=[], exclude_fields_on_show=[], exclude_fields_on_create=[], title="Table", padding=10, **kwargs):
        super().__init__(master, text=title, padding=padding, **kwargs)
        self.title=title
        self.relation = relation_interface
        self.exclude_fields_on_update = exclude_fields_on_update
        self.exclude_fields_on_show = exclude_fields_on_show
        self.update_item_columns = [col for col in DB.get_columns(self.relation.relation_name) if col not in exclude_fields_on_update] 
        self.show_columns = [col for col in DB.get_columns(self.relation.relation_name) if col not in exclude_fields_on_show]
        self.create_item_columns = [col for col in DB.get_columns(self.relation.relation_name) if col not in exclude_fields_on_create]
        self.is_view = is_view
        self.min_width = min_width
        self.min_height = min_height
        self.create_widgets()
        self.popup = None
        self.update_table()
        self.all_columns = DB.get_columns(self.relation.relation_name)
        self.all_column_types = DB.get_column_types(self.relation.relation_name)

        style = ttk.Style()
        style.configure("LightGrey.Treeview",
                        background="#ADD8E6",       
                        fieldbackground="#ADD8E6",
                        bordercolor="#ADD8E6",
                        foreground="black")
        
        def auto_resize_columns(tree, results):
            f = tkfont.Font()  # default font of Treeview
            max_width = dict()
            padding = 0

            # Include header width
            for col in DB.get_columns(self.relation.relation_name):
                max_width[col] = f.measure(col + " " * padding)  # small padding

            # Include row values
            for item in results:
                for col, val in item.items():
                    width = f.measure(str(val) + " " * padding)  # small padding
                    if width > max_width[col]:
                        max_width[col] = width

            # Set column widths
            for col in tree["columns"]:
                if col in max_width:
                    tree.column(col, width=max_width[col])

        auto_resize_columns(self.tree, self.relation.curr_results)

    def create_widgets(self):
        # Configure internal grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Search Frame
        self.search_frame = ttk.Frame(self)
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.search_frame.grid_columnconfigure(0, weight=1)  # Entry expands
        self.search_frame.grid_columnconfigure(1, weight=0)  # Buttons fixed width

        self.search_entry = ttk.Entry(self.search_frame)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=5)
        self.search_entry.bind("<Return>", self.search)

        ttk.Button(self.search_frame, text=self.relation.simple_search_field, command=self.search).grid(row=0, column=1, sticky="ew", padx=5)

        advance_btn = ttk.Button(self.search_frame, text="Advanced Search", style="TButton")
        
        style = ttk.Style()
        style.configure(
                    f"{self.relation.relation_name}AS.TButton",
                    background="black",
                    foreground="black",
        )

        advance_btn.config(command=types.MethodType(self.advanced_search, advance_btn))
        advance_btn.grid(row=1, column=1, sticky="ew", padx=5)
        # Make the entry expand to fill remaining space
        self.search_frame.grid_columnconfigure(0, weight=1)

        # Tree Frame
        self.tree_frame = tk.Frame(self, bd=1, relief="solid", width=self.min_width, height=self.min_height)
        self.tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.tree_frame.grid_propagate(False)

        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree_scroll_y.grid(row=0, column=1, sticky="ns")
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.grid(row=1, column=0, sticky="ew")

        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns = self.show_columns,
            show="headings",
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        for col in self.show_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        # Buttons Frame
        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=3, column=0, pady=5)
        if not self.is_view:
            ttk.Button(self.button_frame, text="Add", command=self.add).pack(side=tk.LEFT, padx=5)
            ttk.Button(self.button_frame, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=5)
            self.tree.bind("<Double-1>", self.on_double_click)
        ttk.Button(self.button_frame, text="Export", command=lambda: self.relation.export_as_excel(exclude_columns=self.exclude_fields_on_show, output_path=f"{self.relation.relation_name}.xlsx")).pack(side=tk.LEFT, padx=5)

    # -------------------- Actions --------------------
    def advanced_search(self, advance_btn):
        if self.popup is not None and self.popup.winfo_exists() == 1:
            return

        self.popup = tk.Toplevel(self)
        popup = self.popup
        popup.title("Advanced Search")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        popup.attributes("-topmost", True)


        frame = ttk.Frame(popup, padding=20)
        frame.grid(sticky="nsew")

        text_predicates = ["startswith", "contains", "endswith", "exactly"]
        number_predicates = ["equal", "not equal", "less than", "greater than", "less than or equal", "greater than or equal"]
        date_predicates = ["last 24 hours", "last week", "last 30 days", "last 6 months", "last year", "all time"]

        # Fetch schema info

        table_columns = self.all_columns
        column_types = self.all_column_types

        def get_filter_json(col, pred, value):
            col_type = column_types.get(col, "").upper()
            if "INTEGER" in col_type or "FLOAT" in col_type:

                out = {
                        "fieldName":col,
                        "filterType":"single-value-number",
                        "predicate": pred,
                        "filterValue": value,
                        "clauses": [],
                        "params": []
                }

                if value == "":
                    return out
                if pred == "equal":
                    out["clauses"].append(f"{col} = ?")
                    out["params"].append(value)

                elif pred == "not equal":
                    out["clauses"].append(f"{col} != ?")
                    out["params"].append(value)

                elif pred == "less than":
                    out["clauses"].append(f"{col} < ?")
                    out["params"].append(value)

                elif pred == "greater than":
                    out["clauses"].append(f"{col} > ?")
                    out["params"].append(value)

                elif pred == "less than or equal":
                    out["clauses"].append(f"{col} <= ?")
                    out["params"].append(value)

                elif pred == "greater than or equal":
                    out["clauses"].append(f"{col} >= ?")
                    out["params"].append(value)

                else:
                    raise ValueError(f"Unknown number predicate: {pred}")

                return out

            elif "TEXT" in col_type:
                out = {
                        "fieldName" : col,
                        "filterType" : "single-value-text",
                        "predicate" : pred,
                        "filterValue": value,
                        "clauses": [],
                        "params": []
                }
                if value == "":
                    return out
                if pred == "startswith":
                    out["clauses"].append(f"{col} LIKE ?")
                    out["params"].append(f"{value}%")
                elif pred == "contains":
                    out["clauses"].append(f"{col} LIKE ?")
                    out["params"].append(f"%{value}%")
                elif pred == "endswith":
                    out["clauses"].append(f"{col} LIKE ?")
                    out["params"].append(f"%{value}")
                elif pred == "exactly":
                    out["clauses"].append(f"{col} = ?")
                    out["params"].append(value)
                else:
                    raise ValueError(f"Unknown text predicate: {pred}")
                return out
            elif "DATE" in col_type:
                out = {
                    "fieldName": col,
                    "filterType": "relative-date",
                    "predicate": pred,
                    "filterValue": pred,
                    "clauses": [],
                    "params": []
                }

                ranges = {
                    "all time": None,
                    "last 24 hours": "-1 day",
                    "last week": "-7 days",
                    "last 30 days": "-30 days",
                    "last 6 months": "-6 months",
                    "last year": "-1 year"
                }

                modifier = ranges[pred]

                if modifier is not None:
                    out["clauses"].append(
                        f"{col} >= datetime('now', ?)"
                    )
                    out["params"].append(modifier)

                return out
            else:
                raise ValueError(f"Unknown column type: {col_type}")

        row = 0
        widgets = {}

        for col in table_columns:

            ttk.Label(frame, text=col).grid(row=row, column=0, sticky="e", pady=4)

            col_type = column_types.get(col, "").upper()

            # TEXT columns get predicate dropdown
            if "TEXT" in col_type:
                pred = ttk.Combobox(
                    frame,
                    values=text_predicates,
                    state="readonly",
                    width=10
                )
                entry = ttk.Entry(frame, width=25)
                pred.set("contains")

                if col in self.relation.filter_dict:
                    text_filter = self.relation.filter_dict[col]
                    entry.delete(0, tk.END)
                    entry.insert(0, text_filter["filterValue"])
                    pred.set(text_filter["predicate"])

                pred.grid(row=row, column=1, padx=5)
                entry.grid(row=row, column=2, padx=5)
                widgets[col] = (entry, pred)

            elif "INTEGER" in col_type or "FLOAT" in col_type:
                pred = ttk.Combobox(
                    frame,
                    values=number_predicates,
                    state="readonly",
                    width=18
                )
                pred.set("equal")

                entry = ttk.Entry(frame, width=25)

                # Restore existing filter (if any)
                if col in self.relation.filter_dict:
                    num_filter = self.relation.filter_dict[col]
                    entry.delete(0, tk.END)
                    entry.insert(0, num_filter["filterValue"])
                    pred.set(num_filter["predicate"])

                pred.grid(row=row, column=1, padx=5)
                entry.grid(row=row, column=2, padx=5)

                widgets[col] = (entry, pred)

            # ---------------- DATE ----------------
            elif "DATE" in col_type:
                pred = ttk.Combobox(frame, values=date_predicates, state="readonly", width=18)
                pred.set(date_predicates[-1])  # default: last 30 days
                if col in self.relation.filter_dict:
                    date_filter = self.relation.filter_dict[col]
                    pred.set(date_filter["filterValue"])
                pred.grid(row=row, column=1, columnspan=2, padx=5)
                widgets[col] = (None, pred)

            # Non-text columns → simple equality
            else:
                entry = ttk.Entry(frame, width=25)
                entry.grid(row=row, column=1, columnspan=2, padx=5)
                widgets[col] = (entry, None)

            row += 1

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=(15, 0))
        
        style = ttk.Style()
        
        def reset_filters():
            self.relation.on_search_field_changed(self.relation.default_search_text)
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, self.relation.default_search_text)
            self.relation.on_filter_changed(self.relation.default_filters)
            self.relation.on_search_clicked()
            self.update_table()
            popup.destroy() 

        def apply_filters(event=None):
            filters = {}
            for col, (entry, pred) in widgets.items():
                value = (None if entry is None else entry.get().strip())
                flter = get_filter_json(col, pred.get(), value)
                filters[flter["fieldName"]] = flter
            self.relation.on_filter_changed(filters)

            self.relation.curr_results = self.relation.on_search_clicked()
            self.update_table()
            popup.destroy()

        ttk.Button(button_frame, text="Apply", command=apply_filters).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Reset", command=reset_filters).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=popup.destroy).pack(side="left", padx=5)

        popup.bind("<Return>", apply_filters)
        popup.update_idletasks()

        # Popup size
        popup_width = popup.winfo_reqwidth()
        popup_height = popup.winfo_reqheight()

        # Parent widget position & size
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()

        # Calculate centered position
        x = parent_x + (parent_width // 2) - (popup_width // 2)
        y = parent_y + (parent_height // 2) - (popup_height // 2)

        popup.geometry(f"+{x}+{y}")

    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.relation.curr_results:
            self.tree.insert("", tk.END, values=[item[col] for col in self.show_columns])
        if self.relation.is_filter_default(): 
            self.configure(text=f"{self.title}")
            self.tree.configure(style="Treeview")
        else:
            self.configure(text=f"{self.title}  (Filtered)")
            self.tree.configure(style="LightGrey.Treeview")

    def on_double_click(self, event):
        selected_item = self.tree.focus()  # get selected item ID
        if not selected_item:
            return

        selected_index = self.tree.index(self.tree.selection()[0])  # numeric index
        data = self.relation.get_item(selected_index)

        self.open_update_popup(selected_item, data)

    def open_update_popup(self, item_id, data):
        if self.popup is not None and self.popup.winfo_exists() == 1:
            return
        self.popup = tk.Toplevel(self)
        popup = self.popup
        popup.title("Update Item")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)


        frame = ttk.Frame(popup, padding=20)
        frame.pack(fill="both", expand=True)

        entries = {}
        
        for i, col in enumerate(data.keys()):
            if col in self.exclude_fields_on_update:
                continue
            ttk.Label(frame, text=f"{col}:").grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(frame)
            entry.grid(row=i, column=1, pady=2, padx=5)
            entry.insert(0, data[col])  # pre-fill current value
            entries[col] = entry

        def save_changes(event=None):
            new_data = {col: entries[col].get() for col in data.keys() if col in entries}
            selected_index = self.tree.index(self.tree.selection()[0])  # numeric index
            result = run_with_error_handling(popup, self.relation.on_item_updated, selected_index, new_data)
            self.update_table()
            popup.destroy()


        def delete_item():
            selected = self.tree.selection()
            if not selected:
                return  # Nothing selected, do nothing

            index = self.tree.index(selected[0])

            # Ask user for confirmation
            confirm = messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to delete this item?",
                parent=popup
            )

            if confirm:
                # Only run deletion if user clicked 'Yes'
                result = run_with_error_handling(
                    self.master,
                    self.relation.on_item_delete_clicked,
                    index
                )

                if result["status"] == "Ok":
                    self.update_table()
                    popup.destroy()
        
        # Create an inner frame to hold both buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=len(data)+1, column=0, columnspan=2, pady=20)  # span two columns

        # Make buttons the same size
        btn_width = 12

        update_btn = ttk.Button(btn_frame, text="Update", width=btn_width, command=save_changes)
        delete_btn = ttk.Button(btn_frame, text="Delete", width=btn_width, command=delete_item)

        # Pack them side by side
        update_btn.pack(side="left")
        delete_btn.pack(side="left", padx=(5,0))  # small space between buttons


        # Center popup over parent
        popup.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")

    def search(self, event=None):
        text = self.search_entry.get()
        self.relation.on_search_field_changed(text)
        self.relation.curr_results = self.relation.on_search_clicked()
        self.update_table()

    def add(self):
        if self.popup is not None and self.popup.winfo_exists() == 1:
            return
        self.popup = tk.Toplevel(self) 
        popup = self.popup
        popup.title("Add A New Item")
        popup.resizable(False, False)
        popup.focus_set() 
        popup.attributes("-topmost", True)

        frame = ttk.Frame(popup, padding=20)
        frame.pack()

        entries = {}
        is_first_field = True
        for i, col in enumerate(DB.get_columns(self.relation.relation_name)):
            if self.create_item_columns and col not in self.create_item_columns:
                continue
            ttk.Label(frame, text=f"{col}:").grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(frame)
            if is_first_field == True:
                entry.focus_set()
                is_first_field = False
            entry.grid(row=i, column=1, pady=2, padx=5)
            entries[col] = entry

        def save_item(event=None):
            details = {col: entries[col].get() for col in self.create_item_columns}
            result = run_with_error_handling(popup, self.relation.on_create_item_clicked, details)
            if result["status"] == "Ok":
                self.update_table()
                popup.destroy() 

        ttk.Button(frame, text="Add Item", command=save_item).grid(row=len(self.show_columns)+1, column=0, columnspan=2, pady=10)
        popup.bind("<Return>", save_item)
        # ---------- Center on parent widget ----------
        popup.update_idletasks()  # calculate size

        # Parent widget position & size
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()

        # Popup size
        popup_width = popup.winfo_width()
        popup_height = popup.winfo_height()

        # Calculate position
        x = parent_x + (parent_width // 2) - (popup_width // 2)
        y = parent_y + (parent_height // 2) - (popup_height // 2)

        # Move popup without changing size
        popup.geometry(f"+{x}+{y}")

    def delete(self):
        # Ask user for confirmation
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this item?",
            parent=self
        )

        if confirm:
            selected = self.tree.selection()
            if not selected:
                return
            indexes = []
            for item in selected:
                index = self.tree.index(item)
                indexes.append(index)

            indexes.sort(reverse=True)
            for index in indexes:
                run_with_error_handling(self.master, self.relation.on_item_delete_clicked, index)
            self.update_table()

