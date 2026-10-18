# Trigger Exercises

These exercises use DML `AFTER` triggers on the verified `dbo.Product` table in `AdventureWorksENG`. They progress from auditing inserts, to comparing old and new values, to flagging a business-rule condition for review.

The database already has triggers on `dbo.City` and a populated `dbo.ActivityLog`. These exercises leave both untouched. They create a dedicated audit table named `dbo.Exercise_ProductTriggerAudit` and triggers with the `trg_Exercises_` prefix. The test data remains in the database until you run the targeted cleanup section.

> Run these exercises only in a training or isolated database. Their sample inserts, updates, and deletes are saved as you run them. Run the cleanup section before reusing the test product numbers.

## Setup

Create the audit table once before beginning. If an object with this name already exists and you did not create it for this collection, stop and choose an isolated database.

```sql
USE AdventureWorksENG;
GO

CREATE TABLE dbo.Exercise_ProductTriggerAudit
(
    AuditID   int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Exercise_ProductTriggerAudit PRIMARY KEY,
    ProductID     int NOT NULL,
    ProductNumber nvarchar(25) NOT NULL,
    Operation     nvarchar(20) NOT NULL,
    OldPrice      money NULL,
    NewPrice      money NULL,
    LoggedAt      datetime2(7) NOT NULL
        CONSTRAINT DF_Exercise_ProductTriggerAudit_LoggedAt
        DEFAULT SYSUTCDATETIME()
);
GO
```

The exercises use distinct `ProductNumber` values beginning with `EX-TRG-`. The audit table stores that value so students can inspect and clean up test records after a product has been deleted. The table's identity column supplies `IDProduct`.

Before starting, confirm that the reserved test product numbers are unused:

```sql
SELECT IDProduct, ProductNumber, Name
FROM dbo.Product
WHERE ProductNumber IN
(
    N'EX-TRG-I-001',
    N'EX-TRG-U-001', N'EX-TRG-U-002',
    N'EX-TRG-D-001', N'EX-TRG-D-002',
    N'EX-TRG-R-001', N'EX-TRG-R-002'
);
```

If the query returns any rows, choose unused test numbers and update the test and cleanup statements to match.

## Exercise 1 — Audit inserted products [BEGINNER]

Create an `AFTER INSERT` trigger named `dbo.trg_Exercises_Product_InsertAudit` on `dbo.Product`.

For every inserted row, add one row to `dbo.Exercise_ProductTriggerAudit` with:

- the new product's `IDProduct` as `ProductID`;
- its `ProductNumber` so the audit row can be matched after the product is deleted;
- `INSERT` as `Operation`;
- `NULL` as `OldPrice`;
- the inserted `PriceWithoutVAT` as `NewPrice`.

Test it with one product, then query the audit row using its `ProductNumber`. The test row remains until the final cleanup.

<details>
<summary>Hint</summary>

An `AFTER INSERT` trigger can read all new rows from `inserted`. Insert into the audit table with one `INSERT ... SELECT` statement.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_Product_InsertAudit
ON dbo.Product
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Exercise_ProductTriggerAudit
    (
        ProductID,
        ProductNumber,
        Operation,
        OldPrice,
        NewPrice
    )
    SELECT
        i.IDProduct,
        i.ProductNumber,
        N'INSERT',
        NULL,
        i.PriceWithoutVAT
    FROM inserted AS i;
END;
GO
```

```sql
INSERT INTO dbo.Product
(
    Name,
    ProductNumber,
    Color,
    MinimumQuantityInStock,
    PriceWithoutVAT,
    SubcategoryID
)
VALUES
(
    N'Exercise insert test product',
    N'EX-TRG-I-001',
    NULL,
    1,
    25.00,
    NULL
);

SELECT a.*
FROM dbo.Exercise_ProductTriggerAudit AS a
WHERE a.ProductNumber = N'EX-TRG-I-001';
GO
```

The query should show one `INSERT` audit row with a `NULL` old price and a new price of `25.00`. The test product and audit row remain until cleanup.

</details>

## Exercise 2 — Audit actual price changes [INTERMEDIATE]

Create an `AFTER UPDATE` trigger named `dbo.trg_Exercises_Product_PriceAudit` on `dbo.Product`.

Write one audit row for each product whose `PriceWithoutVAT` actually changed. Record the old price from `deleted` and the new price from `inserted`. Do not log updates that change other columns or set the price to its existing value.

Test the trigger by inserting two test products, changing both prices in one `UPDATE`, and checking their audit rows.

<details>
<summary>Hint</summary>

An `UPDATE` trigger can read the old and new versions from `deleted` and `inserted`. Join them by `IDProduct`. `UPDATE(PriceWithoutVAT)` tells you whether that column appeared in the statement; compare the old and new values to detect a real change.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_Product_PriceAudit
ON dbo.Product
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF UPDATE(PriceWithoutVAT)
    BEGIN
        INSERT INTO dbo.Exercise_ProductTriggerAudit
        (
            ProductID,
            ProductNumber,
            Operation,
            OldPrice,
            NewPrice
        )
        SELECT
            i.IDProduct,
            i.ProductNumber,
            N'UPDATE',
            d.PriceWithoutVAT,
            i.PriceWithoutVAT
        FROM inserted AS i
        JOIN deleted AS d
            ON d.IDProduct = i.IDProduct
        WHERE d.PriceWithoutVAT <> i.PriceWithoutVAT;
    END;
END;
GO
```

```sql
INSERT INTO dbo.Product
(
    Name,
    ProductNumber,
    Color,
    MinimumQuantityInStock,
    PriceWithoutVAT,
    SubcategoryID
)
VALUES
    (N'Exercise update test product 1', N'EX-TRG-U-001', NULL, 1, 10.00, NULL),
    (N'Exercise update test product 2', N'EX-TRG-U-002', NULL, 1, 20.00, NULL);

UPDATE dbo.Product
SET PriceWithoutVAT = PriceWithoutVAT + 5.00
WHERE ProductNumber IN (N'EX-TRG-U-001', N'EX-TRG-U-002');

SELECT a.*
FROM dbo.Exercise_ProductTriggerAudit AS a
WHERE a.Operation = N'UPDATE'
  AND a.ProductNumber IN (N'EX-TRG-U-001', N'EX-TRG-U-002');
GO
```

The query should show two `UPDATE` rows, with old/new price pairs `10.00`/`15.00` and `20.00`/`25.00`. Both products are changed by one statement, so the trigger must handle multiple rows in `inserted` and `deleted`. The products and audit rows remain until cleanup.

</details>

## Exercise 3 — Audit deleted products [INTERMEDIATE]

Create an `AFTER DELETE` trigger named `dbo.trg_Exercises_Product_DeleteAudit` on `dbo.Product`.

For every deleted row, write an audit row containing its `IDProduct`, `DELETE`, the deleted `PriceWithoutVAT` as `OldPrice`, and `NULL` as `NewPrice`.

Test it by inserting two test products and deleting both with one statement. Check the audit rows by `ProductNumber`; they remain until cleanup.

<details>
<summary>Hint</summary>

Deleted rows are available in `deleted`. The trigger must use a set-based `INSERT ... SELECT` so that one statement deleting several products produces one audit row per product.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_Product_DeleteAudit
ON dbo.Product
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Exercise_ProductTriggerAudit
    (
        ProductID,
        ProductNumber,
        Operation,
        OldPrice,
        NewPrice
    )
    SELECT
        d.IDProduct,
        d.ProductNumber,
        N'DELETE',
        d.PriceWithoutVAT,
        NULL
    FROM deleted AS d;
END;
GO
```

```sql
INSERT INTO dbo.Product
(
    Name,
    ProductNumber,
    Color,
    MinimumQuantityInStock,
    PriceWithoutVAT,
    SubcategoryID
)
VALUES
    (N'Exercise delete test product 1', N'EX-TRG-D-001', NULL, 1, 30.00, NULL),
    (N'Exercise delete test product 2', N'EX-TRG-D-002', NULL, 1, 40.00, NULL);

DELETE FROM dbo.Product
WHERE ProductNumber IN (N'EX-TRG-D-001', N'EX-TRG-D-002');

SELECT a.*
FROM dbo.Exercise_ProductTriggerAudit AS a
WHERE a.Operation = N'DELETE'
  AND a.ProductNumber IN (N'EX-TRG-D-001', N'EX-TRG-D-002')
ORDER BY a.AuditID DESC;
GO
```

The query should show two `DELETE` rows even though the products no longer exist. The test audit rows remain until cleanup.

</details>

## Exercise 4 — Flag large price reductions for review [ADVANCED]

Create an `AFTER UPDATE` trigger named `dbo.trg_Exercises_Product_PriceReview` on `dbo.Product`.

When a product's `PriceWithoutVAT` is reduced by more than 25 percent, write an audit row with `PRICE_REVIEW` as `Operation`, the old price, and the new price. The trigger should:

- compare old and new values for every affected product;
- ignore updates that do not change `PriceWithoutVAT`;
- write one audit row for every qualifying product in a multi-row update.

Test the rule with two products updated together: reduce one price by 20 percent and the other by 30 percent. Check which change was flagged. These products remain until cleanup.

<details>
<summary>Hint</summary>

Join `inserted` and `deleted` on `IDProduct`. Search for rows where the new price is less than 75% of the old price. Use one `INSERT ... SELECT` statement so the trigger can record every matching row.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_Product_PriceReview
ON dbo.Product
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF UPDATE(PriceWithoutVAT)
    BEGIN
        INSERT INTO dbo.Exercise_ProductTriggerAudit
        (
            ProductID,
            ProductNumber,
            Operation,
            OldPrice,
            NewPrice
        )
        SELECT
            i.IDProduct,
            i.ProductNumber,
            N'PRICE_REVIEW',
            d.PriceWithoutVAT,
            i.PriceWithoutVAT
        FROM inserted AS i
        JOIN deleted AS d
            ON d.IDProduct = i.IDProduct
        WHERE i.PriceWithoutVAT < d.PriceWithoutVAT * 0.75;
    END;
END;
GO
```

```sql
INSERT INTO dbo.Product
(
    Name,
    ProductNumber,
    Color,
    MinimumQuantityInStock,
    PriceWithoutVAT,
    SubcategoryID
)
VALUES
    (N'Exercise review test product 1', N'EX-TRG-R-001', NULL, 1, 100.00, NULL),
    (N'Exercise review test product 2', N'EX-TRG-R-002', NULL, 1, 100.00, NULL);

UPDATE dbo.Product
SET PriceWithoutVAT =
    CASE ProductNumber
        WHEN N'EX-TRG-R-001' THEN 80.00
        WHEN N'EX-TRG-R-002' THEN 70.00
    END
WHERE ProductNumber IN (N'EX-TRG-R-001', N'EX-TRG-R-002');

SELECT *
FROM dbo.Exercise_ProductTriggerAudit
WHERE Operation = N'PRICE_REVIEW'
  AND ProductNumber IN (N'EX-TRG-R-001', N'EX-TRG-R-002');
GO
```

The query should show one `PRICE_REVIEW` row for `EX-TRG-R-002` with old/new prices `100.00`/`70.00`. The 20 percent reduction does not meet the review threshold. Both products remain until cleanup.

This exercise records a review flag rather than rejecting the change. In a production design, consider whether a declarative constraint or validation in the application/procedure is a better fit. Triggers add automatic behavior that callers may not see.

</details>

## Cleanup

Run this only after finishing the exercises. It deletes only the sample products identified by their reserved product numbers. The product delete trigger records those deletions; the next statement removes all audit rows for the sample numbers. Then it drops only this collection's trigger names and audit table. It does not remove `dbo.ActivityLog` or any trigger on `dbo.City`.

```sql
DELETE FROM dbo.Product
WHERE ProductNumber IN
(
    N'EX-TRG-I-001',
    N'EX-TRG-U-001', N'EX-TRG-U-002',
    N'EX-TRG-D-001', N'EX-TRG-D-002',
    N'EX-TRG-R-001', N'EX-TRG-R-002'
);
GO

DELETE FROM dbo.Exercise_ProductTriggerAudit
WHERE ProductNumber IN
(
    N'EX-TRG-I-001',
    N'EX-TRG-U-001', N'EX-TRG-U-002',
    N'EX-TRG-D-001', N'EX-TRG-D-002',
    N'EX-TRG-R-001', N'EX-TRG-R-002'
);
GO

DROP TRIGGER IF EXISTS dbo.trg_Exercises_Product_InsertAudit;
DROP TRIGGER IF EXISTS dbo.trg_Exercises_Product_PriceAudit;
DROP TRIGGER IF EXISTS dbo.trg_Exercises_Product_DeleteAudit;
DROP TRIGGER IF EXISTS dbo.trg_Exercises_Product_PriceReview;
DROP TABLE IF EXISTS dbo.Exercise_ProductTriggerAudit;
GO
```

## References

- [Lab 02 – Triggers](../labs/lab02-triggers.md)
- [Create DML Triggers — Microsoft Learn](https://learn.microsoft.com/sql/relational-databases/triggers/create-dml-triggers)
- [Create DML Triggers to Handle Multiple Rows of Data — Microsoft Learn](https://learn.microsoft.com/sql/relational-databases/triggers/create-dml-triggers-to-handle-multiple-rows-of-data)
