import sqlite3

def create_monthly_email_recipients_table(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MonthlyEmailRecipients (
            Email TEXT PRIMARY KEY
        )
    """)


def add_default_monthly_email_recipients(conn):
    cursor = conn.cursor()

    recipients = [
        "ryankennethrom@gmail.com",
        "ryanrom14nalt@gmail.com"
    ]

    for email in recipients:
        cursor.execute("""
            INSERT OR IGNORE INTO MonthlyEmailRecipients (Email)
            VALUES (?)
        """, (email,))

def create_product_vendors_table(conn):
    cursor = conn.cursor()

    cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS ProductVendorDetails (
            id INTEGER PRIMARY KEY,
            ProductName TEXT,
            Price TEXT,
            AlsItemNumber TEXT,
            VendorNumber,
            VendorItemNumber
        );

    """
    )

    cursor.execute(
    """
        INSERT INTO ProductVendorDetails (ProductName, Price, AlsItemNumber, VendorNumber, VendorItemNumber)
        SELECT ProductName, Price, AlsItemNumber, VendorNumber, VendorItemNumber
        FROM Products;
    """
    )

def try_add_discontinued_column(conn):
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE Products ADD COLUMN IsDiscontinued TEXT NOT NULL DEFAULT 'n' CHECK (IsDiscontinued IN ('n', 'y'))")
    except sqlite3.OperationalError:
        pass

def clear_product_vendor_columns_on_products(conn):
    cursor = conn.cursor()


    cursor.execute(
    """
        ALTER TABLE Products DROP COLUMN Price;
    """
    )

    cursor.execute(
            """
                    ALTER TABLE Products DROP COLUMN AlsItemNumber;
            """
    )

    cursor.execute(
            """ALTER TABLE Products DROP COLUMN VendorNumber;"""
    )

    cursor.execute("""ALTER TABLE Products DROP COLUMN VendorItemNumber;""")


def update_vendor_table_constraints(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='trigger';
    """)
    triggers = cursor.fetchall()

    cursor.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='view';
    """)
    views = cursor.fetchall()

    # 3. Drop triggers
    for name, _ in triggers:
        cursor.execute(f"DROP TRIGGER IF EXISTS {name};")

    # 4. Drop views
    for name, _ in views:
        cursor.execute(f"DROP VIEW IF EXISTS {name};")
    
    cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS ProductVendorDetails_new (
            id INTEGER PRIMARY KEY,
            ProductName TEXT,
            Price REAL DEFAULT 0 CHECK (Price >= 0),
            AlsItemNumber TEXT NOT NULL,
            VendorNumber TEXT NOT NULL,
            VendorItemNumber TEXT NOT NULL
        );

    """
    )

    # 6. Copy data from old table
    cursor.execute("""
        INSERT INTO ProductVendorDetails_new
        SELECT * FROM ProductVendorDetails;
    """)

    # 7. Drop old table
    cursor.execute("DROP TABLE ProductVendorDetails;")

    # 8. Rename new table
    cursor.execute("ALTER TABLE ProductVendorDetails_new RENAME TO ProductVendorDetails;")

    # 9. Restore views
    for name, sql in views:
        cursor.execute(sql)

    # 10. Restore triggers
    for name, sql in triggers:
        cursor.execute(sql)

def vendor_productname_and_price_not_empty(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='trigger';
    """)
    triggers = cursor.fetchall()

    cursor.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='view';
    """)
    views = cursor.fetchall()

    # 3. Drop triggers
    for name, _ in triggers:
        cursor.execute(f"DROP TRIGGER IF EXISTS {name};")

    # 4. Drop views
    for name, _ in views:
        cursor.execute(f"DROP VIEW IF EXISTS {name};")
    
    cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS ProductVendorDetails_new (
            id INTEGER PRIMARY KEY,
            ProductName TEXT CHECK (ProductName != ''),
            Price REAL DEFAULT 0 CHECK (Price >= 0 AND Price != ''),
            AlsItemNumber TEXT NOT NULL,
            VendorNumber TEXT NOT NULL,
            VendorItemNumber TEXT NOT NULL
        );

    """
    )

    # 6. Copy data from old table
    cursor.execute("""
        INSERT INTO ProductVendorDetails_new
        SELECT * FROM ProductVendorDetails;
    """)

    # 7. Drop old table
    cursor.execute("DROP TABLE ProductVendorDetails;")

    # 8. Rename new table
    cursor.execute("ALTER TABLE ProductVendorDetails_new RENAME TO ProductVendorDetails;")

    # 9. Restore views
    for name, sql in views:
        cursor.execute(sql)

    # 10. Restore triggers
    for name, sql in triggers:
        cursor.execute(sql)

def only_unopened_are_available(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='trigger';
    """)
    triggers = cursor.fetchall()

    cursor.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='view';
    """)
    views = cursor.fetchall()

    # 3. Drop triggers
    for name, _ in triggers:
        cursor.execute(f"DROP TRIGGER IF EXISTS {name};")

    # 4. Drop views
    for name, _ in views:
        cursor.execute(f"DROP VIEW IF EXISTS {name};")
    

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS ConsumablesAvailableTotaled AS
    SELECT p.ProductName, COALESCE(SUM(CASE WHEN c.DateOpened = '' THEN 1 ELSE 0 END), 0) AS TotalQuantityAvailable
    FROM Products p
    LEFT JOIN ConsumableLogs c ON c.ProductName = p.ProductName
    WHERE p.IsConsumable = 'y'
    GROUP BY p.ProductName
    """)

    # 9. Restore views
    for name, sql in views:
        if name == "ConsumablesAvailableTotaled":
            continue
        cursor.execute(sql)

    # 10. Restore triggers
    for name, sql in triggers:
        cursor.execute(sql)

    
