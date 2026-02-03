import DB
from RelationInterface import RelationInterface

if __name__ == "__main__":
    DB.delete_db()
    DB.init_db()

    # ------------------ Columns definition ------------------
    columns = ["ProductName", "AlsItem", "UnitPrice", "UnitOfMeasure", "ItemDescription",
               "Station", "IsConsumable", "Alert", "VendorItem", "Vendor"]

    # ------------------ Work with Products table ------------------
    print("=== Working with Products table ===")
    products = RelationInterface(
        relation_name="Products",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[],
        columns=columns  # <-- Specify columns here
    )

    # Initial search
    print("Initial Products:")
    for item in products.curr_results:
        print(item)

    # ------------------ Add new products ------------------
    new_products = [
        {
            "ProductName": "iPhone 15",
            "AlsItem": "IP15",
            "UnitPrice": 1299.0,
            "UnitOfMeasure": "pcs",
            "ItemDescription": "Latest iPhone model",
            "Station": "A1",
            "IsConsumable": 1,
            "Alert": 0,
            "VendorItem": "V-IP15",
            "Vendor": "Apple",
            "PO": None
        },
        {
            "ProductName": "Samsung Galaxy S24",
            "AlsItem": "SGS24",
            "UnitPrice": 1199.0,
            "UnitOfMeasure": "pcs",
            "ItemDescription": "Flagship Samsung phone",
            "Station": "A2",
            "IsConsumable": 1,
            "Alert": 0,
            "VendorItem": "V-SGS24",
            "Vendor": "Samsung",
            "PO": None
        },
        {
            "ProductName": "Logitech Mouse",
            "AlsItem": "LM01",
            "UnitPrice": 25.0,
            "UnitOfMeasure": "pcs",
            "ItemDescription": "Wireless mouse",
            "Station": "B1",
            "IsConsumable": 0,
            "Alert": 0,
            "VendorItem": "V-LM01",
            "Vendor": "Logitech",
            "PO": None
        },
        {
            "ProductName": "Mechanical Keyboard",
            "AlsItem": "MK01",
            "UnitPrice": 75.0,
            "UnitOfMeasure": "pcs",
            "ItemDescription": "RGB mechanical keyboard",
            "Station": "B2",
            "IsConsumable": 0,
            "Alert": 0,
            "VendorItem": "V-MK01",
            "Vendor": "Corsair",
            "PO": None
        },
        {
            "ProductName": "HDMI Cable",
            "AlsItem": "HC01",
            "UnitPrice": 10.0,
            "UnitOfMeasure": "pcs",
            "ItemDescription": "High-speed HDMI cable",
            "Station": "C1",
            "IsConsumable": 1,
            "Alert": 0,
            "VendorItem": "V-HC01",
            "Vendor": "Belkin",
            "PO": None
        }
    ]

    for p in new_products:
        products.on_create_item_clicked(p)

    print("\nAfter adding new products:")
    for item in products.curr_results:
        print(item)

    # ------------------ Update first product ------------------
    if products.curr_results:
        products.on_item_save_clicked(0, {"UnitPrice": 1199.0})
        print("\nAfter updating first product price:")
        for item in products.curr_results:
            print(item)

    # ------------------ Delete first product ------------------
    if products.curr_results:
        products.on_item_delete_clicked(0)
        print("\nAfter deleting first product:")
        for item in products.curr_results:
            print(item)

    # ------------------ Export Products table ------------------
    products.export_as_excel("Products.xlsx")

    # ------------------ Work with ProductConsumableQuantity view ------------------
    print("\n=== Working with ProductConsumableQuantity view ===")
    consumables = RelationInterface(
        relation_name="ProductConsumableQuantity",
        default_search_text="",
        simple_search_field="ProductName",
        default_filters=[],
        columns=columns  # specify the same columns if you want consistency
    )

    print("Consumable quantities:")
    for item in consumables.curr_results:
        print(item)

    consumables.export_as_excel("ProductConsumableQuantity.xlsx")
