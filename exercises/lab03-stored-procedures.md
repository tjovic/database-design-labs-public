# Lab 03 – Stored Procedure Exercises

These exercises build on [Lab 03 – Stored Procedures](../labs/lab03-stored-procedures.md) and use the verified tables in `AdventureWorksENG`. They progress from a simple result set to input parameters, `OUTPUT` parameters, a `RETURN` status code, and reusing one procedure from another script.

Exercise 6 inserts a state and two cities; all other exercises only read table data. The cleanup section removes the procedures and the rows inserted by Exercise 6.

## Exercise 1 — List categories [BEGINNER]

Create a procedure named `dbo.usp_Exercises_ListCategories` that returns `IDCategory` and `Name` from `dbo.Category`, sorted by `Name` in ascending order.

Execute the procedure. Then alter it to sort in descending order and execute it again.

<details>
<summary>Hint</summary>

The procedure body can contain the same `SELECT` you would run directly. Use `CREATE OR ALTER PROCEDURE` while developing it.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_ListCategories
AS
BEGIN
    SELECT
        IDCategory,
        Name
    FROM dbo.Category
    ORDER BY Name ASC;
END;
GO

EXEC dbo.usp_Exercises_ListCategories;
GO
```

To change the sort direction, alter `ORDER BY Name ASC` to `ORDER BY Name DESC`, run the `CREATE OR ALTER PROCEDURE` batch again, and execute the procedure.

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_ListCategories
AS
BEGIN
    SELECT
        IDCategory,
        Name
    FROM dbo.Category
    ORDER BY Name DESC;
END;
GO

EXEC dbo.usp_Exercises_ListCategories;
GO
```

</details>

## Exercise 2 — Search customers by last-name pattern [BEGINNER]

Create `dbo.usp_Exercises_CustomersByLastName` with an input parameter named `@LastNamePattern` of type `nvarchar(50)`.

Return `IDCustomer`, `FirstName`, `LastName`, and `Email` for customers whose `LastName` matches the supplied `LIKE` pattern. Sort by `LastName`, then `FirstName`, then `IDCustomer`.

Try patterns such as `N'A%'`, `N'%son'`, and `N'%son%'`.

<details>
<summary>Hint</summary>

Pass the pattern itself as a parameter and use `LastName LIKE @LastNamePattern`. The caller supplies the `%` wildcard characters.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_CustomersByLastName
    @LastNamePattern nvarchar(50)
AS
BEGIN
    SELECT
        IDCustomer,
        FirstName,
        LastName,
        Email
    FROM dbo.Customer
    WHERE LastName LIKE @LastNamePattern
    ORDER BY LastName, FirstName, IDCustomer;
END;
GO

EXEC dbo.usp_Exercises_CustomersByLastName
    @LastNamePattern = N'%son%';
GO
```

</details>

## Exercise 3 — Find products in a price range [BEGINNER]

Create `dbo.usp_Exercises_ProductsByPriceRange` with two input parameters, `@MinimumPrice money` and `@MaximumPrice money`. Return each matching product's `IDProduct`, `Name`, and `PriceWithoutVAT`. Include both endpoints of the range and sort by price, then product ID.

Call the procedure for the range from `0` to `100000`.

<details>
<summary>Hint</summary>

Use `BETWEEN` with the two parameters in the `WHERE` clause.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_ProductsByPriceRange
    @MinimumPrice money,
    @MaximumPrice money
AS
BEGIN
    SELECT
        IDProduct,
        Name,
        PriceWithoutVAT
    FROM dbo.Product
    WHERE PriceWithoutVAT BETWEEN @MinimumPrice AND @MaximumPrice
    ORDER BY PriceWithoutVAT, IDProduct;
END;
GO

EXEC dbo.usp_Exercises_ProductsByPriceRange
    @MinimumPrice = 0,
    @MaximumPrice = 100000;
GO
```

</details>

## Exercise 4 — Find the bug [BEGINNER]

Create this procedure:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_GetProductColor
    @IDProduct int,
    @Color     nvarchar(15) OUTPUT
AS
BEGIN
    SET @Color = NULL;

    SELECT @Color = Color
    FROM dbo.Product
    WHERE IDProduct = @IDProduct;
END;
GO
```

A developer calls it like this:

```sql
DECLARE @Color nvarchar(15);

EXEC dbo.usp_Exercises_GetProductColor
    @IDProduct = 742,
    @Color     = @Color;

SELECT @Color AS ProductColor;
```

The procedure executes, but `@Color` does not contain the value set by the procedure.

1. What is wrong with the call?
2. Where must `OUTPUT` appear?
3. Correct the call.

<details>
<summary>Hint</summary>

Compare the parameter in the procedure header with the same parameter in the `EXEC` statement.

</details>

<details>
<summary>Solution</summary>

The caller forgot the `OUTPUT` keyword. It must appear both in the procedure declaration and in the call when the caller wants to receive the value the procedure sets. Without it, the procedure works on its own copy of the value and the caller's variable stays `NULL`.

```sql
DECLARE @Color nvarchar(15);

EXEC dbo.usp_Exercises_GetProductColor
    @IDProduct = 742,
    @Color     = @Color OUTPUT;

SELECT @Color AS ProductColor;
```

</details>

## Exercise 5 — Return invoices and a match count [INTERMEDIATE]

Create `dbo.usp_Exercises_CustomerInvoices` with these parameters:

| Parameter | Type | Direction | Purpose |
|---|---|---|---|
| `@IDCustomer` | `int` | input | Customer whose invoices are requested |
| `@DateFrom` | `date` | input | First included date |
| `@DateToExclusive` | `date` | input | First excluded date |
| `@InvoiceCount` | `int` | output | Number of invoices returned |

Return one row per invoice with `IDInvoice`, `InvoiceNumber`, `InvoiceDate`, customer first and last name, and the invoice total calculated from `InvoiceItem.TotalPrice`. Include invoices with no matching line items and show their total as zero. Sort by invoice date and then invoice ID.

Use a half-open date interval: `InvoiceDate >= @DateFrom` and `InvoiceDate < @DateToExclusive`. Set `@InvoiceCount` to the number of result rows.

<details>
<summary>Hint</summary>

Join `Invoice` to `Customer`, and use a `LEFT JOIN` to `InvoiceItem` so an invoice without line items is retained. Group by the invoice and customer columns selected outside the aggregate. Assign `@@ROWCOUNT` to `@InvoiceCount` immediately after the result query.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_CustomerInvoices
    @IDCustomer int,
    @DateFrom date,
    @DateToExclusive date,
    @InvoiceCount int OUTPUT
AS
BEGIN
    SELECT
        i.IDInvoice,
        i.InvoiceNumber,
        i.InvoiceDate,
        c.FirstName,
        c.LastName,
        COALESCE(SUM(ii.TotalPrice), 0) AS InvoiceTotal
    FROM dbo.Invoice AS i
    JOIN dbo.Customer AS c
        ON c.IDCustomer = i.CustomerID
    LEFT JOIN dbo.InvoiceItem AS ii
        ON ii.InvoiceID = i.IDInvoice
    WHERE i.CustomerID = @IDCustomer
      AND i.InvoiceDate >= @DateFrom
      AND i.InvoiceDate < @DateToExclusive
    GROUP BY
        i.IDInvoice,
        i.InvoiceNumber,
        i.InvoiceDate,
        c.FirstName,
        c.LastName
    ORDER BY
        i.InvoiceDate,
        i.IDInvoice;

    SET @InvoiceCount = @@ROWCOUNT;
END;
GO
```

Use an existing customer who has an invoice to test it. This example selects one from the data and uses a date range covering the invoice dates in the training database:

```sql
DECLARE @InvoiceCount int;

EXEC dbo.usp_Exercises_CustomerInvoices
    @IDCustomer = 1,
    @DateFrom = '20010101',
    @DateToExclusive = '20050101',
    @InvoiceCount = @InvoiceCount OUTPUT;

SELECT @InvoiceCount AS InvoiceCount;
GO
```

The result set contains that customer's invoices in the selected date interval. `InvoiceCount` contains the number of rows returned. The caller must include `OUTPUT` in the `EXEC` call to receive the value.

</details>

## Exercise 6 — Insert a city and its state [INTERMEDIATE]

Create a procedure named `dbo.usp_Exercises_InsertCityInState` that accepts `@StateName` and `@CityName`.

The procedure must:

1. find the state by name and store its ID in a variable;
2. insert the state if it does not exist, and use `SCOPE_IDENTITY()` to obtain its new ID;
3. insert the city with the correct `StateID`.

Test the procedure with two calls:

```text
State: Canada, City: Toronto
State: Canada, City: Vancouver
```

Finally, verify that `Canada` exists only once in `State` and that both cities reference it.

> [!NOTE]
> This exercise assumes one user and at most one matching state before the first call. Repeating the two calls inserts the cities again: the procedure checks whether the state exists, but not whether the city exists.

<details>
<summary>Hint</summary>

After `SELECT @StateID = IDState FROM dbo.State WHERE Name = @StateName`, the variable is still `NULL` when no state matches. Use `IF @StateID IS NULL` to decide whether to insert the state.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_InsertCityInState
    @StateName nvarchar(50),
    @CityName  nvarchar(50)
AS
BEGIN
    DECLARE @StateID int;

    SELECT @StateID = IDState
    FROM dbo.State
    WHERE Name = @StateName;

    IF @StateID IS NULL
    BEGIN
        INSERT INTO dbo.State (Name)
        VALUES (@StateName);

        SET @StateID = SCOPE_IDENTITY();
    END;

    INSERT INTO dbo.City (Name, StateID)
    VALUES (@CityName, @StateID);
END;
GO

EXEC dbo.usp_Exercises_InsertCityInState
    @StateName = N'Canada',
    @CityName  = N'Toronto';

EXEC dbo.usp_Exercises_InsertCityInState
    @StateName = N'Canada',
    @CityName  = N'Vancouver';

SELECT
    s.Name AS State,
    c.Name AS City
FROM dbo.City AS c
INNER JOIN dbo.State AS s
    ON s.IDState = c.StateID
WHERE s.Name = N'Canada';

SELECT COUNT(*) AS CanadaRowCount
FROM dbo.State
WHERE Name = N'Canada';
GO
```

The first call inserts `Canada` and `Toronto`. The second call finds `Canada` and inserts only `Vancouver`, so `CanadaRowCount` is `1`.

</details>

## Exercise 7 — Return a product, price, and status [ADVANCED]

Create `dbo.usp_Exercises_GetProduct` with an input parameter `@IDProduct int` and an output parameter `@Price money OUTPUT`.

The procedure should:

- return `IDProduct`, `Name`, `ProductNumber`, and `PriceWithoutVAT` as a result set when the product exists;
- set `@Price` to the product's `PriceWithoutVAT`;
- return status `0` when a product is found and `1` when no product matches.

Test the successful lookup with product `782`. Do not modify any table data.

<details>
<summary>Hint</summary>

Initialize the output parameter to `NULL`. Use one `SELECT` to assign the price, then check `@@ROWCOUNT` immediately to tell whether a product was found. `RETURN` sends an integer status; it is separate from both the result set and the output parameter.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_GetProduct
    @IDProduct int,
    @Price money OUTPUT
AS
BEGIN
    SET @Price = NULL;

    SELECT
        @Price = PriceWithoutVAT
    FROM dbo.Product
    WHERE IDProduct = @IDProduct;

    IF @@ROWCOUNT = 0
        RETURN 1;

    SELECT
        IDProduct,
        Name,
        ProductNumber,
        PriceWithoutVAT
    FROM dbo.Product
    WHERE IDProduct = @IDProduct;

    RETURN 0;
END;
GO
```

```sql
DECLARE @Price money;
DECLARE @ReturnCode int;

EXEC @ReturnCode = dbo.usp_Exercises_GetProduct
    @IDProduct = 782,
    @Price = @Price OUTPUT;

SELECT
    @ReturnCode AS ReturnCode,
    @Price AS Price;
GO
```

The call returns the product row, its price, and status `0`. The return code is captured with `EXEC @ReturnCode = ...`; it is not returned as a result set.

</details>

## Exercise 8 — Validate all stored card numbers [ADVANCED]

This exercise reuses `dbo.usp_ValidateCardNumber` from [Section 7 of Lab 03](../labs/lab03-stored-procedures.md#section-7--practical-example-validating-a-card-number), which checks one card number. If the procedure does not exist in your database, create it first by running the `CREATE OR ALTER PROCEDURE` statement from that section.

Your task is to use this procedure to check **all existing card numbers** in `dbo.CreditCard`:

1. Declare a table variable named `@Cards` with these columns:

   | Column | Type | Purpose |
   |---|---|---|
   | `IDCreditCard` | `int PRIMARY KEY` | Identifies the card |
   | `CardNumber` | `varchar(100)` | Number to check |
   | `IsValid` | `bit NULL` | `NULL` = not processed, `0` = rejected, `1` = accepted |

2. Copy `IDCreditCard` and `CardNumber` from `dbo.CreditCard` into `@Cards`. Leave `IsValid` as `NULL`.
3. Use a `WHILE` loop to process rows whose `IsValid` is still `NULL`. In each iteration:
   - select one unprocessed row;
   - call `dbo.usp_ValidateCardNumber`;
   - capture its `OUTPUT` value;
   - update the corresponding row in `@Cards`.
4. Display `IDCreditCard` and `IsValid` for every processed row.
5. Display the number of rows for each validation result.

> [!IMPORTANT]
> Reuse the existing procedure. Do not copy the Luhn calculation into the loop. Store the results only in the table variable; do not modify `dbo.CreditCard`.

> [!NOTE]
> A result of `0` means that the number does not meet the rules of the procedure. It may have an incorrect checksum, contain non-digit characters, or be `NULL` or empty.

Then answer:

1. Why do we initially use `NULL` instead of `0` for `IsValid`?
2. How many times is the validation procedure called?
3. What would happen if we forgot to update the processed row?
4. Does this script change the original `CreditCard` table?

<details>
<summary>Hint</summary>

- `WHILE EXISTS (...)` can continue while unprocessed rows remain.
- `SELECT TOP (1) ... ORDER BY IDCreditCard` selects one row at a time.
- Use `IS NULL` to find unprocessed rows. A result of `0` means **processed and rejected**.
- The caller must specify `OUTPUT` to receive the validation result.
- Use `GROUP BY IsValid` and `COUNT(*)` for the summary.

</details>

<details>
<summary>Solution</summary>

```sql
DECLARE @Cards TABLE
(
    IDCreditCard int PRIMARY KEY,
    CardNumber   varchar(100),
    IsValid      bit NULL
);

INSERT INTO @Cards (IDCreditCard, CardNumber)
SELECT IDCreditCard, CardNumber
FROM dbo.CreditCard;

DECLARE @IDCreditCard int;
DECLARE @CardNumber varchar(100);
DECLARE @IsValid bit;

WHILE EXISTS
(
    SELECT 1
    FROM @Cards
    WHERE IsValid IS NULL
)
BEGIN
    -- Select one unprocessed card.
    SELECT TOP (1)
        @IDCreditCard = IDCreditCard,
        @CardNumber = CardNumber
    FROM @Cards
    WHERE IsValid IS NULL
    ORDER BY IDCreditCard;

    -- Reuse the procedure from Lab 03, Section 7.
    EXEC dbo.usp_ValidateCardNumber
        @CardNumber = @CardNumber,
        @IsValid = @IsValid OUTPUT;

    -- Store the result and mark the row as processed.
    UPDATE @Cards
    SET IsValid = @IsValid
    WHERE IDCreditCard = @IDCreditCard;
END;

-- Individual results.
SELECT IDCreditCard, IsValid
FROM @Cards
ORDER BY IDCreditCard;

-- Summary: 0 = rejected, 1 = accepted.
SELECT
    IsValid,
    COUNT(*) AS CardCount
FROM @Cards
GROUP BY IsValid
ORDER BY IsValid;
GO
```

Run the complete script as **one batch**. The table variable and local variables must remain available throughout the loop and the final queries.

1. `NULL` represents an unprocessed row. `0` represents a completed check with a rejected result.
2. Once for each row copied from `CreditCard`.
3. The row would remain unprocessed, so the loop would repeatedly select it and would never finish.
4. No. The script reads the original table and updates only `@Cards`.

This script calls a procedure once for each card. The additional reading in [Lab 04 – Functions](../labs/lab04-functions.md) shows how to move the checksum calculation into a scalar function and call it directly from a `SELECT` statement.

</details>

## Cleanup

Remove the procedures created for this collection. The last statements delete the cities and the state inserted by Exercise 6.

```sql
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_ListCategories;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_CustomersByLastName;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_ProductsByPriceRange;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_GetProductColor;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_CustomerInvoices;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_InsertCityInState;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_GetProduct;
GO

DELETE FROM dbo.City
WHERE StateID IN (SELECT IDState FROM dbo.State WHERE Name = N'Canada');

DELETE FROM dbo.State
WHERE Name = N'Canada';
GO
```

`dbo.usp_ValidateCardNumber` belongs to Lab 03, so this cleanup leaves it in place.

## References

- [Lab 03 – Stored Procedures](../labs/lab03-stored-procedures.md)
- [CREATE PROCEDURE (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-procedure-transact-sql)
