
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

