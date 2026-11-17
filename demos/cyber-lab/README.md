# Cyber Lab — SQL Injection Demo

An educational FastAPI application about **designing the data access of
an application correctly**, so that SQL injection cannot happen. Each page
has a **vulnerable** version (SQL built by string concatenation) and a
**secure** version (parameterized SQL), running against a live SQL Server
database:

- **`/login`** — a login that answers only *welcome* or *wrong password*;
- **`/search`** — a product search that shows a table of results.

The attacks are shown only to explain **why** each design rule exists —
see [Design rules](#design-rules-this-demo-teaches) below. Pairs with
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

### 2. Configure the connection

Create a file named `.env` in the `demos/cyber-lab` folder (next to
`requirements.txt`). The easiest way is to copy the example file:

```bash
copy .env.example .env
```

Then open `.env` in a text editor and set the values. The complete file
looks like this:

```
SERVER=localhost\SQLEXPRESS
DATABASE=CyberLab
DRIVER=ODBC Driver 18 for SQL Server
DB_USER=
DB_PASSWORD=
```

| Setting | What to put there |
|---|---|
| `SERVER` | Your SQL Server instance — exactly what you type in the **Server name** field in SSMS. `localhost` is the default instance, `localhost\SQLEXPRESS` is a named Express instance. These are **two different instances**. |
| `DATABASE` | `CyberLab` — do not change it. |
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

Without a `.env` file the app uses `SERVER=localhost`,
`DATABASE=CyberLab` and Windows authentication.

### 3. Create the database and data

From `sqlcmd` (or SSMS) run — use the same instance as `SERVER` in
`.env` after `-S`:

```bash
sqlcmd -S localhost\SQLEXPRESS -E -C -i database\init.sql
sqlcmd -S localhost\SQLEXPRESS -E -C -i database\seed.sql
```

`init.sql` creates the `CyberLab` database and three tables: `Users`,
`CreditCards`, and `Products`. `seed.sql` fills them with 3 users, 3
credit cards, and 8 products.

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
| `/` | Home page (links to both demo pages) |
| `/db-test` | Database connection check |
| `/login` | Login form — leaks through welcome / error / blind |
| `/search` | Product search — leaks through `UNION` into the result table |

---

## Running on a computer without Python (packaged .exe)

To run the demo on a computer where you cannot install Python or other
software (for example, a lab computer without admin rights), package it
into a single `.exe` on a machine where you can.

### Build (on your own Windows computer)

**What you need:**

| | Build computer (home) | Lab computer |
|---|---|---|
| Windows 10/11, 64-bit | yes | yes |
| Python 3.10+ in PATH (`python --version` works) | yes | **no** |
| Internet access | first build only (installs packages) | only for the page styling (Bootstrap from a CDN) |
| ODBC Driver 18 for SQL Server | only to test the `.exe` | yes |
| Admin rights | no | no |

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
- A black console window opens. The app first checks the database
  connection: if it fails, the window shows the error and a hint what
  to fix in `config.env`.
- If the connection works, the browser opens
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
| `Login failed for user ...` (18456) alone | With `DB_USER` set: wrong login or password — try the same login in SSMS (*SQL Server Authentication*). The console shows how many characters the password has, which helps to spot extra characters. With `DB_USER` empty: your Windows account has no login on that instance. |
| `Data source name not found` (IM002) | ODBC Driver 18 is not installed. Check in PowerShell: `Get-OdbcDriver`. |
| `[WinError 10048]` / address already in use | Another app uses the port. Change `PORT` in `config.env`. |
| The page has no styling | Bootstrap is loaded from the internet (CDN). The demo still works without it. |
| The console window closes immediately | Open a Command Prompt in the folder and run `cyber-lab.exe` from there to see the error message. |
| A change in `config.env` has no effect | `config.env` is read only at start. Close the console window and start the `.exe` again. |

The lab computer needs **ODBC Driver 18 for SQL Server**; nothing else
has to be installed. The app listens only on `127.0.0.1`, so Windows
Firewall does not ask for permission.

---

## Design rules this demo teaches

The goal of the demo is not to learn attacks, but to learn five rules for
designing an application's database access:

| Rule | Prevents | Seen in the demo |
|---|---|---|
| **1. Parameters, never string concatenation** — user input is sent as a parameter value (`?` placeholders or stored procedure parameters) | the attack itself: input cannot become SQL | the green **Secure** buttons on both pages |
| **2. Generic error messages** — the user sees a general message, the details go to a log | leaking data and table structure through error messages | the vulnerable login prints the SQL error |
| **3. Least privilege** — the application's SQL Server login can reach only what the application needs | one mistake exposing the whole database | the search page reaches `Users` and `CreditCards` |
| **4. Hashed passwords** — the database stores a password hash, never the password | readable passwords in a stolen or copied table | passwords appear in the search results |
| **5. Hiding the output is not protection** | false confidence ("our page shows nothing") | the login leaks data through the welcome text, an error, or yes/no answers |

Rule 1 removes the cause. Rules 2–4 limit the damage if a mistake ever
slips through. Rule 5 warns against a fix that does not work.

> [!NOTE]
> Rules 3 and 4 are **deliberately broken** in this demo: the application
> connects with your own account (which can read every table), and the
> passwords are stored as plain text. That way every effect is visible.
> [lab.md](lab.md#32-design-rule-3--least-privilege) shows how a real
> application login with least privilege is set up.

---

## Demo: how to use

Each page has a red **Vulnerable** and a green **Secure** button. Under
every result is a gray **"Behind the scenes"** panel with the SQL that
actually ran — a classroom X-ray that a real application would never show.

Typical flow for each example:

1. Click a prepared payload (it fills the input).
2. Click **Vulnerable** and look at the result and the executed SQL.
3. Run the same input with **Secure** — it has no effect.
4. Discuss which design rule prevents it.

For the full classroom script, organized around the five rules, see
[lab.md](lab.md).

### Test data (from `seed.sql`)

| Username | Password |
|---|---|
| `admin` | `12345` |
| `tomislav` | `tajna123` |
| `ana` | `ana2025` |

`CreditCards` holds 3 cards, and `Products` holds 8 products.

### Prepared examples

| Page | Example | What it demonstrates | Rule |
|---|---|---|---|
| `/login` | `admin` / `12345` | a normal login — both versions look the same | — |
| `/login` | `admin' --` | input changes the query: login without a password | 1 |
| `/login` | `' OR 1=1 --` | the condition is always true | 1 |
| `/login` | *welcome = a credit card number* | the one value the page shows (the name) is replaced with data from another table | 1, 5 |
| `/login` | *card number inside an error* | the database error message reveals data | 2, 5 |
| `/login` | *blind* (yes / no) | even a yes/no answer leaks data, one character at a time | 5 |
| `/search` | `Logitech` | a normal search | — |
| `/search` | *UNION → user passwords* | the result table lists users and their passwords | 1, 3, 4 |
| `/search` | *UNION → credit cards* | the result table lists credit cards | 1, 3 |

---

## What exactly separates Vulnerable and Secure

The only difference is **how the input reaches SQL Server** —
[app/routes/login.py](app/routes/login.py) and
[app/routes/search.py](app/routes/search.py).

### Vulnerable

```python
query = (
    "SELECT FullName FROM Users "
    f"WHERE Username = '{username}' AND Password = '{password}'"
)
cursor.execute(query)
```

The input is pasted into the SQL text. SQL Server cannot tell which part
of the text came from the developer and which from the user, so the input
can end a condition and add a new one.

### Secure

```python
query = "SELECT FullName FROM Users WHERE Username = ? AND Password = ?"
cursor.execute(query, (username, password))
```

`?` are **placeholders**. The SQL text and the values are sent separately:
SQL Server parses the statement first and then uses the values only as
values. Input such as `admin' --` is just a username that does not exist.
The secure paths also do not print database errors to the user (Rule 2).

Escaping quotes or blacklisting words such as `UNION` is **not** a
substitute: it tries to guess every dangerous input, while a parameter does
not need to guess anything.

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
│   │   ├── login.py           # /login + /login/secure + /login/vulnerable
│   │   └── search.py          # /search (vulnerable + secure, one route)
│   ├── templates/             # Jinja2 (base, index, login, search, _sql_panel)
│   └── static/css/style.css
├── database/
│   ├── init.sql               # CREATE DATABASE + Users, CreditCards, Products
│   └── seed.sql               # INSERT test data
├── build.bat                  # builds dist/cyber-lab.exe
├── config.env.example         # settings for the packaged .exe
├── run.py                     # entry point for the packaged .exe
├── .env.example               # connection settings template (copy to .env)
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
