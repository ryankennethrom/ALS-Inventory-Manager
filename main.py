import tkinter as tk
from tkinter import ttk
import DB
from RelationInterface import RelationInterface
import random
import string

def generate_random_name(length=6):
    letters = string.ascii_uppercase
    digits = string.digits
    random_part = ''.join(random.choices(letters + digits, k=length))
    return f"PROD-{random_part}"

class InventoryTable(ttk.LabelFrame):
    def __init__(self, master, relation_interface, exclude_fields_on_show=[], exclude_fields_on_create=[], title="Table", padding=10, **kwargs):
        super().__init__(master, text=title, padding=padding, **kwargs)
        self.relation = relation_interface
        self.exclude_fields_on_show = exclude_fields_on_show
        self.show_columns = [col for col in DB.get_columns(self.relation.relation_name) if col not in exclude_fields_on_show]
        self.create_item_columns = [col for col in DB.get_columns(self.relation.relation_name) if col not in exclude_fields_on_create]
        self.create_widgets()
        self.update_table()

    def create_widgets(self):
        # Configure internal grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Search Frame
        self.search_frame = ttk.Frame(self)
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.search_entry = ttk.Entry(self.search_frame)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=5)
        self.search_entry.bind("<Return>", self.search)
        ttk.Button(self.search_frame, text=f"Search {self.relation.simple_search_field}", command=self.search).grid(row=0, column=1, padx=5)

        # Tree Frame
        self.tree_frame = tk.Frame(self, bd=1, relief="solid", width=500)
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
        self.button_frame.grid(row=2, column=0, pady=5)
        ttk.Button(self.button_frame, text="Add", command=self.add).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Export", command=lambda: self.relation.export_as_excel(exclude_columns=self.exclude_fields_on_show, output_path=f"{self.relation.relation_name}.xlsx")).pack(side=tk.LEFT, padx=5)

    # -------------------- Actions --------------------
    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.relation.curr_results:
            self.tree.insert("", tk.END, values=[item[col] for col in self.show_columns])

    def search(self, event=None):
        text = self.search_entry.get()
        self.relation.on_search_field_changed(text)
        self.relation.curr_results = self.relation.on_search_clicked()
        self.update_table()

    def add(self):
        popup = tk.Toplevel(self)
        popup.title("Add New Item")
        popup.resizable(False, False)
        frame = ttk.Frame(popup, padding=20)
        frame.pack()

        entries = {}
        for i, col in enumerate(DB.get_columns(self.relation.relation_name)):
            if self.create_item_columns and col not in self.create_item_columns:
                continue
            ttk.Label(frame, text=f"{col}:").grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(frame)
            entry.grid(row=i, column=1, pady=2, padx=5)
            entries[col] = entry

        def save_item():
            details = {col: entries[col].get() for col in self.create_item_columns}
            self.relation.on_create_item_clicked(details)
            self.update_table()
            popup.destroy()

        ttk.Button(frame, text="Save", command=save_item).grid(row=len(self.show_columns)+1, column=0, columnspan=2, pady=10)

    def delete(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = self.tree.index(selected[0])
        self.relation.on_item_delete_clicked(index)
        self.update_table()

# -------------------- Main Window --------------------
root = tk.Tk()
root.title("Dual Inventory Manager")
root.geometry("1200x700")

# Configure two columns
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

DB.init_db()


# RelationInterface instances
products = RelationInterface(
    relation_name="Products",
    default_search_text="",
    simple_search_field="ProductName",
    default_filters=[],
)


# Left widget
left = InventoryTable(
        root, 
        products, 
        title="Products"
)
left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

# RelationInterface instances
consumables = RelationInterface(
    relation_name="ConsumableLogs",
    default_search_text="",
    simple_search_field="DateReceivedIni",
    default_filters=[],
)

# Right widget (reuse same table for demo)
right = InventoryTable(
        root, 
        consumables,
        exclude_fields_on_show=["ExpiryDate"],
        exclude_fields_on_create=["id"], 
        title="Consumables"
        )
right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

root.mainloop()
