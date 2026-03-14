import tkinter as tk
from tkinter import ttk
import DB
from RelationInterface import RelationInterface
from RelationWidget import RelationWidget
from error_handler import run_with_error_handling
import types
import sqlite3
import sys
import ctypes
import registry
import datetime
import argparse
from app_version import version

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ALS Inventory Manager")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode"
    )
    args = parser.parse_args()

    VERSION = version
    TEST_MODE = args.test
    PROD_MODE = not TEST_MODE

    if TEST_MODE:
        db_path = "./inventory.db"
    else:
        db_path = "Z:/InventoryAppData/inventory.db"

    DB.init_db(db_path, test=TEST_MODE)

    with sqlite3.connect(db_path) as conn:
        latest_deployed = DB.get_latest_app_version(conn)
        if latest_deployed < VERSION:
            DB.set_latest_app_version(conn, VERSION)

    def stop_if_instance_active():
        # Make sure one only one process exists
        mutex_name = "ALS Inventory Manager"
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183

        if last_error == ERROR_ALREADY_EXISTS:
            print("Program is already running")
            sys.exit(0)

    stop_if_instance_active()

    def non_cons_log_content(notebook, root):
        # -------------------- Main Window --------------------
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # ---------- RelationInterface instances ----------

        non_consumables = RelationInterface(
            relation_name="NonConsumableLogs",
            default_search_text="",
            order_by="Date DESC, id DESC",
            simple_search_field="ProductName",
            db_path=db_path
        )

        # ---------- InventoryTable widgets ----------

       
        non_cons_widg = RelationWidget(
            root,
            non_consumables,
            exclude_fields_on_update=["CreatedDateTime"],
            exclude_fields_on_create=["id", "CreatedDateTime"],
            title="Non-consumable Logs",
            labels=["Logs"]
        )
        
        non_cons_widg.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        def on_tab_changed(event):
            registry.destroy_all_popups()
        notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    def cons_log_content(notebook, root):
        # -------------------- Main Window --------------------
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # ---------- RelationInterface instances ----------
        consumables = RelationInterface(
            relation_name="ConsumableLogs",
            default_search_text="",
            simple_search_field="ProductName",
            order_by="DateReceived DESC, id DESC",
            db_path=db_path
        )
        consumables.on_create_item_clicked_original = consumables.on_create_item_clicked

        def create_item_quantity_times(obj, details: dict):
            """Insert a new row into the database. Returns (status, user_message, error_details)."""
            print("Hey")
            input_quantity = int(details["Quantity"])
            if input_quantity <= 0:
                raise Exception("Quantity must be > 0")

            details["Quantity"] = "1"
            columns = ", ".join(details.keys())
            placeholders = ", ".join(["?"] * len(details))
            params = list(details.values())

            for i in range(input_quantity):
                obj.on_create_item_clicked_original(details)
            obj.curr_results = obj.on_search_clicked()

        consumables.on_create_item_clicked = types.MethodType(create_item_quantity_times, consumables)

        # ---------- InventoryTable widgets ----------
        cons_widg = RelationWidget(
            root,
            consumables,
            exclude_fields_on_update=["CreatedDateTime"],
            exclude_fields_on_create=["id", "CreatedDateTime"],
            title="Consumable Logs",
            labels=["Logs"]
        )

        cons_widg.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        def on_tab_changed(event):
            registry.destroy_all_popups()
        notebook.bind("<<NotebookTabChanged>>", on_tab_changed)


    
    def product_manager_content(notebook, root):
        # -------------------- Main Window --------------------
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # ---------- RelationInterface instances ----------
        products = RelationInterface(
            relation_name="Products",
            default_search_text="",
            simple_search_field="ProductName",
            db_path=db_path
        )
        

        # ---------- InventoryTable widgets ----------
        left = RelationWidget(
            root,
            products,
            title="Products",
            labels=["Products"]
        )

        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        def on_tab_changed(event):
            registry.destroy_all_popups()
        notebook.bind("<<NotebookTabChanged>>", on_tab_changed)


    def analytics_content(notebook, root):
        # ------------------ Scrollable Canvas ------------------
        canvas = tk.Canvas(root, bg="red", highlightthickness=0)
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

        def resize_inner_frame(event):
            canvas.itemconfig(inner_window, width=event.width, height=event.height)
        canvas.bind("<Configure>", resize_inner_frame)

        # Update scroll region when inner frame changes
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner_frame.bind("<Configure>", on_frame_configure)

        # ------------------ RelationInterface instances ------------------

        dangerouslyLowRI = RelationInterface(
            relation_name="DangerouslyLow",
            default_search_text="",
            simple_search_field="ProductName",
            db_path=db_path
        )
        
        productsTotalSupplyRI = RelationInterface(
            relation_name="ProductsTotalSupply",
            default_search_text="",
            simple_search_field="ProductName",
            db_path=db_path
        )

        reorder_ri = RelationInterface(
            relation_name="ReOrderList",
            default_search_text="",
            simple_search_field="ProductName",
            db_path=db_path
        )

        consumablesReportRI = RelationInterface(
            relation_name="ConsumablesReport",
            default_search_text="",
            order_by='"Date Received" DESC, "Order" DESC',
            simple_search_field="ProductName",
            db_path=db_path
        )
        
        # ------------------ Add RelationWidgets ------------------
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        dangerouslyLow = RelationWidget(
            inner_frame,
            dangerouslyLowRI,
            labels=["Analytics"],
            min_height=int(height*0.3),
            is_view=True,
            title="Consumables/Non-consumables"
        )

        productsTotalSupply = RelationWidget(
            inner_frame,
            productsTotalSupplyRI,
            labels=["Analytics"],
            min_height=int(height*0.3),
            is_view=True,
            title="Consumables/Non-consumables"
        )
        
        reorder = RelationWidget(
            inner_frame,
            reorder_ri,
            labels=["Analytics"],
            min_height=int(height*0.3),
            exclude_fields_on_show=[],
            is_view=True,
            title="Consumables/Non-consumables"
        )

        consumablesReport = RelationWidget(
            inner_frame,
            consumablesReportRI,
            labels=["Analytics"],
            min_height=int(height*0.3),
            exclude_fields_on_show=[],
            is_view=True,
            title="Consumables"
        )

        # -------- Widgets -----------
        low_supply_header_value = len(reorder_ri.curr_results)
        
        # Top header frame
        top_header_frame = tk.Frame(inner_frame)
        top_header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0))
        top_header_frame.grid_columnconfigure(0, weight=1)  # Label expands to left

        # Last Updated label (starts empty)
        last_updated_label = tk.Label(
            top_header_frame,
            text="",
            font=("Segoe UI", 10, "italic"),
            fg="gray"
        )
        last_updated_label.grid(row=0, column=1, sticky="e", padx=(10, 0))
        now = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
        last_updated_label.config(text=f"Last Refresh: {now}")

        def refresh_button():
            registry.refresh(["Analytics"])
            now = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
            last_updated_label.config(text=f"Last Refresh: {now}")

        refresh_button = tk.Button(top_header_frame, text="Refresh Analytics", command=refresh_button)
        refresh_button.grid(row=0, column=2, sticky="e")

         # Low Supply label
        reorder_header = tk.Label(
            inner_frame,
            text=f"Low ({low_supply_header_value})",
            font=("Segoe UI", 16, "bold")
        )

        dangerously_low_header = tk.Label(
            inner_frame,
            text=f"Dangerously Low (Unknown)",
            font=("Segoe UI", 14, "bold")
        )

        all_header = tk.Label(
            inner_frame,
            text="All",
            font=("Segoe UI", 14, "bold")
        ) 

        consumables_report_header = tk.Label(
            inner_frame,
            text="Consumables Report",
            font=("Segoe UI", 14, "bold")
        )
        
        reorder_ri.on_search_clicked_original = reorder_ri.on_search_clicked
        def on_low_supply_tables_update():
            out = reorder_ri.on_search_clicked_original() 
            if reorder_ri.is_filter_equal(reorder_ri.default_filters):
                reorder_header.configure(text=f"Low ({str(len(reorder_ri.curr_results))})")
            return out 
        reorder_ri.on_search_clicked = on_low_supply_tables_update
    

        dangerouslyLowRI.on_search_clicked_original = dangerouslyLowRI.on_search_clicked
        def on_danger_low_tables_update():
            out = dangerouslyLowRI.on_search_clicked_original() 
            if dangerouslyLowRI.is_filter_equal(dangerouslyLowRI.default_filters):
                dangerously_low_header.configure(text=f"Dangerously Low ({str(len(dangerouslyLowRI.curr_results))})")
            return out 
        dangerouslyLowRI.on_search_clicked = on_danger_low_tables_update
        
        dangerously_low_header.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0))
        dangerouslyLow.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(5,20))

        reorder_header.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0))
        reorder.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=(5, 20))

        all_header.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 0))
        productsTotalSupply.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        consumables_report_header.grid(row=6, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 0))
        consumablesReport.grid(row=7, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_columnconfigure(1, weight=1)

        for i in range(7):
            inner_frame.grid_rowconfigure(i, weight=1)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def resize_inner_frame(event):
            canvas.itemconfig(inner_window, width=event.width)


        def on_tab_changed(event):
            registry.destroy_popups(["Database"])
        notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
        canvas.bind("<Configure>", resize_inner_frame)
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        
    def nav(root):

        root.title("ALS Inventory Manager")
        root.geometry("1200x700")

         # NOTEBOOK in row 1 (below the warning)
        notebook = ttk.Notebook(root)
        notebook.grid(row=1, column=0, sticky="nsew")  # fill space

        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Create frames (each tab needs a frame)
        analytics_tab = ttk.Frame(notebook)
        cons_log_tab = ttk.Frame(notebook)
        non_cons_log_tab = ttk.Frame(notebook)
        product_manager_tab = ttk.Frame(notebook)
        
        # Add tabs to notebook
        notebook.add(analytics_tab, text="Analytics & Reporting")
        notebook.add(cons_log_tab, text="Consumable Logs")
        notebook.add(non_cons_log_tab, text="Non-consumable Logs")
        notebook.add(product_manager_tab, text="Products")

        # Initial load
        cons_log_content(notebook, cons_log_tab)
        non_cons_log_content(notebook, non_cons_log_tab)
        analytics_content(notebook, analytics_tab)
        product_manager_content(notebook, product_manager_tab)
        
        registry.refresh_all(exceptions=["Early"])


    root = tk.Tk()
    # root.maxsize(width=1920, height=1080)
    style = ttk.Style()

    run_with_error_handling(root, nav, root)

    def show_warning_if_app_outdated():
        if latest_deployed is not None and latest_deployed > VERSION:
            warning_frame = tk.Frame(root, bg="#8B0000")
            warning_frame.grid(row=0, column=0, sticky="ew")  # fill horizontally

            tk.Label(
                warning_frame,
                text=f"This application is outdated (Ver. {VERSION}). Some features may not work properly. Please grab the latest one.",
                bg="#8B0000",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                pady=8
            ).pack(fill="x")            
    registry.on_table_update(show_warning_if_app_outdated) 
    show_warning_if_app_outdated()

    root.mainloop()

