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
at in SSMS) is in [api/lab.md](api/lab.md). Once you've completed setup
below, [api/README.md](api/README.md) is a quick reference for
re-running the demo without repeating the full setup.

---

## Prerequisites

- Windows + Python 3.10+
- **Microsoft SQL Server** (Express is enough) reachable via Windows authentication
- **ODBC Driver 18 for SQL Server**
  ([download](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server))
- **SQL Server Management Studio (SSMS)** or the `sqlcmd` command-line tool,
  to run the setup scripts in step 3 below

Check that the driver is installed:

```bash
python -c "import pyodbc; print(pyodbc.drivers())"
```

The output must contain `ODBC Driver 18 for SQL Server`.

---

## Setup

### 1. Create a virtual environment and install dependencies

```bash
cd demos/obp-rest-demo
python -m venv .venv
.venv\Scripts\activate
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

### 4. Verify the connection

```bash
python -m api.database
```

This should print `Connected to SQL Server!`. If it fails, see
[Common problems](#common-problems) below before continuing.

### 5. Run the API

```bash
.venv\Scripts\activate
uvicorn api.app:app --reload
```

Open Swagger at <http://localhost:8000/docs>.

> [!NOTE]
> This defaults to port 8000. If [`demos/cyber-lab`](../cyber-lab/) is
> already running on the same machine, it also defaults to port 8000 —
> stop it first, or start this one on a different port:
> `uvicorn api.app:app --reload --port 8001`.

---

## Common problems

**`Login failed for user`** — SQL Server does not allow Windows auth for
the account running the Python process. Add your Windows account to the
SQL Server logins, or switch `.env` to SQL auth and adjust
[api/database.py](api/database.py) to pass a username/password.

**`Data source name not found`** — ODBC Driver 18 is missing. Install it
(link above) and check again with `pyodbc.drivers()`.

**`Cannot open database "OBPRestDemo"`** — you did not run
`sql/01_CreateDatabase.sql`, or you ran it in a session connected to a
different SQL Server instance than the one in `.env`.

**`ModuleNotFoundError` when running `python -m api.database`** — run
this command from the `demos/obp-rest-demo` folder itself, not from
inside `api/`, and make sure the virtual environment is activated.

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
