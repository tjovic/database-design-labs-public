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
| `nvarchar(max)` JSON parameter | `usp_AddInvoice`, called from `POST /invoices` |
| `OPENJSON(@Json, '$.items') WITH (...)` | [sql/03_StoredProcedures.sql](sql/03_StoredProcedures.sql) |
| `BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK` for a 1:N insert | the same procedure, inserting an `Invoice` header and its `InvoiceItem` rows together |
| "Thin API, fat stored procedure" | [api/routes.py](api/routes.py) — the route does no business logic, it only forwards JSON to SQL Server |

The full guided walkthrough (what to click, what to say, what to look
at in SSMS) is in [api/lab.md](api/lab.md). For anyone who wants to know
more, [how-it-works.md](how-it-works.md) explains what happens behind
each request, step by step, with links to Labs 7, 8, and 9. Once you've completed setup
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

Create a file named `.env` in the `demos/obp-rest-demo` folder (next to
`requirements.txt`). The easiest way is to copy the example file:

```bash
copy .env.example .env
```

Then open `.env` in a text editor and set the values. The complete file
looks like this:

```
SERVER=localhost\SQLEXPRESS
DATABASE=OBPRestDemo
DRIVER=ODBC Driver 18 for SQL Server
DB_USER=
DB_PASSWORD=
```

| Setting | What to put there |
|---|---|
| `SERVER` | Your SQL Server instance — exactly what you type in the **Server name** field in SSMS. `localhost` is the default instance, `localhost\SQLEXPRESS` is a named Express instance. These are **two different instances**. |
| `DATABASE` | `OBPRestDemo` — do not change it. |
| `DRIVER` | `ODBC Driver 18 for SQL Server` — the exact name, without `{ }`. Check the installed drivers with `python -c "import pyodbc; print(pyodbc.drivers())"`. |
| `DB_USER`, `DB_PASSWORD` | Leave **both empty** to log in with your Windows account (Windows authentication). Fill them in only for a SQL Server login, e.g. `DB_USER=sa`. |

Rules for the `.env` file:

- one setting per line, in the form `NAME=value`
- **no spaces** around `=`
- write the password exactly as it is, without quotes — characters such
  as `;`, `$`, `{` or `}` are fine. Only if the password contains a
  space or `#`, wrap it in single quotes: `DB_PASSWORD='my #pass'`
- the file name is exactly `.env` (not `.env.txt` — in Notepad, choose
  *Save as type: All files*)
- the app reads `.env` only at start: after a change, stop the app
  (CTRL+C) and start it again

### 3. Create the database

In SQL Server Management Studio (or `sqlcmd`), connected to the **same
instance** as `SERVER` in `.env`, run, in order:

```
sql/01_CreateDatabase.sql
sql/02_SeedData.sql          (run it twice on a new database)
sql/03_StoredProcedures.sql
```

On a brand-new database the first run of `02_SeedData.sql` reports a
`FOREIGN KEY` error (the first `IDENTITY` value on a new table is 0,
not 1); the second run fixes the data.

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

## Running on a computer without Python (packaged .exe)

To run the demo on a computer where you cannot install Python or other
software (for example, a lab computer without admin rights), package it
into a single `.exe` on a machine where you can.

### Build (on your own Windows computer)

```bash
cd demos/obp-rest-demo
build.bat
```

This creates the `dist` folder with everything the lab computer needs:

```
dist/obp-rest-demo.exe
dist/config.env
dist/sql/          (setup scripts)
```

### Run in the lab (step by step)

**1. Copy the files.** Copy the whole `dist` folder to the lab computer
(Desktop or a USB drive is fine). It contains:

```
obp-rest-demo.exe
config.env
sql\
```

**2. Find the SQL Server instance name.** Open SSMS on the lab
computer: the **Server name** field in the *Connect* dialog shows it,
for example `LAB-PC12\SQLEXPRESS`. After connecting you can also run:

```sql
SELECT @@SERVERNAME;
```

> [!IMPORTANT]
> `localhost` and `localhost\SQLEXPRESS` are **two different
> instances**. The database must be created on the same instance that
> you put in `config.env`.

**3. Create the database.** In SSMS, connected to that instance, open
each script (*File → Open → File*) and run it with **Execute** (F5), in
this order:

1. `sql\01_CreateDatabase.sql`
2. `sql\02_SeedData.sql` — run it **twice** on a new database. The
   first run reports a `FOREIGN KEY` error (the first `IDENTITY` value
   on a brand-new table is 0, not 1); the second run fixes the data.
3. `sql\03_StoredProcedures.sql`

Check that the data is there:

```sql
EXEC OBPRestDemo.dbo.usp_GetInvoices;   -- 2 invoices
```

**4. Edit `config.env`** in Notepad and set `SERVER` to the instance
name from step 2:

```
SERVER=LAB-PC12\SQLEXPRESS
```

Leave `DB_USER` and `DB_PASSWORD` empty to log in with your Windows
account. Fill them in only if you use a SQL Server login.

**5. Start the app.** Double-click `obp-rest-demo.exe`.

- If Windows shows *"Windows protected your PC"*, click **More info →
  Run anyway**.
- A black console window opens. The app first checks the database
  connection: if it fails, the window shows the error and a hint what
  to fix in `config.env`.
- If the connection works, the browser opens
  <http://127.0.0.1:8000/docs> automatically. If the browser does not open, type the
  address yourself.
- **Keep the console window open** while you work: closing it stops
  the app.

**6. Stop the app** by closing the console window (or pressing
CTRL+C in it).

### Troubleshooting in the lab

| Error | Cause and fix |
|---|---|
| `Login failed for user ...` (18456) **together with** `Cannot open database ...` (4060) | The database does not exist on that instance. Check that `SERVER` in `config.env` is the instance where you ran the scripts (step 2 and 3). |
| `Login failed for user ...` (18456) alone | With `DB_USER` set: wrong login or password — try the same login in SSMS (*SQL Server Authentication*). The console shows how many characters the password has, which helps to spot extra characters. With `DB_USER` empty: your Windows account has no login on that instance. |
| `Data source name not found` (IM002) | ODBC Driver 18 is not installed. Check in PowerShell: `Get-OdbcDriver`. |
| `[WinError 10048]` / address already in use | Another app uses the port. Change `PORT` in `config.env`. |
| The console window closes immediately | Open a Command Prompt in the folder and run `obp-rest-demo.exe` from there to see the error message. |
| A change in `config.env` has no effect | `config.env` is read only at start. Close the console window and start the `.exe` again. |

The lab computer needs **ODBC Driver 18 for SQL Server**; nothing else
has to be installed. The app listens only on `127.0.0.1`, so Windows
Firewall does not ask for permission.

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
├── how-it-works.md          # optional reading: how the app works, links to Labs 7–9
├── .env.example
├── build.bat               # builds dist/obp-rest-demo.exe
├── config.env.example      # settings for the packaged .exe
├── run.py                  # entry point for the packaged .exe
└── requirements.txt
```
