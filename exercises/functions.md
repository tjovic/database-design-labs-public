# Function Exercises

These exercises build on [Lab 04 – Functions](../labs/lab04-functions.md) and use verified tables in `AdventureWorksENG`. They cover scalar user-defined functions, an inline table-valued function (inline TVF), and a multi-statement table-valued function (MSTVF).

The functions read existing data and do not modify application tables. The MSTVF inserts rows only into its local return table. The only persistent objects created are the functions listed here; use the cleanup section when finished.

## Exercise 1 — Classify a product price [BEGINNER]

Create a scalar function named `dbo.fn_Exercises_PriceBand` that accepts `@Price money` and returns `nvarchar(20)` using these rules:

- `NULL` returns `Unknown`;
- a price below `100` returns `Budget`;
- a price from `100` up to (but not including) `1000` returns `Standard`;
- a price of `1000` or more returns `Premium`.

Call the function with values below, at, and above the boundaries. Also call it with `NULL`.

<details>
<summary>Hint</summary>

Use `IF / ELSE` to handle the `NULL` case and `RETURN` one string for each range. Check the `100` and `1000` boundary values carefully.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER FUNCTION dbo.fn_Exercises_PriceBand
(
    @Price money
)
RETURNS nvarchar(20)
AS
BEGIN
    IF @Price IS NULL
        RETURN N'Unknown';

    IF @Price < 100
        RETURN N'Budget';

    IF @Price < 1000
        RETURN N'Standard';

    RETURN N'Premium';
END;
GO

SELECT
    dbo.fn_Exercises_PriceBand(99.99) AS BelowFirstBoundary,
    dbo.fn_Exercises_PriceBand(100.00) AS AtFirstBoundary,
    dbo.fn_Exercises_PriceBand(999.99) AS BelowSecondBoundary,
    dbo.fn_Exercises_PriceBand(1000.00) AS AtSecondBoundary,
    dbo.fn_Exercises_PriceBand(CAST(NULL AS money)) AS UnknownPrice;
GO
```

</details>

## Exercise 2 — Shorten a product name [BEGINNER]

Create a scalar function named `dbo.fn_Exercises_ShortName` that accepts `@Text nvarchar(max)` and returns `nvarchar(10)`. Return the original text when its length is at most 10 characters. For longer text, return its first 7 characters followed by `...`.

Call the function with one short value and one value longer than 10 characters.

<details>
<summary>Hint</summary>

Use `LEN` to check the input length and `LEFT` to take the first 7 characters.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER FUNCTION dbo.fn_Exercises_ShortName
(
    @Text nvarchar(max)
)
RETURNS nvarchar(10)
AS
BEGIN
    RETURN CASE
        WHEN LEN(@Text) <= 10 THEN @Text
        ELSE LEFT(@Text, 7) + N'...'
    END;
END;
GO

SELECT
    dbo.fn_Exercises_ShortName(N'Bike') AS ShortName,
    dbo.fn_Exercises_ShortName(N'Mountain-200 Black') AS LongName;
GO
```

</details>

## Exercise 3 — Calculate quantity sold for one product [INTERMEDIATE]

Create a scalar function named `dbo.fn_Exercises_ProductQuantitySold` that accepts `@IDProduct int` and returns the sum of `InvoiceItem.Quantity` for that product as an `int`.

If no invoice items match the supplied product ID, return `0` rather than `NULL`.

Use the function in a query for product `782`.

<details>
<summary>Hint</summary>

Assign `SUM(Quantity)` from `dbo.InvoiceItem` to a local `int` variable. `SUM` returns `NULL` when there are no matching rows, so handle that case before returning.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER FUNCTION dbo.fn_Exercises_ProductQuantitySold
(
    @IDProduct int
)
RETURNS int
AS
BEGIN
    DECLARE @QuantitySold int;

    SELECT
        @QuantitySold = SUM(Quantity)
    FROM dbo.InvoiceItem
    WHERE ProductID = @IDProduct;

    RETURN COALESCE(@QuantitySold, 0);
END;
GO
```

```sql
SELECT
    p.*,
    dbo.fn_Exercises_ProductQuantitySold(782) AS QuantitySold
FROM dbo.Product AS p
WHERE p.IDProduct = 782;
GO
```

The query returns the product row together with the total quantity recorded for that product in `InvoiceItem`.

Scalar functions are convenient for one value. Consider how repeatedly calling a scalar function for many rows can affect query performance; compare it with a set-based aggregate query.

</details>

## Exercise 4 — Return a customer's invoices [INTERMEDIATE]

Create an inline TVF named `dbo.fn_Exercises_CustomerInvoices` with these input parameters:

| Parameter | Type | Purpose |
|---|---|---|
| `@IDCustomer` | `int` | Customer whose invoices are requested |
| `@DateFrom` | `date` | First included date |
| `@DateToExclusive` | `date` | First excluded date |

Return one row per matching invoice with `IDInvoice`, `InvoiceNumber`, `InvoiceDate`, and `InvoiceTotal` calculated from `InvoiceItem.TotalPrice`. Keep invoices without line items and return a total of zero for them. Use the date interval `InvoiceDate >= @DateFrom` and `InvoiceDate < @DateToExclusive`.

Query the function from the `FROM` clause and sort the result by invoice date and invoice ID.

<details>
<summary>Hint</summary>

An inline TVF returns one query in parentheses after `RETURN`. Use a `LEFT JOIN` from `Invoice` to `InvoiceItem` and group by the invoice columns. Put `ORDER BY` in the query that calls the function.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER FUNCTION dbo.fn_Exercises_CustomerInvoices
(
    @IDCustomer int,
    @DateFrom date,
    @DateToExclusive date
)
RETURNS TABLE
AS
RETURN
(
    SELECT
        i.IDInvoice,
        i.InvoiceNumber,
        i.InvoiceDate,
        COALESCE(SUM(ii.TotalPrice), 0) AS InvoiceTotal
    FROM dbo.Invoice AS i
    LEFT JOIN dbo.InvoiceItem AS ii
        ON ii.InvoiceID = i.IDInvoice
    WHERE i.CustomerID = @IDCustomer
      AND i.InvoiceDate >= @DateFrom
      AND i.InvoiceDate < @DateToExclusive
    GROUP BY
        i.IDInvoice,
        i.InvoiceNumber,
        i.InvoiceDate
);
GO
```

```sql
SELECT *
FROM dbo.fn_Exercises_CustomerInvoices
(
    1,
    '20010101',
    '20050101'
)
ORDER BY InvoiceDate, IDInvoice;
GO
```

The sample selects a customer with an invoice and uses a date range covering the invoice dates in the training database. The function can be joined to other tables like a table source.

</details>

## Exercise 5 — Filter products by quantity sold [ADVANCED]

Create an MSTVF named `dbo.fn_Exercises_ProductsByQuantitySold` that accepts `@MinimumQuantitySold int` and returns:

- `IDProduct`;
- `ProductName`;
- `QuantitySold`.

If `@MinimumQuantitySold` is `NULL`, return all products, including products with no invoice items. Otherwise, return only products whose total sold quantity is at least the supplied minimum. Products with no invoice items have a quantity sold of `0`.

Use a return table variable, `IF / ELSE`, and `INSERT` statements to populate the return table. Query the function once with `NULL` and once with a minimum such as `100`.

<details>
<summary>Hint</summary>

Start from `dbo.Product` and use a `LEFT JOIN` to `dbo.InvoiceItem`. Group by product ID and name, and convert a missing sum to `0`. Use one `INSERT` branch for the `NULL` parameter and another with a `HAVING` filter for the minimum.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER FUNCTION dbo.fn_Exercises_ProductsByQuantitySold
(
    @MinimumQuantitySold int
)
RETURNS @Result TABLE
(
    IDProduct int NOT NULL,
    ProductName nvarchar(50) NOT NULL,
    QuantitySold int NOT NULL
)
AS
BEGIN
    IF @MinimumQuantitySold IS NULL
    BEGIN
        INSERT INTO @Result
        (
            IDProduct,
            ProductName,
            QuantitySold
        )
        SELECT
            p.IDProduct,
            p.Name,
            COALESCE(SUM(ii.Quantity), 0)
        FROM dbo.Product AS p
        LEFT JOIN dbo.InvoiceItem AS ii
            ON ii.ProductID = p.IDProduct
        GROUP BY
            p.IDProduct,
            p.Name;
    END
    ELSE
    BEGIN
        INSERT INTO @Result
        (
            IDProduct,
            ProductName,
            QuantitySold
        )
        SELECT
            p.IDProduct,
            p.Name,
            COALESCE(SUM(ii.Quantity), 0)
        FROM dbo.Product AS p
        LEFT JOIN dbo.InvoiceItem AS ii
            ON ii.ProductID = p.IDProduct
        GROUP BY
            p.IDProduct,
            p.Name
        HAVING COALESCE(SUM(ii.Quantity), 0) >= @MinimumQuantitySold;
    END;

    RETURN;
END;
GO
```

```sql
SELECT COUNT(*) AS ProductCount
FROM dbo.fn_Exercises_ProductsByQuantitySold(NULL)
;

SELECT TOP (5) *
FROM dbo.fn_Exercises_ProductsByQuantitySold(100)
ORDER BY QuantitySold DESC, ProductName;
GO
```

The `NULL` call includes every product. The second call returns products with at least 100 units sold. The `INSERT` statements populate only the function's local return table; they do not change `Product` or `InvoiceItem`.

</details>

## Cleanup

The functions do not change table data. Remove only the function definitions created for this collection when finished:

```sql
DROP FUNCTION IF EXISTS dbo.fn_Exercises_PriceBand;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_ProductQuantitySold;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_CustomerInvoices;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_ProductsByQuantitySold;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_ShortName;
GO
```

## References

- [Lab 04 – Functions](../labs/lab04-functions.md)
- [Create user-defined functions — Microsoft Learn](https://learn.microsoft.com/en-us/sql/relational-databases/user-defined-functions/create-user-defined-functions-database-engine)
- [Execute user-defined functions — Microsoft Learn](https://learn.microsoft.com/en-us/sql/relational-databases/user-defined-functions/execute-user-defined-functions)
