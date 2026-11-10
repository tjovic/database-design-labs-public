# Trigger Exercises

These exercises build on [Lab 02 – Triggers](../labs/lab02-triggers.md) and use DML `AFTER` triggers in `AdventureWorksENG`. They are in two parts:

- **Part A (Exercises 1–4)** works on `dbo.City` and writes simple text messages to a log table. It covers a first trigger, set-based logging, multi-row safety, and comparing old and new values.
- **Part B (Exercises 5–9)** works on `dbo.Product`. It progresses from auditing inserts, to comparing old and new values, to flagging a business-rule condition for review, to debugging a flawed trigger someone else wrote.

Start with a fresh `AdventureWorksENG`, so no triggers from Lab 02 are still attached to `dbo.City`. The exercises create two log tables, `dbo.Exercise_CityLog` and `dbo.Exercise_ProductTriggerAudit`, and triggers with the `trg_Exercises_` prefix. The test data remains in the database until you run the targeted cleanup section.

> Run these exercises only in a training or isolated database. Their sample inserts, updates, and deletes are saved as you run them. Run the cleanup section before reusing the test names and product numbers.

## Setup

Create both log tables once before beginning. If an object with one of these names already exists and you did not create it for this collection, stop and choose an isolated database.

```sql
USE AdventureWorksENG;
GO

CREATE TABLE dbo.Exercise_CityLog
(
    IDLog    int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Exercise_CityLog PRIMARY KEY,
    Message  nvarchar(500) NOT NULL,
    LoggedAt datetime2(7) NOT NULL
        CONSTRAINT DF_Exercise_CityLog_LoggedAt
        DEFAULT SYSDATETIME()
);
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

Part A inserts test cities whose names start with `Exercise City`. Before starting, confirm that no such cities exist:

```sql
SELECT IDCity, Name
FROM dbo.City
WHERE Name LIKE N'Exercise City%';
```

Part B uses distinct `ProductNumber` values beginning with `EX-TRG-`. The audit table stores that value so students can inspect and clean up test records after a product has been deleted. The table's identity column supplies `IDProduct`.

Before starting, confirm that the reserved test product numbers are unused:

```sql
SELECT IDProduct, ProductNumber, Name
FROM dbo.Product
WHERE ProductNumber IN
(
    N'EX-TRG-I-001',
    N'EX-TRG-U-001', N'EX-TRG-U-002',
    N'EX-TRG-D-001', N'EX-TRG-D-002',
    N'EX-TRG-R-001', N'EX-TRG-R-002',
    N'EX-TRG-F-001', N'EX-TRG-F-002'
);
```

If the query returns any rows, choose unused test numbers and update the test and cleanup statements to match.

---

# Part A – Logging changes to `City`

## Exercise 1 — First logging trigger [BEGINNER]

Create an `AFTER INSERT` trigger named `dbo.trg_Exercises_City_LogInsert` on `dbo.City`.

Whenever a row is inserted into `City`, write this message to `Exercise_CityLog`:

```text
A city was inserted.
```

Then insert one test city, `Exercise City 1` in state `1`, and check the log.

<details>
<summary>Hint</summary>

The trigger body needs only one `INSERT INTO dbo.Exercise_CityLog (Message) VALUES (...)` statement. It does not need to read `inserted` yet.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_City_LogInsert
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO dbo.Exercise_CityLog (Message)
    VALUES (N'A city was inserted.');
END;
GO

INSERT INTO dbo.City (Name, StateID)
VALUES (N'Exercise City 1', 1);

SELECT *
FROM dbo.Exercise_CityLog
ORDER BY IDLog DESC;
GO
```

The log contains one new row with the fixed message.

</details>

## Exercise 2 — Log inserted rows [BEGINNER]

Modify `trg_Exercises_City_LogInsert`.

Instead of a fixed message, write one log entry for every inserted city, containing its `IDCity` and `Name`.

Then test it with a two-row `INSERT` of `Exercise City 2` and `Exercise City 3`.

<details>
<summary>Hint</summary>

Replace `VALUES` with `INSERT ... SELECT ... FROM inserted`. Convert `IDCity` to text with `CAST` before joining it to the message.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_City_LogInsert
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO dbo.Exercise_CityLog (Message)
    SELECT
        N'City inserted: ID='
        + CAST(IDCity AS nvarchar(10))
        + N', Name='
        + Name
    FROM inserted;
END;
GO

INSERT INTO dbo.City (Name, StateID)
VALUES
    (N'Exercise City 2', 1),
    (N'Exercise City 3', 1);

SELECT *
FROM dbo.Exercise_CityLog
ORDER BY IDLog DESC;
GO
```

The trigger fires once, but writes two log rows: one for each row in `inserted`.

</details>

## Exercise 3 — Multi-row safety [INTERMEDIATE]

First remove the trigger from Exercises 1–2, so its messages do not mix with this exercise:

```sql
DROP TRIGGER IF EXISTS dbo.trg_Exercises_City_LogInsert;
GO
```

Look at this trigger:

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_City_BadExample
ON dbo.City
AFTER INSERT
AS
BEGIN
    DECLARE @CityID int;

    SELECT @CityID = IDCity
    FROM inserted;

    INSERT INTO dbo.Exercise_CityLog (Message)
    VALUES (
        N'Inserted city ID='
        + CAST(@CityID AS nvarchar(10))
    );
END;
GO
```

Now imagine this statement:

```sql
INSERT INTO dbo.City (Name, StateID)
VALUES
    (N'Exercise City A', 1),
    (N'Exercise City B', 1),
    (N'Exercise City C', 1);
```

Answer these questions, then create the trigger and run the statement to check your answers:

1. How many times does the trigger fire?
2. How many rows are in `inserted`?
3. How many log rows does the trigger create?
4. What is wrong with this design?
5. Rewrite it correctly.

<details>
<summary>Hint</summary>

A scalar variable can hold only one value. Ask how many `IDCity` values the `SELECT @CityID = ...` statement has to choose from.

</details>

<details>
<summary>Solution</summary>

The trigger fires **once**. `inserted` contains **three rows**. The trigger creates only **one** log row, because the scalar variable can hold only one `IDCity`. Which of the three IDs it keeps is not guaranteed.

The design assumes one row per statement. A correct, set-based version reads every row of `inserted`:

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_City_BadExample
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO dbo.Exercise_CityLog (Message)
    SELECT
        N'Inserted city ID='
        + CAST(IDCity AS nvarchar(10))
    FROM inserted;
END;
GO
```

Insert three more cities (`Exercise City D`, `E` and `F`) to confirm that the fixed trigger writes three log rows.

</details>

## Exercise 4 — Log renamed cities [INTERMEDIATE]

Create an `AFTER UPDATE` trigger named `dbo.trg_Exercises_City_LogRename` on `dbo.City` that logs every **actual** change to `City.Name`. The message should contain the old and the new name.

Test it with:

1. a rename of `Exercise City 1` to `Exercise City 1 (renamed)`;
2. an update that assigns `Name = Name` to all `Exercise City` rows, so nothing really changes.

<details>
<summary>Hint</summary>

Join `inserted` and `deleted` on the primary key. The old name is in `deleted`, the new one in `inserted`. Keep only the rows where they differ.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_City_LogRename
ON dbo.City
AFTER UPDATE
AS
BEGIN
    INSERT INTO dbo.Exercise_CityLog (Message)
    SELECT
        N'City renamed from "'
        + d.Name
        + N'" to "'
        + i.Name
        + N'"'
    FROM inserted AS i
    INNER JOIN deleted AS d
        ON d.IDCity = i.IDCity
    WHERE d.Name <> i.Name;
END;
GO

UPDATE dbo.City
SET Name = N'Exercise City 1 (renamed)'
WHERE Name = N'Exercise City 1';

UPDATE dbo.City
SET Name = Name
WHERE Name LIKE N'Exercise City%';

SELECT *
FROM dbo.Exercise_CityLog
ORDER BY IDLog DESC;
GO
```

The first update writes one log row. The second update fires the trigger as well, but writes nothing: `WHERE d.Name <> i.Name` filters out rows whose name did not change.

</details>

---

# Part B – Auditing changes to `Product`

## Exercise 5 — Audit inserted products [BEGINNER]

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

## Exercise 6 — Audit actual price changes [INTERMEDIATE]

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

## Exercise 7 — Audit deleted products [INTERMEDIATE]

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

## Exercise 8 — Flag large price reductions for review [ADVANCED]

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

## Exercise 9 — Debug a flawed price-audit trigger [ADVANCED]

A teammate wrote this trigger, meant to do the same job as Exercise 6's trigger — log every update that changes a product's price:

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_Product_PriceAudit_Flawed
ON dbo.Product
AFTER UPDATE
AS
BEGIN
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
            ON d.IDProduct = i.IDProduct;
    END;
END;
GO
```

Before running anything, answer:

1. What does `UPDATE(PriceWithoutVAT)` actually test: that the column was assigned a value, or that the value changed?
2. Suppose a caller always sends full-column `UPDATE` statements, so `PriceWithoutVAT = PriceWithoutVAT` appears in the `SET` list even when only `MinimumQuantityInStock` is meant to change. Will this trigger write an audit row for that statement? Should it?
3. Compare this trigger with the one from Exercise 6. What single condition is missing?

Then create the trigger, test your prediction, and fix it.

<details>
<summary>Hint</summary>

`UPDATE(PriceWithoutVAT)` only reports that the column appeared in the statement's `SET` clause, not that its value changed. Compare `inserted` and `deleted` directly, the way Exercise 6's trigger does, to confirm a real change.

</details>

<details>
<summary>Solution</summary>

**Answers:**

1. `UPDATE(PriceWithoutVAT)` only reports that `PriceWithoutVAT` was included in the triggering statement's `SET` clause. It says nothing about whether the value actually changed.
2. Yes, the flawed trigger writes an audit row for every affected product, even though `PriceWithoutVAT` kept its old value. Those rows are misleading: they record a price change that never happened.
3. The flawed trigger is missing the `WHERE d.PriceWithoutVAT <> i.PriceWithoutVAT` condition that Exercise 6's trigger uses to confirm the value actually changed.

**Reproduce the bug:**

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_Product_PriceAudit_Flawed
ON dbo.Product
AFTER UPDATE
AS
BEGIN
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
            ON d.IDProduct = i.IDProduct;
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
    (N'Exercise flawed-trigger test product 1', N'EX-TRG-F-001', NULL, 1, 50.00, NULL),
    (N'Exercise flawed-trigger test product 2', N'EX-TRG-F-002', NULL, 1, 60.00, NULL);

UPDATE dbo.Product
SET PriceWithoutVAT = PriceWithoutVAT,
    MinimumQuantityInStock = MinimumQuantityInStock + 1
WHERE ProductNumber IN (N'EX-TRG-F-001', N'EX-TRG-F-002');

SELECT *
FROM dbo.Exercise_ProductTriggerAudit
WHERE ProductNumber IN (N'EX-TRG-F-001', N'EX-TRG-F-002')
ORDER BY AuditID;
GO
```

This returns two `UPDATE` rows with `OldPrice` equal to `NewPrice`, confirmed by running the statements above: the flawed trigger only checks that `PriceWithoutVAT` was mentioned in the `SET` clause, not that its value changed, so a no-op price assignment still produces audit noise.

**Fix:**

```sql
CREATE OR ALTER TRIGGER dbo.trg_Exercises_Product_PriceAudit_Flawed
ON dbo.Product
AFTER UPDATE
AS
BEGIN
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

Running the same no-op update again now writes zero new audit rows, confirmed by checking `AuditID` values added after the fix. A follow-up update that changes `EX-TRG-F-001`'s price from `50.00` to `55.00` still produces exactly one audit row, so the fix does not silently swallow real changes. This is the same trigger built in Exercise 6 — the point of this exercise is recognizing why the missing condition matters, not writing new logic from scratch.

</details>

## Cleanup

Run this only after finishing the exercises. It deletes only the sample products identified by their reserved product numbers. The product delete trigger records those deletions; the next statement removes all audit rows for the sample numbers. Then it drops only this collection's trigger names and audit table. The Part A statements delete only the test cities whose names start with `Exercise City`, and drop only this collection's `City` triggers and log table.

```sql
DELETE FROM dbo.Product
WHERE ProductNumber IN
(
    N'EX-TRG-I-001',
    N'EX-TRG-U-001', N'EX-TRG-U-002',
    N'EX-TRG-D-001', N'EX-TRG-D-002',
    N'EX-TRG-R-001', N'EX-TRG-R-002',
    N'EX-TRG-F-001', N'EX-TRG-F-002'
);
GO

DELETE FROM dbo.Exercise_ProductTriggerAudit
WHERE ProductNumber IN
(
    N'EX-TRG-I-001',
    N'EX-TRG-U-001', N'EX-TRG-U-002',
    N'EX-TRG-D-001', N'EX-TRG-D-002',
    N'EX-TRG-R-001', N'EX-TRG-R-002',
    N'EX-TRG-F-001', N'EX-TRG-F-002'
);
GO

DROP TRIGGER IF EXISTS dbo.trg_Exercises_Product_InsertAudit;
DROP TRIGGER IF EXISTS dbo.trg_Exercises_Product_PriceAudit;
DROP TRIGGER IF EXISTS dbo.trg_Exercises_Product_DeleteAudit;
DROP TRIGGER IF EXISTS dbo.trg_Exercises_Product_PriceReview;
DROP TRIGGER IF EXISTS dbo.trg_Exercises_Product_PriceAudit_Flawed;
DROP TABLE IF EXISTS dbo.Exercise_ProductTriggerAudit;
GO

-- Part A
DROP TRIGGER IF EXISTS dbo.trg_Exercises_City_LogInsert;
DROP TRIGGER IF EXISTS dbo.trg_Exercises_City_BadExample;
DROP TRIGGER IF EXISTS dbo.trg_Exercises_City_LogRename;
GO

DELETE FROM dbo.City
WHERE Name LIKE N'Exercise City%';

DROP TABLE IF EXISTS dbo.Exercise_CityLog;
GO
```

## References

- [Lab 02 – Triggers](../labs/lab02-triggers.md)
- [Create DML Triggers — Microsoft Learn](https://learn.microsoft.com/sql/relational-databases/triggers/create-dml-triggers)
- [Create DML Triggers to Handle Multiple Rows of Data — Microsoft Learn](https://learn.microsoft.com/sql/relational-databases/triggers/create-dml-triggers-to-handle-multiple-rows-of-data)
