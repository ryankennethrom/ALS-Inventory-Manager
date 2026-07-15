
def create_monthly_email_recipients_table(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MonthlyEmailRecipients (
            Email TEXT PRIMARY KEY
        )
    """)

