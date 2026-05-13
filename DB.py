import sqlite3
import os
import re
import os
import configparser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

APP_NAME = "InventoryApp"
CONFIG_FILE = "config.ini"
PATH = None

def get_config_path():
    appdata = os.getenv("APPDATA")
    config_dir = os.path.join(appdata, APP_NAME)
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, CONFIG_FILE)


def select_database_file():
    root = tk.Tk()
    root.withdraw()

    messagebox.showinfo(
        "Database Required",
        "Please select the inventory database file."
    )

    file_path = filedialog.askopenfilename(
        title="Select Inventory Database",
        filetypes=[("SQLite Database", "*.db")]
    )

    root.destroy()
    return file_path

def get_db_path(test_mode=False):
    if test_mode:
        return "./dist/Resources/Database/data.db"
    else:
        return "./Resources/Database/data.db"

def ask_for_db_path():
    config_path = get_config_path()
    config = configparser.ConfigParser()

    # If config file does not exist
    if not os.path.exists(config_path):
        db_path = select_database_file()

        if not db_path:
            messagebox.showerror("Error", "Database file not selected.")
            raise Exception("Database not selected")

        config["Database"] = {"db_path": db_path}
        with open(config_path, "w") as f:
            config.write(f)

        return db_path

    # Read config
    config.read(config_path)
    db_path = config["Database"]["db_path"]

    # If database file missing
    if not os.path.exists(db_path):
        root = tk.Tk()
        root.withdraw()

        messagebox.showwarning(
            "Database Not Found",
            "Database file could not be found. Please locate it."
        )

        new_db_path = select_database_file()

        if not new_db_path:
            messagebox.showerror("Error", "Database file not selected.")
            raise Exception("Database not selected")

        config["Database"]["db_path"] = new_db_path
        with open(config_path, "w") as f:
            config.write(f)

        return new_db_path

    return db_path

def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")  # ensure FK checks
    return conn

def try_add_discontinued_column(db_path):
    conn = connect(db_path)
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE Products ADD COLUMN IsDiscontinued TEXT NOT NULL DEFAULT 'n' CHECK (IsDiscontinued IN ('n', 'y'))")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def recreate_dangerously_low(db_path):
    conn = connect(db_path)
    cursor = conn.cursor()

    cursor.execute(""" DROP VIEW IF EXISTS DangerouslyLow; """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS DangerouslyLow AS
    SELECT c.ProductName, c.TotalQuantityAvailable, p.IsConsumable, p.UnitOfMeasure, p.Station, p.EmergencyCount
    FROM ConsumablesAvailableTotaled c
    LEFT JOIN Products p ON c.ProductName = p.ProductName
    WHERE c.TotalQuantityAvailable <= p.EmergencyCount AND p.IsDiscontinued = 'n'

    UNION ALL

    SELECT
        p.ProductName,
        COALESCE(n.TotalQuantityAvailable, 0) AS TotalQuantityAvailable,
        p.IsConsumable,
        p.UnitOfMeasure,
        p.Station,
        p.EmergencyCount
    FROM Products p
    LEFT JOIN AvailableNonConsumables n
        ON n.ProductName = p.ProductName
    WHERE p.IsConsumable = 'n'
      AND COALESCE(n.TotalQuantityAvailable, 0) <= p.EmergencyCount AND p.IsDiscontinued = 'n';
    """)

    conn.commit()
    conn.close()

def recreate_products_total_supply(db_path):
    conn = connect(db_path)
    cursor = conn.cursor()

    cursor.execute(""" DROP VIEW IF EXISTS ProductsTotalSupply; """)
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS ProductsTotalSupply AS
    SELECT p.ProductName, p.IsDiscontinued, COALESCE(c.TotalQuantityAvailable, 0) as TotalQuantityAvailable, p.Station, p.IsConsumable, p.UnitOfMeasure
    FROM Products p
    LEFT JOIN ConsumablesAvailableTotaled c ON c.ProductName = p.ProductName
    WHERE p.IsConsumable = 'y'

    UNION ALL

    SELECT p.ProductName, p.IsDiscontinued, COALESCE(n.TotalQuantityAvailable, 0), p.Station, p.IsConsumable, p.UnitOfMeasure
    FROM Products p
    LEFT JOIN AvailableNonConsumables n ON n.ProductName = p.ProductName
    WHERE p.IsConsumable = 'n'
    """)

    conn.commit()
    conn.close()


def recreate_reorder_list(db_path):
    conn = connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(""" DROP VIEW IF EXISTS ReOrderList; """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS ReOrderList AS
    SELECT c.ProductName, c.TotalQuantityAvailable, p.IsConsumable, p.UnitOfMeasure, p.Station, p.LowSupplyCount
    FROM ConsumablesAvailableTotaled c
    LEFT JOIN Products p ON c.ProductName = p.ProductName
    WHERE c.TotalQuantityAvailable <= p.LowSupplyCount AND p.IsDiscontinued = 'n'

    UNION ALL

    SELECT
        p.ProductName,
        COALESCE(n.TotalQuantityAvailable, 0) AS TotalQuantityAvailable,
        p.IsConsumable,
        p.UnitOfMeasure,
        p.Station,
        p.LowSupplyCount
    FROM Products p
    LEFT JOIN AvailableNonConsumables n
        ON n.ProductName = p.ProductName
    WHERE p.IsConsumable = 'n'
      AND COALESCE(n.TotalQuantityAvailable, 0) <= p.LowSupplyCount AND p.IsDiscontinued = 'n';
    """)

    conn.commit()
    conn.close()

def add_barcode_check_constraint(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Disable FK checks for migration
    cursor.execute("PRAGMA foreign_keys = OFF;")
    conn.execute("BEGIN TRANSACTION;")

    # 1. Fetch triggers referencing Products
    cursor.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='trigger' AND sql LIKE '%Products%';
    """)
    triggers = cursor.fetchall()

    # 2. Fetch views referencing Products
    cursor.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='view' AND sql LIKE '%Products%';
    """)
    views = cursor.fetchall()

    # 3. Drop triggers
    for name, _ in triggers:
        cursor.execute(f"DROP TRIGGER IF EXISTS {name};")

    # 4. Drop views
    for name, _ in views:
        cursor.execute(f"DROP VIEW IF EXISTS {name};")

    # 5. Create new table with the corrected schema
    cursor.execute("""
        CREATE TABLE Products_new (
            ProductName TEXT PRIMARY KEY,
            BarcodeContains TEXT NOT NULL UNIQUE CHECK (BarcodeContains <> ''),
            UnitOfMeasure TEXT NOT NULL,
            ItemDescription TEXT NOT NULL,
            Station TEXT NOT NULL,
            IsConsumable TEXT NOT NULL CHECK (IsConsumable IN ('n', 'y')),
            Price REAL DEFAULT 0 CHECK (Price >= 0),
            LowSupplyCount INTEGER NOT NULL CHECK (LowSupplyCount >= 0),
            EmergencyCount INTEGER NOT NULL DEFAULT 0 CHECK (EmergencyCount >= 0),
            AlsItemNumber TEXT NOT NULL,
            VendorNumber TEXT NOT NULL,
            VendorItemNumber TEXT NOT NULL,
            IsDiscontinued TEXT NOT NULL DEFAULT 'n' CHECK (IsDiscontinued IN ('n', 'y')),
            CHECK (LowSupplyCount >= EmergencyCount)
        ) STRICT;
    """)

    # 6. Copy data from old table
    cursor.execute("""
        INSERT INTO Products_new (
            ProductName, BarcodeContains, UnitOfMeasure, ItemDescription,
            Station, IsConsumable, Price, LowSupplyCount, EmergencyCount,
            AlsItemNumber, VendorNumber, VendorItemNumber, IsDiscontinued
        )
        SELECT
            ProductName, BarcodeContains, UnitOfMeasure, ItemDescription,
            Station, IsConsumable, Price, LowSupplyCount, EmergencyCount,
            AlsItemNumber, VendorNumber, VendorItemNumber, IsDiscontinued
        FROM Products;
    """)

    # 7. Drop old table
    cursor.execute("DROP TABLE Products;")

    # 8. Rename new table
    cursor.execute("ALTER TABLE Products_new RENAME TO Products;")

    # 9. Restore views
    for name, sql in views:
        cursor.execute(sql)

    # 10. Restore triggers
    for name, sql in triggers:
        cursor.execute(sql)

    # Re-enable FK checks
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    conn.close()

    print("Migration complete: CHECK constraint added, views and triggers restored.")

def init_db(db_path, test=False):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # ---------- Products ----------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Products (
        ProductName TEXT PRIMARY KEY,
        Barcode TEXT NOT NULL UNIQUE,
        UnitOfMeasure TEXT NOT NULL,
        ItemDescription TEXT NOT NULL,
        Station TEXT NOT NULL,
        IsConsumable TEXT NOT NULL CHECK (IsConsumable IN ('n', 'y')),
        Price REAL DEFAULT 0 CHECK (Price >= 0),
        LowSupplyCount INTEGER NOT NULL CHECK (LowSupplyCount >= 0),
        EmergencyCount INTEGER NOT NULL DEFAULT 0 CHECK (EmergencyCount >= 0),
        AlsItemNumber TEXT NOT NULL,
        VendorNumber TEXT NOT NULL,
        VendorItemNumber TEXT NOT NULL,
        CHECK ( LowSupplyCount >= EmergencyCount )
    ) STRICT;
    """)
    
    # ---------- Consumable Logs ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ConsumableLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductName TEXT NOT NULL,
            CertifiedValue TEXT NOT NULL CHECK (CertifiedValue != ''),
            CertificationDate TEXT NOT NULL
                CHECK (
                    (CertificationDate GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                    AND CertificationDate = date(CertificationDate))
                    OR CertificationDate = 'Not Set'
                ),
            LOT TEXT NOT NULL CHECK (LOT != ''),
            CoaFilePath TEXT NOT NULL CHECK (CoaFilePath != ''),
            Quantity INTEGER NOT NULL
                CHECK (Quantity = 1),

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
            PONumber TEXT NOT NULL CHECK (PONumber != ''),
            Comments TEXT DEFAULT '',

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

            Date TEXT NOT NULL
                CHECK (
                    Date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                    AND Date = date(Date)
                ),

            Initials TEXT NOT NULL
                CHECK (length(Initials) BETWEEN 2 AND 5),

            ActionType TEXT NOT NULL
                CHECK (
                    ActionType IN ('Received', 'Opened')
                ),
            PONumber TEXT NOT NULL CHECK (ActionType = 'Opened' OR PONumber != ''),
            FOREIGN KEY (ProductName)
                REFERENCES Products(ProductName)
                ON DELETE RESTRICT
        ) STRICT;
    """)

    # ---------- Application Details ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS AppVersion (
            OnlyRow INTEGER PRIMARY KEY CHECK (OnlyRow = 1),
            Version INTEGER NOT NULL DEFAULT 1
        ) STRICT;
    """)
    
    # ---------- Triggers ----------
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS already_opened_one
    BEFORE UPDATE ON ConsumableLogs
    BEGIN
        SELECT
            CASE
                WHEN
                    OLD.ProductName = NEW.ProductName AND
                    EXISTS(SELECT 1 FROM ConsumableLogs WHERE ProductName = NEW.ProductName AND id != NEW.id AND DateFinished = '' AND DateOpened != '' AND NEW.DateOpened >= DateOpened)
                THEN RAISE(ABORT, 'Cannot open when there is an unfinished item')
            END;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS on_emergency_opened_consumables 
    AFTER UPDATE ON ConsumableLogs
    BEGIN
        SELECT
            CASE
                WHEN 
                    OLD.ProductName = NEW.ProductName AND 
                    OLD.DateOpened = '' AND 
                    NEW.DateOpened != '' AND 
                    (SELECT COUNT(*) FROM ConsumableLogs WHERE ProductName = OLD.ProductName AND DateFinished = '' AND DateOpened = '') < (SELECT EmergencyCount FROM Products WHERE ProductName = OLD.ProductName)
                THEN RAISE(FAIL, 'Attempt to use emergency supplies.')
            END;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS on_emergency_opened_non_consumables
    AFTER INSERT ON NonConsumableLogs
    BEGIN
        SELECT
            CASE
                WHEN 
                    NEW.ActionType = 'Opened' AND
                    (SELECT COALESCE(SUM(Quantity), 0) FROM NonConsumableLogs WHERE ProductName = NEW.ProductName AND ActionType = 'Received') - (SELECT COALESCE(SUM(Quantity), 0) FROM NonConsumableLogs WHERE ProductName = NEW.ProductName AND ActionType = 'Opened') < (SELECT EmergencyCount FROM Products WHERE ProductName = NEW.ProductName)
                THEN RAISE(FAIL, 'Attempt to use emergency supplies.')
            END;
    END;
    """)

    if test:
        cursor.execute("DROP TRIGGER IF EXISTS on_update_negative_total;")

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS on_update_negative_total
    AFTER UPDATE ON NonConsumableLogs
    BEGIN
        SELECT
            CASE
                WHEN ((SELECT COALESCE(SUM(Quantity), 0) FROM NonConsumableLogs WHERE ProductName = NEW.ProductName AND ActionType = 'Received') - (SELECT COALESCE(SUM(Quantity), 0) FROM NonConsumableLogs WHERE ProductName = NEW.ProductName AND ActionType = 'Opened') < 0) OR ((SELECT COALESCE(SUM(Quantity), 0) FROM NonConsumableLogs WHERE ProductName = OLD.ProductName AND ActionType = 'Received') - (SELECT COALESCE(SUM(Quantity), 0) FROM NonConsumableLogs WHERE ProductName = OLD.ProductName AND ActionType = 'Opened') < 0) 
                THEN RAISE(ABORT, 'Cannot have negative total quantity')
            END;
    END;
    """)


    if test:
        cursor.execute("DROP TRIGGER IF EXISTS on_delete_negative_total;")

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS on_delete_negative_total
    BEFORE DELETE ON NonConsumableLogs
    BEGIN
        SELECT
            CASE
                WHEN (SELECT COALESCE(SUM(Quantity), 0) FROM NonConsumableLogs WHERE ProductName = OLD.ProductName AND ActionType = 'Received') - (SELECT COALESCE(SUM(Quantity), 0) FROM NonConsumableLogs WHERE ProductName = OLD.ProductName AND ActionType = 'Opened') + OLD.Quantity < 0
                THEN RAISE(ABORT, 'Cannot have negative total quantity')
            END;
    END;
    """)

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

    if test:
        cursor.execute("DROP TRIGGER IF EXISTS limit_nonconsumable_opened;")

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS limit_nonconsumable_opened
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
    recreate_products_total_supply(db_path)

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
    CREATE VIEW IF NOT EXISTS ConsumablesReport AS
    SELECT c.ProductName, p.Station, c.id AS "Order", c.LOT AS "Lot Number", c.CertifiedValue AS "Certified Value", c.CertificationDate AS "Certification Date", c.PONumber, c.DateReceived AS "Date Received", c.ReceivedInitials AS "Received by", c.DateOpened AS "Date Opened", c.OpenedInitials AS "Opened by", c.ExpiryDate AS "Expiry Date", c.DateFinished AS "Date Depleted", c.FinishedInitials AS "Disposed by", c.Comments
    FROM ConsumableLogs c
    LEFT JOIN Products p ON c.ProductName = p.ProductName;
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS AvailableConsumables AS
    SELECT l.*, p.Station
    FROM ConsumableLogs l
    JOIN Products p ON p.ProductName = l.ProductName 
    WHERE l.DateFinished == '';
    """)
    
    if test:
        cursor.execute("""
    DROP VIEW IF EXISTS OutOfStockNonConsumables;
    """)
    
    # Create the new view
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS OutOfStockNonConsumables AS
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

    if test:
        cursor.execute("""
    DROP VIEW IF EXISTS AvailableNonConsumables;
    """)
 
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS AvailableNonConsumables AS
    SELECT
        p.ProductName,
        COALESCE(SUM(CASE WHEN l.ActionType = 'Received' THEN l.Quantity ELSE 0 END), 0) AS TotalQuantityReceived,
        COALESCE(SUM(CASE WHEN l.ActionType = 'Opened' THEN l.Quantity ELSE 0 END), 0) AS TotalQuantityOpened,
        COALESCE(SUM(CASE WHEN l.ActionType = 'Received' THEN l.Quantity ELSE 0 END), 0)
            - COALESCE(SUM(CASE WHEN l.ActionType = 'Opened' THEN l.Quantity ELSE 0 END), 0) AS TotalQuantityAvailable,
        p.Station
    FROM Products p
    LEFT JOIN NonConsumableLogs l
        ON p.ProductName = l.ProductName
    WHERE p.IsConsumable = 'n'
    GROUP BY p.ProductName
    HAVING TotalQuantityReceived > TotalQuantityOpened;
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS ConsumablesAvailableTotaled AS
    SELECT p.ProductName, COALESCE(SUM(CASE WHEN c.DateFinished = '' THEN 1 ELSE 0 END), 0) AS TotalQuantityAvailable
    FROM Products p
    LEFT JOIN ConsumableLogs c ON c.ProductName = p.ProductName
    WHERE p.IsConsumable = 'y'
    GROUP BY p.ProductName
    """)


    recreate_dangerously_low(db_path)
    recreate_reorder_list(db_path) 
    
    if test:
        cursor.execute(""" DROP VIEW IF EXISTS OutOfStock; """)
    
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS OutOfStock AS
    SELECT
        p.ProductName,
        COALESCE(SUM(CASE WHEN l.ActionType = 'Received' THEN l.Quantity ELSE 0 END), 0)
            - COALESCE(SUM(CASE WHEN l.ActionType = 'Opened' THEN l.Quantity ELSE 0 END), 0) AS TotalQuantityAvailable,
        p.Station,
        p.IsConsumable
    FROM Products p
    LEFT JOIN NonConsumableLogs l
        ON p.ProductName = l.ProductName
    WHERE p.IsConsumable = 'n'
    GROUP BY p.ProductName
    HAVING TotalQuantityAvailable <= 0

    UNION ALL

    SELECT
        p.ProductName,
        COALESCE(SUM(CASE WHEN l2.DateFinished = '' THEN l2.Quantity ELSE 0 END), 0) AS TotalQuantityAvailable,
        p.Station,
        p.IsConsumable
    FROM Products p
    LEFT JOIN ConsumableLogs l2
        ON p.ProductName = l2.ProductName
    WHERE p.IsConsumable = 'y'
    GROUP BY p.ProductName
    HAVING TotalQuantityAvailable <= 0;

    """)

    conn.commit()
    conn.close()

def delete_db(db_path):
    """Delete the SQLite database file."""
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Database '{db_path}' deleted successfully.")
    else:
        print(f"Database '{db_path}' does not exist.")

def get_columns(relation_name, db_path):
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

def get_column_types(table_name, db_path):
    """
    Returns a dict mapping column name -> logical type: 'integer', 'float', 'text', 'date'
    """
    types = {}

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        for _, name, col_type, _, _, _ in cursor.fetchall():
            col_type_upper = col_type.upper()

            # Detect integer
            if "INT" in col_type_upper or "QUANTITY" in name.upper():
                types[name] = "integer"
            # Detect float/real/numeric
            elif any(x in col_type_upper for x in ["REAL", "FLOA", "DOUB"]):
                types[name] = "float"
            # Detect dates by name
            elif "DATE" in name.upper():
                types[name] = "date"
            else:
                types[name] = "text"

    return types

def get_expanded_query(relation_interface, db_path):
    """
    Build a SQL query that expands foreign key columns
    by LEFT JOINing referenced tables.
    """
    table_name = relation_interface.relation_name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1️⃣ Get foreign keys of this table
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    fks = cursor.fetchall()
    # Each row: (id, seq, table, from, to, on_update, on_delete, match)
    # 'from' = column in this table, 'table' = referenced table, 'to' = referenced column

    select_cols = [f"{table_name}.*"]  # start with all columns from main table
    join_clauses = []

    for fk in fks:
        fk_column = fk[3]       # column in this table
        ref_table = fk[2]       # referenced table
        ref_column = fk[4]      # referenced column

        # 2️⃣ Get columns from referenced table
        cursor.execute(f"PRAGMA table_info({ref_table})")
        ref_cols = cursor.fetchall()

        for col in ref_cols:
            col_name = col[1]
            # Exclude the foreign key column itself to avoid duplication
            if col_name != ref_column:
                alias = f"{fk_column}_{col_name}"
                select_cols.append(f"{ref_table[0].lower()}.{col_name}")

        # 3️⃣ Add LEFT JOIN for this foreign key
        join_clauses.append(f"LEFT JOIN {ref_table} {ref_table[0].lower()} "
                            f"ON {table_name}.{fk_column} = {ref_table[0].lower()}.{fk_column}")

    # 4️⃣ Build the final SQL
    where_clause, where_params = relation_interface.get_where_clauses_and_params()
    select_clause = ", ".join(select_cols)
    join_clause = " ".join(join_clauses)
    query = f"SELECT {select_clause} FROM {table_name} {join_clause} {where_clause};"
    conn.close()
    return query, where_params

def get_query(relation_interface, db_path):
    """
    Build a SQL query that selects all columns from the given table,
    without following foreign keys.
    """
    table_name = relation_interface.relation_name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get column names from this table
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]

    # Build SELECT clause
    select_clause = ", ".join([f"{table_name}.{col}" for col in columns])

    # Build WHERE clause from relation_interface
    where_clause, where_params = relation_interface.get_where_clauses_and_params()

    # Final query
    query = f"SELECT {select_clause} FROM {table_name} {where_clause};"

    conn.close()
    return query, where_params

def get_productname_recommendations(db_path, group_names):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            conditions = []

            group_names

            if "Without Discontinued" in group_names: 
                conditions.append("IsDiscontinued = 'n'")

            if "Nonconsumables Only" in group_names:
                conditions.append("IsConsumable = 'n'")
            elif "Consumables Only" in group_names:
                conditions.append("IsConsumable = 'y'")

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)

            query = f"SELECT ProductName FROM Products{where_clause} ORDER BY ProductName"
            cursor.execute(query)

            return [row[0] for row in cursor.fetchall()]

    except Exception as e:
        print("Error fetching product names:", e)
        return []

    return get_productnames(db_path, group_name)

def get_stations(db_path):
        """
        Returns a list of unique station names
        from the Products table.
        """
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT Station
                    FROM Products
                    WHERE Station IS NOT NULL
                    ORDER BY Station
                """)
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            print("Error fetching stations:", e)
            return []

def set_latest_app_version(db_path, version: int):
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        # Important for shared drives
        conn.execute("PRAGMA journal_mode=DELETE;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        conn.execute("PRAGMA synchronous = NORMAL;")

        conn.execute("""
            INSERT INTO AppVersion (OnlyRow, Version)
            VALUES (1, ?)
            ON CONFLICT(OnlyRow)
            DO UPDATE SET Version = excluded.Version;
        """, (version,))

        conn.commit()   # Explicit commit
    finally:
        conn.close()    # Explicit close

def is_product_consumable(db_path, name):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT *
            FROM Products
            WHERE ProductName = ?;
        """, (name,))

        row = cursor.fetchone()

        if row is None:
            raise Exception("The product does not exist")
        if row["IsConsumable"] == "n":
            return False
        return True

def set_barcode(db_path, name, barcode):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE Products
            SET BarcodeContains = ?
            WHERE ProductName = ?
        """, (barcode, name))
        if cur.rowcount <= 0:
            raise Exception("No product was updated")

def get_product_name(db_path, barcode_pattern):
    with sqlite3.connect(db_path) as conn:  
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT ProductName
            FROM Products
            WHERE ? LIKE '%' || BarcodeContains || '%'
            ORDER BY LENGTH(BarcodeContains) DESC
        """, (barcode_pattern,))
        row = cursor.fetchone()
    
    if row is None:
        return ""

    return row["ProductName"]

def is_non_cons_product_openable(db_path, name):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT 1
            FROM ProductsTotalSupply
            WHERE ProductName = ? and TotalQuantityAvailable = 0;
        """, (name,))

    return cursor.fetchone() is None

def is_cons_product_openable(db_path, name):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT 1
            FROM ConsumableLogs
            WHERE ProductName = ? and DateOpened != '' and DateFinished = ''
            LIMIT 1;
        """, (name,))

    return cursor.fetchone() is None

def is_cons_product_openable(db_path, name):
    with sqlite3.connect(db_path) as conn:   
        conn.row_factory = sqlite3.Row

        # Check if any unfinished product exists
        unfinished = conn.execute("""
            SELECT 1
            FROM ConsumableLogs
            WHERE ProductName = ? AND DateOpened != '' AND DateFinished = ''
            LIMIT 1
        """, (name,)).fetchone()

        if unfinished:
            # There is an unfinished product, cannot open a new one
            return False

        # Check if any available product exists
        available = conn.execute("""
            SELECT 1
            FROM ConsumableLogs
            WHERE ProductName = ? AND DateOpened = '' AND DateFinished = ''
            LIMIT 1
        """, (name,)).fetchone()

    return available is not None

def is_cons_product_finishable(db_path, name):
    with sqlite3.connect(db_path) as conn:   
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT 1
            FROM ConsumableLogs
            WHERE ProductName = ? and DateOpened != '' and DateFinished = ''
            LIMIT 1;
        """, (name,))

    return cursor.fetchone() is not None

def get_latest_app_version(db_path) -> int:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cursor = conn.execute("""
            SELECT Version FROM AppVersion WHERE OnlyRow = 1
        """)
        row = cursor.fetchone()
    finally:
        conn.close()
        return row[0] if row else 1
    return 1

def run_with_disabled_emergency_lock(db_path, func, *args, **kwargs):
    trigger_name_1 = "on_emergency_opened_non_consumables"
    trigger_name_2 = "on_emergency_opened_consumables"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # --- Internal helpers ---
    def get_trigger_sql(name):
        cur.execute(
            "SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?",
            (name,)
        )
        row = cur.fetchone()
        return row[0] if row else None

    def disable_trigger(name):
        cur.execute(f"DROP TRIGGER IF EXISTS {name}")
        conn.commit()

    def enable_trigger(name, sql):
        if sql:
            cur.execute(sql)
            conn.commit()

    # --- Backup original SQL ---
    sql_1 = get_trigger_sql(trigger_name_1)
    sql_2 = get_trigger_sql(trigger_name_2)

    try:
        # Disable both triggers
        disable_trigger(trigger_name_1)
        disable_trigger(trigger_name_2)

        # Run the wrapped function
        result = func(*args, **kwargs)

        # Restore triggers
        enable_trigger(trigger_name_1, sql_1)
        enable_trigger(trigger_name_2, sql_2)

        return result

    except Exception as e:
        # Always attempt to restore triggers
        try:
            enable_trigger(trigger_name_1, sql_1)
        except Exception:
            pass

        try:
            enable_trigger(trigger_name_2, sql_2)
        except Exception:
            pass

        # Re-raise original error
        raise e

    finally:
        conn.close()

