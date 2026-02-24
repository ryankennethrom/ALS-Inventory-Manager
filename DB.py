import sqlite3
import os
import re

def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")  # ensure FK checks
    return conn

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # ---------- Products ----------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Products (
        ProductName TEXT PRIMARY KEY,
        UnitOfMeasure TEXT NOT NULL,
        ItemDescription TEXT NOT NULL,
        Station TEXT NOT NULL,
        IsConsumable TEXT NOT NULL CHECK (IsConsumable IN ('n', 'y')),
        Alert INTEGER NOT NULL CHECK (Alert >= 0) 
    ) STRICT;
    """)
    
    # ---------- Consumable Logs ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ConsumableLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductName TEXT NOT NULL,
            LOT TEXT NOT NULL,
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
            PONumber TEXT NOT NULL,
            AlsItemNumber TEXT NOT NULL,
            VendorNumber TEXT NOT NULL,
            VendorItemNumber TEXT NOT NULL,


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
    WHERE DateFinished == '';
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
    CREATE VIEW IF NOT EXISTS ConsumablesAvailableTotaled AS
    SELECT p.ProductName, COALESCE(SUM(CASE WHEN c.DateFinished = '' THEN 1 ELSE 0 END), 0) AS TotalQuantityAvailable
    FROM Products p
    LEFT JOIN ConsumableLogs c ON c.ProductName = p.ProductName
    WHERE p.IsConsumable = 'y'
    GROUP BY p.ProductName
    """)


    cursor.execute(""" DROP VIEW IF EXISTS ReOrderList; """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS ReOrderList AS
    SELECT c.ProductName, c.TotalQuantityAvailable, p.IsConsumable, p.UnitOfMeasure, p.Station, p.Alert
    FROM ConsumablesAvailableTotaled c
    LEFT JOIN Products p ON c.ProductName = p.ProductName
    WHERE c.TotalQuantityAvailable <= p.Alert

    UNION ALL

    SELECT
        p.ProductName,
        COALESCE(n.TotalQuantityAvailable, 0) AS TotalQuantityAvailable,
        p.IsConsumable,
        p.UnitOfMeasure,
        p.Station,
        p.Alert
    FROM Products p
    LEFT JOIN AvailableNonConsumables n
        ON n.ProductName = p.ProductName
    WHERE p.IsConsumable = 'n'
      AND COALESCE(n.TotalQuantityAvailable, 0) <= p.Alert;
    """)

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
    date_pattern = re.compile(r'date', re.IGNORECASE)

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
            elif date_pattern.search(name):
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

def get_productnames(db_path, relation_name):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            if "nonconsumable" in relation_name.lower():
                where_clause = "WHERE IsConsumable = 'n'"
            elif "consumable" in relation_name.lower():
                where_clause = "WHERE IsConsumable = 'y'"
            else:
                where_clause = ""
            cursor.execute(f"SELECT ProductName FROM Products {where_clause} ORDER BY ProductName")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
    except Exception as e:
        print("Error fetching product names:", e)
        return []

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
