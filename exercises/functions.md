# Function Exercises

These exercises build on [Lab 04 – Functions](../labs/lab04-functions.md) and use verified tables in `AdventureWorksENG`. Exercise 7 uses a separate fictional `PayrollLab` database. They cover scalar user-defined functions, an inline table-valued function (inline TVF), and a multi-statement table-valued function (MSTVF). Exercise 8 adds checksum validation using ISO 7064 MOD 11,10.

The functions read existing data and do not modify application tables. The MSTVF inserts rows only into its local return table. Exercises 1–6 and 8 create only function definitions. Exercise 7 also creates a separate example database and two tables through its setup script; use the cleanup section when finished.

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

## Exercise 3 — Find a customer's latest invoice date [INTERMEDIATE]

Create a scalar function named `dbo.fn_Exercises_LatestInvoiceDate` that accepts `@IDCustomer int` and returns the most recent `InvoiceDate` from `dbo.Invoice` for that customer. Return `NULL` if the customer has no invoices.

Use the function in a query for customer `1`.

<details>
<summary>Hint</summary>

Select the latest matching date with `TOP (1)` and sort `InvoiceDate` in descending order.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER FUNCTION dbo.fn_Exercises_LatestInvoiceDate
(
    @IDCustomer int
)
RETURNS datetime
AS
BEGIN
    DECLARE @LatestInvoiceDate datetime;

    SELECT TOP (1)
        @LatestInvoiceDate = InvoiceDate
    FROM dbo.Invoice
    WHERE CustomerID = @IDCustomer
    ORDER BY InvoiceDate DESC, IDInvoice DESC;

    RETURN @LatestInvoiceDate;
END;
GO

SELECT dbo.fn_Exercises_LatestInvoiceDate(1) AS LatestInvoiceDate;
GO
```

</details>

## Exercise 4 — Calculate quantity sold for one product [INTERMEDIATE]

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

## Exercise 5 — Return a customer's invoices [INTERMEDIATE]

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

## Exercise 6 — Filter products by quantity sold [ADVANCED]

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

## Exercise 7 — Extended net salary calculation [ADVANCED]

Extend the simplified payroll example from Section 3 of [Lab 04](../labs/lab04-functions.md). This is a real-world-inspired calculation split into two scalar functions: one calculates a personal allowance, and the other uses that result to calculate net salary.

**Database:** `PayrollLab`. All employee records are fictional. Rules and source links were checked on **24 October 2026**.

### Scope and assumptions

Assume one employer, one standard monthly salary payment, membership in both pension pillars, and the full eligible personal allowance allocated to that employer. Dependent eligibility has already been established; the input counts represent dependents whose allowance is fully claimed by this employee. Exclude disability-related allowances and other special cases. Calculate monthly net salary before annual tax settlements or refunds.

Support gross salary from **EUR 0 to EUR 10,000**, inclusive. Values below the full-time minimum are included to practise low-pay and boundary calculations, for example for a partial month or part-time work. The upper limit deliberately keeps this exercise below the 2026 maximum monthly pillar-I contribution base of EUR 11,958; the function does not implement that cap.

### Setup

The following setup is also provided in Section 3 of the lab. If you completed that example, continue with your existing `PayrollLab` database and skip this setup. Otherwise, run it below. All payroll functions in this exercise belong in `PayrollLab`.

```sql
USE master;
GO
CREATE DATABASE PayrollLab;
GO
USE PayrollLab;
GO

CREATE TABLE dbo.TaxJurisdiction
(
    TaxJurisdictionID int PRIMARY KEY,
    Name nvarchar(100) NOT NULL,
    LowerRate decimal(5,2) NOT NULL CHECK (LowerRate BETWEEN 0 AND 100),
    HigherRate decimal(5,2) NOT NULL CHECK (HigherRate BETWEEN 0 AND 100)
);
GO

CREATE TABLE dbo.Employee
(
    IDEmployee int PRIMARY KEY,
    FirstName nvarchar(50) NOT NULL,
    LastName nvarchar(50) NOT NULL,
    GrossSalary decimal(10,2) NOT NULL CHECK (GrossSalary BETWEEN 0 AND 10000),
    TaxJurisdictionID int NOT NULL REFERENCES dbo.TaxJurisdiction(TaxJurisdictionID),
    ChildCount tinyint NOT NULL DEFAULT 0,
    OtherDependentCount tinyint NOT NULL DEFAULT 0
);
GO

INSERT INTO dbo.TaxJurisdiction (TaxJurisdictionID, Name, LowerRate, HigherRate)
VALUES (1, N'Zagreb', 23.00, 33.00);

INSERT INTO dbo.Employee
    (IDEmployee, FirstName, LastName, GrossSalary, TaxJurisdictionID,
     ChildCount, OtherDependentCount)
VALUES
    (1, N'Ana', N'Horvat', 2000.00, 1, 0, 0),
    (2, N'Marko', N'Novak', 3000.00, 1, 2, 0),
    (3, N'Iva', N'Kovac', 1300.00, 1, 0, 0),
    (4, N'Luka', N'Babic', 6000.00, 1, 1, 1),
    (5, N'Ema', N'Maric', 7000.00, 1, 0, 0);
GO
```

Add two more fictional employees to cover the reduced contribution base and higher tax bracket:

```sql
USE PayrollLab;
GO
INSERT INTO dbo.Employee
    (IDEmployee, FirstName, LastName, GrossSalary, TaxJurisdictionID,
     ChildCount, OtherDependentCount)
VALUES
    (6, N'Petra', N'Jurisic', 1100.00, 1, 0, 0),
    (7, N'Ivan', N'Peric', 8000.00, 1, 0, 0);
GO
```

### Part A – Calculate the personal allowance

Create `dbo.fn_Exercises_PersonalAllowance` with parameters `@ChildCount tinyint` and `@OtherDependentCount tinyint`. Return `decimal(12,2)`.

The basic monthly allowance is EUR 600. Add EUR 300 for each eligible other dependent. For children, multiply EUR 600 by the **sum** of the coefficients of the claimed children:

| Child in order | Individual coefficient | Cumulative coefficient |
| ---: | ---: | ---: |
| 1 | 0.5 | 0.5 |
| 2 | 0.7 | 1.2 |
| 3 | 1.0 | 2.2 |
| 4 | 1.4 | 3.6 |
| 5 | 1.9 | 5.5 |
| 6 | 2.5 | 8.0 |
| 7 | 3.2 | 11.2 |
| 8 | 4.0 | 15.2 |
| 9 | 4.9 | 20.1 |

This exercise supports **0–9 children** only. Within this published table, the differences between successive individual coefficients are 0.2, 0.3, 0.4, and so on. Use a `WHILE` loop to accumulate coefficients. Return `NULL` if either parameter is `NULL` or the child count exceeds 9. Do not extrapolate the table to further children.

For example, two children and one other dependent give `(1 + 1.2 + 0.5) * 600 = 1620`.

### Part B – Calculate net salary

Create `dbo.fn_Exercises_NetSalary` with these parameters:

| Parameter | Type |
| --- | --- |
| `@GrossSalary` | `decimal(10,2)` |
| `@LowerRate` | `decimal(5,2)` |
| `@HigherRate` | `decimal(5,2)` |
| `@ChildCount` | `tinyint` |
| `@OtherDependentCount` | `tinyint` |

Return `decimal(10,2)`. Return `NULL` for a missing input, gross salary outside the supported range, rates outside 0–100, a higher rate below the lower rate, or a child count above 9.

Apply these rules in order:

1. Calculate the reduction of the **pillar-I contribution base**: up to EUR 700 gross, use EUR 300, capped at the gross salary; from EUR 700.01 to EUR 1,300, use `0.5 * (1300 - gross)`; above EUR 1,300, use zero. Round the reduction to cents.
2. Calculate pillar I as **15% of the reduced base** and pillar II as **5% of the full gross salary**. Round each contribution separately to cents.
3. Call your Part A function to calculate the personal allowance.
4. Calculate the tax base as gross salary minus both contributions minus the allowance. Replace a negative tax base with zero.
5. Apply the lower rate to the first EUR 5,000 of the tax base and the higher rate only to the excess. Round each bracket's tax to cents before adding them.
6. Return gross salary minus both contributions minus income tax.

The reduction affects only the pillar-I contribution base. The personal allowance affects only the income tax base. Neither is an additional deduction from the final net amount.

### Part C – Use the functions in a query

Join employees to `TaxJurisdiction` and display their names, gross salary, personal allowance, and calculated net salary. Pass the rates from the reference table into the main function.

If you also created `dbo.fn_NetSalarySimple` in the lab, compare its result with the extended result. Expect differences for employees claiming additional allowances and `NULL` from the simple function for salaries outside its range.

### Expected results

Use the following independent cases to check the branches. Rates are 23% and 33%, and there are no other dependents unless specified.

| Gross EUR | Children | Other dependents | Expected net EUR | Case |
| ---: | ---: | ---: | ---: | --- |
| 0.00 | 0 | 0 | 0.00 | Zero input |
| 250.00 | 0 | 0 | 237.50 | Reduction capped at gross |
| 700.00 | 0 | 0 | 603.85 | Fixed reduction |
| 1100.00 | 0 | 0 | 827.15 | Gradual reduction |
| 1300.00 | 0 | 0 | 938.80 | Reduction reaches zero |
| 2000.00 | 0 | 0 | 1370.00 | Basic allowance |
| 2000.00 | 2 | 1 | 1600.00 | Allowance exceeds income |
| 7000.00 | 0 | 0 | 4450.00 | Tax base exactly EUR 5,000 |
| 8000.00 | 0 | 0 | 4986.00 | Higher tax bracket |

Also try values immediately below and above EUR 700 and EUR 1,300, missing inputs, and gross salary above EUR 10,000. Check that Part A returns `1620.00` for `(2, 1)`, `12660.00` for `(9, 0)`, and `NULL` for `(10, 0)`.

<details>
<summary>Hint</summary>

Start with the allowance function. Track the current child number, its individual coefficient, and a running total. In the net salary function, use separate local variables for the base reduction, each contribution, the allowance, the tax base, and income tax. Create the helper before the main function that calls it.

</details>

<details>
<summary>Solution</summary>

```sql
USE PayrollLab;
GO
CREATE OR ALTER FUNCTION dbo.fn_Exercises_PersonalAllowance
(
    @ChildCount tinyint,
    @OtherDependentCount tinyint
)
RETURNS decimal(12,2)
AS
BEGIN
    IF @ChildCount IS NULL OR @OtherDependentCount IS NULL OR @ChildCount > 9
        RETURN NULL;

    DECLARE @ChildNumber int = 1;
    DECLARE @ChildCoefficient decimal(10,2) = 0.50;
    DECLARE @TotalChildCoefficient decimal(12,2) = 0;

    WHILE @ChildNumber <= @ChildCount
    BEGIN
        SET @TotalChildCoefficient = @TotalChildCoefficient + @ChildCoefficient;
        SET @ChildNumber = @ChildNumber + 1;
        SET @ChildCoefficient = @ChildCoefficient + @ChildNumber * 0.10;
    END;

    RETURN (1 + @TotalChildCoefficient + @OtherDependentCount * 0.50) * 600;
END;
GO

CREATE OR ALTER FUNCTION dbo.fn_Exercises_NetSalary
(
    @GrossSalary decimal(10,2),
    @LowerRate decimal(5,2),
    @HigherRate decimal(5,2),
    @ChildCount tinyint,
    @OtherDependentCount tinyint
)
RETURNS decimal(10,2)
AS
BEGIN
    IF @GrossSalary IS NULL OR @LowerRate IS NULL OR @HigherRate IS NULL
       OR @ChildCount IS NULL OR @OtherDependentCount IS NULL
        RETURN NULL;

    IF @GrossSalary < 0 OR @GrossSalary > 10000
       OR @LowerRate < 0 OR @LowerRate > 100
       OR @HigherRate < 0 OR @HigherRate > 100
       OR @HigherRate < @LowerRate OR @ChildCount > 9
        RETURN NULL;

    DECLARE @Reduction decimal(10,2) = 0;

    IF @GrossSalary <= 700
    BEGIN
        SET @Reduction = 300;
        IF @Reduction > @GrossSalary
            SET @Reduction = @GrossSalary;
    END
    ELSE IF @GrossSalary <= 1300
        SET @Reduction = ROUND(0.50 * (1300 - @GrossSalary), 2);

    DECLARE @PensionI decimal(10,2) =
        ROUND((@GrossSalary - @Reduction) * 0.15, 2);
    DECLARE @PensionII decimal(10,2) = ROUND(@GrossSalary * 0.05, 2);

    DECLARE @Allowance decimal(12,2) =
        dbo.fn_Exercises_PersonalAllowance(@ChildCount, @OtherDependentCount);

    DECLARE @TaxBase decimal(12,2) =
        @GrossSalary - @PensionI - @PensionII - @Allowance;

    IF @TaxBase < 0
        SET @TaxBase = 0;

    DECLARE @IncomeTax decimal(12,2);

    IF @TaxBase <= 5000
        SET @IncomeTax = ROUND(@TaxBase * @LowerRate / 100, 2);
    ELSE
        SET @IncomeTax = ROUND(5000 * @LowerRate / 100, 2)
                      + ROUND((@TaxBase - 5000) * @HigherRate / 100, 2);

    RETURN @GrossSalary - @PensionI - @PensionII - @IncomeTax;
END;
GO
```

Use the functions for all employees:

```sql
SELECT
    e.IDEmployee,
    e.FirstName,
    e.LastName,
    e.GrossSalary,
    e.ChildCount,
    e.OtherDependentCount,
    dbo.fn_Exercises_PersonalAllowance(e.ChildCount, e.OtherDependentCount)
        AS PersonalAllowance,
    dbo.fn_Exercises_NetSalary
    (
        e.GrossSalary, t.LowerRate, t.HigherRate,
        e.ChildCount, e.OtherDependentCount
    ) AS NetSalary
FROM dbo.Employee AS e
INNER JOIN dbo.TaxJurisdiction AS t
    ON t.TaxJurisdictionID = e.TaxJurisdictionID
ORDER BY e.IDEmployee;
GO
```

Optional comparison, after creating `fn_NetSalarySimple` from the lab:

```sql
SELECT
    e.IDEmployee,
    e.GrossSalary,
    dbo.fn_NetSalarySimple(e.GrossSalary, t.LowerRate) AS SimpleNetSalary,
    dbo.fn_Exercises_NetSalary
    (
        e.GrossSalary, t.LowerRate, t.HigherRate,
        e.ChildCount, e.OtherDependentCount
    ) AS ExtendedNetSalary
FROM dbo.Employee AS e
INNER JOIN dbo.TaxJurisdiction AS t
    ON t.TaxJurisdictionID = e.TaxJurisdictionID
ORDER BY e.IDEmployee;
GO
```

The main function calls the allowance function as an expression. Neither function changes employee data. The setup scripts create and populate the example tables outside the functions.

</details>

Rule sources (checked 24 October 2026):

- [Personal allowance — Croatian Tax Administration](https://porezna-uprava.gov.hr/hr/osobni-odbitak/4134)
- [Income tax and the tax threshold — gov.hr](https://gov.hr/hr/porez-na-dohodak/1466)
- [Zagreb tax rates, NN 28/2025](https://narodne-novine.nn.hr/clanci/sluzbeni/full/2025_02_28_291.html)
- [Reduction of the pension contribution base — Croatian Tax Administration](https://porezna-uprava.gov.hr/en/brosura-umanjenje-mjesecne-osnovice/7618)
- [Contribution bases for 2026, NN 150/2025](https://narodne-novine.nn.hr/clanci/sluzbeni/2025_12_150_2237.html)

Before returning to the other exercises, switch databases:

```sql
USE AdventureWorksENG;
GO
```

## Exercise 8 — Validate an OIB checksum [ADVANCED]

An OIB is a Croatian personal identification number containing 11 digits. Its last digit checks the preceding ten using **ISO 7064 MOD 11,10**. This is a different checksum algorithm from Luhn.

Create a scalar function named `dbo.fn_Exercises_IsValidOIB` that accepts `@OIB varchar(50)` and returns `bit`:

- return `1` when the input has exactly 11 ASCII digits and the last digit matches the calculated check digit;
- return `0` for `NULL`, an incorrect length, any non-digit character, or an incorrect check digit.

Keep the input as text so that leading zeros are preserved. Do not trim spaces: they make the input invalid. A matching checksum confirms only format and mathematical consistency; it does **not** establish that an OIB has been assigned or identify its holder.

### Algorithm

Start with an accumulator of `10`. Process only the first ten digits, from left to right:

1. Add the current digit to the accumulator.
2. Take the remainder after division by `10`. Replace a zero remainder with `10`.
3. Multiply by `2`, then take the remainder after division by `11`.
4. Continue with the next digit using the updated accumulator.

After the tenth digit, the check digit is `0` when the accumulator equals `1`; otherwise it is `11 - accumulator`. Compare this calculated digit with the eleventh input digit.

Consider the OIB `04296383653`:

| Position | Digit | Accumulator + digit | % 10 (0 → 10) | × 2, % 11 |
|---:|---:|---:|---:|---:|
| 1 | 0 | 10 | 10 | 9 |
| 2 | 4 | 13 | 3 | 6 |
| 3 | 2 | 8 | 8 | 5 |
| 4 | 9 | 14 | 4 | 8 |
| 5 | 6 | 14 | 4 | 8 |
| 6 | 3 | 11 | 1 | 2 |
| 7 | 8 | 10 | 10 | 9 |
| 8 | 3 | 12 | 2 | 4 |
| 9 | 6 | 10 | 10 | 9 |
| 10 | 5 | 14 | 4 | 8 |

After the tenth digit, the accumulator is `8`. Since it is not `1`, the check digit is `11 - 8 = 3`, which matches the eleventh digit of `04296383653`. The checksum is valid.

### Input validation

Validate the input before using `CAST` on individual characters. Use `DATALENGTH` to check length, since `LEN` ignores trailing spaces. With `varchar`, 11 ASCII digits occupy 11 bytes.

Use `LIKE '%[^0-9]%'` to reject any non-digit character before it reaches `CAST`.

Use a sufficiently wide parameter to inspect the complete input. With `char(11)`, an overlong input can be truncated before the function checks it. A generously sized, but still bounded, `varchar(50)` avoids that truncation just as well as `varchar(max)` would, without declaring an unbounded large-object parameter for an identifier that is always 11 characters.

### Apply the function to multiple inputs

Use the sample table variable in the solution to list every candidate and its validation result. Then return only the candidates whose validation result is `0`. The sample strings are constructed for this exercise; they are not taken from employee records, and their assignment status is unknown.

<details>
<summary>Hint</summary>

Use `WHILE` with positions 1 through 10, `SUBSTRING` to read a character, `CAST` to convert it to a digit, and `%` for each remainder. Keep the check digit outside the loop. Perform the format checks first so that invalid text returns `0` instead of causing a conversion error.

</details>

<details>
<summary>Solution</summary>

```sql
USE AdventureWorksENG;
GO
CREATE OR ALTER FUNCTION dbo.fn_Exercises_IsValidOIB
(
    @OIB varchar(50)
)
RETURNS bit
AS
BEGIN
    -- Reject obviously invalid input before using CAST on its characters.
    IF @OIB IS NULL
        RETURN 0;

    IF DATALENGTH(@OIB) <> 11
        RETURN 0;

    IF @OIB LIKE '%[^0-9]%'
        RETURN 0;

    -------------------------------------------------------
    -- Calculate the ISO 7064 MOD 11,10 checksum
    -------------------------------------------------------
    DECLARE @Position int = 1;
    DECLARE @Accumulator int = 10;
    DECLARE @Digit int;

    WHILE @Position <= 10
    BEGIN
        SET @Digit = CAST(SUBSTRING(@OIB, @Position, 1) AS int);
        SET @Accumulator = (@Accumulator + @Digit) % 10;

        -- A zero remainder is treated as 10, not 0.
        IF @Accumulator = 0
            SET @Accumulator = 10;

        SET @Accumulator = (@Accumulator * 2) % 11;
        SET @Position = @Position + 1;
    END;

    -------------------------------------------------------
    -- Compare the calculated check digit with the input
    -------------------------------------------------------
    DECLARE @CheckDigit int;

    IF @Accumulator = 1
        SET @CheckDigit = 0;
    ELSE
        SET @CheckDigit = 11 - @Accumulator;

    IF @CheckDigit = CAST(SUBSTRING(@OIB, 11, 1) AS int)
        RETURN 1;

    RETURN 0;
END;
GO
```

The first two candidates satisfy the checksum; the others demonstrate invalid input. The leading-zero example shows why this identifier should be text.

```sql
DECLARE @Candidates TABLE
(
    CaseName nvarchar(50),
    OIB varchar(100),
    ExpectedResult bit
);

INSERT INTO @Candidates (CaseName, OIB, ExpectedResult)
VALUES
    (N'Matching checksum', '12345678903', 1),
    (N'Leading zeros', '00000000001', 1),
    (N'Wrong check digit', '12345678904', 0),
    (N'Too short', '1234567890', 0),
    (N'Too long', '123456789030', 0),
    (N'Non-digit character', '1234567890A', 0),
    (N'Trailing space', '12345678903 ', 0),
    (N'Missing input', NULL, 0);

SELECT
    CaseName,
    OIB,
    ExpectedResult,
    dbo.fn_Exercises_IsValidOIB(OIB) AS ActualResult
FROM @Candidates;

SELECT CaseName, OIB
FROM @Candidates
WHERE dbo.fn_Exercises_IsValidOIB(OIB) = 0;
GO
```

Both queries belong in the same batch as the table variable declaration.

</details>

Algorithm source: [OIB checksum procedure — REGOS](https://regos.hr/app/uploads/2018/07/KONTROLA-OIB-a.pdf).

## Cleanup

The functions do not change table data. Select `AdventureWorksENG` and remove the definitions for Exercises 1–6 and 8:

```sql
USE AdventureWorksENG;
GO
DROP FUNCTION IF EXISTS dbo.fn_Exercises_PriceBand;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_ProductQuantitySold;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_LatestInvoiceDate;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_CustomerInvoices;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_ProductsByQuantitySold;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_ShortName;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_IsValidOIB;
GO
```

For Exercise 7, run the following only if you created `PayrollLab`. Drop the main function before its helper. Keep the payroll tables for later practice.

```sql
USE PayrollLab;
GO
DROP FUNCTION IF EXISTS dbo.fn_Exercises_NetSalary;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_PersonalAllowance;
GO
USE AdventureWorksENG;
GO
```

The optional `fn_NetSalarySimple` belongs to the lab and is removed by its cleanup section.

## References

- [Lab 04 – Functions](../labs/lab04-functions.md)
- [Create user-defined functions — Microsoft Learn](https://learn.microsoft.com/en-us/sql/relational-databases/user-defined-functions/create-user-defined-functions-database-engine)
- [Execute user-defined functions — Microsoft Learn](https://learn.microsoft.com/en-us/sql/relational-databases/user-defined-functions/execute-user-defined-functions)
