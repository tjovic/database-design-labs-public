# Lab 00 – T-SQL Essentials Exercises

These exercises build on [Lab 00 – T-SQL Essentials](../labs/lab00-tsql-essentials.md) and use `AdventureWorksENG`. They practise batches, variables, table variables, `IF / ELSE`, `SCOPE_IDENTITY()`, `WHILE`, `CASE`, `@@ROWCOUNT`, and `TRY/CATCH` — the building blocks used throughout the later labs.

Most exercises only read data. Exercises 7 and 8 insert a state and its cities, and Exercise 12 updates a product that does not exist, so it changes no rows. Run the exercises in order on a freshly restored `AdventureWorksENG` (see [About the database](../README.md#about-the-database)). The solutions do not remove the objects and rows they create, and later exercises may rely on earlier ones; to start over, restore the database again.

```sql
USE AdventureWorksENG;
GO
```

---

## Exercise 1 — Variables from a table [BEGINNER]

Declare `@FirstName` and `@LastName`.

Load their values from `Customer` for `IDCustomer = 1`, then print both
values.

<details>
<summary>Hint</summary>

Use one `SELECT` that assigns both variables, for example `SELECT @FirstName = FirstName, ...`.

</details>

<details>
<summary>Solution</summary>

```sql
DECLARE @FirstName nvarchar(50);
DECLARE @LastName  nvarchar(50);

SELECT
    @FirstName = FirstName,
    @LastName  = LastName
FROM Customer
WHERE IDCustomer = 1;

PRINT @FirstName;
PRINT @LastName;
GO
```

</details>

---

## Exercise 2 — Variables and batches [BEGINNER]

What happens when you run the following script?

```sql
DECLARE @City nvarchar(50) = N'Zagreb';

PRINT @City;
GO

PRINT @City;
GO
```

Try to predict the result, then fix the script so that both `PRINT` statements work.

<details>
<summary>Hint</summary>

Count the batches. In which batch is `@City` declared?

</details>

<details>
<summary>Solution</summary>

The first `PRINT` prints `Zagreb`. The second batch fails:

```text
Must declare the scalar variable "@City".
```

A variable exists only in the batch in which it is declared, and `GO` ends that batch. Remove the `GO` between the two statements:

```sql
DECLARE @City nvarchar(50) = N'Zagreb';

PRINT @City;
PRINT @City;
GO
```

</details>

---

## Exercise 3 — The no-row trap [BEGINNER]

What will the following script print if no customer has
`IDCustomer = -1`?

Try to predict the result before running it.

```sql
DECLARE @FirstName nvarchar(50) = 'Unknown';

SELECT @FirstName = FirstName
FROM Customer
WHERE IDCustomer = -1;

PRINT @FirstName;
GO
```

<details>
<summary>Hint</summary>

Ask whether the `SELECT` assigns anything when no row matches the `WHERE` condition.

</details>

<details>
<summary>Solution</summary>

It prints:

```text
Unknown
```

The `SELECT` returned no rows, so no assignment took place. The variable
kept its previous value.

</details>

---

## Exercise 4 — The multi-row trap [BEGINNER]

Modify Exercise 1 by removing the `WHERE` clause so that the query reads
all customers.

What happens to `@FirstName` and `@LastName`?

Can you safely predict which customer's values will remain in the
variables?

<details>
<summary>Hint</summary>

Count how many rows the `SELECT` now reads, and how many times each variable is assigned.

</details>

<details>
<summary>Solution</summary>

```sql
DECLARE @FirstName nvarchar(50);
DECLARE @LastName  nvarchar(50);

SELECT
    @FirstName = FirstName,
    @LastName  = LastName
FROM Customer;

PRINT @FirstName;
PRINT @LastName;
GO
```

The variables are assigned repeatedly as rows are processed.

The final values come from the last row processed, but you should **not
rely on which row that will be**. If you need one specific customer,
write the query so that it identifies that row explicitly.

</details>

---

## Exercise 5 — Table variable [BEGINNER]

Declare a table variable named `@Products`.

It should contain:

- `IDProduct`;
- `Name`;
- `Color`.

Insert all black products (`Color = 'Crna'`) from `Product` into the table variable.

Then return the rows from `@Products`.

<details>
<summary>Hint</summary>

Declare the table variable with `DECLARE @Products TABLE (...)`, then fill it with `INSERT INTO @Products (...) SELECT ...`. Colors in `AdventureWorksENG` are stored in Croatian, for example `'Crna'` for black.

</details>

<details>
<summary>Solution</summary>

```sql
DECLARE @Products TABLE
(
    IDProduct int,
    Name      nvarchar(100),
    Color     nvarchar(30)
);

INSERT INTO @Products
(
    IDProduct,
    Name,
    Color
)
SELECT
    IDProduct,
    Name,
    Color
FROM Product
WHERE Color = N'Crna';

SELECT *
FROM @Products;
GO
```

</details>

---

## Exercise 6 — IF / ELSE [BEGINNER]

Count the rows in `Customer`.

If there are more than `20000` customers, print:

```text
Big database
```

Otherwise print:

```text
Still growing
```

<details>
<summary>Hint</summary>

Store `COUNT(*)` in a variable first, then compare the variable in `IF`.

</details>

<details>
<summary>Solution</summary>

```sql
DECLARE @Count int;

SELECT @Count = COUNT(*)
FROM Customer;

IF @Count > 20000
BEGIN
    PRINT 'Big database';
END
ELSE
BEGIN
    PRINT 'Still growing';
END
GO
```

</details>

---

## Exercise 7 — SCOPE_IDENTITY() [INTERMEDIATE]

Insert a new state named `'India'`.

1. Capture its generated ID in `@StateID`.
2. Insert two cities, `'Agra'` and `'Delhi'`, that reference the new
    state.
3. Select the two cities to verify the result.

<details>
<summary>Hint</summary>

Call `SCOPE_IDENTITY()` immediately after the `INSERT` into `State`, and use the variable in the `INSERT` into `City`.

</details>

<details>
<summary>Solution</summary>

```sql
DECLARE @StateID int;

INSERT INTO State (Name)
VALUES ('India');

SET @StateID = SCOPE_IDENTITY();

INSERT INTO City (Name, StateID)
VALUES
    ('Agra',  @StateID),
    ('Delhi', @StateID);

SELECT *
FROM City
WHERE StateID = @StateID;
GO
```

</details>

---

## Exercise 8 — Put it together [INTERMEDIATE]

Create a small script that combines several concepts from this lab.

1. Declare `@StateID`.
2. Insert a state named `'Portugal'`.
3. Store the generated ID in `@StateID`.
4. If `@StateID` is not `NULL`, print:

```text
New state ID: X
```

where `X` is the generated ID.

5. Insert `'Lisbon'` into `City` using the new `@StateID`.
6. Select the new state and city.

<details>
<summary>Hint</summary>

Combine the pattern from Exercise 7 with an `IF @StateID IS NOT NULL` block. Use `CAST` to join the number to the text.

</details>

<details>
<summary>Solution</summary>

```sql
DECLARE @StateID int;

INSERT INTO State (Name)
VALUES ('Portugal');

SET @StateID = SCOPE_IDENTITY();

IF @StateID IS NOT NULL
BEGIN
    PRINT 'New state ID: '
        + CAST(@StateID AS nvarchar(10));

    INSERT INTO City (Name, StateID)
    VALUES ('Lisbon', @StateID);
END

SELECT
    s.IDState,
    s.Name AS StateName,
    c.Name AS CityName
FROM State AS s
LEFT JOIN City AS c
    ON c.StateID = s.IDState
WHERE s.IDState = @StateID;
GO
```

</details>

---

## Exercise 9 — WHILE loop [BEGINNER]

Use a `WHILE` loop to print the square of each number from 1 to 5
(`1, 4, 9, 16, 25`).

<details>
<summary>Hint</summary>

Declare a counter, loop `WHILE @Counter <= 5`, and increase the counter at the end of every iteration.

</details>

<details>
<summary>Solution</summary>

```sql
DECLARE @Counter int = 1;

WHILE @Counter <= 5
BEGIN
    PRINT CAST(@Counter * @Counter AS nvarchar(10));
    SET @Counter = @Counter + 1;
END
GO
```

</details>

---

## Exercise 10 — CASE WHEN [BEGINNER]

Write a query against `Product` that returns `IDProduct`, `Name`, and
`Color`, together with a new column `ColorGroup`:

- `'Crna'` (black) or `'Srebrna'` (silver) -> `'Neutral'`
- `'Crvena'` (red) or `'Plava'` (blue) -> `'Bold'`
- anything else -> `'Other'`

<details>
<summary>Hint</summary>

Use a searched `CASE WHEN Color IN (...) THEN ... ELSE ... END` expression. The colors are stored in Croatian: `'Crna'` (black), `'Srebrna'` (silver), `'Crvena'` (red), and `'Plava'` (blue).

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    IDProduct,
    Name,
    Color,
    CASE
        WHEN Color IN (N'Crna', N'Srebrna') THEN 'Neutral'
        WHEN Color IN (N'Crvena', N'Plava') THEN 'Bold'
        ELSE 'Other'
    END AS ColorGroup
FROM Product;
GO
```

</details>

---

## Exercise 11 — CASE with aggregate functions [INTERMEDIATE]

Write **one** query against `Product` that returns a single row with four columns:

- `TotalProducts` — all products;
- `BlackProducts` — products with `Color = 'Crna'`;
- `RedProducts` — products with `Color = 'Crvena'`;
- `ProductsWithoutColor` — products whose `Color` is `NULL`.

<details>
<summary>Hint</summary>

Combine `SUM()` with a `CASE` that returns `1` or `0`, as in Lab 0, Section 8.4. A missing color is checked with `IS NULL`: the condition `Color = NULL` is never true.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    COUNT(*) AS TotalProducts,
    SUM(CASE WHEN Color = N'Crna' THEN 1 ELSE 0 END) AS BlackProducts,
    SUM(CASE WHEN Color = N'Crvena' THEN 1 ELSE 0 END) AS RedProducts,
    SUM(CASE WHEN Color IS NULL THEN 1 ELSE 0 END) AS ProductsWithoutColor
FROM Product;
GO
```

Result:

| TotalProducts | BlackProducts | RedProducts | ProductsWithoutColor |
|---:|---:|---:|---:|
| 504 | 93 | 38 | 248 |

With `WHEN Color = NULL`, the last column would be `0`, because a comparison with `NULL` is never true.

</details>

---

## Exercise 12 — @@ROWCOUNT and SET NOCOUNT ON [INTERMEDIATE]

Write a script that:

1. Turns off row-count messages for the session.
2. Updates `MinimumQuantityInStock` for the product with `IDProduct = 99999`,
    increasing it by 1.
3. Immediately saves the number of affected rows into a variable.
4. Prints `'Rows updated: '` followed by that number.
5. Prints `'No product was updated.'` instead, if no row was affected.
6. Turns row-count messages back on.

<details>
<summary>Hint</summary>

`@@ROWCOUNT` describes only the most recent statement, so read it in the statement directly after the `UPDATE`.

</details>

<details>
<summary>Solution</summary>

```sql
SET NOCOUNT ON;

UPDATE Product
SET MinimumQuantityInStock = MinimumQuantityInStock + 1
WHERE IDProduct = 99999;

DECLARE @RowsUpdated int = @@ROWCOUNT;

IF @RowsUpdated = 0
BEGIN
    PRINT 'No product was updated.';
END
ELSE
BEGIN
    PRINT 'Rows updated: ' + CAST(@RowsUpdated AS nvarchar(10));
END

SET NOCOUNT OFF;
GO
```

</details>

---

## Exercise 13 — TRY/CATCH [INTERMEDIATE]

Write a script that:

1. Tries to `CAST('N/A' AS int)` inside a `TRY` block.
2. In the `CATCH` block, selects `ERROR_NUMBER()` and `ERROR_MESSAGE()`.

Run it, then change the value being cast to a valid integer, such as
`'42'`, and run it again.

<details>
<summary>Hint</summary>

Put the risky statement in `BEGIN TRY ... END TRY` and the error-reporting `SELECT` in `BEGIN CATCH ... END CATCH`.

</details>

<details>
<summary>Solution</summary>

```sql
BEGIN TRY
    SELECT CAST('N/A' AS int) AS ConvertedValue;
END TRY
BEGIN CATCH
    SELECT
        ERROR_NUMBER()  AS ErrorNumber,
        ERROR_MESSAGE() AS ErrorMessage;
END CATCH
GO
```

With `'N/A'`, the `CATCH` block runs and returns the error number and
message. With `'42'`, the `TRY` block completes successfully and the
`CATCH` block does not run.

</details>

---

## References

- [Lab 00 – T-SQL Essentials](../labs/lab00-tsql-essentials.md)
- [Variables (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/variables-transact-sql)
- [Control-of-Flow — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/control-of-flow)
- [TRY...CATCH (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/try-catch-transact-sql)
