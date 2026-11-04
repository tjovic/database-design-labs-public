# Cyber Lab — SQL Injection Demo

An educational FastAPI application that uses a single login form to show
the difference between a **vulnerable** (concatenated SQL) and a **secure**
(parameterized SQL) approach, and demonstrates classic SQL injection
attacks against a live SQL Server database.

> This application is intended for local learning only. The vulnerable
> endpoint really does execute user input as SQL — **do not expose it to
> a public network**.

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

The connection string is hard-coded in [app/database.py](app/database.py):

```python
SERVER=localhost
DATABASE=CyberLab
Trusted_Connection=yes
```

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
│   ├── database.py            # pyodbc connection
│   ├── routes/
│   │   ├── home.py            # / and /db-test
│   │   └── login.py           # /login + /login/secure + /login/vulnerable
│   ├── templates/             # Jinja2 (base, index, login)
│   └── static/css/style.css
├── database/
│   ├── init.sql               # CREATE DATABASE + CREATE TABLE
│   └── seed.sql               # INSERT test data
├── requirements.txt
└── README.md
```

---

## Common problems

**`Login failed for user`** — SQL Server does not allow Windows auth for
the account running the Python process. Add your Windows account to the
SQL Server logins, or switch the connection string to SQL auth
(`UID=...; PWD=...`).

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
