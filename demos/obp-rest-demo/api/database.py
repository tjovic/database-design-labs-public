import pyodbc

from api.config import SERVER
from api.config import DATABASE
from api.config import DRIVER


def get_connection():

    connection_string = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string)


def get_customers():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("EXEC sp_GetCustomers")

    result = cursor.fetchall()

    conn.close()

    return result


def get_invoice(invoice_id: int):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "EXEC sp_GetInvoice ?",
        invoice_id
    )

    result = cursor.fetchall()

    conn.close()

    return result


def get_invoices():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("EXEC sp_GetInvoices")

    result = cursor.fetchall()

    conn.close()

    return result


if __name__ == "__main__":

    conn = get_connection()

    print("Connected to SQL Server!")

    conn.close()
