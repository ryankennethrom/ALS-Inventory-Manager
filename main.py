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

if __name__ == "__main__":
    TEST_MODE = "--test" in sys.argv
    PROD_MODE = not TEST_MODE
    
    if TEST_MODE:
        db_path = "./inventory.db"
    else:
        db_path = "Z:/InventoryAppData/inventory.db"
    
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
    
   

    def database_manager_content(notebook, root):
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
            db_path=db_path
        )

        # products.on_batch_create_clicked("test.xlsm", "Product_Manager")

        consumables = RelationInterface(
            relation_name="ConsumableLogs",
            default_search_text="",
            simple_search_field="ProductName",
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

        non_consumables = RelationInterface(
            relation_name="NonConsumableLogs",
            default_search_text="",
            simple_search_field="ProductName",
            db_path=db_path
        )

        # ---------- InventoryTable widgets ----------
        left = RelationWidget(
            root,
            products,
            title="Products"
        )

        middle = RelationWidget(
            root,
            consumables,
            exclude_fields_on_update=["CreatedDateTime"],
            exclude_fields_on_create=["id", "CreatedDateTime"],
            title="Consumable Logs"
        )
        
        right = RelationWidget(
            root,
            non_consumables,
            exclude_fields_on_update=["CreatedDateTime"],
            exclude_fields_on_create=["id", "CreatedDateTime"],
            title="Non-consumable Logs"
        )
        non_consumables.filter_dict["Date"]["predicate"] = "past 30 days"
        right.advance_button.invoke()
        right.apply_filters_button.invoke()
        non_consumables.set_current_filters_as_default()
        
        consumables.filter_dict["DateReceived"]["predicate"] = "past 30 days"
        middle.advance_button.invoke()
        middle.apply_filters_button.invoke()
        consumables.set_current_filters_as_default()

        middle.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        right.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        
        registry.register(left, ["Database"])
        registry.register(middle, ["Database", "Early"])
        registry.register(right, ["Database", "Early"])

    def analytics_content(notebook, root):
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
            db_path=db_path
        )

        outOfStockNonConsumablesRI = RelationInterface(
            relation_name="OutOfStockNonConsumables",
            default_search_text="",
            simple_search_field="ProductName",
            db_path=db_path
        )

        availableConsumablesRI = RelationInterface(
            relation_name="AvailableConsumables",
            default_search_text="",
            simple_search_field="ProductName",
            db_path=db_path
        )

        availableNonConsumablesRI = RelationInterface(
            relation_name="AvailableNonConsumables",
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
        low_supply_header_value = len(reorder_ri.curr_results)
        out_of_stock_header_value = len(outOfStockConsumablesRI.curr_results)+len(outOfStockNonConsumablesRI.curr_results)
        
        # Top header frame
        top_header_frame = tk.Frame(inner_frame)
        top_header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0))
        top_header_frame.grid_columnconfigure(0, weight=1)  # Label expands to left

        # Low Supply label
        reorder_header = tk.Label(
            top_header_frame,
            text=f"Low Supply ({low_supply_header_value})",
            font=("Segoe UI", 16, "bold")
        )
        reorder_header.grid(row=0, column=0, sticky="w")

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

        def on_tab_changed(event):
            selected_tab_id = notebook.select()
            selected_frame = notebook.nametowidget(selected_tab_id)

            if selected_frame == root:
                refresh_button.invoke()

        out_of_stock_header = tk.Label(
            inner_frame,
            text=f"Out Of Stock ({str(out_of_stock_header_value)})",
            font=("Segoe UI", 14, "bold")
        )

        available_header = tk.Label(
            inner_frame,
            text="Available",
            font=("Segoe UI", 14, "bold")
        )
        
        reorder_ri.on_search_clicked_original = reorder_ri.on_search_clicked
        def on_low_supply_tables_update():
            out = reorder_ri.on_search_clicked_original() 
            if reorder_ri.is_filter_equal(reorder_ri.default_filters):
                reorder_header.configure(text=f"Low Supply ({str(len(reorder_ri.curr_results))})")
            return out 
        reorder_ri.on_search_clicked = on_low_supply_tables_update

        out_of_stock_values = {
                "consumables": len(outOfStockConsumablesRI.curr_results),
                "nonconsumables": len(outOfStockNonConsumablesRI.curr_results),
        }
     
        def on_out_of_stock_tables_update(updating_ri):
            out = updating_ri.on_search_clicked_original()
            con_ri = outOfStockConsumablesRI
            noncon_ri = outOfStockNonConsumablesRI
            if con_ri.is_filter_equal(con_ri.default_filters):
                out_of_stock_values["consumables"] = len(con_ri.curr_results)
            if noncon_ri.is_filter_equal(noncon_ri.default_filters):
                out_of_stock_values["nonconsumables"] = len(noncon_ri.curr_results)
            out_of_stock_header.configure(text=f"Out Of Stock ({str(out_of_stock_values["consumables"]+out_of_stock_values["nonconsumables"])})")
            return out

        outOfStockConsumablesRI.on_search_clicked_original = outOfStockConsumablesRI.on_search_clicked
        outOfStockNonConsumablesRI.on_search_clicked_original = outOfStockNonConsumablesRI.on_search_clicked
        
        outOfStockConsumablesRI.on_search_clicked = types.MethodType(on_out_of_stock_tables_update, outOfStockConsumablesRI)
        outOfStockNonConsumablesRI.on_search_clicked = types.MethodType(on_out_of_stock_tables_update, outOfStockNonConsumablesRI)

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

        registry.register(availableConsumables, ["Analytics"])
        registry.register(availableNonConsumables, ["Analytics"])
        registry.register(outOfStockConsumables, ["Analytics"]) 
        registry.register(outOfStockNonConsumables, ["Analytics"])
        registry.register(reorder, ["Analytics"])


    def nav(root):
        DB.init_db(db_path)

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
        analytics_content(notebook, analytics_tab)
        database_manager_content(notebook, database_manager_tab)
        
        registry.refresh_all(exceptions=["Early"])


    root = tk.Tk()
    style = ttk.Style()
    run_with_error_handling(root, nav, root)
    root.lift()
    root.focus_force()
    root.mainloop()

