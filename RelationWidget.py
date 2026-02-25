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
from entry_helpers import attach_datepicker, attach_listpicker, attach_fuzzy_list, attach_helper
import copy
from tkinter import filedialog, messagebox
import uuid
import registry

def generate_random_name(length=6):
    letters = string.ascii_uppercase
    digits = string.digits
    random_part = ''.join(random.choices(letters + digits, k=length))
    return f"PROD-{random_part}"

class RelationWidget(ttk.LabelFrame):
    def __init__(self, master, relation_interface, labels=[], min_width=400, min_height=200, is_view=False, exclude_fields_on_update=[], exclude_fields_on_show=[], exclude_fields_on_create=[], title="Table", padding=10, **kwargs):
        super().__init__(master, text=title, padding=padding, **kwargs)
        self.title=title
        self.relation = relation_interface
        self.all_columns = DB.get_columns(self.relation.relation_name, self.relation.db_path)
        self.all_column_types = DB.get_column_types(self.relation.relation_name, self.relation.db_path)
        self.exclude_fields_on_update = exclude_fields_on_update
        self.exclude_fields_on_show = exclude_fields_on_show
        self.update_item_columns = [col for col in self.all_columns if col not in exclude_fields_on_update] 
        self.show_columns = [col for col in self.all_columns if col not in exclude_fields_on_show]
        self.create_item_columns = [col for col in self.all_columns if col not in exclude_fields_on_create]
        self.is_view = is_view
        self.min_width = min_width
        self.min_height = min_height
        registry.register(self,labels)
        self.popup = None
        self.advance_button = None
        self.advanced_search_widgets = None
        self.search_button = None
        self.create_widgets()
        self.update_table()
        self.apply_filters_button = None

        style = ttk.Style()
        style.configure("LightGrey.Treeview",
                        background="#ADD8E6",       
                        fieldbackground="#ADD8E6",
                        bordercolor="#ADD8E6",
                        foreground="black")

        def resize_columns(tree, results):
            f = tkfont.Font()
            max_width = dict()
            padding = 10

            for col in self.all_columns:
                max_width[col] = f.measure(col + " " * padding)  # small padding

            for item in results:
                for col, val in item.items():
                    width = f.measure(str(val) + " " * padding)  # small padding
                    if width > max_width[col]:
                        max_width[col] = width

            for col in tree["columns"]:
                if col in max_width:
                    tree.column(col, width=max_width[col], stretch=False)
                    # tree.column(col, stretch=False)

            tree.column(tree["columns"][-1], stretch=True)
        resize_columns(self.tree, self.relation.curr_results)

        popup = self.create_popup(title="Advanced Search")
        popup.withdraw()
        frame = self.create_frame(popup)
        advanced_search_widgets = self.create_advanced_search_widgets(frame, self.all_columns, self.all_column_types)
        inactive_filters = copy.deepcopy(self.get_filters(advanced_search_widgets, self.all_columns, self.all_column_types))
        popup.destroy()
        self.relation.on_filter_changed(inactive_filters)
        self.relation.on_search_field_changed("")
        self.relation.set_current_filters_as_inactive()
        self.relation.set_current_filters_as_default()

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

        attach_helper(self.master, self.relation.simple_search_field, self.search_entry, self.relation.db_path, self.relation.relation_name, self.all_columns, self.all_column_types)
        
        self.search_button = ttk.Button(self.search_frame, text=self.relation.simple_search_field, command=self.search)
        self.search_button.grid(row=0, column=1, sticky="ew", padx=5)
        

        self.advance_button = ttk.Button(self.search_frame, text="Advanced Search", style="TButton")
        
        advance_btn = self.advance_button

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
        self.search_entry.bind("<Return>", lambda e: (self.search(e), self.tree.focus_force()))

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        for i in range(len(self.show_columns)-1):
            col = self.show_columns[i]
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, stretch=False)
        self.tree.heading(self.show_columns[-1], text=self.show_columns[-1], anchor="w")
        self.tree.column(self.show_columns[-1], stretch=True)

        self.results_number = tk.Label(self, text=f"Results : {len(self.relation.curr_results)}", anchor="w")
        self.results_number.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=0) 

        # Buttons Frame
        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=4, column=0, pady=5)
        if not self.is_view:
            ttk.Button(self.button_frame, text="Add", command=self.add).pack(side=tk.LEFT, padx=5)
            ttk.Button(self.button_frame, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=5)
            self.tree.bind("<Double-1>", self.on_double_click)
        ttk.Button(self.button_frame, text="Export Results", command=self.export_results).pack(side=tk.LEFT, padx=5)

    def create_popup(self, title):
        popup = tk.Toplevel(self)
        popup.title(title)
        popup.transient(self.master)
        popup.resizable(False, False)
        # popup.attributes("-topmost", True)
        popup.lift()
        return popup

    def create_frame(self, popup):
        frame = tk.Frame(popup, padx=20, pady=20)
        frame.grid(sticky="nsew")
        return frame
    
    def hold_popup(self, popup):
        def center_popup(event=None):
            if not popup or not popup.winfo_exists():
                return
            popup.update_idletasks()
            popup_width = popup.winfo_reqwidth()
            popup_height = popup.winfo_reqheight()

            parent_x = self.winfo_rootx()
            parent_y = self.winfo_rooty()
            parent_width = self.winfo_width()
            parent_height = self.winfo_height()

            x = parent_x + (parent_width // 2) - (popup_width // 2)
            y = parent_y + (parent_height // 2) - (popup_height // 2)

            popup.geometry(f"+{x}+{y}")
        center_popup()
        self.winfo_toplevel().bind("<Configure>", center_popup)
    
    def export_results(self):
        def _export():
            def ask_exclude_fields():

                result = None

                title = ""
                
                if self.popup is not None and self.popup.winfo_exists():
                    return

                self.popup = self.create_popup(title=title)
                popup = self.popup
                frame = self.create_frame(popup)

                vars_map = {}

                for col in self.show_columns:
                    var = tk.BooleanVar(value=True)
                    chk = tk.Checkbutton(frame, text=col, variable=var)
                    chk.pack(anchor="w")
                    vars_map[col] = var

                def confirm():
                    nonlocal result
                    result = [col for col, var in vars_map.items() if not var.get()]
                    popup.destroy()

                tk.Button(frame, text="Export", command=confirm).pack()
                
                self.hold_popup(popup)
                popup.wait_window()

                return result

            def ask_columns_checkbox_popup(title):
                popup = self.create_popup(title=title)

                frame = tk.Frame(popup, padx=20, pady=20)
                frame.grid(sticky="nsew")

                vars_dict = {}

                row = 0
                for col in self.show_columns:

                    var = tk.BooleanVar(value=True)  # default checked

                    chk = ttk.Checkbutton(
                        frame,
                        text=col,
                        variable=var
                    )
                    chk.grid(row=row, column=0, sticky="w", pady=2)

                    vars_dict[col] = var
                    row += 1

                result = []

                def on_confirm():
                    popup.destroy()

                def on_cancel():
                    vars_dict.clear()
                    popup.destroy()

                # Buttons
                btn_frame = tk.Frame(frame)
                btn_frame.grid(row=row, column=0, pady=(10, 0), sticky="e")

                ttk.Button(btn_frame, text="OK", command=on_confirm).pack(side="right", padx=5)
                ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right")

                
                self.hold_popup(popup)
                popup.wait_window()

                # Return unchecked columns (to exclude)
                if not vars_dict:
                    return None  # user cancelled

                excluded = [
                    col for col, var in vars_dict.items()
                    if not var.get()
                ]


                return excluded

            exclude_fields = ask_exclude_fields()
            
            if exclude_fields is None:
                return

            hash_part = uuid.uuid4().hex[:8]
            default_name = f"{self.relation.relation_name}_{hash_part}.xlsx"

            output_path = filedialog.asksaveasfilename(
                title="Save Excel File As",
                defaultextension=".xlsx",
                initialfile=default_name,
                filetypes=[("Excel Files", "*.xlsx")]
            )

            if not output_path:
                return

            self.relation.export_as_excel(
                exclude_columns=exclude_fields,
                output_path=output_path
            )

        run_with_error_handling(self, _export)


    def create_advanced_search_widgets(self, frame, columns, column_types):
        row = 0
        widgets = {}

        text_predicates = ["startswith", "contains", "endswith", "exactly"]
        number_predicates = ["equal", "not equal", "less than", "greater than", "less than or equal", "greater than or equal"]
        date_predicates = ["past 24 hours", "past week", "past 30 days", "past 6 months", "past year", "all time"]

        for col in columns:

            ttk.Label(frame, text=col).grid(row=row, column=0, sticky="e", pady=2)

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
                pred.set(date_predicates[-1])
                if col in self.relation.filter_dict:
                    date_filter = self.relation.filter_dict[col]
                    pred.set(date_filter["predicate"])
                pred.grid(row=row, column=1, columnspan=2, padx=5)
                widgets[col] = (None, pred)

            # Non-text columns → simple equality
            else:
                entry = ttk.Entry(frame, width=25)
                entry.grid(row=row, column=1, columnspan=2, padx=5)
                widgets[col] = (entry, None)
            
            attach_helper(self.master, col, entry, self.relation.db_path, self.relation.relation_name, self.all_columns, self.all_column_types)

            row += 1

        return widgets
    
    def get_filters(self, widgets, columns, column_types):
        
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
                    "past 24 hours": "-1 day",
                    "past week": "-7 days",
                    "past 30 days": "-30 days",
                    "past 6 months": "-6 months",
                    "past year": "-1 year"
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
        
        filters = {}
        for col, (entry, pred) in widgets.items():
            value = (None if entry is None else entry.get().strip())
            flter = get_filter_json(col, pred.get(), value)
            filters[flter["fieldName"]] = flter
        return filters

    # -------------------- Actions --------------------
    def advanced_search(self, advance_btn):
        if self.popup is not None and self.popup.winfo_exists():
            return
        self.popup = self.create_popup(title="Advanced Search")
        popup = self.popup
        frame = self.create_frame(popup)

        advanced_search_widgets = self.create_advanced_search_widgets(frame, self.all_columns, self.all_column_types)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(self.all_columns), column=0, columnspan=3, pady=(15, 0))

        def reset_filters():
            self.refresh()
            popup.destroy()

        def apply_filters(event=None):
            filters = self.get_filters(advanced_search_widgets, self.all_columns, self.all_column_types)
            self.relation.on_filter_changed(filters)
            self.relation.on_search_field_changed(self.relation.search_field_text)
            self.relation.on_search_clicked()
            self.update_table()
            popup.destroy()

        self.apply_filters_button = ttk.Button(button_frame, text="Apply", command=apply_filters)
        self.apply_filters_button.pack(side="left", padx=5)
        ttk.Button(button_frame, text="Reset", command=reset_filters).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=popup.destroy).pack(side="left", padx=5)

        self.hold_popup(popup)
    
    def refresh(self):
        self.relation.on_search_field_changed(self.relation.default_search_text)
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, self.relation.default_search_text)
        self.relation.on_filter_changed(self.relation.default_filters)
        self.relation.on_search_clicked()
        self.update_table()
                             
    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.relation.curr_results:
            self.tree.insert("", tk.END, values=[item[col] for col in self.show_columns])
        
        widget_status = []
        if self.relation.is_filter_active():
            widget_status.append("(Filtered)")
            self.tree.configure(style="LightGrey.Treeview")
        else:
            self.tree.configure(style="Treeview")

        self.results_number.configure(text=f"Results : {len(self.relation.curr_results)}")
        self.configure(text=f"{self.title} {" ".join(widget_status)}") 

    def on_double_click(self, event):
        selected_item = self.tree.focus()  # get selected item ID
        if not selected_item:
            return

        selected_index = self.tree.index(self.tree.selection()[0])  # numeric index
        data = self.relation.get_item(selected_index)

        self.open_update_popup(selected_item, data)

    def open_update_popup(self, item_id, data):
        if self.popup is not None and self.popup.winfo_exists():
            return
        self.popup = self.create_popup(title="Update Item")

        frame = ttk.Frame(self.popup, padding=20)
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

            attach_helper(self.master, col, entry, self.relation.db_path, self.relation.relation_name, self.all_columns, self.all_column_types)

        def save_changes(event=None):
            new_data = {col: entries[col].get() for col in data.keys() if col in entries}
            selected_index = self.tree.index(self.tree.selection()[0])  # numeric index
            result = run_with_error_handling(self.popup, self.relation.on_item_updated, selected_index, new_data)
            self.update_table()
            self.popup.destroy()


        def delete_item():
            selected = self.tree.selection()
            if not selected:
                return  # Nothing selected, do nothing

            index = self.tree.index(selected[0])

            # Ask user for confirmation
            confirm = messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to delete this item?",
                parent=self.popup
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
                    self.popup.destroy()
        
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
        self.popup.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (self.popup.winfo_width() // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (self.popup.winfo_height() // 2)
        self.popup.geometry(f"+{x}+{y}")
        
        self.hold_popup(self.popup)

    def search(self, event=None):
        text = self.search_entry.get()
        self.relation.on_search_field_changed(text)
        self.relation.curr_results = self.relation.on_search_clicked()
        self.update_table()
        self.tree.focus_set()

    def add(self):
        if self.popup is not None and self.popup.winfo_exists():
            return
        self.popup = self.create_popup(title="Add A New Item")

        frame = ttk.Frame(self.popup, padding=20)
        frame.pack()

        entries = {}
        for i, col in enumerate(self.all_columns):
            if self.create_item_columns and col not in self.create_item_columns:
                continue
            ttk.Label(frame, text=f"{col}:").grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(frame)
            attach_helper(self.master, col, entry, self.relation.db_path, self.relation.relation_name, self.all_columns, self.all_column_types)
            entry.grid(row=i, column=1, pady=2, padx=5)
            entries[col] = entry

        def save_item(event=None):
            details = {col: entries[col].get() for col in self.create_item_columns}
            result = run_with_error_handling(self.popup, self.relation.on_create_item_clicked, details)
            if result["status"] == "Ok":
                self.update_table()
                self.popup.destroy() 

        ttk.Button(frame, text="Add Item", command=save_item).grid(row=len(self.show_columns)+1, column=0, columnspan=2, pady=10)
        # ---------- Center on parent widget ----------
        self.popup.update_idletasks()  # calculate size

        # Parent widget position & size
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()

        # Popup size
        popup_width = self.popup.winfo_width()
        popup_height = self.popup.winfo_height()

        # Calculate position
        x = parent_x + (parent_width // 2) - (popup_width // 2)
        y = parent_y + (parent_height // 2) - (popup_height // 2)

        # Move popup without changing size
        self.popup.geometry(f"+{x}+{y}")
        self.hold_popup(self.popup)

    def delete(self):
        # Ask user for confirmation
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete the selected items?",
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

