import tkinter as tk
from tkinter import ttk
import DB
from RelationInterface import RelationInterface
from RelationWidget import RelationWidget
from error_handler import run_with_error_handling

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
        default_filters=[]
    )

    consumables = RelationInterface(
        relation_name="ConsumableLogs",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
    )

    non_consumables = RelationInterface(
        relation_name="NonConsumableLogs",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
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
        title="NonConsumable Logs"
    )
    right.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

def analytics_content_old(root):
    # -------------------- Grid Setup --------------------
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)   # <-- add second column

    # ---------- RelationInterface instances ----------
    outOfStockConsumables = RelationInterface(
        relation_name="OutOfStockConsumables",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
    )

    outOfStockNonConsumables = RelationInterface(
        relation_name="OutOfStockNonConsumables",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
    )

    availableConsumables = RelationInterface(
        relation_name="AvailableConsumables",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
    ) 
    
    availableNonConsumables = RelationInterface(
        relation_name="AvailableNonConsumables",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
    )

    # ---------- Left Widget ----------
    left = RelationWidget(
        root,
        outOfStockConsumables,
        is_view=True,
        title="Out Of Stock Consumables"
    )
    left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    middle = RelationWidget(
        root,
        outOfStockNonConsumables,
        exclude_fields_on_show=["TotalQuantityReceived", "TotalQuantityOpened"],
        is_view=True,
        title="Out Of Stock NonConsumables"
    )
    middle.grid(row=0, column=1, stick="nsew", padx=10, pady=10)

    # ---------- Right Widget ----------
    avcon = RelationWidget(
        root,
        availableConsumables,
        is_view=True,
        title="Available Consumables"
    )
    avcon.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    
    avNonCon = RelationWidget(
        root,
        availableNonConsumables,
        is_view=True,
        exclude_fields_on_show=["TotalQuantityReceived", "TotalQuantityOpened"],
        title="Available NonConsumables"
    )
    avNonCon.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

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
    outOfStockConsumables = RelationInterface(
        relation_name="OutOfStockConsumables",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
    )

    outOfStockNonConsumables = RelationInterface(
        relation_name="OutOfStockNonConsumables",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
    )

    availableConsumables = RelationInterface(
        relation_name="AvailableConsumables",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
    )

    availableNonConsumables = RelationInterface(
        relation_name="AvailableNonConsumables",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
    )

    reOrderList = RelationInterface(
        relation_name="ReOrderList",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[]
    )

    # ------------------ Add RelationWidgets in 2x2 grid ------------------
    left = RelationWidget(
        inner_frame,
        outOfStockConsumables,
        is_view=True,
        title="Out Of Stock Consumables"
    )

    middle = RelationWidget(
        inner_frame,
        outOfStockNonConsumables,
        exclude_fields_on_show=["TotalQuantityReceived", "TotalQuantityOpened"],
        is_view=True,
        title="Out Of Stock Non-consumables"
    )

    avcon = RelationWidget(
        inner_frame,
        availableConsumables,
        is_view=True,
        title="Available Consumables"
    )

    avNonCon = RelationWidget(
        inner_frame,
        availableNonConsumables,
        exclude_fields_on_show=["TotalQuantityReceived", "TotalQuantityOpened"],
        is_view=True,
        title="Available Non-consumables"
    )
    
    reorder = RelationWidget(
        inner_frame,
        reOrderList,
        exclude_fields_on_show=[],
        is_view=True,
        title="Re-order List"
    )
    
    left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    middle.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
    avcon.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    avNonCon.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
    reorder.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

    # Make columns expand evenly
    inner_frame.grid_columnconfigure(0, weight=1)
    inner_frame.grid_columnconfigure(1, weight=1)
    inner_frame.grid_rowconfigure(0, weight=1)
    inner_frame.grid_rowconfigure(1, weight=1)
    inner_frame.grid_rowconfigure(2, weight=1)  # for reorder row

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def resize_inner_frame(event):
        canvas.itemconfig(inner_window, width=event.width)

    canvas.bind("<Configure>", resize_inner_frame)
    canvas.bind_all("<MouseWheel>", _on_mousewheel)


def nav(root):
    DB.init_db()

    root.title("ALS Inventory App")
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

    # Add content inside tabs
    database_manager_content(database_manager_tab)
    analytics_content(analytics_tab)

    root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    run_with_error_handling(root, nav, root)
