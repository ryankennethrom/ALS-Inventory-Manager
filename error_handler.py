from error_ui import show_error_ui
import traceback
import sqlite3

def humanize_sqlite_error(e: Exception) -> tuple[str, str]:
    msg = str(e)

    if isinstance(e, sqlite3.IntegrityError):
        if "UNIQUE constraint failed" in msg:
            return (
                "Duplicate value",
                "This record already exists. Please use a unique value."
            )

        if "FOREIGN KEY constraint failed" in msg:
            return (
                "Invalid reference",
                "The selected item does not exist or was deleted."
            )

        if "NOT NULL constraint failed" in msg:
            field = msg.split(":")[-1].strip()
            return (
                "Missing required field",
                f"The field '{field}' must not be empty."
            )

        if "CHECK constraint failed" in msg:
            return (
                "Invalid value",
                "One or more values do not meet the required conditions."
            )

    if isinstance(e, sqlite3.OperationalError):
        if "database is locked" in msg:
            return (
                "Database busy",
                "Another operation is using the database. Please try again."
            )

        if "no such table" in msg or "no such column" in msg:
            return (
                "Internal error",
                "The application is out of sync with the database schema."
            )

    return (
        "Database error",
        msg  # fallback to raw details
    )

def run_with_error_handling(func, *args, **kwargs):
    """
    Run any function safely and return:
        status_code: "ok" or "error"
        result: function result or None
        error_details: traceback if error or None
    Shows error UI automatically if an exception occurs.
    """
    try:
        result = func(*args, **kwargs)
        return "ok", result, None
    except Exception as e:
        short, details = humanize_sqlite_error(e)
        return "error", None, {"short":short, "details": details}
