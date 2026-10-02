# Lab 2 – Views (continued)

**Database:** `AdventureWorksENG`

In Lab 1, Views were introduced mainly as a way to simplify queries and hide complexity.

In this lab, we continue with a different question:

> **What rules apply when we modify data through a View?**

We will also look at several View options that control how a View behaves.

---

## Learning objectives

After completing this lab, you should be able to:

- modify data through a simple View;
- explain why some Views are not updatable;
- use `WITH CHECK OPTION` to prevent changes that would make rows disappear from a filtered View;
- use `WITH SCHEMABINDING` to prevent incompatible schema changes;
- explain what `WITH ENCRYPTION` does and does not protect;
- combine View options correctly.

Start by selecting the database:

```sql
USE AdventureWorksENG;
GO
```

---

# Section 1 – Modifying data through a View

A View is usually used for reading data, but some Views can also be used for:

- `INSERT`
- `UPDATE`
- `DELETE`

The important question is:

> Can SQL Server clearly map the change made through the View back to the underlying table?

A simple View over one table is often updatable.

More complex Views have additional restrictions.

---

## A simple updatable View

Create a simple View over `Customer`:

```sql
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

Now insert through the View:

```sql
INSERT INTO dbo.vCustomers
(
    FirstName,
    LastName,
    Email,
    PhoneNumber,
    CityID
)
VALUES
(
    'Grace',
    'Hopper',
    'grace@example.com',
    '555-0002',
    1
);
```

The row is inserted into the underlying `Customer` table.

Verify it:

```sql
SELECT *
FROM Customer
WHERE Email = 'grace@example.com';
```

You can also update through the View:

```sql
UPDATE dbo.vCustomers
SET PhoneNumber = '555-9999'
WHERE Email = 'grace@example.com';
```

And delete through the View:

```sql
DELETE FROM dbo.vCustomers
WHERE Email = 'grace@example.com';
```

The View itself does not store a separate copy of the row.

The modification affects the underlying table.

---

## General rules

A View is more likely to be updatable when SQL Server can clearly identify the affected base-table rows.

Typical restrictions include:

- the change should affect columns from one base table;
- calculated columns cannot be modified directly;
- aggregate results cannot be modified directly;
- `GROUP BY`, `HAVING`, and `DISTINCT` make direct modifications more restricted;
- the View must expose the columns required to create a valid row in the underlying table.

The easiest way to understand these rules is to look at examples.

---

## JOIN Views have additional restrictions

Create a View that joins `Customer` and `City`:

```sql
CREATE OR ALTER VIEW dbo.vCustomerCities
AS
SELECT
    c.IDCustomer,
    c.FirstName,
    c.LastName,
    c.Email,
    c.PhoneNumber,
    c.CityID,
    ci.Name AS CityName
FROM Customer AS c
JOIN City AS ci
    ON ci.IDCity = c.CityID;
GO
```

Reading from the View works normally:

```sql
SELECT TOP (10) *
FROM dbo.vCustomerCities;
```

A modification that SQL Server can map to one base table may be allowed.

For example:

```sql
UPDATE dbo.vCustomerCities
SET LastName = 'Updated'
WHERE IDCustomer = 1;
```

Only a column from `Customer` is being modified.

However, one statement cannot use the View to modify columns from multiple base tables at the same time.

For example:

```sql
UPDATE dbo.vCustomerCities
SET
    LastName = 'Updated',
    CityName = 'New City'
WHERE IDCustomer = 1;
```

This attempts to modify both:

- `Customer.LastName`
- `City.Name`

SQL Server rejects the statement because one View modification cannot update multiple base tables.

> **Key idea:** A joined View is not automatically read-only, but modifications are limited to changes SQL Server can map unambiguously to one base table.

---

## Calculated columns are read-only

A View can contain calculated values:

```sql
CREATE OR ALTER VIEW dbo.vInvoiceItems
AS
SELECT
    IDInvoiceItem,
    Quantity,
    InitialPrice,
    Quantity * InitialPrice AS LineTotal
FROM InvoiceItem;
GO
```

Reading the calculated column is fine:

```sql
SELECT TOP (10) *
FROM dbo.vInvoiceItems;
```

Updating a normal base-table column can work:

```sql
UPDATE dbo.vInvoiceItems
SET Quantity = 5
WHERE IDInvoiceItem = 1;
```

But the calculated value itself cannot be directly updated:

```sql
UPDATE dbo.vInvoiceItems
SET LineTotal = 500
WHERE IDInvoiceItem = 1;
```

Why?

`LineTotal` is not a stored value in `InvoiceItem`.

It is calculated from:

```sql
Quantity * InitialPrice
```

---

## Aggregate Views are not directly updatable

Create a View with aggregate functions:

```sql
CREATE OR ALTER VIEW dbo.vInvoiceSummary
AS
SELECT
    InvoiceID,
    COUNT(*) AS NumberOfItems,
    SUM(Quantity) AS TotalQuantity,
    SUM(Quantity * InitialPrice) AS TotalAmount
FROM InvoiceItem
GROUP BY InvoiceID;
GO
```

Querying it works normally:

```sql
SELECT TOP (10) *
FROM dbo.vInvoiceSummary;
```

But this does not work:

```sql
UPDATE dbo.vInvoiceSummary
SET TotalAmount = 1000
WHERE InvoiceID = 1;
```

`TotalAmount` is calculated from several rows in `InvoiceItem`.

It does not represent one stored column in one base-table row.

---

## DISTINCT also restricts modifications

A View may remove duplicate values using `DISTINCT`:

```sql
CREATE OR ALTER VIEW dbo.vCreditCardTypes
AS
SELECT DISTINCT
    Type
FROM CreditCard;
GO
```

Querying it is fine:

```sql
SELECT *
FROM dbo.vCreditCardTypes;
```

But this is not directly updatable:

```sql
UPDATE dbo.vCreditCardTypes
SET Type = 'VISA'
WHERE Type = 'Visa';
```

One row in the View may represent many rows in `CreditCard`.

---

## Check your understanding

1. Why can a simple one-table View often be updated?
2. Can a calculated column be updated directly?
3. Why are aggregate Views usually not directly updatable?
4. Is every JOIN View read-only?
5. Can one View modification change columns from two base tables at the same time?

<details>
<summary>Show answers</summary>

1. Because SQL Server can usually map the View row directly to one row in one base table.
2. No. The value is derived from other columns.
3. Because one View row may represent calculations over several base-table rows.
4. No. Some modifications may be allowed when the change maps to one base table.
5. No. A single modification through such a View cannot update multiple base tables.

</details>

---

## Cleanup

```sql
DROP VIEW IF EXISTS dbo.vCustomers;
DROP VIEW IF EXISTS dbo.vCustomerCities;
DROP VIEW IF EXISTS dbo.vInvoiceItems;
DROP VIEW IF EXISTS dbo.vInvoiceSummary;
DROP VIEW IF EXISTS dbo.vCreditCardTypes;
GO

DELETE FROM Customer
WHERE Email = 'grace@example.com';
GO
```

---

# Section 2 – WITH CHECK OPTION

A filtered View shows only rows that satisfy its `WHERE` condition.

But by default, SQL Server may allow a change through the View that creates a row which does **not** satisfy that condition.

The result can be surprising:

> You insert a row through the View, but the row immediately disappears from the View.

---

## The disappearing row problem

Create a View that shows only Visa cards:

```sql
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

Insert an American Express card through the Visa View:

```sql
INSERT INTO dbo.vVisaCards
(
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
)
VALUES
(
    'American Express',
    '378282246310005',
    12,
    2030
);
```

The insert succeeds.

But the row is not visible through the View:

```sql
SELECT *
FROM dbo.vVisaCards
WHERE CardNumber = '378282246310005';
```

It does exist in the base table:

```sql
SELECT *
FROM CreditCard
WHERE CardNumber = '378282246310005';
```

Why?

The View filters with:

```sql
WHERE Type = 'Visa'
```

but the inserted row has `Type = 'American Express'`.

---

## Visualizing the problem

```mermaid
flowchart LR
    A["INSERT through View"]
    B{"Row satisfies<br/>View WHERE?"}
    C["Visible through View"]
    D["Stored in base table<br/>but invisible in View"]

    A --> B
    B -->|Yes| C
    B -->|No| D
```

---

## The fix – WITH CHECK OPTION

Add `WITH CHECK OPTION` at the end of the View definition:

```sql
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

Now try to insert an invalid row:

```sql
INSERT INTO dbo.vVisaCards
(
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
)
VALUES
(
    'Discover',
    '6011000000000000',
    6,
    2029
);
```

SQL Server rejects the change because the new row would not be visible through the View.

A valid row still works:

```sql
INSERT INTO dbo.vVisaCards
(
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
)
VALUES
(
    'Visa',
    '4111111111111111',
    3,
    2028
);
```

```mermaid
flowchart LR
    A["INSERT / UPDATE through View"]
    B{"Row satisfies<br/>View WHERE?"}
    C["Allowed"]
    D["Rejected by<br/>WITH CHECK OPTION"]

    A --> B
    B -->|Yes| C
    B -->|No| D
```

> **WITH CHECK OPTION ensures that rows modified through the View remain visible through that View.**

---

## Check your understanding

1. Without `WITH CHECK OPTION`, can a row inserted through a filtered View become invisible through that View?
2. Where is that row stored?
3. What does `WITH CHECK OPTION` prevent?
4. Does `WITH CHECK OPTION` change which rows the View displays?

<details>
<summary>Show answers</summary>

1. Yes.
2. In the underlying base table.
3. It prevents modifications through the View that would create rows which do not satisfy the View's filter.
4. No. The filter still determines what the View displays.

</details>

---

## Cleanup

```sql
DROP VIEW IF EXISTS dbo.vVisaCards;
GO

DELETE FROM CreditCard
WHERE CardNumber IN
(
    '378282246310005',
    '4111111111111111',
    '6011000000000000'
);
GO
```

---

# Section 3 – WITH SCHEMABINDING

A normal View depends on underlying tables, but SQL Server may allow a schema change that later causes the View to fail.

`WITH SCHEMABINDING` creates a stronger dependency between the View and the objects it references.

> **SCHEMABINDING prevents incompatible schema changes that would break the View.**

For safety, we will use a temporary demonstration table.

---

## Without SCHEMABINDING

```sql
CREATE TABLE dbo.SchemaBindingDemo
(
    ID   int IDENTITY PRIMARY KEY,
    Name nvarchar(50),
    Note nvarchar(200)
);
GO

INSERT INTO dbo.SchemaBindingDemo (Name, Note)
VALUES
    ('Row 1', 'first'),
    ('Row 2', 'second');
GO
```

Create a normal View:

```sql
CREATE OR ALTER VIEW dbo.vDemoContacts
AS
SELECT
    ID,
    Name,
    Note
FROM dbo.SchemaBindingDemo;
GO
```

Now drop a column the View uses:

```sql
ALTER TABLE dbo.SchemaBindingDemo
DROP COLUMN Note;
GO
```

SQL Server allows the change.

But now:

```sql
SELECT *
FROM dbo.vDemoContacts;
```

fails because the View still expects `Note`.

Add the column back:

```sql
ALTER TABLE dbo.SchemaBindingDemo
ADD Note nvarchar(200) NULL;
GO
```

---

## With SCHEMABINDING

Rewrite the View:

```sql
CREATE OR ALTER VIEW dbo.vDemoContacts
WITH SCHEMABINDING
AS
SELECT
    ID,
    Name,
    Note
FROM dbo.SchemaBindingDemo;
GO
```

Now try:

```sql
ALTER TABLE dbo.SchemaBindingDemo
DROP COLUMN Note;
```

SQL Server refuses the change because the schemabound View depends on that column.

### Requirements used here

With `SCHEMABINDING`:

- use two-part object names such as `dbo.SchemaBindingDemo`;
- explicitly list the columns instead of using `SELECT *`.

---

## Check your understanding

1. What problem does `WITH SCHEMABINDING` help prevent?
2. Does it prevent every possible change to the underlying table?
3. Why do we use `dbo.SchemaBindingDemo` instead of only `SchemaBindingDemo`?
4. Can we use `SELECT *` in this schemabound View?

<details>
<summary>Show answers</summary>

1. It prevents incompatible schema changes to referenced objects that would break the View.
2. No. It prevents changes that conflict with the View's dependencies.
3. Schemabound object references use two-part names.
4. No. The referenced columns must be listed explicitly.

</details>

---

## Cleanup

```sql
DROP VIEW IF EXISTS dbo.vDemoContacts;
GO

DROP TABLE IF EXISTS dbo.SchemaBindingDemo;
GO
```

---

# Section 4 – WITH ENCRYPTION

`WITH ENCRYPTION` hides a View definition from normal metadata tools such as `sp_helptext`.

> **Important:** This should not be treated as a security boundary. It hides the definition from normal inspection, but it is not a substitute for permissions or proper security controls.

Create a normal View:

```sql
CREATE OR ALTER VIEW dbo.vActiveCards
AS
SELECT
    IDCreditCard,
    Type,
    CardNumber
FROM CreditCard
WHERE ExpirationYear >= 2026;
GO
```

Its definition can be inspected:

```sql
EXECUTE sp_helptext 'dbo.vActiveCards';
```

Rewrite it:

```sql
CREATE OR ALTER VIEW dbo.vActiveCards
WITH ENCRYPTION
AS
SELECT
    IDCreditCard,
    Type,
    CardNumber
FROM CreditCard
WHERE ExpirationYear >= 2026;
GO
```

Now:

```sql
EXECUTE sp_helptext 'dbo.vActiveCards';
```

does not return the View definition.

The View itself still works:

```sql
SELECT TOP (10) *
FROM dbo.vActiveCards;
```

> Always keep the original View source in version control.

---

## Check your understanding

1. What does `WITH ENCRYPTION` hide?
2. Does the View still work normally?
3. Should `WITH ENCRYPTION` be treated as strong security?
4. Where should the original View source code be stored?

<details>
<summary>Show answers</summary>

1. The View definition from normal metadata inspection tools such as `sp_helptext`.
2. Yes.
3. No.
4. In version control, such as Git.

</details>

---

## Cleanup

```sql
DROP VIEW IF EXISTS dbo.vActiveCards;
GO
```

---

# Section 5 – Combining View options

The View options used in this lab appear in different positions.

| Option | Position |
|---|---|
| `WITH SCHEMABINDING` | before `AS` |
| `WITH ENCRYPTION` | before `AS` |
| `WITH CHECK OPTION` | after the query |

Options before `AS` use one `WITH` clause and are separated by commas.

Example:

```sql
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

Query it:

```sql
SELECT TOP (5) *
FROM dbo.vVisaCards;
```

---

## Check your understanding

1. Where does `WITH SCHEMABINDING` appear?
2. Where does `WITH CHECK OPTION` appear?
3. How are multiple options before `AS` separated?
4. Can `SCHEMABINDING` and `CHECK OPTION` be used together?

<details>
<summary>Show answers</summary>

1. Before `AS`.
2. At the end of the query.
3. With commas inside one `WITH` clause.
4. Yes.

</details>

---

## Cleanup

```sql
DROP VIEW IF EXISTS dbo.vVisaCards;
GO
```

---

# Exercises

Try each exercise before opening the solution.

---

## Exercise 1 – Modify data through a simple View

Create `dbo.vCategories` that returns all columns from `Category`.

Through the View:

1. insert a category named `'Alarms'`;
2. rename it to `'Active Protection'`;
3. delete it;
4. drop the View.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER VIEW dbo.vCategories
AS
SELECT *
FROM Category;
GO

INSERT INTO dbo.vCategories (Name)
VALUES ('Alarms');

UPDATE dbo.vCategories
SET Name = 'Active Protection'
WHERE Name = 'Alarms';

DELETE FROM dbo.vCategories
WHERE Name = 'Active Protection';

DROP VIEW dbo.vCategories;
GO
```

</details>

---

## Exercise 2 – JOIN View restrictions

Create `dbo.vCustomerLocations` returning:

- `IDCustomer`;
- `FirstName`;
- `LastName`;
- `Email`;
- `PhoneNumber`;
- `CityID`;
- city name as `CityName`;
- state name as `StateName`.

Use `Customer`, `City`, and `State`.

Then test the View:

1. update only `Customer.LastName` through the View;
2. try to update both `Customer.LastName` and `City.Name` in the same statement;
3. explain why the two statements behave differently;
4. drop the View.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER VIEW dbo.vCustomerLocations
AS
SELECT
    c.IDCustomer,
    c.FirstName,
    c.LastName,
    c.Email,
    c.PhoneNumber,
    c.CityID,
    ci.Name AS CityName,
    s.Name  AS StateName
FROM Customer AS c
JOIN City AS ci
    ON ci.IDCity = c.CityID
JOIN State AS s
    ON s.IDState = ci.StateID;
GO
```

This targets only `Customer`:

```sql
UPDATE dbo.vCustomerLocations
SET LastName = LastName
WHERE IDCustomer = 1;
```

Now try to modify two base tables:

```sql
UPDATE dbo.vCustomerLocations
SET
    LastName = 'Test',
    CityName = 'Test City'
WHERE IDCustomer = 1;
```

This fails because the statement attempts to modify both `Customer` and `City`.

```sql
DROP VIEW dbo.vCustomerLocations;
GO
```

</details>

---

## Exercise 3 – WITH CHECK OPTION

Create `dbo.vAcceptedCards` showing cards whose `Type` is `'Visa'` or `'MasterCard'`.

Then:

1. insert an American Express card through the View;
2. query the View for the new card;
3. query the base table for the new card;
4. add `WITH CHECK OPTION`;
5. try another American Express insert;
6. remove `WITH CHECK OPTION`;
7. drop the View.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER VIEW dbo.vAcceptedCards
AS
SELECT
    IDCreditCard,
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
FROM CreditCard
WHERE Type IN ('Visa', 'MasterCard');
GO
```

```sql
INSERT INTO dbo.vAcceptedCards
(
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
)
VALUES
(
    'American Express',
    '378282246310005',
    12,
    2030
);
```

```sql
SELECT *
FROM dbo.vAcceptedCards
WHERE CardNumber = '378282246310005';

SELECT *
FROM CreditCard
WHERE CardNumber = '378282246310005';
```

Add `WITH CHECK OPTION`:

```sql
CREATE OR ALTER VIEW dbo.vAcceptedCards
AS
SELECT
    IDCreditCard,
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
FROM CreditCard
WHERE Type IN ('Visa', 'MasterCard')
WITH CHECK OPTION;
GO
```

This insert is rejected:

```sql
INSERT INTO dbo.vAcceptedCards
(
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
)
VALUES
(
    'American Express',
    '371449635398431',
    12,
    2030
);
```

Remove the option:

```sql
CREATE OR ALTER VIEW dbo.vAcceptedCards
AS
SELECT
    IDCreditCard,
    Type,
    CardNumber,
    ExpirationMonth,
    ExpirationYear
FROM CreditCard
WHERE Type IN ('Visa', 'MasterCard');
GO

DROP VIEW dbo.vAcceptedCards;
GO
```

</details>

---

## Exercise 4 – SCHEMABINDING

Create a temporary table with:

- `ID`
- `Name`
- `Description`

Create a normal View over the table.

1. Drop `Description`.
2. Observe what happens when you query the View.
3. Add the column back.
4. Recreate the View using `WITH SCHEMABINDING`.
5. Try to drop `Description` again.
6. Explain the difference.

<details>
<summary>Show solution</summary>

```sql
CREATE TABLE dbo.SchemaExercise
(
    ID          int IDENTITY PRIMARY KEY,
    Name        nvarchar(50),
    Description nvarchar(200)
);
GO

CREATE OR ALTER VIEW dbo.vSchemaExercise
AS
SELECT
    ID,
    Name,
    Description
FROM dbo.SchemaExercise;
GO

ALTER TABLE dbo.SchemaExercise
DROP COLUMN Description;
GO
```

Restore the column:

```sql
ALTER TABLE dbo.SchemaExercise
ADD Description nvarchar(200) NULL;
GO
```

Recreate the View:

```sql
CREATE OR ALTER VIEW dbo.vSchemaExercise
WITH SCHEMABINDING
AS
SELECT
    ID,
    Name,
    Description
FROM dbo.SchemaExercise;
GO
```

This is rejected:

```sql
ALTER TABLE dbo.SchemaExercise
DROP COLUMN Description;
```

Cleanup:

```sql
DROP VIEW IF EXISTS dbo.vSchemaExercise;
GO

DROP TABLE IF EXISTS dbo.SchemaExercise;
GO
```

</details>

---

# Cleanup

Run this if you stopped the lab before completing all individual cleanup steps:

```sql
DROP VIEW IF EXISTS dbo.vCustomers;
DROP VIEW IF EXISTS dbo.vCustomerCities;
DROP VIEW IF EXISTS dbo.vInvoiceItems;
DROP VIEW IF EXISTS dbo.vInvoiceSummary;
DROP VIEW IF EXISTS dbo.vCreditCardTypes;
DROP VIEW IF EXISTS dbo.vVisaCards;
DROP VIEW IF EXISTS dbo.vDemoContacts;
DROP VIEW IF EXISTS dbo.vActiveCards;
DROP VIEW IF EXISTS dbo.vCategories;
DROP VIEW IF EXISTS dbo.vCustomerLocations;
DROP VIEW IF EXISTS dbo.vAcceptedCards;
DROP VIEW IF EXISTS dbo.vSchemaExercise;
GO

DELETE FROM CreditCard
WHERE CardNumber IN
(
    '378282246310005',
    '4111111111111111',
    '6011000000000000',
    '371449635398431'
);

DELETE FROM Customer
WHERE Email = 'grace@example.com';

DROP TABLE IF EXISTS dbo.SchemaBindingDemo;
DROP TABLE IF EXISTS dbo.SchemaExercise;
GO
```

---

# What you should know after this lab

The important ideas are:

```text
Simple View
    -> may allow INSERT / UPDATE / DELETE

Complex View
    -> additional modification restrictions
```

```text
WITH CHECK OPTION
    -> modified rows must remain visible through the View
```

```text
WITH SCHEMABINDING
    -> prevents incompatible schema changes to referenced objects
```

```text
WITH ENCRYPTION
    -> hides the View definition from normal metadata inspection
    -> not a security boundary
```

And remember:

> **A View is not just a saved SELECT. Its definition also determines what can be modified through it and which rules apply.**

---

# Where to go next

In the next lab, **Triggers**, the database becomes active.

A View responds when you query or modify it.

A Trigger reacts automatically when data changes.
