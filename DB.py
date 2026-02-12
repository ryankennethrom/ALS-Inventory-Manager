import sqlite3
import os
import re

# db_path = "Z:/InventoryAppData/inventory.db"
db_path = "inventory.db"

def connect():
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")  # ensure FK checks
    return conn

def update(table, row_id, data):
    """
    Update a row in `table` by id.
    Returns: (success: bool, error_message: str)
    """
    columns = ", ".join(f"{col}=?" for col in data.keys())
    values = list(data.values())
    values.append(row_id)
    query = f"UPDATE {table} SET {columns} WHERE id=?"

    try:
        with connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
        return True, ""
    except sqlite3.IntegrityError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def init_db(db_path=db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # ---------- Products ----------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Products (
        ProductName TEXT PRIMARY KEY,
        AlsItem TEXT UNIQUE,
        UnitPrice REAL NOT NULL CHECK (UnitPrice >= 0),
        UnitOfMeasure TEXT NOT NULL,
        ItemDescription TEXT NOT NULL,
        Station TEXT NOT NULL,
        IsConsumable INTEGER NOT NULL CHECK (IsConsumable IN (0, 1)),
        Alert INTEGER NOT NULL CHECK (Alert IN (0, 1)),
        VendorItem TEXT,
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
        DateReceived TEXT NOT NULL CHECK(DateReceived GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'),
        ReceivedInitials TEXT NOT NULL,
        ExpiryDate TEXT NOT NULL CHECK(ExpiryDate GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'),

        DateOpened TEXT CHECK(DateOpened IS NULL OR DateOpened GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'),
        OpenedInitials TEXT,

        DateFinished TEXT CHECK(DateFinished IS NULL OR DateFinished GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'),
        FinishedInitials TEXT,

        -- Lifecycle constraints
        CHECK (
            (DateOpened IS NULL AND DateFinished IS NULL)
            OR (DateOpened IS NOT NULL AND DateFinished IS NULL)
            OR (DateOpened IS NOT NULL AND DateFinished IS NOT NULL)
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
        Quantity INTEGER NOT NULL CHECK (Quantity > 0),
        Date TEXT NOT NULL CHECK(Date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'),
        Initials TEXT NOT NULL CHECK (length(Initials) BETWEEN 2 AND 5),
        ActionType TEXT NOT NULL CHECK (
            ActionType IN ('Received', 'Opened')
        ),
        FOREIGN KEY (ProductName)
            REFERENCES Products(ProductName)
            ON DELETE RESTRICT
    ) STRICT;
    """)

    # ---------- Trigger to enforce IsConsumable = 0 ----------
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS check_non_consumable_product
    BEFORE INSERT ON NonConsumableLogs
    FOR EACH ROW
    BEGIN
        SELECT
            CASE
                WHEN (SELECT IsConsumable FROM Products WHERE ProductName = NEW.ProductName) != 0
                THEN RAISE(ABORT, 'Cannot add non-consumable log for a consumable product')
            END;
    END;
    """)

    # ---------- Trigger to enforce IsConsumable = 1 for ConsumableLogs ----------
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS check_consumable_product
    BEFORE INSERT ON ConsumableLogs
    FOR EACH ROW
    BEGIN
        SELECT
            CASE
                WHEN (SELECT IsConsumable FROM Products WHERE ProductName = NEW.ProductName) != 1
                THEN RAISE(ABORT, 'Cannot add consumable log for a non-consumable product')
            END;
    END;
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

