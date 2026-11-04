# OBP REST Demo

Demonstration application for lab exercises of the course **Database Design**.

---

## Before the lab

### 1. Start SQL Server

Verify that the SQL Server service is running.

---

### 2. Open the project

Open the project folder in Visual Studio Code.

---

### 3. Activate the virtual environment

PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

---

### 4. Start the REST API

```bash
uvicorn api.app:app --reload
```

If everything is fine, this will be displayed:

```
Uvicorn running on http://127.0.0.1:8000
```

---

### 5. Open Swagger

```
http://localhost:8000/docs
```

---

### 6. Reset the data

Run in SQL Server Management Studio:

```
sql/02_SeedData.sql
```

This resets the database to its initial state.

---

# Demonstration

1. GET /customers

2. GET /invoices

3. GET /invoices/{id}

4. POST /invoices

Verify in SSMS:

```sql
SELECT * FROM Invoice;

SELECT * FROM InvoiceItem;
```

5. PUT /invoices/{id}

6. DELETE /invoices/{id}

Verify again:

```sql
SELECT * FROM Invoice;

SELECT * FROM InvoiceItem;
```

Explain the effect of **ON DELETE CASCADE**.

---

# Stopping the application

In the terminal press:

```
CTRL + C
```
