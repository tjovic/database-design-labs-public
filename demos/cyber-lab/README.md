# Cyber Lab — SQL Injection Demo

An educational FastAPI application that uses a single login form to show
the difference between a **vulnerable** (concatenated SQL) and a **secure**
(parameterized SQL) approach, and demonstrates classic SQL injection
attacks against a live SQL Server database. Pairs with
[Lab 8, Section 2 — Client-Side Query Building](../../labs/lab08-complex-parameters.md).

> This application is intended for local learning only. The vulnerable
> endpoint really does execute user input as SQL — **do not expose it to
> a public network**.

This page covers setup. For a guided, click-by-click classroom script
(with diagrams for each payload), see [lab.md](lab.md).

---

## Prerequisites

- Windows + Python 3.10+
- **Microsoft SQL Server** (Express is enough) reachable via Windows
  authentication
- **ODBC Driver 18 for SQL Server**
  ([download](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server))
- **SQL Server Management Studio (SSMS)** or the `sqlcmd` command-line tool,
  to run the setup scripts in step 3 below
- Access to SQL Server with an account that has permission to create a database

Check that the driver is installed:

```bash
python -c "import pyodbc; print(pyodbc.drivers())"
```

The output must contain `ODBC Driver 18 for SQL Server`.

---

## Setup

### 1. Create a virtual environment and install dependencies

```bash
cd demos/cyber-lab
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Connection configuration

The defaults in [app/config.py](app/config.py) work for a local,
Windows-authenticated SQL Server:

```
SERVER=localhost
DATABASE=CyberLab
DRIVER=ODBC Driver 18 for SQL Server
```

To use another instance (for example `localhost\SQLEXPRESS`) or SQL
authentication, create a `.env` file in `demos/cyber-lab` with the
values you want to change, plus `DB_USER` and `DB_PASSWORD` for SQL
authentication.

### 3. Create the database and data

From `sqlcmd` (or SSMS) run:

```bash
sqlcmd -S localhost -E -C -i database\init.sql
sqlcmd -S localhost -E -C -i database\seed.sql
```

`init.sql` creates the `CyberLab` database and the `Users` and `CreditCards`
tables. `seed.sql` populates 3 users and 3 cards.

### 4. Verify the DB connection

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/db-test` — it returns the SQL Server version
if the connection works.

---

## Running

```bash
cd demos/cyber-lab
.venv\Scripts\activate
uvicorn app.main:app --reload
```

Endpoints:

| URL | Description |
|---|---|
| `/` | Home page |
| `/db-test` | Database connection check |
| `/login` | SQL injection demo (form + payload buttons) |

---

## Running on a computer without Python (packaged .exe)

To run the demo on a computer where you cannot install Python or other
software (for example, a lab computer without admin rights), package it
into a single `.exe` on a machine where you can.

### Build (on your own Windows computer)

```bash
cd demos/cyber-lab
build.bat
```

This creates the `dist` folder with everything the lab computer needs:

```
dist/cyber-lab.exe
dist/config.env
dist/database/     (setup scripts)
```

The packaged app uses port **8001**, so it can run next to the packaged
`obp-rest-demo` (port 8000). It listens only on `127.0.0.1`, so it is
not reachable from the network — important for an app that is
deliberately vulnerable.

### Run in the lab (step by step)

**1. Copy the files.** Copy the whole `dist` folder to the lab computer
(Desktop or a USB drive is fine). It contains:

```
cyber-lab.exe
config.env
database\
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

1. `database\init.sql`
2. `database\seed.sql`

Check that the data is there:

```sql
SELECT * FROM CyberLab.dbo.Users;   -- 3 users
```

**4. Edit `config.env`** in Notepad and set `SERVER` to the instance
name from step 2:

```
SERVER=LAB-PC12\SQLEXPRESS
```

Leave `DB_USER` and `DB_PASSWORD` empty to log in with your Windows
account. Fill them in only if you use a SQL Server login.

**5. Start the app.** Double-click `cyber-lab.exe`.

- If Windows shows *"Windows protected your PC"*, click **More info →
  Run anyway**.
- A black console window opens and the browser opens
  <http://127.0.0.1:8001/login> automatically. If the browser does not open, type the
  address yourself.
- **Keep the console window open** while you work: closing it stops
  the app.

**6. Stop the app** by closing the console window (or pressing
CTRL+C in it).

### Troubleshooting in the lab

| Error | Cause and fix |
|---|---|
| `Login failed for user ...` (18456) **together with** `Cannot open database ...` (4060) | The database does not exist on that instance. Check that `SERVER` in `config.env` is the instance where you ran the scripts (step 2 and 3). |
| `Login failed for user ...` (18456) alone | Your Windows account has no login on that instance. Use a SQL Server login (`DB_USER`, `DB_PASSWORD`). |
| `Data source name not found` (IM002) | ODBC Driver 18 is not installed. Check in PowerShell: `Get-OdbcDriver`. |
| `[WinError 10048]` / address already in use | Another app uses the port. Change `PORT` in `config.env`. |
| The page has no styling | Bootstrap is loaded from the internet (CDN). The demo still works without it. |
| The console window closes immediately | Open a Command Prompt in the folder and run `cyber-lab.exe` from there to see the error message. |
| A change in `config.env` has no effect | `config.env` is read only at start. Close the console window and start the `.exe` again. |

The lab computer needs **ODBC Driver 18 for SQL Server**; nothing else
has to be installed. The app listens only on `127.0.0.1`, so Windows
Firewall does not ask for permission.

---

## Demo: how to use

At `/login` there is a single form with two submit buttons:

- **Vulnerable** (`/login/vulnerable`) — builds SQL by string concatenation
- **Secure** (`/login/secure`) — uses a parameterized query (`?` placeholders)

Below the form are buttons that fill the `username` and `password` fields
with example payloads in one click. Run the demo like this:

1. Click a payload button (fills the inputs).
2. Click **Vulnerable** → see the effect of the attack.
3. Click the same payload again, then **Secure** → see that the attack
   fails.

### Test users (from `seed.sql`)

| Username | Password |
|---|---|
| `admin` | `12345` |
| `tomislav` | `tajna123` |
| `ana` | `ana2025` |

### Prepared payloads

#### 1. `' OR 1=1 --` — classic authentication bypass

The vulnerable query becomes:

```sql
SELECT Id, Username, FullName, Department, Password
FROM Users
WHERE Username = '' OR 1=1 --' AND Password = 'x'
```

`--` comments out everything after it, `1=1` is always true → **all users
are returned** together with their passwords (the "Password (leaked!)"
column in the results table).

#### 2. `admin' --` — log in as admin without knowing the password

```sql
WHERE Username = 'admin' --' AND Password = 'x'
```

The password check is commented out, the row for `admin` is returned.

#### 3. `' OR Username='admin' --` — targeted bypass

Similar to #1 but uses a specific condition instead of `1=1`, useful when
the attacker knows who they want to log in as.

#### 4. `' UNION SELECT Id, CardNumber, CVV, Owner, ExpiryDate FROM CreditCards --` — **data exfiltration**

```sql
SELECT Id, Username, FullName, Department, Password FROM Users
WHERE Username = ''
UNION
SELECT Id, CardNumber, CVV, Owner, ExpiryDate FROM CreditCards --' AND Password = 'x'
```

The login endpoint returns **credit card numbers** from a completely
different table. This is a qualitatively different attack from a bypass:
it is not about circumventing an access control, it is about stealing
data from a table that has nothing to do with login.

UNION requires the number and types of columns to match the original
query (here 5 nvarchar/int columns).

#### 5. `admin / 12345` — valid combination

For comparison — shows what a normal, legitimate login looks like.

---

## What exactly separates Vulnerable and Secure

### Vulnerable — [app/routes/login.py](app/routes/login.py) `/login/vulnerable`

```python
query = (
    "SELECT Id, Username, FullName, Department, Password "
    "FROM Users "
    f"WHERE Username = '{username}' AND Password = '{password}'"
)
cursor.execute(query)
```

User input becomes **part of the SQL statement's text**. The SQL parser
cannot tell data from code → the input can terminate a SQL clause and
inject a new one.

### Secure — [app/routes/login.py](app/routes/login.py) `/login/secure`

```python
query = """
    SELECT Id, Username, FullName, Department
    FROM Users
    WHERE Username = ? AND Password = ?
"""
cursor.execute(query, (username, password))
```

`?` are **placeholders**. The ODBC driver sends the SQL and parameters
separately; a parameter never becomes part of the parsed SQL. Input
`' OR 1=1 --` is interpreted as a literal username of that length —
there is no user with that name, so 0 rows are returned. Also:
`/login/secure` does not `SELECT` `Password`, so an accidental leak
cannot expose it.

Rule: **always use parameterized queries**. Input sanitization (escaping,
character blacklists) is fragile and bypassable; parameterization is
structurally safe.

---

## Project structure

```
cyber-lab/
├── app/
│   ├── main.py                # FastAPI entry point
│   ├── config.py              # connection settings and folder paths
│   ├── database.py            # pyodbc connection
│   ├── routes/
│   │   ├── home.py            # / and /db-test
│   │   └── login.py           # /login + /login/secure + /login/vulnerable
│   ├── templates/             # Jinja2 (base, index, login)
│   └── static/css/style.css
├── database/
│   ├── init.sql               # CREATE DATABASE + CREATE TABLE
│   └── seed.sql               # INSERT test data
├── build.bat                  # builds dist/cyber-lab.exe
├── config.env.example         # settings for the packaged .exe
├── run.py                     # entry point for the packaged .exe
├── requirements.txt
├── README.md                  # this file — setup
└── lab.md                     # guided classroom walkthrough
```

---

## Common problems

**`Login failed for user`** — SQL Server does not allow Windows auth for
the account running the Python process. Add your Windows account to the
SQL Server logins, or switch to SQL auth by setting
`DB_USER` and `DB_PASSWORD` (in `.env`, or in `config.env` for the .exe).

**`Cannot open database "CyberLab"`** — you did not run `init.sql`. Run
it from `sqlcmd` (above).

**`Data source name not found`** — ODBC Driver 18 is missing. Install it
(link above) and check again with `pyodbc.drivers()`.

**Port 8000 already in use** — if `demos/obp-rest-demo` is already running
on the same machine, it also defaults to port 8000. Stop it first, or
start this app on a different port: `uvicorn app.main:app --reload --port 8001`.

**Injection does not work (returns 0 rows even in vulnerable mode)** —
verify that you actually clicked the red **Vulnerable** button, not the
green **Secure** one. Both are `type="submit"` in the same form.
