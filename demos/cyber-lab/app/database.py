import pyodbc

from app.config import SERVER, DATABASE, DRIVER, DB_USER, DB_PASSWORD


def get_connection():
    connection_string = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "TrustServerCertificate=yes;"
    )

    if DB_USER:
        # SQL authentication (login and password)
        connection_string += f"UID={DB_USER};PWD={DB_PASSWORD};"
    else:
        # Windows authentication
        connection_string += "Trusted_Connection=yes;"

    conn = pyodbc.connect(connection_string)

    return conn
