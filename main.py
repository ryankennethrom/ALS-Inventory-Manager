import tkinter as tk
import DB
from RelationInterface import RelationInterface
from RelationWidget import RelationWidget
from error_ui import show_error_ui

if __name__ == "__main__":
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
    left = RelationWidget(
        root,
        products,
        title="Products"
    )
    left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    middle = RelationWidget(
        root,
        consumables,
        exclude_fields_on_show=["ExpiryDate"],
        exclude_fields_on_create=["id"],
        title="Consumables"
    )
    middle.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    right = RelationWidget(
        root,
        non_consumables,
        exclude_fields_on_create=["id"],
        title="Non-Consumables"
    )
    right.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

    root.mainloop()
