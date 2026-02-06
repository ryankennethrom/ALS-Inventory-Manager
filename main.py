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

        # Regular Search button
        ttk.Button(self.search_frame, text="Search", command=self.search).grid(row=0, column=1, padx=5)

        # Advanced Search button
        ttk.Button(self.search_frame, text="Advanced Search", command=self.advanced_search).grid(row=0, column=2, padx=5)

        # Make the entry expand to fill remaining space
        self.search_frame.grid_columnconfigure(0, weight=1)
        
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
        self.tree.bind("<Double-1>", self.on_double_click)

    # -------------------- Actions --------------------
    def advanced_search(self):
        popup = tk.Toplevel(self)
        popup.title("Advanced Search")
        popup.resizable(False, False)

        frame = ttk.Frame(popup, padding=20)
        frame.pack(fill="both", expand=True)

        # Create an entry for each column
        entries = {}
        for i, col in enumerate(DB.get_columns(self.relation.relation_name)):
            if col in self.exclude_fields_on_show:
                continue
            ttk.Label(frame, text=f"{col}:").grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(frame)
            entry.grid(row=i, column=1, pady=2, padx=5)
            entries[col] = entry

        def apply_filters():
            filter_values = {col: entries[col].get() for col in entries.keys() if entries[col].get().strip()}
            self.relation.on_filter_changed(filter_values)
            self.relation.curr_results = self.relation.on_search_clicked()
            self.update_table()
            popup.destroy()

        ttk.Button(frame, text="Apply", command=apply_filters).grid(row=len(entries)+1, column=0, columnspan=2, pady=10)

        # Center popup over the widget
        popup.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")

    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.relation.curr_results:
            self.tree.insert("", tk.END, values=[item[col] for col in self.show_columns])
    
    def update_item(self, item_index: int, new_data: dict):
        """
        Update a row in the table from the InventoryWidget GUI.
        Delegates to RelationInterface.on_item_updated()
        """
        try:
            self.relation.on_item_updated(item_index, new_data)
        except ValueError as e:
            tk.messagebox.showerror("Update Error", str(e))
    
    def on_double_click(self, event):
        selected_item = self.tree.focus()  # get selected item ID
        if not selected_item:
            return

        values = self.tree.item(selected_item, "values")
        # Assuming your tree columns match your table columns
        columns = DB.get_columns(self.relation.relation_name)  # or your list of columns
        data = dict(zip(columns, values))

        self.open_update_popup(selected_item, data)

    def open_update_popup(self, item_id, data):
        popup = tk.Toplevel(self)
        popup.title("Update Item")
        popup.resizable(False, False)
        
        frame = ttk.Frame(popup, padding=20)
        frame.pack(fill="both", expand=True)

        entries = {}
        for i, col in enumerate(data.keys()):
            ttk.Label(frame, text=f"{col}:").grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(frame)
            entry.grid(row=i, column=1, pady=2, padx=5)
            entry.insert(0, data[col])  # pre-fill current value
            entries[col] = entry

        def save_changes():
            new_data = {col: entries[col].get() for col in data.keys()}
            selected_index = self.tree.index(self.tree.selection()[0])  # numeric index
            self.update_item(selected_index, new_data)
            self.update_table()
            popup.destroy()

        ttk.Button(frame, text="Save", command=save_changes).grid(
            row=len(data)+1, column=0, columnspan=2, pady=10
        )

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
        selected = self.tree.selection()
        if not selected:
            return
        index = self.tree.index(selected[0])
        self.relation.on_item_delete_clicked(index)
        self.update_table()

# -------------------- Main Window --------------------
root = tk.Tk()
root.title("Triple Inventory Manager")
root.geometry("1800x700")  # wider window for 3 columns

# Configure three columns
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)

# Initialize DB
DB.init_db()

# ---------- RelationInterface instances ----------
products = RelationInterface(
    relation_name="Products",
    default_search_text="",
    simple_search_field="ProductName",
    default_filters=[]
)

consumables = RelationInterface(
    relation_name="ConsumableLogs",
    default_search_text="",
    simple_search_field="DateReceivedIni",
    default_filters=[]
)

non_consumables = RelationInterface(
    relation_name="NonConsumableLogs",
    default_search_text="",
    simple_search_field="Date",
    default_filters=[]
)

# ---------- InventoryTable widgets ----------
left = InventoryTable(
    root,
    products,
    title="Products"
)
left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

middle = InventoryTable(
    root,
    consumables,
    exclude_fields_on_show=["ExpiryDate"],
    exclude_fields_on_create=["id"],
    title="Consumables"
)
middle.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

right = InventoryTable(
    root,
    non_consumables,
    exclude_fields_on_create=["id"],
    title="Non-Consumables"
)
right.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

root.mainloop()
