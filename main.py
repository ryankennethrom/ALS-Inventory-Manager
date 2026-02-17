import tkinter as tk
from tkinter import ttk
import DB
from RelationInterface import RelationInterface
from RelationWidget import RelationWidget
from error_handler import run_with_error_handling
import types
import sqlite3

def create_item_quantity_times(obj, details: dict):
        """Insert a new row into the database. Returns (status, user_message, error_details)."""
        obj.validate_date_inputs(details)
        
        input_quantity = int(details["Quantity"])
        if input_quantity <= 0:
            raise Exception("Quantity must be > 0")

        details["Quantity"] = "1"
        columns = ", ".join(details.keys())
        placeholders = ", ".join(["?"] * len(details))
        params = list(details.values())
        
        for i in range(input_quantity):
            query = f"INSERT INTO {obj.relation_name} ({columns}) VALUES ({placeholders})"
            with sqlite3.connect(obj.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
    
        obj.curr_results = obj.on_search_clicked()

def database_manager_content(root):
    # -------------------- Main Window --------------------
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_columnconfigure(2, weight=1)


    # ---------- RelationInterface instances ----------
    products = RelationInterface(
        relation_name="Products",
        default_search_text="",
        simple_search_field="ProductName",
    )

    consumables = RelationInterface(
        relation_name="ConsumableLogs",
        default_search_text="",
        simple_search_field="ProductName",
    )

    consumables.on_create_item_clicked = types.MethodType(create_item_quantity_times, consumables)

    non_consumables = RelationInterface(
        relation_name="NonConsumableLogs",
        default_search_text="",
        simple_search_field="ProductName",
    )

    # ---------- InventoryTable widgets ----------
    left = RelationWidget(
        root,
        products,
        title="Products"
    )
    left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    middle = RelationWidget(
        root,
        consumables,
        exclude_fields_on_update=["CreatedDateTime"],
        exclude_fields_on_create=["id", "CreatedDateTime"],
        title="Consumable Logs"
    )
    middle.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    right = RelationWidget(
        root,
        non_consumables,
        exclude_fields_on_update=["CreatedDateTime"],
        exclude_fields_on_create=["id", "CreatedDateTime"],
        title="Non-consumable Logs"
    )
    right.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

def analytics_content(root):
    # ------------------ Scrollable Canvas ------------------
    canvas = tk.Canvas(root)
    v_scroll = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)

    canvas.grid(row=0, column=0, sticky="nsew")
    v_scroll.grid(row=0, column=1, sticky="ns")

    # Make canvas expand with window
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # ------------------ Inner Frame ------------------
    inner_frame = tk.Frame(canvas)
    inner_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    # Update scroll region when inner frame changes
    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    inner_frame.bind("<Configure>", on_frame_configure)

    # ------------------ RelationInterface instances ------------------
    outOfStockConsumablesRI = RelationInterface(
        relation_name="OutOfStockConsumables",
        default_search_text="",
        simple_search_field="ProductName",
    )

    outOfStockNonConsumablesRI = RelationInterface(
        relation_name="OutOfStockNonConsumables",
        default_search_text="",
        simple_search_field="ProductName",
    )

    availableConsumablesRI = RelationInterface(
        relation_name="AvailableConsumables",
        default_search_text="",
        simple_search_field="ProductName",
    )

    availableNonConsumablesRI = RelationInterface(
        relation_name="AvailableNonConsumables",
        default_search_text="",
        simple_search_field="ProductName",
    )

    reorder_ri = RelationInterface(
        relation_name="ReOrderList",
        default_search_text="",
        simple_search_field="ProductName",
    )

    # ------------------ Add RelationWidgets in 2x2 grid ------------------
    outOfStockConsumables = RelationWidget(
        inner_frame,
        outOfStockConsumablesRI,
        is_view=True,
        title="Consumables"
    )

    outOfStockNonConsumables = RelationWidget(
        inner_frame,
        outOfStockNonConsumablesRI,
        exclude_fields_on_show=["TotalQuantityReceived", "TotalQuantityOpened"],
        is_view=True,
        title="Non-consumables"
    )

    availableConsumables = RelationWidget(
        inner_frame,
        availableConsumablesRI,
        is_view=True,
        title="Consumables"
    )

    availableNonConsumables = RelationWidget(
        inner_frame,
        availableNonConsumablesRI,
        exclude_fields_on_show=["TotalQuantityReceived", "TotalQuantityOpened"],
        is_view=True,
        title="Non-consumables"
    )
    
    reorder = RelationWidget(
        inner_frame,
        reorder_ri,
        exclude_fields_on_show=[],
        is_view=True,
        title="Consumables/Non-consumables"
    )

    # -------- Widgets -----------
    reorder_header = tk.Label(
        inner_frame,
        text=f"Low Supply {"(" + str(len(reorder_ri.curr_results)) + ")"}",
        font=("Segoe UI", 16, "bold")
    )

    out_of_stock_header = tk.Label(
        inner_frame,
        text=f"Out Of Stock {"(" + str(len(outOfStockConsumablesRI.curr_results)+len(outOfStockNonConsumablesRI.curr_results)) + ")"}",
        font=("Segoe UI", 14, "bold")
    )

    available_header = tk.Label(
        inner_frame,
        text="Available",
        font=("Segoe UI", 14, "bold")
    )

    # Headers
    reorder_header.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0))
    reorder.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(5, 20))

    out_of_stock_header.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0))
    outOfStockConsumables.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
    outOfStockNonConsumables.grid(row=3, column=1, sticky="nsew", padx=10, pady=10)

    available_header.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 0))
    availableConsumables.grid(row=5, column=0, sticky="nsew", padx=10, pady=10)
    availableNonConsumables.grid(row=5, column=1, sticky="nsew", padx=10, pady=10)
    

    inner_frame.grid_columnconfigure(0, weight=1)
    inner_frame.grid_columnconfigure(1, weight=1)

    for i in range(6):
        inner_frame.grid_rowconfigure(i, weight=1)
    
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def resize_inner_frame(event):
        canvas.itemconfig(inner_window, width=event.width)

    canvas.bind("<Configure>", resize_inner_frame)
    canvas.bind_all("<MouseWheel>", _on_mousewheel)


def nav(root):
    DB.init_db()

    root.title("ALS Inventory Manager")
    root.geometry("1200x700")

    # Create Notebook (tab container)
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Create frames (each tab needs a frame)
    analytics_tab = ttk.Frame(notebook)
    database_manager_tab = ttk.Frame(notebook)
    
    # Add tabs to notebook
    notebook.add(analytics_tab, text="Analytics")
    notebook.add(database_manager_tab, text="Database Manager")

    # Initial load
    analytics_content(analytics_tab)
    database_manager_content(database_manager_tab)

    # ---------------- RELOAD HANDLER ----------------
    def on_tab_changed(event):
        selected_tab_id = notebook.select()
        selected_frame = notebook.nametowidget(selected_tab_id)

        # Clear tab contents
        for child in selected_frame.winfo_children():
            child.destroy()

        # Reload correct content
        if selected_frame == analytics_tab:
            analytics_content(analytics_tab)

        elif selected_frame == database_manager_tab:
            database_manager_content(database_manager_tab)

    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    run_with_error_handling(root, nav, root)
