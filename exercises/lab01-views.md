# Lab 01 – View Exercises

These exercises build on [Lab 01 – Views](../labs/lab01-views.md) and use `AdventureWorksENG`. **Part A** (Exercises 1–5) practises creating, changing, and querying Views and reading metadata from system Views. **Part B** (Exercises 6–9) modifies data through Views and uses `WITH CHECK OPTION` and `WITH SCHEMABINDING`.

Exercises 6 and 7 change data only temporarily or not at all. Exercise 8 inserts one test credit card, and Exercise 9 creates a small test table. The cleanup section removes them together with the Views.

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

# Part B – Modifying data and View options

## Exercise 6 — Modify data through a simple View [INTERMEDIATE]

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

## Exercise 7 — JOIN View restrictions [INTERMEDIATE]

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

## Exercise 8 — WITH CHECK OPTION [ADVANCED]

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

## Exercise 9 — SCHEMABINDING [ADVANCED]

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

The cleanup section removes the View and the table.

</details>

---

## Cleanup

Remove the Views, the test card from Exercise 8, and the test table from Exercise 9:

```sql
DROP VIEW IF EXISTS dbo.vCustomers;
DROP VIEW IF EXISTS dbo.vCustomerCities;
DROP VIEW IF EXISTS dbo.vCategories;
DROP VIEW IF EXISTS dbo.vCustomerLocations;
DROP VIEW IF EXISTS dbo.vAcceptedCards;
DROP VIEW IF EXISTS dbo.vSchemaExercise;
GO

DELETE FROM dbo.CreditCard
WHERE CardNumber = '378282246310005';

DROP TABLE IF EXISTS dbo.SchemaExercise;
GO
```

## References

- [Lab 01 – Views](../labs/lab01-views.md)
- [CREATE VIEW (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-view-transact-sql)
- [Modify data through a view — Microsoft Learn](https://learn.microsoft.com/en-us/sql/relational-databases/views/modify-data-through-a-view)
