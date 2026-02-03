import sqlite3
import os

def init_db(db_path="inventory.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # ---------- Tables ----------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Products (
        ProductName TEXT PRIMARY KEY,
        AlsItem TEXT,
        UnitPrice REAL NOT NULL,
        UnitOfMeasure TEXT NOT NULL,
        ItemDescription TEXT NOT NULL,
        Station TEXT NOT NULL,
        IsConsumable INTEGER NOT NULL,
        Alert INTEGER NOT NULL,
        VendorItem TEXT,
        Vendor TEXT NOT NULL,
        PO TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ConsumableReceivedLogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ProductName TEXT NOT NULL,
        LOT TEXT NOT NULL,
        DateReceived TEXT NOT NULL,
        DateReceivedIni TEXT NOT NULL,
        ExpiryDate TEXT NOT NULL,
        FOREIGN KEY (ProductName) REFERENCES Products(ProductName)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ConsumableOpenedLogs (
        id INTEGER PRIMARY KEY,
        DateOpened TEXT NOT NULL,
        DateOpenedIni TEXT NOT NULL,
        FOREIGN KEY (id) REFERENCES ConsumableReceivedLogs(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ConsumableFinishedLogs (
        id INTEGER PRIMARY KEY,
        DateFinished TEXT NOT NULL,
        DateFinishedIni TEXT NOT NULL,
        FOREIGN KEY (id) REFERENCES ConsumableOpenedLogs(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS NonConsumableLogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ProductName TEXT NOT NULL,
        Quantity INTEGER NOT NULL CHECK (Quantity > 0),
        Date TEXT NOT NULL,
        Initials TEXT NOT NULL,
        ActionType TEXT NOT NULL CHECK (ActionType IN ('Received', 'Opened')),
        FOREIGN KEY (ProductName) REFERENCES Products(ProductName)
    );
    """)

    # ---------- View ----------

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS ProductConsumableQuantity AS
    SELECT
        p.ProductName,
        p.AlsItem,
        p.UnitPrice,
        p.UnitOfMeasure,
        p.ItemDescription,
        p.Station,
        p.IsConsumable,
        p.Alert,
        p.VendorItem,
        p.Vendor,
        p.PO,
        COUNT(cr.id) AS Quantity
    FROM Products p
    LEFT JOIN ConsumableReceivedLogs cr
        ON cr.ProductName = p.ProductName
    LEFT JOIN ConsumableFinishedLogs cf
        ON cf.id = cr.id
    WHERE p.IsConsumable = 1
      AND cf.id IS NULL
    GROUP BY p.ProductName;
    """)

    conn.commit()
    conn.close()

def delete_db(db_path="inventory.db"):
    """Delete the SQLite database file."""
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Database '{db_path}' deleted successfully.")
    else:
        print(f"Database '{db_path}' does not exist.")
