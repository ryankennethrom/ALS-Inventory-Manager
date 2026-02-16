import sqlite3
import os
import re

# db_path = "Z:/InventoryAppData/inventory.db"
db_path = "inventory.db"

def connect():
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")  # ensure FK checks
    return conn

def init_db(db_path=db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # ---------- Products ----------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Products (
        ProductName TEXT PRIMARY KEY,
        AlsItemNumber TEXT UNIQUE,
        UnitPrice REAL NOT NULL CHECK (UnitPrice >= 0),
        UnitOfMeasure TEXT NOT NULL,
        ItemDescription TEXT NOT NULL,
        Station TEXT NOT NULL,
        IsConsumable TEXT NOT NULL CHECK (IsConsumable IN ('n', 'y')),
        Alert INTEGER NOT NULL CHECK (Alert >= 0),
        VendorItemNumber TEXT,
        Vendor TEXT NOT NULL,
        PO TEXT
    ) STRICT;
    """)

    # ---------- Consumable Logs ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ConsumableLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductName TEXT NOT NULL,
            LOT TEXT NOT NULL,

            -- Dates for lifecycle
            DateReceived TEXT NOT NULL
                CHECK (
                    DateReceived GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                    AND DateReceived = date(DateReceived)
                ),

            ReceivedInitials TEXT NOT NULL 
                CHECK (
                    ReceivedInitials != ''
                ),

            ExpiryDate TEXT NOT NULL
                CHECK (
                    ExpiryDate GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                    AND ExpiryDate = date(ExpiryDate)
                ),

            DateOpened TEXT
                CHECK (
                    DateOpened == '' OR
                    (
                        DateOpened GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                        AND DateOpened = date(DateOpened)
                    )
                ),

            OpenedInitials TEXT
                CHECK (
                    ( OpenedInitials == '' AND DateOpened == '' ) or (OpenedInitials != '' AND DateOpened != '')
                ),

            DateFinished TEXT
                CHECK (
                    DateFinished == '' OR
                    (
                        DateFinished GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                        AND DateFinished = date(DateFinished)
                    )
                ),

            FinishedInitials TEXT
                CHECK (
                    (FinishedInitials == '' AND DateFinished == '') or (FinishedInitials != '' AND DateFinished != '')
                ),

            CreatedDateTime TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),

            -- Lifecycle state consistency
            CHECK (
                (DateOpened == '' AND DateFinished == '')
                OR (DateOpened != '' AND DateFinished == '')
                OR (DateOpened != '' AND DateFinished != '')
            ),

            FOREIGN KEY (ProductName)
                REFERENCES Products(ProductName)
                ON DELETE RESTRICT
        ) STRICT;
    """)
   
    # ---------- Non-consumable logs ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS NonConsumableLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductName TEXT NOT NULL,

            Quantity INTEGER NOT NULL
                CHECK (Quantity > 0),

            DateReceived TEXT NOT NULL
                CHECK (
                    DateReceived GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                    AND DateReceived = date(DateReceived)
                ),

            Initials TEXT NOT NULL
                CHECK (length(Initials) BETWEEN 2 AND 5),

            ActionType TEXT NOT NULL
                CHECK (
                    ActionType IN ('Received', 'Opened')
                ),

            CreatedDateTime TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),

            FOREIGN KEY (ProductName)
                REFERENCES Products(ProductName)
                ON DELETE RESTRICT
        ) STRICT;
    """)
    
    # ---------- Triggers ----------
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS check_non_consumable_product
    BEFORE INSERT ON NonConsumableLogs
    FOR EACH ROW
    BEGIN
        SELECT
            CASE
                WHEN (SELECT IsConsumable FROM Products WHERE ProductName = NEW.ProductName) LIKE 'y'
                THEN RAISE(ABORT, 'Cannot add non-consumable log for a consumable product')
            END;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS check_consumable_product
    BEFORE INSERT ON ConsumableLogs
    FOR EACH ROW
    BEGIN
        SELECT
            CASE
                WHEN (SELECT IsConsumable FROM Products WHERE ProductName = NEW.ProductName) LIKE 'n'
                THEN RAISE(ABORT, 'Cannot add consumable log for a non-consumable product')
            END;
    END;
    """)


    cursor.execute("DROP TRIGGER IF EXISTS limit_nonconsumable_opened;")

    cursor.execute("""
    CREATE TRIGGER limit_nonconsumable_opened
    BEFORE INSERT ON NonConsumableLogs
    FOR EACH ROW
    WHEN NEW.ActionType = 'Opened'
    BEGIN
        -- Compute total received
        SELECT
            CASE
                WHEN (
                    (SELECT COALESCE(SUM(Quantity), 0)
                     FROM NonConsumableLogs
                     WHERE ProductName = NEW.ProductName AND ActionType = 'Received')
                    <
                    (SELECT COALESCE(SUM(Quantity), 0)
                     FROM NonConsumableLogs
                     WHERE ProductName = NEW.ProductName AND ActionType = 'Opened')
                    + NEW.Quantity
                )
                THEN RAISE(ABORT, 'Cannot open more than total received quantity')
            END;
    END;
    """)

    # ----------- Views ------------------
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS OutOfStockConsumables AS
    SELECT p.ProductName
    FROM Products p
    WHERE p.IsConsumable = 'y'
    AND (
        SELECT COUNT(*)
        FROM ConsumableLogs l2
        WHERE l2.ProductName = p.ProductName
          AND l2.DateFinished = ''
    ) = 0;
    """)
    
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS AvailableConsumables AS
    SELECT *
    FROM ConsumableLogs
    WHERE DateFinished == ''
    ORDER BY CreatedDateTime ASC;
    """)
    
    cursor.execute("""
    DROP VIEW IF EXISTS OutOfStockNonConsumables;
    """)
    
    # Create the new view
    cursor.execute("""
    CREATE VIEW OutOfStockNonConsumables AS
    SELECT
        p.ProductName,
        COALESCE(SUM(CASE WHEN l.ActionType = 'Received' THEN l.Quantity ELSE 0 END), 0) AS TotalQuantityReceived,
        COALESCE(SUM(CASE WHEN l.ActionType = 'Opened' THEN l.Quantity ELSE 0 END), 0) AS TotalQuantityOpened
    FROM Products p
    LEFT JOIN NonConsumableLogs l
        ON p.ProductName = l.ProductName
    WHERE p.IsConsumable = 'n'
    GROUP BY p.ProductName
    HAVING TotalQuantityReceived <= TotalQuantityOpened;
    """)

    cursor.execute("""
    DROP VIEW IF EXISTS AvailableNonConsumables;
    """)
 
    cursor.execute("""
    CREATE VIEW AvailableNonConsumables AS
    SELECT
        p.ProductName,
        COALESCE(SUM(CASE WHEN l.ActionType = 'Received' THEN l.Quantity ELSE 0 END), 0) AS TotalQuantityReceived,
        COALESCE(SUM(CASE WHEN l.ActionType = 'Opened' THEN l.Quantity ELSE 0 END), 0) AS TotalQuantityOpened,
        COALESCE(SUM(CASE WHEN l.ActionType = 'Received' THEN l.Quantity ELSE 0 END), 0)
            - COALESCE(SUM(CASE WHEN l.ActionType = 'Opened' THEN l.Quantity ELSE 0 END), 0) AS TotalQuantityAvailable
    FROM Products p
    LEFT JOIN NonConsumableLogs l
        ON p.ProductName = l.ProductName
    WHERE p.IsConsumable = 'n'
    GROUP BY p.ProductName
    HAVING TotalQuantityReceived > TotalQuantityOpened;
    """)

    cursor.execute("""
    DROP VIEW IF EXISTS ReOrderList;
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS ReOrderList AS
    SELECT c.ProductName, COUNT(*) AS TotalQuantityAvailable, p.Alert
    FROM Products p
    LEFT JOIN ConsumableLogs c ON c.ProductName = p.ProductName
    WHERE c.DateFinished == ''
    GROUP BY c.ProductName
    HAVING TotalQuantityAvailable <= p.Alert

    UNION ALL

    SELECT
        p.ProductName,
        COALESCE(n.TotalQuantityAvailable, 0) AS TotalQuantityAvailable,
        p.Alert
    FROM Products p
    LEFT JOIN AvailableNonConsumables n
        ON n.ProductName = p.ProductName
    WHERE p.IsConsumable = 'n';
    """)

    conn.commit()
    conn.close()

def delete_db(db_path=db_path):
    """Delete the SQLite database file."""
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Database '{db_path}' deleted successfully.")
    else:
        print(f"Database '{db_path}' does not exist.")

def get_columns(relation_name, db_path=db_path):
    """
    Returns a list of column names for a SQLite table or view.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({relation_name});")
    rows = cursor.fetchall()

    conn.close()

    # row format:
    # (cid, name, type, notnull, dflt_value, pk)
    return [row[1] for row in rows]

def get_column_types(table_name, db_path=db_path):
    """
    Returns a dict mapping column name -> logical type: 'integer', 'float', 'text', 'date'
    """
    types = {}
    date_pattern = re.compile(r'date', re.IGNORECASE)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        for _, name, col_type, _, _, _ in cursor.fetchall():
            col_type_upper = col_type.upper()

            # Detect integer
            if "INT" in col_type_upper:
                types[name] = "integer"
            # Detect float/real/numeric
            elif any(x in col_type_upper for x in ["REAL", "FLOA", "DOUB"]):
                types[name] = "float"
            # Detect dates by name
            elif date_pattern.search(name):
                types[name] = "date"
            else:
                types[name] = "text"

    return types

