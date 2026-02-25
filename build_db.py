import DB
import pandas as pd
import sqlite3
from datetime import datetime

def insert_excel_to_sqlite(
    excel_path: str,
    db_path: str,
    table_name: str,
    sheet_names,
    include_columns: dict | None = None,  # {excel_col: db_col}
):
    """
    Reads specific sheet(s) from an Excel file and inserts rows into an SQLite table.

    :param excel_path: Path to Excel file
    :param db_path: Path to SQLite database
    :param table_name: Table name to insert into
    :param sheet_names: Single sheet name (str) or list of sheet names
    :param include_columns: Optional dict mapping {excel_column: db_column}
    """

    if isinstance(sheet_names, str):
        sheet_names = [sheet_names]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        for sheet in sheet_names:
            df = pd.read_excel(excel_path, sheet_name=sheet)

            # Filter + rename columns if mapping provided
            if include_columns is not None:
                missing = set(include_columns.keys()) - set(df.columns)
                if missing:
                    raise ValueError(
                        f"Columns not found in sheet '{sheet}': {missing}"
                    )

                # Keep only mapped columns
                df = df[list(include_columns.keys())]

                # Rename to DB column names
                df = df.rename(columns=include_columns)

            # Convert datetime columns to YYYY-MM-DD
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.strftime("%Y-%m-%d")

            # Replace NaN with None (SQLite friendly)
            df = df.where(pd.notnull(df), None)

            columns = df.columns

            # Create table if it doesn't exist
            column_defs = ", ".join([f'"{col}" TEXT' for col in columns])
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {column_defs}
            )
            """
            cursor.execute(create_sql)

            # Prepare insert statement
            placeholders = ", ".join(["?"] * len(columns))
            column_names = ", ".join([f'"{c}"' for c in columns])

            insert_sql = f"""
            INSERT INTO "{table_name}" ({column_names})
            VALUES ({placeholders})
            """

            cursor.executemany(insert_sql, df.to_records(index=False))

        conn.commit()


def excel_to_dataframe(file_path, sheet_name: str, include_columns: dict):
    """
    file_path: path to Excel file
    
    sheet_name: name of sheet to process (str)

    include_columns: dict of {original_column: new_column_name}
        e.g. {"Customer Name": "customer", "Order Date": "date"}

    Returns:
        pandas DataFrame
    """

    # Read only the specified sheet
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Keep only columns that exist
    valid_columns = [col for col in include_columns if col in df.columns]
    df = df[valid_columns]

    # Rename columns
    df = df.rename(columns=include_columns)

    return df

def deduplicate(df, col_name="ProductName"):
    df['nan_count'] = df.isna().sum(axis=1)

    df_sorted = df.sort_values(by=[col_name, 'nan_count'])

    df_deduped = df_sorted.drop_duplicates(subset=col_name, keep='first')

    df_deduped = df_deduped.drop(columns='nan_count')
    
    return df_deduped

if __name__ == "__main__":
    db_path = "./inventory.db"
    DB.delete_db(db_path)
    DB.init_db(db_path)

    pm_df = excel_to_dataframe("./test.xlsm", "Product_Manager", {"Product Name":"ProductName", "UOM":"UnitOfMeasure", "Item Description":"ItemDescription", "Station":"Station", "Consumable":"IsConsumable"})
    print(pm_df.head(5))
    print(pm_df.tail(5))

    id_df = excel_to_dataframe("./test.xlsm", "Inventory", {"Product Name":"ProductName", "Consumable":"IsConsumable", "Alert number": "Alert"})
    alert_df = id_df.dropna(subset=["ProductName"])
    print(alert_df.head(5))
    print(alert_df.tail(5))


    merged = pd.merge(pm_df, alert_df, on=['ProductName','IsConsumable'], how='outer')
    
    print(merged.columns)
    
    print(f"Merged with duplicates: {len(merged)}")
    
    is_consumable_nan_rows = merged[merged['IsConsumable'].isna()]
    print(f"IsConsumable Nan rows : {len(is_consumable_nan_rows)}")
    print(merged)

    merged = deduplicate(merged)
    
    merged['ProductName_lower'] = merged['ProductName'].str.lower()
    merged = deduplicate(merged, col_name="ProductName_lower")

    print(f"Rows after deduplication: {len(merged)}")
    
    merged['Alert'] = merged['Alert'].fillna(5)
    merged['UnitOfMeasure'] = merged['UnitOfMeasure'].fillna('Not yet set')
    merged['ItemDescription'] = merged['ItemDescription'].fillna('Not yet set')
    merged['Station'] = merged['Station'].fillna('Not yet set')

    merged = merged.drop(columns=['ProductName_lower'])

    # merged.loc[merged["ProductName"] == "Centrifuge Tubes", "IsConsumable"] = 'n'
    # merged.loc[merged["ProductName"] == "FTIR Tips Wide Bore (Chanshow)", "IsConsumable"] = 'n'
    # merged.loc[merged["ProductName"] == "GC Caps Blue", "IsConsumable"] = 'n'
    # merged.loc[merged["ProductName"] == "KF Silver Caps with White Septa", "IsConsumable"] = 'n'
    # merged.loc[merged["ProductName"] == "Tubing, Black-Black PVCSolva 2-Stop 0.76mm pkg/12", "IsConsumable"] = 'n'
    # merged.loc[merged["ProductName"] == "Tubing, Grey-Grey Solva 2-Stop 1.3mm", "IsConsumable"] = 'n'

    id_df = excel_to_dataframe("./test.xlsm", "Inventory_Detailed", {"Product Name":"ProductName", "LOT":"LOT", "Quantity":"Quantity", "Date Received":"DateReceived", "Date Expired":"ExpiryDate", "Date Opened": "DateOpened", "Date Finished": "DateFinished", "PO#":"PONumber", "ALS Item#": "AlsItemNumber", "Vendor Item #":"VendorItemNumber"})
    
    df_source = pd.read_excel("./test.xlsm", sheet_name="Inventory_Detailed")
    ini = df_source.iloc[:, 5].copy()
    id_df["ReceivedInitials"] = ini.values
    ini = df_source.iloc[:, 8].copy()
    id_df["OpenedInitials"] = ini.values
    ini = df_source.iloc[:, 10].copy()
    id_df["FinishedInitials"] = ini.values

    id_df['AlsItemNumber'] = id_df['AlsItemNumber'].fillna(0)
    id_df['AlsItemNumber'] = id_df['AlsItemNumber'].astype(int)
    id_df['AlsItemNumber'] = id_df['AlsItemNumber'].replace({0:""})
    id_df['VendorNumber'] = ""
    id_df['VendorItemNumber'] = id_df['VendorItemNumber'].fillna("")
    id_df['PONumber'] = id_df['PONumber'].fillna("")
    id_df['DateReceived'] = id_df['DateReceived'].dt.strftime('%Y-%m-%d')
    id_df['ExpiryDate'] = id_df['ExpiryDate'].dt.strftime('%Y-%m-%d')
    id_df['DateOpened'] = id_df['DateOpened'].dt.strftime('%Y-%m-%d')
    id_df['DateOpened'] = id_df['DateOpened'].fillna("")
    id_df['DateFinished'] = id_df['DateFinished'].dt.strftime('%Y-%m-%d')
    id_df['DateFinished'] = id_df['DateFinished'].fillna("")
    id_df['OpenedInitials'] = id_df['OpenedInitials'].fillna("")
    id_df['FinishedInitials'] = id_df['FinishedInitials'].fillna("")
    
    with pd.option_context('display.max_columns', None):
        print(id_df.head(5))
        print(id_df.tail(5))

    
    # Create a mapping from df1 lowercase → df1 original casing
    mapping = merged.set_index(merged['ProductName'].str.lower())['ProductName'].to_dict()

    # Update df2 ProductName using the mapping
    id_df['ProductName'] = id_df['ProductName'].str.lower().map(mapping).fillna(id_df['ProductName'])
    print(f"Number of ComsumableLogs : {len(id_df)}")

    merged["IsConsumable"] = 'n'
    merged.loc[merged["ProductName"].isin(id_df["ProductName"]), 'IsConsumable'] = 'y'

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        merged.to_sql('Products', conn, if_exists='append', index=False)


    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        # id_df.to_sql('ConsumableLogs', conn, if_exists='append', index=False)
        cursor = conn.cursor()

        # Get the existing columns from Products table
        cursor.execute("PRAGMA table_info(ConsumableLogs)")
        existing_columns = [info[1] for info in cursor.fetchall()]  # info[1] is column name
        print(f"Existing columns in table: {existing_columns}")

        # Keep only DataFrame columns that exist in the table
        df_to_insert = id_df[[col for col in id_df.columns if col in existing_columns]]

        # Insert each row
        for _, row in df_to_insert.iterrows():
            columns_str = ", ".join(df_to_insert.columns)
            placeholders = ", ".join(["?"] * len(df_to_insert.columns))
            data_tuple = tuple(row)

            print(f"Inserting into columns ({columns_str}): {data_tuple}")
            cursor.execute(f'''
                INSERT INTO ConsumableLogs ({columns_str})
                VALUES ({placeholders})
            ''', data_tuple)

    i_df = excel_to_dataframe("./test.xlsm", "Inventory", {"Product Name":"ProductName", "Quantity":"Quantity" })
    i_df = i_df.dropna(subset=["ProductName"])

    mapping = merged.set_index(merged['ProductName'].str.lower())['ProductName'].to_dict()
    i_df['ProductName'] = i_df['ProductName'].str.lower().map(mapping).fillna(i_df['ProductName'])


    prod_quant = pd.merge(i_df, merged, on=['ProductName'], how='outer')
    prod_quant = prod_quant[prod_quant['IsConsumable'] != 'y']
    prod_quant = prod_quant.drop(columns=['IsConsumable', 'UnitOfMeasure', 'ItemDescription',
       'Station', 'Alert'])
    prod_quant["Initials"] = "RR"
    prod_quant["ActionType"] = "Received"
    prod_quant["Date"] = "1998-01-01"


    na_rows = prod_quant[prod_quant['Quantity'].isna()]
    
    with pd.option_context('display.max_columns', None):
        print(na_rows.head(5))

    print(f"Number of rows that has NaN value at the Quantity column: {len(na_rows)}")
    
    prod_quant = prod_quant.dropna(subset=["Quantity"])

    print(f"Minimum Quantity : {prod_quant["Quantity"].min()}")
    print(prod_quant.columns)
    print(prod_quant[prod_quant["Quantity"]==-1.0])

    prod_quant = prod_quant[prod_quant["Quantity"] > 0]
    
    # prod_quant = prod_quant[prod_quant["ProductName"] != "AN Std"]
    # prod_quant = prod_quant[prod_quant["ProductName"] != "ICP Std V26-10"]
    # prod_quant = prod_quant[prod_quant["ProductName"] != "ICP Std V26-500"]
    # prod_quant = prod_quant[prod_quant["ProductName"] != "Lithium Chloride, 2M in Ethanol 250mL"]
    # prod_quant = prod_quant[prod_quant["ProductName"] != "Conductivity TDS Std"]
    # prod_quant = prod_quant[prod_quant["ProductName"] != "Custom MA5 2000ug/g"]


    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        # id_df.to_sql('ConsumableLogs', conn, if_exists='append', index=False)
        cursor = conn.cursor()

        # Get the existing columns from Products table
        cursor.execute("PRAGMA table_info(NonConsumableLogs)")
        existing_columns = [info[1] for info in cursor.fetchall()]  # info[1] is column name
        print(f"Existing columns in table: {existing_columns}")

        # Keep only DataFrame columns that exist in the table
        df_to_insert = prod_quant[[col for col in prod_quant.columns if col in existing_columns]]

        # Insert each row
        for _, row in df_to_insert.iterrows():
            columns_str = ", ".join(df_to_insert.columns)
            placeholders = ", ".join(["?"] * len(df_to_insert.columns))
            data_tuple = tuple(row)

            print(f"Inserting into columns ({columns_str}): {data_tuple}")
            cursor.execute(f'''
                INSERT INTO NonConsumableLogs ({columns_str})
                VALUES ({placeholders})
            ''', data_tuple)

     # with sqlite3.connect(db_path) as conn:
     #    conn.execute("PRAGMA foreign_keys = ON;")
     #   prod_quant.to_sql('NonConsumableLogs', conn, if_exists='append', index=False)

