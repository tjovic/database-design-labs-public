# Lab 02 – Trigger Exercises

**Database:** `AdventureWorksENG`, plus two log tables created in [Setup](#setup)

These exercises build on [Lab 02 – Triggers](../labs/lab02-triggers.md) and use DML `AFTER` triggers in `AdventureWorksENG`. They are in two parts:

- **Part A (Exercises 1–6)** works on `dbo.City` and writes simple text messages to a log table. It covers a first trigger, set-based logging, multi-row safety, comparing old and new values, one trigger for all three events, and checking new rows against existing ones.
- **Part B (Exercises 7–12)** works on `dbo.Product`. It progresses from auditing inserts, to comparing old and new values and classifying them with `CASE`, to flagging a business-rule condition for review, to debugging a flawed trigger someone else wrote.

Start with a fresh `AdventureWorksENG`, so no triggers from Lab 02 are still attached to `dbo.City`. The exercises create two log tables, `dbo.CityLog` and `dbo.ProductTriggerAudit`, and several triggers. Run them in order. The solutions do not remove the objects and rows they create, and later exercises may rely on earlier ones; to start over, restore the database again.

## Setup

Create both log tables once before beginning.

```sql
USE AdventureWorksENG;
GO

CREATE TABLE dbo.CityLog
(
    IDLog    int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_CityLog PRIMARY KEY,
    Message  nvarchar(500) NOT NULL,
    LoggedAt datetime2(7) NOT NULL
        CONSTRAINT DF_CityLog_LoggedAt
        DEFAULT SYSDATETIME()
);
GO

CREATE TABLE dbo.ProductTriggerAudit
(
    AuditID   int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_ProductTriggerAudit PRIMARY KEY,
    ProductID     int NOT NULL,
    ProductNumber nvarchar(25) NOT NULL,
    Operation     nvarchar(20) NOT NULL,
    OldPrice      money NULL,
    NewPrice      money NULL,
    LoggedAt      datetime2(7) NOT NULL
        CONSTRAINT DF_ProductTriggerAudit_LoggedAt
        DEFAULT SYSUTCDATETIME()
);
GO
```

Part A inserts test cities whose names start with `Exercise City`. Part B inserts test products whose `ProductNumber` starts with `EX-TRG-`; the audit table stores that value, so you can still find a product's audit rows after the product has been deleted.

---

# Part A – Logging changes to `City`

## Exercise 1 — First logging trigger [BEGINNER]

Create an `AFTER INSERT` trigger named `dbo.trg_City_LogInsert` on `dbo.City`.

Whenever a row is inserted into `City`, write this message to `CityLog`:

```text
A city was inserted.
```

Then insert one test city, `Exercise City 1` in state `1`, and check the log.

<details>
<summary>Hint</summary>

The trigger body needs only one `INSERT INTO dbo.CityLog (Message) VALUES (...)` statement. It does not need to read `inserted` yet.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_LogInsert
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO dbo.CityLog (Message)
    VALUES (N'A city was inserted.');
END;
GO

INSERT INTO dbo.City (Name, StateID)
VALUES (N'Exercise City 1', 1);

SELECT *
FROM dbo.CityLog
ORDER BY IDLog DESC;
GO
```

The log contains one new row with the fixed message.

</details>

## Exercise 2 — Log inserted rows [BEGINNER]

Modify `trg_City_LogInsert`.

Instead of a fixed message, write one log entry for every inserted city, containing its `IDCity` and `Name`.

Then test it with a two-row `INSERT` of `Exercise City 2` and `Exercise City 3`.

<details>
<summary>Hint</summary>

Replace `VALUES` with `INSERT ... SELECT ... FROM inserted`. Convert `IDCity` to text with `CAST` before joining it to the message.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_LogInsert
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO dbo.CityLog (Message)
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
FROM dbo.CityLog
ORDER BY IDLog DESC;
GO
```

The trigger fires once, but writes two log rows: one for each row in `inserted`.

</details>

## Exercise 3 — Multi-row safety [INTERMEDIATE]

First remove the trigger from Exercises 1–2, so its messages do not mix with this exercise:

```sql
DROP TRIGGER IF EXISTS dbo.trg_City_LogInsert;
GO
```

Look at this trigger:

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_BadExample
ON dbo.City
AFTER INSERT
AS
BEGIN
    DECLARE @CityID int;

    SELECT @CityID = IDCity
    FROM inserted;

    INSERT INTO dbo.CityLog (Message)
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
CREATE OR ALTER TRIGGER dbo.trg_City_BadExample
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO dbo.CityLog (Message)
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

Create an `AFTER UPDATE` trigger named `dbo.trg_City_LogNameChange` on `dbo.City` that logs every **actual** change to `City.Name`. The message should contain the old and the new name.

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
CREATE OR ALTER TRIGGER dbo.trg_City_LogNameChange
ON dbo.City
AFTER UPDATE
AS
BEGIN
    INSERT INTO dbo.CityLog (Message)
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
FROM dbo.CityLog
ORDER BY IDLog DESC;
GO
```

The first update writes one log row. The second update fires the trigger as well, but writes nothing: `WHERE d.Name <> i.Name` filters out rows whose name did not change.

`City.Name` allows `NULL`. A rename from or to `NULL` would need the NULL-safe comparison from Lab 2, Section 5, and the message would also have to handle the `NULL` name.

</details>

## Exercise 5 — One trigger for all three events [INTERMEDIATE]

First remove the `City` triggers from Exercises 3–4, so their messages do not mix with this exercise:

```sql
DROP TRIGGER IF EXISTS dbo.trg_City_BadExample;
DROP TRIGGER IF EXISTS dbo.trg_City_LogNameChange;
GO
```

Create one trigger named `dbo.trg_City_AllEvents` on `dbo.City` for `INSERT`, `UPDATE`, and `DELETE`. For every statement, it writes one log message with the event and the number of affected rows, for example:

```text
UPDATE: 2 row(s)
```

Test it:

1. insert `Exercise City X1` and `Exercise City X2` in one statement;
2. rename both in one statement by adding ` (changed)` to their names;
3. delete both in one statement;
4. run an `UPDATE` that matches no city, such as `WHERE IDCity = -1`.

What does the trigger write for the fourth statement, and why?

<details>
<summary>Hint</summary>

Count the rows in `inserted` and `deleted` and store the counts in variables. Which tables contain rows tells you the event, as in Lab 2, Section 8. Build the message with `CAST`, as in Exercise 2.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_AllEvents
ON dbo.City
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    DECLARE @InsertedRows int = (SELECT COUNT(*) FROM inserted);
    DECLARE @DeletedRows int = (SELECT COUNT(*) FROM deleted);
    DECLARE @Event nvarchar(10);
    DECLARE @Rows int;

    IF @InsertedRows > 0 AND @DeletedRows = 0
    BEGIN
        SET @Event = N'INSERT';
        SET @Rows = @InsertedRows;
    END
    ELSE IF @InsertedRows > 0 AND @DeletedRows > 0
    BEGIN
        SET @Event = N'UPDATE';
        SET @Rows = @InsertedRows;
    END
    ELSE IF @DeletedRows > 0
    BEGIN
        SET @Event = N'DELETE';
        SET @Rows = @DeletedRows;
    END
    ELSE
    BEGIN
        SET @Event = N'UNKNOWN';
        SET @Rows = 0;
    END

    INSERT INTO dbo.CityLog (Message)
    VALUES (@Event + N': ' + CAST(@Rows AS nvarchar(10)) + N' row(s)');
END;
GO

INSERT INTO dbo.City (Name, StateID)
VALUES
    (N'Exercise City X1', 1),
    (N'Exercise City X2', 1);

UPDATE dbo.City
SET Name = Name + N' (changed)'
WHERE Name IN (N'Exercise City X1', N'Exercise City X2');

DELETE FROM dbo.City
WHERE Name LIKE N'Exercise City X_ (changed)';

UPDATE dbo.City
SET Name = N'Nothing'
WHERE IDCity = -1;

SELECT TOP (4) Message
FROM dbo.CityLog
ORDER BY IDLog DESC;
GO
```

The newest four messages are `UNKNOWN: 0 row(s)`, `DELETE: 2 row(s)`, `UPDATE: 2 row(s)`, and `INSERT: 2 row(s)`.

The trigger fires once per statement, even when the statement affects no rows. Then both `inserted` and `deleted` are empty, so the trigger cannot tell which statement ran. This is the limitation described in Lab 2, Section 8.

</details>

## Exercise 6 — Detect duplicate cities [INTERMEDIATE]

Create an `AFTER INSERT` trigger named `dbo.trg_City_DuplicateCheck` on `dbo.City`. For every inserted city whose name **already exists in the same state**, it writes this message:

```text
Duplicate city: Exercise City Dup (StateID=1)
```

The insert itself is not stopped.

Test it by inserting `Exercise City Dup` in state `1` twice, in two separate statements. Which insert writes the message?

<details>
<summary>Hint</summary>

Check the rows in `inserted` against `dbo.City` with `EXISTS`. In an `AFTER` trigger, the new row is already in `dbo.City`, so it would match itself: exclude it by comparing `IDCity`.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_DuplicateCheck
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO dbo.CityLog (Message)
    SELECT
        N'Duplicate city: '
        + i.Name
        + N' (StateID='
        + CAST(i.StateID AS nvarchar(10))
        + N')'
    FROM inserted AS i
    WHERE EXISTS
    (
        SELECT 1
        FROM dbo.City AS c
        WHERE c.Name = i.Name
          AND c.StateID = i.StateID
          AND c.IDCity <> i.IDCity
    );
END;
GO

INSERT INTO dbo.City (Name, StateID)
VALUES (N'Exercise City Dup', 1);

INSERT INTO dbo.City (Name, StateID)
VALUES (N'Exercise City Dup', 1);

SELECT Message
FROM dbo.CityLog
WHERE Message LIKE N'Duplicate city:%';
GO
```

Only the second insert writes the message. Without `c.IDCity <> i.IDCity`, the first insert would also be reported, because every new row finds itself in `dbo.City`.

The trigger from Exercise 5 is still active, so the log also contains its `INSERT` messages; the query filters them out.

</details>

---

# Part B – Auditing changes to `Product`

## Exercise 7 — Audit inserted products [BEGINNER]

Create an `AFTER INSERT` trigger named `dbo.trg_Product_InsertAudit` on `dbo.Product`.

For every inserted row, add one row to `dbo.ProductTriggerAudit` with:

- the new product's `IDProduct` as `ProductID`;
- its `ProductNumber` so the audit row can be matched after the product is deleted;
- `INSERT` as `Operation`;
- `NULL` as `OldPrice`;
- the inserted `PriceWithoutVAT` as `NewPrice`.

Test it with one product, then query the audit row using its `ProductNumber`.

<details>
<summary>Hint</summary>

An `AFTER INSERT` trigger can read all new rows from `inserted`. Insert into the audit table with one `INSERT ... SELECT` statement.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Product_InsertAudit
ON dbo.Product
AFTER INSERT
AS
BEGIN
    INSERT INTO dbo.ProductTriggerAudit
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
FROM dbo.ProductTriggerAudit AS a
WHERE a.ProductNumber = N'EX-TRG-I-001';
GO
```

The query should show one `INSERT` audit row with a `NULL` old price and a new price of `25.00`.

</details>

## Exercise 8 — Audit actual price changes [INTERMEDIATE]

Create an `AFTER UPDATE` trigger named `dbo.trg_Product_PriceAudit` on `dbo.Product`.

Write one audit row for each product whose `PriceWithoutVAT` actually changed. Record the old price from `deleted` and the new price from `inserted`. Do not log updates that change other columns or set the price to its existing value.

Test the trigger by inserting two test products, changing both prices in one `UPDATE`, and checking their audit rows.

<details>
<summary>Hint</summary>

An `UPDATE` trigger can read the old and new versions from `deleted` and `inserted`. Join them by `IDProduct`. `UPDATE(PriceWithoutVAT)` tells you whether that column appeared in the statement; compare the old and new values to detect a real change.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Product_PriceAudit
ON dbo.Product
AFTER UPDATE
AS
BEGIN
    IF UPDATE(PriceWithoutVAT)
    BEGIN
        INSERT INTO dbo.ProductTriggerAudit
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
FROM dbo.ProductTriggerAudit AS a
WHERE a.Operation = N'UPDATE'
  AND a.ProductNumber IN (N'EX-TRG-U-001', N'EX-TRG-U-002');
GO
```

The query should show two `UPDATE` rows, with old/new price pairs `10.00`/`15.00` and `20.00`/`25.00`. Both products are changed by one statement, so the trigger must handle multiple rows in `inserted` and `deleted`.

</details>

## Exercise 9 — Price up or down [INTERMEDIATE]

Create an `AFTER UPDATE` trigger named `dbo.trg_Product_PriceDirection` on `dbo.Product`. For every product whose price actually changed, write an audit row with `Operation`:

- `PRICE_UP` when the new price is higher;
- `PRICE_DOWN` when the new price is lower.

The trigger must handle several products in one statement.

Test it by inserting two test products and updating both in one statement: raise the first price from `10.00` to `12.00` and lower the second from `20.00` to `15.00`.

<details>
<summary>Hint</summary>

Use a `CASE` expression in the `SELECT` list of `INSERT ... SELECT`, so each row gets its own `Operation`. Do not copy values into variables: a scalar variable holds only one row.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Product_PriceDirection
ON dbo.Product
AFTER UPDATE
AS
BEGIN
    INSERT INTO dbo.ProductTriggerAudit
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
        CASE
            WHEN i.PriceWithoutVAT > d.PriceWithoutVAT THEN N'PRICE_UP'
            ELSE N'PRICE_DOWN'
        END,
        d.PriceWithoutVAT,
        i.PriceWithoutVAT
    FROM inserted AS i
    JOIN deleted AS d
        ON d.IDProduct = i.IDProduct
    WHERE d.PriceWithoutVAT <> i.PriceWithoutVAT;
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
    (N'Exercise direction test product 1', N'EX-TRG-C-001', NULL, 1, 10.00, NULL),
    (N'Exercise direction test product 2', N'EX-TRG-C-002', NULL, 1, 20.00, NULL);

UPDATE dbo.Product
SET PriceWithoutVAT =
    CASE ProductNumber
        WHEN N'EX-TRG-C-001' THEN 12.00
        WHEN N'EX-TRG-C-002' THEN 15.00
    END
WHERE ProductNumber IN (N'EX-TRG-C-001', N'EX-TRG-C-002');

SELECT ProductNumber, Operation, OldPrice, NewPrice
FROM dbo.ProductTriggerAudit
WHERE Operation IN (N'PRICE_UP', N'PRICE_DOWN')
  AND ProductNumber IN (N'EX-TRG-C-001', N'EX-TRG-C-002');
GO
```

Result:

| ProductNumber | Operation | OldPrice | NewPrice |
|---|---|---:|---:|
| EX-TRG-C-001 | PRICE_UP | 10.00 | 12.00 |
| EX-TRG-C-002 | PRICE_DOWN | 20.00 | 15.00 |

The price-audit trigger from Exercise 8 fires for the same statement and writes its own `UPDATE` rows; the query keeps only this trigger's rows.

</details>

## Exercise 10 — Audit deleted products [INTERMEDIATE]

Create an `AFTER DELETE` trigger named `dbo.trg_Product_DeleteAudit` on `dbo.Product`.

For every deleted row, write an audit row containing its `IDProduct`, `DELETE`, the deleted `PriceWithoutVAT` as `OldPrice`, and `NULL` as `NewPrice`.

Test it by inserting two test products and deleting both with one statement. Check the audit rows by `ProductNumber`.

<details>
<summary>Hint</summary>

Deleted rows are available in `deleted`. The trigger must use a set-based `INSERT ... SELECT` so that one statement deleting several products produces one audit row per product.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Product_DeleteAudit
ON dbo.Product
AFTER DELETE
AS
BEGIN
    INSERT INTO dbo.ProductTriggerAudit
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
FROM dbo.ProductTriggerAudit AS a
WHERE a.Operation = N'DELETE'
  AND a.ProductNumber IN (N'EX-TRG-D-001', N'EX-TRG-D-002')
ORDER BY a.AuditID DESC;
GO
```

The query should show two `DELETE` rows even though the products no longer exist.

</details>

## Exercise 11 — Flag large price reductions for review [ADVANCED]

Create an `AFTER UPDATE` trigger named `dbo.trg_Product_PriceReview` on `dbo.Product`.

When a product's `PriceWithoutVAT` is reduced by more than 25 percent, write an audit row with `PRICE_REVIEW` as `Operation`, the old price, and the new price. The trigger should:

- compare old and new values for every affected product;
- ignore updates that do not change `PriceWithoutVAT`;
- write one audit row for every qualifying product in a multi-row update.

Test the rule with two products updated together: reduce one price by 20 percent and the other by 30 percent. Check which change was flagged.

<details>
<summary>Hint</summary>

Join `inserted` and `deleted` on `IDProduct`. Search for rows where the new price is less than 75% of the old price. Use one `INSERT ... SELECT` statement so the trigger can record every matching row.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_Product_PriceReview
ON dbo.Product
AFTER UPDATE
AS
BEGIN
    IF UPDATE(PriceWithoutVAT)
    BEGIN
        INSERT INTO dbo.ProductTriggerAudit
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
FROM dbo.ProductTriggerAudit
WHERE Operation = N'PRICE_REVIEW'
  AND ProductNumber IN (N'EX-TRG-R-001', N'EX-TRG-R-002');
GO
```

The query should show one `PRICE_REVIEW` row for `EX-TRG-R-002` with old/new prices `100.00`/`70.00`. The 20 percent reduction does not meet the review threshold.

This exercise records a review flag rather than rejecting the change. In a production design, consider whether a declarative constraint or validation in the application/procedure is a better fit. Triggers add automatic behavior that callers may not see.

</details>

## Exercise 12 — Debug a flawed price-audit trigger [ADVANCED]

A teammate wrote this trigger, meant to do the same job as Exercise 8's trigger — log every update that changes a product's price:

```sql
CREATE OR ALTER TRIGGER dbo.trg_Product_PriceAudit_Flawed
ON dbo.Product
AFTER UPDATE
AS
BEGIN
    IF UPDATE(PriceWithoutVAT)
    BEGIN
        INSERT INTO dbo.ProductTriggerAudit
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
3. Compare this trigger with the one from Exercise 8. What single condition is missing?

Then create the trigger, test your prediction, and fix it.

<details>
<summary>Hint</summary>

`UPDATE(PriceWithoutVAT)` only reports that the column appeared in the statement's `SET` clause, not that its value changed. Compare `inserted` and `deleted` directly, the way Exercise 8's trigger does, to confirm a real change.

</details>

<details>
<summary>Solution</summary>

**Answers:**

1. `UPDATE(PriceWithoutVAT)` only reports that `PriceWithoutVAT` was included in the triggering statement's `SET` clause. It says nothing about whether the value actually changed.
2. Yes, the flawed trigger writes an audit row for every affected product, even though `PriceWithoutVAT` kept its old value. Those rows are misleading: they record a price change that never happened.
3. The flawed trigger is missing the `WHERE d.PriceWithoutVAT <> i.PriceWithoutVAT` condition that Exercise 8's trigger uses to confirm the value actually changed.

**Reproduce the bug:**

```sql
CREATE OR ALTER TRIGGER dbo.trg_Product_PriceAudit_Flawed
ON dbo.Product
AFTER UPDATE
AS
BEGIN
    IF UPDATE(PriceWithoutVAT)
    BEGIN
        INSERT INTO dbo.ProductTriggerAudit
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
FROM dbo.ProductTriggerAudit
WHERE Operation = N'UPDATE'
  AND ProductNumber IN (N'EX-TRG-F-001', N'EX-TRG-F-002')
ORDER BY AuditID;
GO
```

This returns two `UPDATE` rows with `OldPrice` equal to `NewPrice`, confirmed by running the statements above: the flawed trigger only checks that `PriceWithoutVAT` was mentioned in the `SET` clause, not that its value changed, so a no-op price assignment still produces audit noise.

**Fix:**

```sql
CREATE OR ALTER TRIGGER dbo.trg_Product_PriceAudit_Flawed
ON dbo.Product
AFTER UPDATE
AS
BEGIN
    IF UPDATE(PriceWithoutVAT)
    BEGIN
        INSERT INTO dbo.ProductTriggerAudit
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

Running the same no-op update again now writes zero new audit rows, confirmed by checking `AuditID` values added after the fix. A follow-up update that changes `EX-TRG-F-001`'s price from `50.00` to `55.00` still produces exactly one audit row, so the fix does not silently swallow real changes. This is the same trigger built in Exercise 8 — the point of this exercise is recognizing why the missing condition matters, not writing new logic from scratch.

</details>

## References

- [Lab 02 – Triggers](../labs/lab02-triggers.md)
