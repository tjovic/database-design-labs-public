# Lab 2 – Views (continued)

Database: `AdventureWorksENG`

Today you will learn:
- How to INSERT, UPDATE, DELETE through a View (and its rules)
- WITH CHECK OPTION — the View refuses changes that break its filter
- WITH SCHEMABINDING — the underlying tables cannot silently break the View
- WITH ENCRYPTION — hide the View's definition
- How to combine these options

Key idea to remember all lesson:

> A View is not just a window. A View has rules.

```sql
USE AdventureWorksENG;
GO
```

## Part 1 – Modifying Data Through a View

The rules for writing through a View:

1. The change must reference columns from EXACTLY ONE table.
2. Referenced columns must not be results of subqueries, aggregates, or calculations.
3. Referenced columns must not appear in GROUP BY, HAVING, or DISTINCT.
4. The View must include every column the target table needs (e.g. all NOT NULL columns without defaults).

```sql
-- Create the simple View from Lab 1
GO

CREATE OR ALTER VIEW dbo.vCustomers
AS
SELECT
    FirstName,
    LastName,
    Email,
    PhoneNumber,
    CityID
FROM Customer;
GO
```

```sql
-- INSERT through the View — it lands in the Customer table
INSERT INTO dbo.vCustomers (FirstName, LastName, Email, PhoneNumber, CityID)
VALUES ('Grace', 'Hopper', 'grace@example.com', '555-0002', 1);


-- Verify in the base table
SELECT *
FROM Customer
WHERE FirstName = 'Grace';
```

### A JOIN View is usually NOT updatable

```sql
GO

CREATE OR ALTER VIEW dbo.vCustomerCities
AS
SELECT
    c.IDCustomer,
    c.FirstName,
    c.LastName,
    ci.Name AS City
FROM Customer AS c
JOIN City AS ci ON ci.IDCity = c.CityID;
GO
```

```sql
-- Reading works fine
SELECT * FROM dbo.vCustomerCities;


-- INSERT that touches columns from BOTH tables will fail
INSERT INTO dbo.vCustomerCities (FirstName, LastName, City)
VALUES ('Alan', 'Turing', 'London');
-- Error: cannot decide which table this belongs to.


-- Even INSERT that touches only Customer columns is usually REFUSED.
-- SQL Server plays it safe with join Views and rejects the whole class:
--   Msg 4405: "View or function is not updatable because the modification
--              affects multiple base tables."
-- To make a join View updatable, use an INSTEAD OF trigger (out of scope here).
INSERT INTO dbo.vCustomerCities (FirstName, LastName)
VALUES ('Alan', 'Turing');
```

```sql
-- Cleanup for this section
GO

DROP VIEW IF EXISTS dbo.vCustomers;
GO

DROP VIEW IF EXISTS dbo.vCustomerCities;
GO
```

## Part 2 – WITH CHECK OPTION

The trap: a row you insert can vanish from your own View.

```sql
-- A View that filters credit cards
GO

CREATE OR ALTER VIEW dbo.vVisaCards
AS
SELECT
    IDCreditCard,
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
FROM CreditCard
WHERE Type = 'Visa';
GO
```

```sql
-- Query it — only Visa cards
SELECT * FROM dbo.vVisaCards;


-- Insert an American Express through the View
-- Default behavior: SUCCEEDS silently
INSERT INTO dbo.vVisaCards (Type, CardNumber, ExpirationMonth, ExpirationYear)
VALUES ('American Express', '378282246310005', 12, 2030);


-- But the new row does NOT appear through the View
SELECT * FROM dbo.vVisaCards WHERE CardNumber = '378282246310005';


-- It IS in the base table
SELECT * FROM CreditCard WHERE CardNumber = '378282246310005';
```

### The fix: WITH CHECK OPTION

```sql
-- Rewrite the View with WITH CHECK OPTION at the very end
GO

CREATE OR ALTER VIEW dbo.vVisaCards
AS
SELECT
    IDCreditCard,
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
FROM CreditCard
WHERE Type = 'Visa'
WITH CHECK OPTION;
GO
```

```sql
-- Now the same insert is REFUSED
INSERT INTO dbo.vVisaCards (Type, CardNumber, ExpirationMonth, ExpirationYear)
VALUES ('Discover', '6011000000000000', 6, 2029);
-- Error: value violates the CHECK OPTION.


-- A valid insert still works
INSERT INTO dbo.vVisaCards (Type, CardNumber, ExpirationMonth, ExpirationYear)
VALUES ('Visa', '4111111111111111', 3, 2028);
```

```sql
-- Cleanup for this section
GO

DROP VIEW IF EXISTS dbo.vVisaCards;
DELETE FROM CreditCard WHERE CardNumber IN ('378282246310005', '4111111111111111');
GO
```

## Part 3 – WITH SCHEMABINDING

Prevent underlying tables from silently breaking the View.

IMPORTANT: we do NOT touch shared tables like Customer here — dropping a column from a real table would destroy production data. Instead we create a throwaway table `SchemaBindingDemo` just for this demo.

```sql
-- Create a fresh test table we can safely drop columns from
GO

CREATE TABLE dbo.SchemaBindingDemo
(
    ID       int IDENTITY PRIMARY KEY,
    Name     nvarchar(50),
    Note     nvarchar(200)
);

INSERT INTO dbo.SchemaBindingDemo (Name, Note) VALUES
    ('Row 1', 'first'),
    ('Row 2', 'second');
GO
```

```sql
-- A plain View over our test table (no SCHEMABINDING)
GO

CREATE OR ALTER VIEW dbo.vDemoContacts
AS
SELECT ID, Name, Note
FROM dbo.SchemaBindingDemo;
GO
```

```sql
-- Drop a column the View depends on — nothing warns us
ALTER TABLE dbo.SchemaBindingDemo DROP COLUMN Note;


-- Now the View is broken
SELECT * FROM dbo.vDemoContacts;
-- Error: Invalid column name 'Note'.
```

```sql
-- Add the column back so the rest of the demo works
GO

ALTER TABLE dbo.SchemaBindingDemo ADD Note nvarchar(200) NULL;
```

### The fix: WITH SCHEMABINDING (goes BEFORE the AS)

Requires: two-part names (`dbo.SchemaBindingDemo`) and no `SELECT *`.

```sql
GO

CREATE OR ALTER VIEW dbo.vDemoContacts
WITH SCHEMABINDING
AS
SELECT ID, Name, Note
FROM dbo.SchemaBindingDemo;
GO
```

```sql
-- Now try to drop the column again
ALTER TABLE dbo.SchemaBindingDemo DROP COLUMN Note;
-- Error: dependent on column 'Note'. Refused.
```

```sql
-- Cleanup for this section
GO

DROP VIEW IF EXISTS dbo.vDemoContacts;
GO

DROP TABLE IF EXISTS dbo.SchemaBindingDemo;
GO
```

## Part 4 – WITH ENCRYPTION

Hide the View definition from `sp_helptext`. (Not real security — a determined attacker with privileges can still recover it.)

```sql
-- Plain View — definition is readable
GO

CREATE OR ALTER VIEW dbo.vActiveCards
AS
SELECT IDCreditCard, Type, CardNumber
FROM CreditCard
WHERE ExpirationYear >= 2026;
GO
```

```sql
-- sp_helptext shows the source
EXECUTE sp_helptext 'dbo.vActiveCards';
```

```sql
-- Encrypt it (option goes BEFORE the AS)
GO

CREATE OR ALTER VIEW dbo.vActiveCards
WITH ENCRYPTION
AS
SELECT IDCreditCard, Type, CardNumber
FROM CreditCard
WHERE ExpirationYear >= 2026;
GO
```

```sql
-- Now sp_helptext refuses
EXECUTE sp_helptext 'dbo.vActiveCards';


-- Query still works
SELECT * FROM dbo.vActiveCards;
```

Warning: once encrypted, you cannot un-encrypt. Losing your original source code means you can only DROP and re-CREATE. Always keep the source in Git.

```sql
GO

DROP VIEW IF EXISTS dbo.vActiveCards;
GO
```

## Part 5 – Combining Options

Placement rules:
- SCHEMABINDING and ENCRYPTION → BEFORE the AS
- CHECK OPTION → AFTER the SELECT

Multiple options before AS use one WITH, comma-separated. Order between them does not matter.

```sql
GO

CREATE OR ALTER VIEW dbo.vVisaCards
WITH SCHEMABINDING, ENCRYPTION
AS
SELECT
    IDCreditCard,
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
FROM dbo.CreditCard
WHERE Type = 'Visa'
WITH CHECK OPTION;
GO
```

```sql
-- Verify
SELECT TOP (5) * FROM dbo.vVisaCards;

GO

DROP VIEW IF EXISTS dbo.vVisaCards;
GO
```

## Exercises

Try each exercise on your own first. Only look at the solution after you have attempted it.

### Exercise 1 – Modify data through a View

Task:
- Create `dbo.vCategories` that returns all columns and rows from Category.
- Through the View:
  - (a) INSERT a category named 'Alarms'.
  - (b) RENAME it to 'Active Protection'.
  - (c) DELETE it.
  - (d) DROP the View.

**Solution**

```sql
GO

CREATE OR ALTER VIEW dbo.vCategories
AS
SELECT * FROM Category;
GO

-- (a) Insert
INSERT INTO dbo.vCategories (Name) VALUES ('Alarms');

-- (b) Update
UPDATE dbo.vCategories
SET Name = 'Active Protection'
WHERE Name = 'Alarms';

-- (c) Delete
DELETE FROM dbo.vCategories WHERE Name = 'Active Protection';

-- (d) Drop
GO

DROP VIEW dbo.vCategories;
GO
```

### Exercise 2 – Multi-table View: what is updatable?

Task:
- Create `dbo.vCustomerLocations` returning:
  - city name (CityName)
  - state name (StateName)
  - all customer columns
  - using Customer + City + State.
- Then try:
  - (a) INSERT a new city through the View. What happens?
  - (b) INSERT a new state through the View. What happens?
  - (c) INSERT a new customer using ONLY Customer columns. Did it work? Can you see them through the View? Are they in the Customer table?
  - (d) DROP the View.

**Solution**

```sql
GO

CREATE OR ALTER VIEW dbo.vCustomerLocations
AS
SELECT
    ci.Name AS CityName,
    s.Name  AS StateName,
    c.IDCustomer,
    c.FirstName,
    c.LastName,
    c.Email,
    c.PhoneNumber,
    c.CityID
FROM Customer AS c
JOIN City  AS ci ON ci.IDCity  = c.CityID
JOIN State AS s  ON s.IDState = ci.StateID;
GO

-- (a) Might succeed or fail depending on SQL Server version.
-- If it succeeds, it inserts into City (because CityName maps to City.Name only).
-- We use a clearly-labeled test value so cleanup can find it.
INSERT INTO dbo.vCustomerLocations (CityName) VALUES ('_TestCity_Lab02');

-- (b) Similar — may insert into State if it succeeds.
INSERT INTO dbo.vCustomerLocations (StateName) VALUES ('_TestState_Lab02');

-- (c) Should succeed — references only Customer columns.
--     Use unique test email so cleanup can find it later.
INSERT INTO dbo.vCustomerLocations (FirstName, LastName, Email, PhoneNumber, CityID)
VALUES ('Marie', 'Curie', 'marie@example.com', '555-0002', 1);

-- Check the base table (find our test row)
SELECT * FROM Customer WHERE Email = 'marie@example.com';

-- (d) Drop the view
GO

DROP VIEW dbo.vCustomerLocations;
GO

-- Clean up anything the tests may have actually inserted
DELETE FROM City  WHERE Name = '_TestCity_Lab02';
DELETE FROM State WHERE Name = '_TestState_Lab02';
DELETE FROM Customer WHERE Email = 'marie@example.com';
GO
```

### Exercise 3 – WITH CHECK OPTION

Task:
- Create `dbo.vAcceptedCards` returning all columns from CreditCard where Type is 'Visa' or 'MasterCard'.
- Then:
  - (a) INSERT an American Express through the View.
  - (b) Query the View for the new card. Do you see it? Is it in the table?
  - (c) Modify the View to REFUSE rows that would not be visible through it.
  - (d) Try INSERTing American Express again.
  - (e) Modify the View back to the default (allow invisible inserts).
  - (f) DROP the View.

**Solution**

```sql
-- Step 1: create
GO

CREATE OR ALTER VIEW dbo.vAcceptedCards
AS
SELECT IDCreditCard, Type, CardNumber, ExpirationMonth, ExpirationYear
FROM CreditCard
WHERE Type IN ('Visa', 'MasterCard');
GO

-- (a) Insert Amex — succeeds silently
INSERT INTO dbo.vAcceptedCards (Type, CardNumber, ExpirationMonth, ExpirationYear)
VALUES ('American Express', '378282246310005', 12, 2030);

-- (b) Query — you will NOT see it through the View
SELECT * FROM dbo.vAcceptedCards WHERE CardNumber = '378282246310005';

-- But it IS in the table
SELECT * FROM CreditCard WHERE CardNumber = '378282246310005';

-- (c) Add CHECK OPTION
GO

CREATE OR ALTER VIEW dbo.vAcceptedCards
AS
SELECT IDCreditCard, Type, CardNumber, ExpirationMonth, ExpirationYear
FROM CreditCard
WHERE Type IN ('Visa', 'MasterCard')
WITH CHECK OPTION;
GO

-- (d) Try Amex again — now refused
INSERT INTO dbo.vAcceptedCards (Type, CardNumber, ExpirationMonth, ExpirationYear)
VALUES ('American Express', '378282246310005', 12, 2030);

-- (e) Remove CHECK OPTION
GO

CREATE OR ALTER VIEW dbo.vAcceptedCards
AS
SELECT IDCreditCard, Type, CardNumber, ExpirationMonth, ExpirationYear
FROM CreditCard
WHERE Type IN ('Visa', 'MasterCard');
GO

-- (f) Drop
DROP VIEW dbo.vAcceptedCards;
GO
```

## Cleanup

```sql
-- Remove any leftover Views
GO

DROP VIEW IF EXISTS dbo.vCategories;
GO

DROP VIEW IF EXISTS dbo.vCustomerLocations;
GO

DROP VIEW IF EXISTS dbo.vAcceptedCards;

-- Remove test data.
-- Identify test customers by the unique test emails we assigned above,
-- NEVER by FirstName alone (there are many real customers with these names).
DELETE FROM CreditCard WHERE CardNumber IN ('378282246310005', '4111111111111111');
DELETE FROM Customer WHERE Email IN
    ('grace@example.com', 'marie@example.com', 'ada@example.com');
-- The 'Alan Turing' INSERT attempts above all failed (Msg 4405 or Msg 515),
-- so there is nothing to clean up for them.

-- Drop the safety table if it survived a partial run
DROP TABLE IF EXISTS dbo.SchemaBindingDemo;
GO
```
