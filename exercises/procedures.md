# Stored Procedure Exercises

These exercises build on [Lab 03 – Stored Procedures](../labs/lab03-stored-procedures.md) and use the verified tables in `AdventureWorksENG`. They progress from a simple result set to input parameters, an `OUTPUT` parameter, and a `RETURN` status code.

All exercises are read-only: the procedures run `SELECT` statements and do not change table data. The only database objects they create are the procedures listed here. Use the cleanup section to remove those procedure definitions when finished.

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
    SET NOCOUNT ON;

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
    SET NOCOUNT ON;

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
    SET NOCOUNT ON;

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
    SET NOCOUNT ON;

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

## Exercise 4 — Return invoices and a match count [INTERMEDIATE]

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
    SET NOCOUNT ON;

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

## Exercise 5 — Return a product, price, and status [ADVANCED]

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
    SET NOCOUNT ON;
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

## Cleanup

The exercises do not add or change table data. When finished, remove only the procedure definitions created for this collection:

```sql
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_ListCategories;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_CustomersByLastName;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_CustomerInvoices;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_GetProduct;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_ProductsByPriceRange;
GO
```

## References

- [Lab 03 – Stored Procedures](../labs/lab03-stored-procedures.md)
- [CREATE PROCEDURE (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-procedure-transact-sql)
