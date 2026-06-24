from datetime import date

def get_today_date_str():
    """Return today's date as a YYYY-MM-DD string."""
    return date.today().strftime("%Y-%m-%d")
