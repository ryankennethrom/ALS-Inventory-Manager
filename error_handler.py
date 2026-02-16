from error_ui import show_error_ui
import traceback
import sqlite3

def humanize_error(e: Exception) -> tuple[str, str]:
    msg = str(e)

    out = {"Short": "Unknown Error", "Details":msg}

    if "UNIQUE constraint failed: Products.ProductName" in msg:
        out["Short"]="This product name already exists in the database."
    
    elif "UNIQUE constraint failed: Products.AlsItemNumber" in msg:
        out["Short"]="This ALS item number already exists in the database."
    
    elif "cannot store TEXT value in REAL column Products.UnitPrice" in msg:
        out["Short"]="Unit Price must be a number greater than or equal to zero."
    
    elif "Cannot add consumable log for a non-consumable product" in msg:
        out["Short"]="The product is as a non-consumable. Please log it in Non-Consumable logs."
    
    elif "CHECK constraint failed: Alert >= 0" in msg:
        out["Short"]="Alert must be greater than or equal to zero."
    
    elif "CHECK constraint failed: IsConsumable IN ('n', 'y')" in msg:
        out["Short"]="IsConsumable must be either 'n' or 'y'."

    elif "ValueError: Invalid date" in msg:
        out["Short"]="Invalid date. Make sure Date has the format YYYY-MM-DD and is a real date."

    elif "CHECK constraint failed: length(Initials) BETWEEN 2 AND 5" in msg:
        out["Short"]="Initials must be between 2 and 5 characters."

    elif "sqlite3.IntegrityError: CHECK constraint failed: ActionType IN ('Received', 'Opened')" in msg:
        out["Short"]="Action Type must be 'Received' or 'Opened'."
    
    elif "FOREIGN KEY constraint failed" in msg:
        out["Short"]="Logs must reference an existing product name."
    
    elif "CHECK constraint failed: ( OpenedInitials == '' AND DateOpened == '' ) or (OpenedInitials != '' AND DateOpened != '')" in msg:
        out["Short"]="OpenedInitials and DateOpened must both have values."
    
    return (out["Short"],out["Details"])

def run_with_error_handling(master, func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        payload = {
                "status": "Ok",
                "result": result
        }
        return payload
    except Exception as e:
        short, details = humanize_error(traceback.format_exc())
        print(details)
        show_error_ui(short, details, master) 
        payload = {
                "status": "Error",
                "result": "None"
        }
        return payload
