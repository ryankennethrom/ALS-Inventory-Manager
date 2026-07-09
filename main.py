import tkinter as tk
from tkinter import ttk
import DB
from Application import Application
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
import tkinter.font as tkfont
from PIL import Image, ImageDraw, ImageFont, ImageTk
from entry_helpers import attach_helper
import entry_helpers
from tkinter import messagebox
import pyautogui
from datetime import date
import subprocess
import os
from relation_widget_builder import RelationWidgetBuilder
from titled_grids_builder import TitledGridsBuilder
from override_utils import override_object_function
from stock_verify_action import StockVerifyAction

def create_consumables_table(parent):
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
            parent,
            consumables,
            exclude_fields_on_update=["CreatedDateTime"],
            exclude_fields_on_create=["id", "CreatedDateTime"],
            title="Consumable Logs",
            labels=["Logs", "Consumables Only"]
        )

        return cons_widg, consumables

def create_non_consumables_table(parent):
        non_consumables = RelationInterface(
            relation_name="NonConsumableLogs",
            default_search_text="",
            order_by="Date DESC, id DESC",
            simple_search_field="ProductName",
            db_path=db_path
        )

        # ---------- InventoryTable widgets ----------


        non_cons_widg = RelationWidget(
            parent,
            non_consumables,
            exclude_fields_on_update=["CreatedDateTime"],
            exclude_fields_on_create=["id", "CreatedDateTime"],
            title="Non-consumable Logs",
            labels=["Logs", "Nonconsumables Only"]
        )

        return non_cons_widg, non_consumables

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="ALS Inventory Manager")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode"
    )
    args = parser.parse_args()

    VERSION = version
    BackupFolderName = "VersionHistory"
    TEST_MODE = args.test
    PROD_MODE = not TEST_MODE
    
    if not TEST_MODE:
        if not Application.is_allowed_to_run():
            Application.kill_all_instance()
            sys.exit()
        Application.run_helper_if_not_running()

    def stop_if_instance_active():
        # Make sure one only one process exists
        if TEST_MODE:
            mutex_name = "ALS Inventory Manager TEST"
        else:
            mutex_name = "ALS Inventory Manager"
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183

        if last_error == ERROR_ALREADY_EXISTS:
            print("Program is already running")
            pid = os.getpid()
            CREATE_NO_WINDOW = 0x08000000
            subprocess.run([
                "taskkill",
                "/F",
                "/T",
                "/PID",
                str(pid)
            ],creationflags=CREATE_NO_WINDOW)

    stop_if_instance_active()   

    if TEST_MODE:
        db_path = "./Resources/Database/data.db"
    else:
        default_path = "./Resources/Database/data.db"
        db_path = default_path
        Application.save(BackupFolderName, f"v{VERSION}")
        Application.run_on_startup(True)

    DB.PATH = db_path
    DB.migrate(db_path)
    DB.add_column(db_path, "NonconsumableLogs", "Comments", "TEXT", default="''")
    Application.DatabasePath = db_path

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
            labels=["Logs", "Nonconsumables Only"]
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
            labels=["Logs", "Consumables Only"]
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
            labels=["Analytics", "Without Discontinued"],
            min_height=int(height*0.3),
            is_view=True,
            title="Without Discontinued"
        )

        productsTotalSupply = RelationWidget(
            inner_frame,
            productsTotalSupplyRI,
            labels=["Analytics"],
            min_height=int(height*0.3),
            is_view=True,
            title="All Products"
        )
        
        reorder = RelationWidget(
            inner_frame,
            reorder_ri,
            labels=["Analytics", "Without Discontinued"],
            min_height=int(height*0.3),
            exclude_fields_on_show=[],
            is_view=True,
            title="Without Discontinued"
        )

        consumablesReport = RelationWidget(
            inner_frame,
            consumablesReportRI,
            labels=["Analytics", "Consumables Only"],
            min_height=int(height*0.3),
            exclude_fields_on_show=[],
            is_view=True,
            title="With Discontinued"
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

        emergency_widget = ( 
                            RelationWidgetBuilder(db_path=db_path, parent=inner_frame)
                            .default_widget(title="Without Discontinued", is_view=True, minimum_height=200, relation_name="OnEmergency", labels=["Analytics"])
                            .default_results_highlight(color="#FFA07A")
                            .build()
        )

        ( 

         TitledGridsBuilder(inner_frame)
         .add_section_bottom(emergency_widget, heading="Emergency")
         # .add_section_bottom(dangerouslyLow, heading="DangerouslyLow")
         .add_section_bottom(reorder, heading="Low")
         .add_section_bottom(productsTotalSupply, heading="All")
         .add_section_bottom(consumablesReport, heading="Consumables Report")
         .build()

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
        
        # dangerously_low_header.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0))
        # dangerouslyLow.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(5,20))

        # reorder_header.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0))
        # reorder.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=(5, 20))

        # all_header.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 0))
        # productsTotalSupply.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        # consumables_report_header.grid(row=6, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 0))
        # consumablesReport.grid(row=7, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        
        # inner_frame.grid_columnconfigure(0, weight=1)
        # inner_frame.grid_columnconfigure(1, weight=1)

        # for i in range(7):
        #    inner_frame.grid_rowconfigure(i, weight=1)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def resize_inner_frame(event):
            canvas.itemconfig(inner_window, width=event.width)


        def on_tab_changed(event):
            registry.destroy_popups(["Database"])
        notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
        canvas.bind("<Configure>", resize_inner_frame)
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def quicklogs_content(notebook, root, db_path):
        # -------------------- Main Window --------------------
        frequency = 0.2

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("ActionFrame.TFrame", background="lightgrey")
        style.configure("ActionButton.TButton", background="lightgrey")
        style.configure("LeftFrame.TFrame", background="darkgrey")

        main_frame = ttk.Frame(root)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=9)
        main_frame.grid_rowconfigure(0,weight=1)
        
        main_frame.grid(row=0, column=0, sticky="nsew", pady=10)


        label_font = tkfont.Font(size=8, weight="bold")
        
        # ---------- Input Frame ----------
        left_frame = ttk.Frame(main_frame)
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(2, weight=1)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10)


        input_frame = ttk.Frame(left_frame)
        input_frame.grid(row=0, column=0, pady=(0, 10), sticky="new")

        input_frame.grid_columnconfigure(1, weight=1)

        # Barcode
        ttk.Label(input_frame, text="Barcode:", font=label_font)\
            .grid(row=0, column=0, padx=5, pady=5, sticky="w")

        barcode_entry = ttk.Entry(input_frame)
        barcode_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Station
        ttk.Label(input_frame, text="Station:", font=label_font)\
            .grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        station_entry = ttk.Entry(input_frame)
        station_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Product Name
        ttk.Label(input_frame, text="Product Name:", font=label_font)\
            .grid(row=2, column=0, padx=5, pady=5, sticky="w")

                
        product_entry = ttk.Entry(input_frame)
        product_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # ---------- Result Frame (vertical buttons) ----------
        action_frame = ttk.LabelFrame(left_frame, text="Available actions", padding=10)
        action_frame.grid(row=2, column=0, sticky="nsew")

        # Add buttons dynamically
        button_widgets = []
        
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.grid(row=0, column=1, sticky="nsew", padx=10)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        consumables_widget, consumables_ri = create_consumables_table(results_frame)
        consumables_widget.grid(row=0, column=0, sticky="nsew")
        registry.register(consumables_widget, "Results")

        non_cons_result_frame = ttk.Frame(results_frame, padding=10)
        non_cons_result_frame.grid_columnconfigure(0, weight=5)
        non_cons_result_frame.grid_columnconfigure(1, weight=5)
        non_cons_result_frame.grid_rowconfigure(0, weight=1)

        non_consumables_widget, non_cons_ri = create_non_consumables_table(non_cons_result_frame)

        non_consumables_widget.grid(row=0, column=0, sticky="nsew", padx=10)
        registry.register(non_consumables_widget, "Results")

        productsTotalSupplyRI = RelationInterface(
            relation_name="ProductsTotalSupply",
            default_search_text="",
            simple_search_field="ProductName",
            db_path=db_path
        )

        productsTotalSupply = RelationWidget(
            non_cons_result_frame,
            productsTotalSupplyRI,
            is_view=True,
            labels=["Results"],
            title="Total Quantity Available"
        )


        productsTotalSupply.grid(row=0, column=1, sticky="nsew", padx=10)

        non_cons_result_frame.grid(row=0, column=0, sticky="nsew",)

        non_cons_result_frame.grid_remove()
        consumables_widget.grid_remove()
        
        def open_non_cons(name, barcode):
            override_object_function(non_consumables_widget, "get_add_item_title", lambda self: f"Open a '{name}'")
            non_consumables_widget.add_button.invoke()
            non_consumables_widget.add_entries["ActionType"].delete(0, tk.END)
            non_consumables_widget.add_entries["ActionType"].insert(0, "Opened")
            non_consumables_widget.add_entries["ProductName"].delete(0, tk.END)
            non_consumables_widget.add_entries["ProductName"].insert(0, name)
            

            modify_widgets(non_consumables_widget.add_widgets, include=["Quantity", "Date", "Initials"])
            non_consumables_widget.hold_popup(non_consumables_widget.popup)

        def receive_non_cons(name, barcode):
            override_object_function(non_consumables_widget, "get_add_item_title", lambda self: f"Receive a '{name}'")
            non_consumables_widget.add_button.invoke()
            non_consumables_widget.add_entries["ActionType"].delete(0, tk.END)
            non_consumables_widget.add_entries["ActionType"].insert(0, "Received")
            non_consumables_widget.add_entries["ProductName"].delete(0, tk.END)
            non_consumables_widget.add_entries["ProductName"].insert(0, name)
            

            modify_widgets(non_consumables_widget.add_widgets, include=["Quantity", "Date", "Initials", "PONumber"])
            non_consumables_widget.hold_popup(non_consumables_widget.popup)

        def set_current_barcode(name, barcode):
            answer = messagebox.askyesno(
                title="Confirm ",
                message=f"If the entered barcode has the string '{barcode}' then get '{name}'?"
            )

            if answer:
                root.config(cursor="watch")
                result = run_with_error_handling(root, DB.set_barcode, db_path, name, barcode)
                root.config(cursor="")
                if result["status"].lower() == "ok":
                    messagebox.showinfo("Success", f"Now returning '{name}' when barcode contains '{barcode}'")
            else:
                print("Action canceled")
        
        def modify_widgets(widgets, include=[], exclude=[]):
            for key in widgets.keys():
                value = widgets[key]
                if include: 
                    if key in include:
                        value["Label"].grid()
                        value["Entry"].grid()
                    else:
                        value["Label"].grid_remove()
                        value["Entry"].grid_remove()

                if exclude:
                    if key in exclude:
                        value["Label"].grid_remove()
                        value["Entry"].grid_remove()
                    else:
                        value["Label"].grid()
                        value["Entry"].grid()


        def build_available_cons_actions(product_name, barcode):        
            for widg in button_widgets:
                widg.destroy()

            button_widgets.clear()

            def rebuild():
                build_available_cons_actions(product_name, barcode)

            receive_action = StockVerifyAction(db_path, product_name, non_consumables_widget, consumables_widget, button_widgets, frequency=frequency)
            
            override_object_function(receive_action, "action", lambda self: receive_cons(product_name, barcode))

            buttons = [
                ("Set Fetch Rule", set_current_barcode),
                ("Receive", lambda *_: (receive_action.execute(), build_available_cons_actions(product_name, barcode))),
                ("Verify Stock", lambda *_: (receive_action.verify_product_quantity(), rebuild()))
            ] 

            if DB.is_cons_product_openable(db_path, product_name):
                open_action = StockVerifyAction(db_path, product_name, non_consumables_widget, consumables_widget, button_widgets, frequency=frequency)
                override_object_function(open_action, "action", lambda self: open_cons(product_name, barcode))
                buttons.append(("Open", lambda *_: (open_action.execute(), build_available_cons_actions(product_name, barcode))))

            if DB.is_cons_product_finishable(db_path, product_name):
                finish_action = StockVerifyAction(db_path, product_name, non_consumables_widget, consumables_widget, button_widgets, frequency=frequency)
                override_object_function(finish_action, "action", lambda self: finish_cons(product_name, barcode))
                buttons.append(("Finish", lambda *_: (finish_action.execute(), build_available_cons_actions(product_name,barcode))))

            for label, cmd in buttons:
                btn = ttk.Button(action_frame, text=label, command=lambda c=cmd: c(product_name, barcode), padding=10)
                btn.pack(anchor="w", pady=3, fill="x")
                button_widgets.append(btn)

            productsTotalSupply.update_table()

        def receive_cons(name, barcode):
            override_object_function(consumables_widget, "get_add_item_title", lambda self: f"Receive a '{name}'")
            consumables_widget.add_button.invoke()
            consumables_widget.popup.bind("<Destroy>", lambda e: build_available_cons_actions(name, barcode))
            modify_widgets(consumables_widget.add_widgets, exclude=["id", "DateOpened", "OpenedInitials", "DateFinished", "FinishedInitials"])
            consumables_widget.add_widgets["ProductName"]["Entry"].delete(0, tk.END)
            consumables_widget.add_widgets["ProductName"]["Entry"].insert(0, name)
            consumables_widget.hold_popup(consumables_widget.popup)

        def open_cons(name, barcode):
            override_object_function(consumables_widget, "get_update_item_title", lambda self: f"Open a '{name}'")
            consumables_widget.double_click("DateOpened", "")
            consumables_widget.popup.bind("<Destroy>", lambda e: build_available_cons_actions(name, barcode))
            modify_widgets(consumables_widget.update_widgets, include=["id", "DateOpened", "OpenedInitials"])
            consumables_widget.update_widgets["DateOpened"]["Entry"].delete(0, tk.END)
            consumables_widget.update_widgets["DateOpened"]["Entry"].insert(0, date.today().strftime("%Y-%m-%d"))
            consumables_widget.hold_popup(consumables_widget.popup)

        def finish_cons(name, barcode):
            override_object_function(consumables_widget, "get_update_item_title", lambda self: f"Finish a '{name}'")
            consumables_widget.double_click(field="DateFinished", value="")
            consumables_widget.popup.bind("<Destroy>", lambda e: build_available_cons_actions(name, barcode))
            modify_widgets(consumables_widget.update_widgets, include=["id", "DateFinished", "FinishedInitials"])
            consumables_widget.update_widgets["DateFinished"]["Entry"].delete(0, tk.END)
            consumables_widget.update_widgets["DateFinished"]["Entry"].insert(0, date.today().strftime("%Y-%m-%d"))
            consumables_widget.hold_popup(consumables_widget.popup)

        def build_available_non_cons_actions(product_name, barcode):
            for widg in button_widgets:
                widg.destroy()

            button_widgets.clear()

            def rebuild():
                build_available_non_cons_actions(product_name, barcode)

            def on_popup_destroy():
                if non_consumables_widget.popup is not None and non_consumables_widget.popup.winfo_exists():
                    non_consumables_widget.popup.bind("<Destroy>", lambda *_: rebuild())

            receive_action = StockVerifyAction(db_path, product_name, non_consumables_widget, consumables_widget, button_widgets, frequency=frequency)
            override_object_function(receive_action, "action", lambda self: (receive_non_cons(product_name, barcode_entry.get()), rebuild()))

            buttons = [
                ("Set Fetch Rule", set_current_barcode),
                ("Receive", lambda *_: (receive_action.execute(), on_popup_destroy())),
                ("Verify Stock", lambda *_: (receive_action.verify_product_quantity(),rebuild()))
            ]

            if DB.is_non_cons_product_openable(db_path, product_entry.get()):
                open_action = StockVerifyAction(db_path, product_name, non_consumables_widget, consumables_widget, button_widgets, frequency=frequency)
                override_object_function(open_action, "action", lambda self: (open_non_cons(product_name, barcode_entry.get()), rebuild()))
                buttons.append(("Open", lambda *_: (open_action.execute(), on_popup_destroy())))

            for label, cmd in buttons:
                btn = ttk.Button(action_frame, text=label, command=lambda c=cmd: c(product_entry.get(), barcode_entry.get()), padding=10)
                btn.pack(anchor="w", pady=3, fill="x")
                button_widgets.append(btn)


            productsTotalSupply.search_button.invoke()


        def on_product_entered(event=None):
            try:
                product_name=product_entry.get()
                root.config(cursor="watch")

                barcode, station = DB.get_barcode_and_station(Application.DatabasePath, product_name)
                
                barcode_entry.delete(0, tk.END)
                barcode_entry.insert(0, barcode)
                
                station_entry.delete(0, tk.END)
                station_entry.insert(0, station)

                for widg in button_widgets:
                    widg.destroy()
                
                non_cons_result_frame.grid_remove()
                consumables_widget.grid_remove()

                is_consumable = False
                try:
                    is_consumable = DB.is_product_consumable(productsTotalSupplyRI.db_path, product_entry.get())
                except Exception:
                    root.config(cursor="")
                    return

                if not is_consumable:
                    productsTotalSupply.advanced_search(productsTotalSupply.advance_button, silent=True)
                    productsTotalSupply.advanced_search_widgets["ProductName"][1].set("exactly")
                    productsTotalSupply.advanced_search_widgets["ProductName"][0].delete(0, tk.END)
                    productsTotalSupply.advanced_search_widgets["ProductName"][0].insert(0, product_entry.get())
                    productsTotalSupply.apply_filters_button.invoke()

                    non_consumables_widget.advanced_search(non_consumables_widget.advance_button, silent=True)
                    non_consumables_widget.advanced_search_widgets["ProductName"][1].set("exactly")
                    non_consumables_widget.advanced_search_widgets["ProductName"][0].delete(0, tk.END)
                    non_consumables_widget.advanced_search_widgets["ProductName"][0].insert(0, product_entry.get())
                    non_consumables_widget.apply_filters_button.invoke()
                    
                   

                    non_cons_result_frame.grid()
                    build_available_non_cons_actions(product_name, barcode_entry.get())
                    
                else:
                    consumables_widget.advanced_search(non_consumables_widget.advance_button, silent=True)
                    consumables_widget.advanced_search_widgets["ProductName"][1].set("exactly")
                    consumables_widget.advanced_search_widgets["ProductName"][0].delete(0, tk.END)
                    consumables_widget.advanced_search_widgets["ProductName"][0].insert(0, product_entry.get())
                    consumables_widget.apply_filters_button.invoke()

                    consumables_widget.grid()

                    build_available_cons_actions(product_name, barcode_entry.get())

                root.config(cursor="")
            except Exception as e:
                root.config(cursor="")
                raise

        # ---------- Tab Change Cleanup ----------
        def on_tab_changed(event):
            barcode_entry.focus()
            registry.destroy_all_popups()

        attach_helper(root, "ProductName", product_entry, productsTotalSupplyRI.db_path, ["Without Discontinued"], productsTotalSupply.all_columns, productsTotalSupply.all_column_types)
        attach_helper(root, "Station", station_entry, productsTotalSupplyRI.db_path, [], productsTotalSupply.all_columns, productsTotalSupply.all_column_types)

        def clear_fields():
            barcode_entry.delete(0, "end")
            station_entry.delete(0, "end")
            product_entry.delete(0, "end")

            entry_helpers.unattach_helpers(product_entry)
            attach_helper(root, "ProductName", product_entry, productsTotalSupplyRI.db_path, ["Without Discontinued"], productsTotalSupply.all_columns, productsTotalSupply.all_column_types)

            non_cons_result_frame.grid_remove()
            consumables_widget.grid_remove()

            for widg in button_widgets:
                    widg.destroy()

        clear_button = ttk.Button(input_frame, text="Clear", command=clear_fields)
        clear_button.grid(row=3, column=1, padx=5, pady=5, sticky="e")

        def on_station_entered():
            new_station = station_entry.get()
            clear_fields()
            station_entry.insert(0, new_station)
            entry_helpers.unattach_helpers(product_entry)
            attach_helper(root, "ProductName", product_entry, productsTotalSupplyRI.db_path, ["Without Discontinued"], productsTotalSupply.all_columns, productsTotalSupply.all_column_types, filters=([f"Station = '{station_entry.get()}'"] if station_entry.get() != "" else []))
            product_entry.focus_set()

        def populate_and_invoke_product_entry(event):
            root.config(cursor="watch")
            product_entry.delete(0, tk.END)
            product_entry.insert(0, DB.get_product_name(db_path, barcode_entry.get()))
            on_product_entered()
            root.config(cursor="")

        barcode_entry.bind("<Return>", lambda event: run_with_error_handling(root, populate_and_invoke_product_entry, event))
        barcode_entry.bind("<Tab>", lambda event: run_with_error_handling(root, populate_and_invoke_product_entry, event))

        station_entry.bind("<Return>", lambda event: on_station_entered())
        station_entry.bind("<Tab>", lambda event: on_station_entered())

        product_entry.bind("<Return>", on_product_entered)
        product_entry.bind("<Tab>", on_product_entered)
        
        notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    def nav(root, db_path):
        
        if TEST_MODE:
            root.title("ALS Inventory Manager TEST")
        else:
            root.title("ALS Inventory Manager")
        
        root.geometry("1200x700")

        # NOTEBOOK in row 1 (below the warning)
        notebook = ttk.Notebook(root)
        notebook.grid(row=1, column=2, sticky="nsew")  # fill space

        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)
        
       
        # Create frames (each tab needs a frame)
        analytics_tab = ttk.Frame(notebook)
        cons_log_tab = ttk.Frame(notebook)
        non_cons_log_tab = ttk.Frame(notebook)
        product_manager_tab = ttk.Frame(notebook)
        quicklogs_tab = ttk.Frame(notebook)

        # Add tabs to notebook
        notebook.add(analytics_tab, text="Analytics & Reporting")
        notebook.add(quicklogs_tab, text="Quick Logs")
        notebook.add(cons_log_tab, text="Consumable Logs")
        notebook.add(non_cons_log_tab, text="Non-consumable Logs")
        notebook.add(product_manager_tab, text="Products")

        # Initial load
        cons_log_content(notebook, cons_log_tab)
        non_cons_log_content(notebook, non_cons_log_tab)
        analytics_content(notebook, analytics_tab)
        product_manager_content(notebook, product_manager_tab)
        quicklogs_content(notebook, quicklogs_tab, db_path)

        registry.refresh_all(exceptions=["Early"])


    root = tk.Tk()
    style = ttk.Style()

    def on_closing():
        answer = messagebox.askyesno("Exit", "Are you sure you want to exit the app ? ")
        if answer:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", lambda: root.iconify())

    run_with_error_handling(root, nav, root, db_path)

    def show_warning_if_app_outdated():
        if latest_deployed is not None and latest_deployed > VERSION:
            warning_frame = tk.Frame(root, bg="#8B0000")
            warning_frame.grid(row=0, column=1, sticky="ew")

            tk.Label(
                warning_frame,
                text=f"This application is outdated (Ver. {VERSION}). Some features may not work properly. Please grab the latest one.",
                bg="#8B0000",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                pady=8
            ).pack(fill="x")            
    # registry.on_table_update(show_warning_if_app_outdated) 
    # show_warning_if_app_outdated()
    
    registry.on_table_update(entry_helpers.update_helpers, parents=["Products"])

    root.mainloop()
