# Lab 01 – View Exercises

These exercises build on [Lab 01 – Views](../labs/lab01-views.md) and use `AdventureWorksENG`. **Part A** (Exercises 1–6) practises creating, changing, and querying Views, reading metadata from system Views, and using an aggregate View in a query. **Part B** (Exercises 7–11) modifies data through Views and uses `WITH CHECK OPTION`, `WITH SCHEMABINDING`, and `WITH ENCRYPTION`.

Exercises 7 and 8 change data only temporarily or not at all. Exercise 9 inserts one test credit card, and Exercise 10 creates a small test table. Run the exercises in order on a freshly restored `AdventureWorksENG` (see [About the database](../README.md#about-the-database)). The solutions do not remove the objects and rows they create, and later exercises may rely on earlier ones; to start over, restore the database again.

```sql
USE AdventureWorksENG;
GO
```

---

# Part A – View fundamentals

## Exercise 1 — Create your first View [BEGINNER]

Create a View named:

```text
dbo.vCustomers
```

It should return:

- `FirstName`
- `LastName`
- `Email`

from `Customer`.

Then query the View.

<details>
<summary>Hint</summary>

A View is a saved `SELECT`: `CREATE OR ALTER VIEW dbo.vCustomers AS SELECT ... FROM Customer;`. Query it like a table.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER VIEW dbo.vCustomers
AS
SELECT
    FirstName,
    LastName,
    Email
FROM Customer;
GO

SELECT *
FROM dbo.vCustomers;
```

</details>

---

## Exercise 2 — Modify the View [BEGINNER]

Modify `dbo.vCustomers` so that it also returns:

```text
PhoneNumber
```

Use `CREATE OR ALTER VIEW`.

Then query the View again.

<details>
<summary>Hint</summary>

`CREATE OR ALTER VIEW` replaces the whole definition, so repeat all the columns and add the new one.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER VIEW dbo.vCustomers
AS
SELECT
    FirstName,
    LastName,
    Email,
    PhoneNumber
FROM Customer;
GO

SELECT *
FROM dbo.vCustomers;
```

</details>

---

## Exercise 3 — Hide a JOIN inside a View [BEGINNER]

Create:

```text
dbo.vCustomerCities
```

The View should return:

- `FirstName`
- `LastName`
- city name as `City`

Use `Customer` and `City`.

Then query the View **without writing a JOIN in the final SELECT**.

<details>
<summary>Hint</summary>

Join the tables inside the View: `Customer.CityID -> City.IDCity`. The final `SELECT` then reads only from the View.

</details>

<details>
<summary>Solution</summary>

```sql
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

SELECT *
FROM dbo.vCustomerCities;
```

</details>

---

## Exercise 4 — Explore system Views [BEGINNER]

Using `sys.tables`, count how many user tables exist in the current database.

<details>
<summary>Hint</summary>

`sys.tables` returns one row per user table.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT COUNT(*) AS TableCount
FROM sys.tables;
```

</details>

---

## Exercise 5 — List table columns [INTERMEDIATE]

Using `sys.tables` and `sys.columns`, list all columns belonging to the `Customer` table.

Return:

- table name;
- column name.

<details>
<summary>Hint</summary>

Join `sys.tables` and `sys.columns` on `object_id`, and filter on the table name.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    t.name AS TableName,
    c.name AS ColumnName
FROM sys.tables AS t
JOIN sys.columns AS c
    ON c.object_id = t.object_id
WHERE t.name = 'Customer'
ORDER BY c.column_id;
```

</details>

---

## Exercise 6 — An aggregate View in a query [INTERMEDIATE]

1. Create `dbo.vCustomerInvoiceCount` that returns `CustomerID` and the number of invoices for each customer as `InvoiceCount`.
2. Use the View in a query that returns `FirstName`, `LastName`, and `InvoiceCount` for the five customers with the most invoices. Join the View with `Customer`.
3. Change the View with `ALTER VIEW` so that it also returns the date of each customer's last invoice as `LastInvoiceDate`.
4. Try to change `InvoiceCount` through the View with `UPDATE`. What happens, and why?
5. Remove the View with `DROP VIEW`.

<details>
<summary>Hint</summary>

The View groups `Invoice` by `CustomerID`. The query treats the View like a table and joins it on `Customer.IDCustomer`. Lab 1, Section 6 explains why aggregate Views are not updatable.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER VIEW dbo.vCustomerInvoiceCount
AS
SELECT
    CustomerID,
    COUNT(*) AS InvoiceCount
FROM Invoice
GROUP BY CustomerID;
GO

SELECT TOP (5)
    c.FirstName,
    c.LastName,
    v.InvoiceCount
FROM dbo.vCustomerInvoiceCount AS v
JOIN Customer AS c
    ON c.IDCustomer = v.CustomerID
ORDER BY v.InvoiceCount DESC, c.LastName, c.FirstName;
GO
```

Result:

| FirstName | LastName | InvoiceCount |
|---|---|---:|
| Dalton | Perez | 28 |
| Mason | Roberts | 28 |
| Fernando | Barnes | 27 |
| Nancy | Chapman | 27 |
| Daniel | Davis | 27 |

Add the date of the last invoice:

```sql
ALTER VIEW dbo.vCustomerInvoiceCount
AS
SELECT
    CustomerID,
    COUNT(*) AS InvoiceCount,
    MAX(InvoiceDate) AS LastInvoiceDate
FROM Invoice
GROUP BY CustomerID;
GO
```

This update is rejected:

```sql
UPDATE dbo.vCustomerInvoiceCount
SET InvoiceCount = 100
WHERE CustomerID = 1;
```

`InvoiceCount` is calculated from many rows in `Invoice`; it is not stored in any base-table row, so SQL Server cannot change it.

```sql
DROP VIEW dbo.vCustomerInvoiceCount;
GO
```

</details>

---

# Part B – Modifying data and View options

## Exercise 7 — Modify data through a simple View [INTERMEDIATE]

Create `dbo.vCategories` that returns all columns from `Category`.

Through the View:

1. insert a category named `'Alarms'`;
2. rename it to `'Active Protection'`;
3. delete it;
4. drop the View.

<details>
<summary>Hint</summary>

`INSERT`, `UPDATE`, and `DELETE` work through a simple View over one table as if it were the table. `IDCategory` is an identity column, so insert only `Name`.

</details>

<details>
<summary>Solution</summary>

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

## Exercise 8 — JOIN View restrictions [INTERMEDIATE]

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
<summary>Hint</summary>

A statement that modifies data through a View may change only one base table.

</details>

<details>
<summary>Solution</summary>

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

## Exercise 9 — WITH CHECK OPTION [ADVANCED]

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
<summary>Hint</summary>

Without `WITH CHECK OPTION`, a row inserted through the View does not have to satisfy the View's `WHERE` condition.

</details>

<details>
<summary>Solution</summary>

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

## Exercise 10 — SCHEMABINDING [ADVANCED]

Create a test table `dbo.SchemaExercise` with:

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
<summary>Hint</summary>

`WITH SCHEMABINDING` requires two-part names (`dbo.Table`) and an explicit column list, not `SELECT *`.

</details>

<details>
<summary>Solution</summary>

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

SELECT *
FROM dbo.vSchemaExercise;
```

The `ALTER TABLE` succeeds, but the query fails: the View still refers to the `Description` column, which no longer exists. The View breaks silently and the error appears only when someone uses it.

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

With `WITH SCHEMABINDING`, SQL Server protects the columns the View depends on: the table cannot be changed in a way that would break the View. Without it, the change succeeds and the View fails later.

</details>

---

## Exercise 11 — WITH ENCRYPTION [INTERMEDIATE]

1. Create `dbo.vProductsWithoutColor` that returns `IDProduct`, `Name`, and `ProductNumber` for products whose `Color` is `NULL`.
2. Display the View definition with `sp_helptext`.
3. Change the View so that its definition is hidden, and run `sp_helptext` again.
4. Query the View. Does it still work?
5. A month later, you need to add a column to the View. Where do you get its current definition?
6. Drop the View.

<details>
<summary>Hint</summary>

`WITH ENCRYPTION` goes before `AS`, as in Lab 1, Section 9.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER VIEW dbo.vProductsWithoutColor
AS
SELECT
    IDProduct,
    Name,
    ProductNumber
FROM Product
WHERE Color IS NULL;
GO

EXECUTE sp_helptext 'dbo.vProductsWithoutColor';
GO
```

Hide the definition:

```sql
CREATE OR ALTER VIEW dbo.vProductsWithoutColor
WITH ENCRYPTION
AS
SELECT
    IDProduct,
    Name,
    ProductNumber
FROM Product
WHERE Color IS NULL;
GO

EXECUTE sp_helptext 'dbo.vProductsWithoutColor';
```

`sp_helptext` now reports *"The text for object 'dbo.vProductsWithoutColor' is encrypted."*

The View still works:

```sql
SELECT COUNT(*) AS ProductsWithoutColor
FROM dbo.vProductsWithoutColor;
```

The database no longer shows the definition, so you need the original script, kept in version control. Change it there and run it again with `CREATE OR ALTER VIEW`.

```sql
DROP VIEW dbo.vProductsWithoutColor;
GO
```

</details>

---

## References

- [Lab 01 – Views](../labs/lab01-views.md)
- [CREATE VIEW (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-view-transact-sql)
- [Modify data through a view — Microsoft Learn](https://learn.microsoft.com/en-us/sql/relational-databases/views/modify-data-through-a-view)
