import pyodbc


def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=CyberLab;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    return conn