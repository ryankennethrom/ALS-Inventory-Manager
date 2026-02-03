# test_relation_interface.py
import DB
import sqlite3
from RelationInterface import RelationInterface
import os

# -------------------- Setup --------------------
DB.delete_db()  # remove old DB
DB.init_db()    # initialize fresh DB

# -------------------- Helper --------------------
def get_columns(table_name, db_path="inventory.db"):
    """Fetch column names dynamically from SQLite table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]  # 2nd item is column name
    conn.close()
    return columns

# -------------------- Test RelationInterface --------------------
if __name__ == "__main__":
    table_name = "ConsumableReceivedLogs"
    columns = get_columns(table_name)
    consumables = RelationInterface(
        relation_name=table_name,
        default_search_text="",
        simple_search_field="DateReceivedIni",
        default_filters=[],
        columns=columns
    )

    # ---- Test: Create new log ----
    new_item = {
        "ProductName": "iPhone 15",
        "LOT": "LOT123",
        "DateReceived": "2026-02-02",
        "DateReceivedIni": "20260202",
        "ExpiryDate": "2026-12-31"
    }
    consumables.on_create_item_clicked(new_item)

    # ---- Test: Search ----
    consumables.on_search_field_changed("202602")  # should match DateReceivedIni
    results = consumables.on_search_clicked()
    print("Search results:")
    for r in results:
        print(r)

    # ---- Test: Update ----
    if results:
        consumables.on_item_save_clicked(0, {"LOT": "LOT999"})
        print("\nAfter update:")
        for r in consumables.curr_results:
            print(r)

    # ---- Test: Delete ----
    if consumables.curr_results:
        consumables.on_item_delete_clicked(0)
        print("\nAfter delete:")
        for r in consumables.curr_results:
            print(r)

    # ---- Test: Export ----
    consumables.export_as_excel("ConsumableReceivedLogs.xlsx")
    print(f"\nExcel exported to {os.path.abspath('ConsumableReceivedLogs.xlsx')}")
