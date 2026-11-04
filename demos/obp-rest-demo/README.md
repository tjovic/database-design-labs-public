# OBP REST Demo — JSON, REST, and Stored Procedures

An educational FastAPI application that exposes a small invoicing API
backed by SQL Server. It demonstrates the pattern taught in
[Lab 8, Section 6 — JSON Parameters](../../labs/lab08-complex-parameters.md):
a REST client sends a JSON document over HTTP, and a stored procedure
shreds it with `OPENJSON` and inserts it atomically.

> This application is a teaching aid for local use. It has no
> authentication and is not hardened for production — **do not expose
> it to a public network.**

---

## What it shows

| Lab 8 concept | Where it lives here |
|---|---|
| `nvarchar(max)` JSON parameter | `sp_AddInvoice`, called from `POST /invoices` |
| `OPENJSON(@Json, '$.items') WITH (...)` | [sql/03_StoredProcedures.sql](sql/03_StoredProcedures.sql) |
| `BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK` for a 1:N insert | the same procedure, inserting an `Invoice` header and its `InvoiceItem` rows together |
| "Thin API, fat stored procedure" | [api/routes.py](api/routes.py) — the route does no business logic, it only forwards JSON to SQL Server |

The full guided walkthrough (what to click, what to say, what to look
at in SSMS) is in [api/lab.md](api/lab.md). Setup details specific to
the API itself are in [api/README.md](api/README.md).

---

## Prerequisites

- Windows + Python 3.10+
- **Microsoft SQL Server** (Express is enough) reachable via Windows authentication
- **ODBC Driver 18 for SQL Server**
  ([download](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server))

---

## Setup

### 1. Install dependencies

```bash
cd demos/obp-rest-demo
pip install -r requirements.txt
```

### 2. Configure the connection

Copy the example environment file and adjust if needed (the defaults
work for a local, Windows-authenticated SQL Server instance):

```bash
copy .env.example .env
```

### 3. Create the database

In SQL Server Management Studio (or `sqlcmd`), run, in order:

```
sql/01_CreateDatabase.sql
sql/02_SeedData.sql
sql/03_StoredProcedures.sql
```

`01_CreateDatabase.sql` drops and recreates a dedicated `OBPRestDemo`
database — it does **not** touch `AdventureWorksENG`. `02_SeedData.sql`
can be re-run at any time to reset the demo data.

### 4. Run the API

```bash
uvicorn api.app:app --reload
```

Open Swagger at <http://localhost:8000/docs>.

---

## Project structure

```
obp-rest-demo/
├── api/
│   ├── app.py              # FastAPI entry point
│   ├── config.py           # reads .env
│   ├── database.py         # pyodbc connection + read helpers
│   ├── models.py           # Pydantic request/response shapes
│   ├── routes.py           # GET/POST/PUT/DELETE /invoices, GET /customers
│   ├── README.md           # API-specific setup notes
│   └── lab.md              # guided classroom walkthrough
├── sql/
│   ├── 01_CreateDatabase.sql
│   ├── 02_SeedData.sql
│   └── 03_StoredProcedures.sql
├── .env.example
└── requirements.txt
```
