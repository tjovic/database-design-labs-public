# Lab 1 – Views

Database: `AdventureWorksENG`

Today you will learn:
- What a View is (a saved SELECT statement, not stored data)
- How to create, use, modify, and drop Views
- How to query the database's own metadata using system Views

**Key idea to remember all lesson:**

> Views store SQL. Tables store data.

```sql
USE AdventureWorksENG;
GO
```

## Part 1 – Why Views Exist

A query that grows uncomfortable to read.

```sql
-- Stage 1: a plain SELECT
SELECT
    c.FirstName,
    c.LastName
FROM Customer AS c;
```

```sql
-- Stage 2: join the customer's city
SELECT
    c.FirstName,
    c.LastName,
    ci.Name AS City
FROM Customer AS c
JOIN City AS ci ON ci.IDCity = c.CityID;
```

```sql
-- Stage 3: add the state
SELECT
    c.FirstName,
    c.LastName,
    ci.Name AS City,
    s.Name  AS State
FROM Customer AS c
JOIN City  AS ci ON ci.IDCity  = c.CityID
JOIN State AS s  ON s.IDState = ci.StateID;
```

```sql
-- Stage 4: add purchase history
SELECT
    c.FirstName,
    c.LastName,
    ci.Name AS City,
    s.Name  AS State,
    COUNT(DISTINCT i.IDInvoice) AS InvoiceCount,
    SUM(ii.TotalPrice)          AS TotalSpent
FROM Customer AS c
JOIN City  AS ci ON ci.IDCity  = c.CityID
JOIN State AS s  ON s.IDState = ci.StateID
LEFT JOIN Invoice     AS i  ON i.CustomerID = c.IDCustomer
LEFT JOIN InvoiceItem AS ii ON ii.InvoiceID = i.IDInvoice
GROUP BY
    c.FirstName, c.LastName, ci.Name, s.Name;
```

```sql
-- Stage 5: add filtering, calculated column, ordering
SELECT
    c.FirstName + ' ' + c.LastName AS CustomerName,
    ci.Name AS City,
    s.Name  AS State,
    COUNT(DISTINCT i.IDInvoice) AS InvoiceCount,
    SUM(ii.TotalPrice)          AS TotalSpent,
    MAX(i.InvoiceDate)          AS LastPurchase
FROM Customer AS c
JOIN City  AS ci ON ci.IDCity  = c.CityID
JOIN State AS s  ON s.IDState = ci.StateID
LEFT JOIN Invoice     AS i  ON i.CustomerID = c.IDCustomer
LEFT JOIN InvoiceItem AS ii ON ii.InvoiceID = i.IDInvoice
WHERE i.InvoiceDate >= '2004-01-01'
GROUP BY
    c.FirstName, c.LastName, ci.Name, s.Name
HAVING SUM(ii.TotalPrice) > 1000
ORDER BY TotalSpent DESC;
```

```sql
-- Save this query as a View and call it with a single line
GO

CREATE VIEW dbo.vCustomerOverview
AS
SELECT
    c.FirstName + ' ' + c.LastName AS CustomerName,
    ci.Name AS City,
    s.Name  AS State,
    COUNT(DISTINCT i.IDInvoice) AS InvoiceCount,
    SUM(ii.TotalPrice)          AS TotalSpent,
    MAX(i.InvoiceDate)          AS LastPurchase
FROM Customer AS c
JOIN City  AS ci ON ci.IDCity  = c.CityID
JOIN State AS s  ON s.IDState = ci.StateID
LEFT JOIN Invoice     AS i  ON i.CustomerID = c.IDCustomer
LEFT JOIN InvoiceItem AS ii ON ii.InvoiceID = i.IDInvoice
WHERE i.InvoiceDate >= '2004-01-01'
GROUP BY
    c.FirstName, c.LastName, ci.Name, s.Name
HAVING SUM(ii.TotalPrice) > 1000;
GO
```

```sql
SELECT * FROM dbo.vCustomerOverview;

DROP VIEW dbo.vCustomerOverview;
GO
```

## Part 2 – The View Owns Nothing

A small, two-column View makes it easy to spot the moment when the underlying table changes and the View reflects it — without being touched.

```sql
GO

CREATE VIEW dbo.vCustomerNames
AS
SELECT
    FirstName,
    LastName
FROM Customer;
GO
```

```sql
SELECT * FROM dbo.vCustomerNames;
```

### Proving the View owns no data

```sql
-- Insert a new customer directly into the base table
INSERT INTO Customer (FirstName, LastName, Email, PhoneNumber, CityID)
VALUES ('Ada', 'Lovelace', 'ada@example.com', '555-0001', 1);
```

```sql
-- The View immediately shows the new row — because it runs its SELECT again
SELECT *
FROM dbo.vCustomerNames
WHERE FirstName = 'Ada';
```

```sql
-- Same idea with UPDATE — target our own test row (never real data)
UPDATE Customer
SET FirstName = 'Augusta'
WHERE Email = 'ada@example.com';
```

```sql
SELECT *
FROM dbo.vCustomerNames
WHERE LastName = 'Lovelace';
```

## Part 3 – Modifying and Dropping Views

```sql
-- Old-style: ALTER VIEW replaces the definition
GO

ALTER VIEW dbo.vCustomerNames
AS
SELECT
    FirstName,
    LastName,
    Email
FROM Customer;
GO
```

```sql
SELECT * FROM dbo.vCustomerNames;
```

```sql
-- Modern idiom (SQL Server 2016+): CREATE OR ALTER
-- Works whether the View exists or not — perfect for deployment scripts
GO

CREATE OR ALTER VIEW dbo.vCustomerNames
AS
SELECT
    FirstName,
    LastName,
    Email
FROM Customer;
GO
```

```sql
-- Remove the View (data is untouched)
DROP VIEW dbo.vCustomerNames;
GO
```

```sql
-- Underlying data still exists
SELECT TOP (5) *
FROM Customer;
```

## Part 4 – System Views: The Database Describing Itself

```sql
-- Every row = one table in the current database
SELECT * FROM sys.tables;
```

```sql
-- Every row = one column
SELECT * FROM sys.columns;
```

Two vocabularies for the same idea:

```sql
-- SQL Server-specific:
SELECT name FROM sys.tables ORDER BY name;
```

```sql
-- ANSI-standard (also works in MySQL, PostgreSQL, Oracle):
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_NAME;
```

```sql
-- List every column of every table
SELECT
    t.name AS TableName,
    c.name AS ColumnName
FROM sys.tables AS t
JOIN sys.columns AS c
    ON c.object_id = t.object_id
ORDER BY
    t.name,
    c.column_id;
```

```sql
-- Objects have IDs, just like business entities
SELECT OBJECT_ID('Customer');
SELECT OBJECT_NAME(OBJECT_ID('Customer'));
```

## Exercises

Try each exercise on your own first. Only look at the solution after you have attempted it.

### Exercise 1 – Create your first View

Task: Create a View named dbo.vCustomers that returns three columns from Customer: FirstName, LastName, Email. Then query the View and confirm rows come back.

**Solution**

```sql
GO

CREATE VIEW dbo.vCustomers
AS
SELECT
    FirstName,
    LastName,
    Email
FROM Customer;
GO

SELECT * FROM dbo.vCustomers;
```

### Exercise 2 – Modify the View

Task: Use CREATE OR ALTER VIEW to modify dbo.vCustomers so it also returns PhoneNumber. Query the View to verify.

**Solution**

```sql
GO

CREATE OR ALTER VIEW dbo.vCustomers
AS
SELECT
    FirstName,
    LastName,
    Email,
    PhoneNumber
FROM Customer;
GO

SELECT * FROM dbo.vCustomers;
```

### Exercise 3 – Hide a JOIN inside a View

Task: Create a View named dbo.vCustomerCities that returns FirstName, LastName, and the city name (aliased as City). The city name comes from the City table. Then query the View WITHOUT writing a JOIN.

**Hints**
- Customer.CityID → City.IDCity (join condition)

**Solution**

```sql
GO

CREATE OR ALTER VIEW dbo.vCustomerCities
AS
SELECT
    c.FirstName,
    c.LastName,
    ci.Name AS City
FROM Customer AS c
JOIN City AS ci
    ON ci.IDCity = c.CityID;
GO

SELECT * FROM dbo.vCustomerCities;
```

### Bonus Exercise (if you finish early)

Task: Using sys.tables, count how many tables exist in this database.

**Solution**

```sql
SELECT COUNT(*) AS TableCount
FROM sys.tables;
```

## Cleanup

Drop the Views you created so the training database stays clean.

```sql
GO

DROP VIEW IF EXISTS dbo.vCustomers;
GO

DROP VIEW IF EXISTS dbo.vCustomerCities;
GO

-- Also remove the test customer we inserted (identified by unique email)
DELETE FROM Customer WHERE Email = 'ada@example.com';
GO
```
