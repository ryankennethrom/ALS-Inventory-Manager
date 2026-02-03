import tkinter as tk
from tkinter import ttk, messagebox
from RelationInterface import RelationInterface
import DB
import random
import string

# -------------------- Database --------------------
DB.init_db()

# Define the columns for Products
columns = ["ProductName", "AlsItem", "UnitPrice", "UnitOfMeasure", "ItemDescription",
           "Station", "IsConsumable", "Alert", "VendorItem", "Vendor", "PO"]

# Create RelationInterface for Products table
products = RelationInterface(
    relation_name="Products",
    default_search_text="",
    simple_search_field="ProductName",
    default_filters=[],
    columns=columns
)

# -------------------- Helper Functions --------------------
def generate_random_name(length=6):
    letters = string.ascii_uppercase
    digits = string.digits
    random_part = ''.join(random.choices(letters + digits, k=length))
    return f"PROD-{random_part}"

# -------------------- Modular Inventory Table --------------------
class InventoryTable(ttk.LabelFrame):
    def __init__(
        self,
        master,
        relation_interface,
        title="Table",
        width=1000,
        height=500,
        padding=10,
        **kwargs
    ):
        super().__init__(
            master,
            text=title,
            padding=padding,
            **kwargs
        )

        self.relation = relation_interface
        self.width = width
        self.height = height
        self.columns = relation_interface.columns

        self.grid_propagate(False)
        self.create_widgets()
        self.update_table()

    def create_widgets(self):
        # -------------------- Configure internal grid --------------------
        self.grid_rowconfigure(1, weight=1)   # Treeview row grows
        self.grid_columnconfigure(0, weight=1)

        # -------------------- Search Frame --------------------
        self.search_frame = tk.Frame(self, bg="#e0e0e0", padx=5, pady=5)
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.search_frame.grid_columnconfigure(0, weight=1)

        # Search Entry
        self.search_entry = ttk.Entry(self.search_frame, width=30)
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_entry.bind("<Return>", self.search)

        # Search Button
        self.search_button = ttk.Button(
            self.search_frame,
            text="Search",
            command=self.search
        )
        self.search_button.grid(row=0, column=1, padx=5)

        # -------------------- Tree Frame --------------------
        self.tree_frame = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        self.tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        # Scrollbars
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree_scroll_y.grid(row=0, column=1, sticky="ns")
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.grid(row=1, column=0, sticky="ew")

        # Treeview style
        style = ttk.Style()
        style.configure("Treeview",
                        background="#f9f9f9",
                        foreground="#333333",
                        rowheight=25,
                        fieldbackground="#f9f9f9")
        style.map("Treeview", background=[("selected", "#3399ff")], foreground=[("selected", "#ffffff")])

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.columns,
            show="headings",
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set,
            style="Treeview"
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        # -------------------- Buttons Frame --------------------
        self.button_frame = tk.Frame(self, bg="#e0e0e0", padx=5, pady=5)
        self.button_frame.grid(row=2, column=0, pady=(10, 0))

        ttk.Button(self.button_frame, text="Add", command=self.add_popup).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Export", command=lambda: self.relation.export_as_excel("Products.xlsx")).pack(side=tk.LEFT, padx=5)

    # -------------------- Actions --------------------
    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.relation.curr_results:
            self.tree.insert("", tk.END, values=[item[col] for col in self.columns])

    def search(self, event=None):
        search_text = self.search_entry.get()
        self.relation.on_search_field_changed(search_text)
        self.relation.curr_results = self.relation.on_search_clicked()
        self.update_table()
    
    def add_popup(self):
        """Open a popup to enter new product details with natural size."""
        popup = tk.Toplevel(self)
        popup.title("Add New Item")
        popup.transient(self)  # Keep on top of parent
        popup.grab_set()       # Modal window

        # Frame for padding
        frame = tk.Frame(popup, padx=0, pady=0)
        frame.pack(fill="both", expand=True)

        entries = {}

        # Create labels and entries for each column
        for i, col in enumerate(self.columns):
            tk.Label(frame, text=col, anchor="w").grid(row=i, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(frame, width=25)
            entry.grid(row=i, column=1, pady=5, padx=5)
            entries[col] = entry

            # Prefill some defaults
            if col == "ProductName":
                entry.insert(0, generate_random_name())
            elif col == "UnitPrice":
                entry.insert(0, "0.0")
            elif col in ["IsConsumable", "Alert"]:
                entry.insert(0, "0")

        # Centered Save button
        def save_item():
            details = {col: entries[col].get() for col in self.columns}
            try:
                details["UnitPrice"] = float(details["UnitPrice"])
            except ValueError:
                details["UnitPrice"] = 0.0
            for field in ["IsConsumable", "Alert"]:
                try:
                    details[field] = int(details[field])
                except ValueError:
                    details[field] = 0

            self.relation.on_create_item_clicked(details)
            self.update_table()
            popup.destroy()

        save_button = ttk.Button(frame, text="Save", command=save_item)
        save_button.grid(row=len(self.columns), column=0, columnspan=2, pady=10)

        # Wrap content and center on screen
        popup.update_idletasks()  # calculate sizes
        width = frame.winfo_reqwidth() + 40
        height = frame.winfo_reqheight() + 40
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.resizable(False, False)  # Make size fixed
    
    def add_popup_copy(self):
        """Open a popup to enter new product details."""
        popup = tk.Toplevel(self)
        popup.title("Add New Product")
        popup.geometry("400x500")
        popup.transient(self)
        popup.grab_set()

        entries = {}

        # Scrollable frame
        canvas = tk.Canvas(popup)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        # Entry fields for each column
        for i, col in enumerate(self.columns):
            tk.Label(scroll_frame, text=col).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            entry = ttk.Entry(scroll_frame)
            entry.grid(row=i, column=1, pady=3, padx=5)
            entries[col] = entry

            # Pre-fill some fields
            if col == "ProductName":
                entry.insert(0, generate_random_name())
            elif col == "UnitPrice":
                entry.insert(0, "0.0")
            elif col in ["IsConsumable", "Alert"]:
                entry.insert(0, "0")

        def save_item():
            details = {col: entries[col].get() for col in self.columns}
            # Convert numeric fields
            try:
                details["UnitPrice"] = float(details["UnitPrice"])
            except ValueError:
                details["UnitPrice"] = 0.0
            for field in ["IsConsumable", "Alert"]:
                try:
                    details[field] = int(details[field])
                except ValueError:
                    details[field] = 0

            self.relation.on_create_item_clicked(details)
            self.update_table()
            popup.destroy()

        ttk.Button(scroll_frame, text="Save", command=save_item).grid(
            row=len(self.columns), column=0, columnspan=2, pady=10
        )

    def delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No item selected")
            return
        index = self.tree.index(selected[0])
        self.relation.on_item_delete_clicked(index)
        self.update_table()

# -------------------- Main Window --------------------
root = tk.Tk()
root.title("Modular Inventory Manager")
root.geometry("1200x700")

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

left = InventoryTable(root, products, title="Products", width=550, height=600)
left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

right = InventoryTable(root, products, title="Consumable Inventory", width=550, height=600)
right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

root.mainloop()
