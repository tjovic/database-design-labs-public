import pyodbc

from api.config import SERVER
from api.config import DATABASE
from api.config import DRIVER
from api.config import DB_USER
from api.config import DB_PASSWORD


def quote(value):
    """Wrap a value in { } so that characters such as ; or } in a
    password cannot break the connection string (ODBC escaping rule)."""
    return "{" + value.replace("}", "}}") + "}"


def get_connection():

    connection_string = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "TrustServerCertificate=yes;"
    )

    if DB_USER:
        # SQL authentication (login and password)
        connection_string += f"UID={quote(DB_USER)};PWD={quote(DB_PASSWORD or '')};"
    else:
        # Windows authentication
        connection_string += "Trusted_Connection=yes;"

    return pyodbc.connect(connection_string)


def get_customers():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("EXEC usp_GetCustomers")

    result = cursor.fetchall()

    conn.close()

    return result


def get_invoice(invoice_id: int):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "EXEC usp_GetInvoice ?",
        invoice_id
    )

    result = cursor.fetchall()

    conn.close()

    return result


def get_invoices():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("EXEC usp_GetInvoices")

    result = cursor.fetchall()

    conn.close()

    return result


if __name__ == "__main__":

    conn = get_connection()

    print("Connected to SQL Server!")

    conn.close()
