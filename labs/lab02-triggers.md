# Lab 2 – Triggers

**Database:** `AdventureWorksENG`

A trigger is database code that runs automatically when a specified event occurs.

In this lab, we focus on **DML AFTER triggers** that react to:

- `INSERT`
- `UPDATE`
- `DELETE`

> [!IMPORTANT]
> **Core idea:** A trigger fires automatically. You do not call it.

---

## Learning objectives

After completing this lab, you should be able to:

- explain what a DML trigger is;
- create an `AFTER INSERT`, `AFTER UPDATE`, or `AFTER DELETE` trigger;
- use the `inserted` and `deleted` special tables;
- explain why triggers must be written to handle multiple rows;
- compare old and new values during an `UPDATE`;
- temporarily disable and re-enable a trigger;
- recognize situations where triggers are useful and where they can make a design harder to understand.

This lab assumes you already know:

- batches and `GO`;
- T-SQL variables;
- `IF / ELSE`;
- `CAST`.

---

# Section 1 – What is a trigger?

A **trigger** is code that runs automatically when a specified event occurs.

Unlike normal SQL statements that we execute explicitly, a trigger waits for an event and reacts to it automatically.

## A simple analogy

Think about a **security alarm** in a building.

You do not manually activate the alarm when someone breaks in. Instead, the alarm system is connected to sensors and reacts automatically when a specific event occurs.

```mermaid
flowchart LR
    A["Door opens"] --> B["Sensor detects the event"]
    B --> C["Alarm is triggered"]
    C --> D["Alarm sounds"]
```

A database trigger works in a similar way.

Instead of a door opening, the event is usually a change to data:
- INSERT
- UPDATE
- DELETE

For example, imagine that we want to keep a record of every new product added to the database.

An application executes:

```sql
INSERT INTO Product (Name, PriceWithoutVAT)
VALUES ('Keyboard', 25.00);
```

The application does not need to explicitly execute the logging code.

The `INSERT` itself causes the trigger to fire automatically:

```mermaid
flowchart LR
    A["INSERT new Product"] --> B["Product table"]
    B --> C["Trigger fires automatically"]
    C --> D["Write entry to audit log"]
```

The important idea is:

> **An event happens → the trigger reacts automatically.**

The SQL statement that caused the event does not explicitly call the trigger.

---

## Triggers are attached to database objects

A DML trigger is attached to a particular **table or view**.

For example, a trigger attached to the `Product` table could react when rows in that table are:

- inserted,
- updated,
- deleted.

```mermaid
flowchart TD
    A["Product table"]

    B["INSERT"]
    C["UPDATE"]
    D["DELETE"]

    B --> A
    C --> A
    D --> A

    A --> E["Trigger"]
    E --> F["Trigger code executes"]
```

A trigger can react to one or more of these events.

For example:

```sql
AFTER INSERT
```

means:

> Execute the trigger after an `INSERT` occurs.

A trigger can also react to multiple events:

```sql
AFTER INSERT, UPDATE, DELETE
```

---

## DML and DDL triggers

SQL Server supports several kinds of triggers.

In this course, we focus on **DML triggers**.

DML triggers react to changes in **table data**:

- `INSERT`
- `UPDATE`
- `DELETE`

```mermaid
flowchart LR
    A["Data changes"] --> B["INSERT"]
    A --> C["UPDATE"]
    A --> D["DELETE"]

    B --> E["DML trigger"]
    C --> E
    D --> E
```

SQL Server also supports **DDL triggers**.

DDL triggers react to changes in the **database structure**, for example:

```sql
CREATE TABLE
ALTER TABLE
DROP TABLE
```

A simple way to remember the difference is:

| Trigger type | Reacts to | Examples |
|---|---|---|
| **DML trigger** | Changes to data | `INSERT`, `UPDATE`, `DELETE` |
| **DDL trigger** | Changes to database structure | `CREATE`, `ALTER`, `DROP` |

> [!NOTE]
> DDL triggers are outside the scope of this lab. We will work with **DML triggers**.

---

## AFTER and INSTEAD OF triggers

For DML operations, two important trigger types are:

- `AFTER` – executes after the DML operation has been applied;
- `INSTEAD OF` – executes instead of the original DML operation.

Consider an `INSERT`.

With an `AFTER` trigger:

```mermaid
flowchart LR
    A["INSERT"] --> B["Row is inserted"]
    B --> C["AFTER trigger executes"]
```

With an `INSTEAD OF` trigger:

```mermaid
flowchart LR
    A["INSERT"] --> B["INSTEAD OF trigger executes"]
    B -.-> C["Original INSERT does not execute automatically"]
```

This lab focuses on **AFTER triggers**.

> [!IMPORTANT]
> An `AFTER` trigger executes as part of the **same transaction** as the statement that caused it. If the trigger fails and the transaction is rolled back, the original data change is rolled back as well. Transactions will be covered in more detail later in this course. 

For now, remember the basic pattern:

```text
DML statement
     ↓
data changes
     ↓
AFTER trigger fires
     ↓
trigger code executes
```

In the next sections, we will create our first trigger and see exactly how this works in SQL Server.

---

## When are triggers useful?

Typical uses include:

- **audit and activity logging**;
- **enforcing rules that are difficult to express with normal constraints**;
- **maintaining related data that must always remain consistent**.

In modern systems, many business rules and workflows are implemented in the **application or service layer** rather than with database triggers.

Triggers are still useful when a rule or action must be enforced **at the database level**, regardless of which application, script, or tool modifies the data.

However, triggers also introduce **hidden behavior**.

A developer can execute a simple `INSERT`, `UPDATE`, or `DELETE` without immediately seeing that additional code will execute automatically.

> [!WARNING]
> **Use triggers deliberately.** They are useful when automatic database-level behavior is required, but overusing them can make systems harder to understand, test, and debug.

---

## Check your understanding

1. What causes a trigger to execute?
2. Do you call a trigger with `EXEC`?
3. What three DML events can a trigger react to?
4. What is the difference between `AFTER` and `INSTEAD OF`?

<details>
<summary>Show answers</summary>

1. A configured event on the trigger's parent table or view.
2. No. A trigger fires automatically.
3. `INSERT`, `UPDATE`, and `DELETE`.
4. An `AFTER` trigger runs after the DML operation has been applied. An `INSTEAD OF` trigger replaces the original operation.

</details>

---

# Section 2 – Your first trigger

We will first create a simple table that triggers can write to:

```sql
CREATE TABLE ActivityLog
(
    IDActivityLog int IDENTITY(1,1) PRIMARY KEY,
    Message       nvarchar(500) NOT NULL,
    LoggedAt      datetime2 NOT NULL DEFAULT SYSDATETIME()
);
GO
```

Now create a trigger on `City`:

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_Insert
ON dbo.City
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO ActivityLog (Message)
    VALUES ('A row was inserted into City.');
END
GO
```

> [!TIP]
> `SET NOCOUNT ON` stops SQL Server from sending `(n rows affected)` messages for each statement inside the trigger. It has nothing to do with the trigger's own event — it is the same `SET NOCOUNT ON` from Lab 00, Section 9. 

Breakdown:

```mermaid
flowchart LR
    A["dbo.trg_City_Insert<br/><b>Trigger name</b>"]
    B["ON dbo.City<br/><b>Parent table</b>"]
    C["AFTER INSERT<br/><b>Trigger event</b>"]
    D["AS BEGIN ... END<br/><b>Trigger body</b>"]

    A --> B --> C --> D
```

The trigger now exists in the database.

We do not call it.

We fire it by inserting into `City`:

```sql
INSERT INTO City (Name, StateID)
VALUES ('Zadar', 1);
```

Check the log:

```sql
SELECT *
FROM ActivityLog
ORDER BY LoggedAt DESC;
```

One statement was executed explicitly:

```sql
INSERT INTO City ...
```

But another action happened automatically:

```sql
INSERT INTO ActivityLog ...
```

That second action came from the trigger.

### Can we call the trigger directly?

Try:

```sql
EXEC dbo.trg_City_Insert;
```

SQL Server returns an error.

`EXEC` is used to run a stored procedure explicitly. Stored procedures are covered in Lab 3.

A trigger works differently:

- a stored procedure runs only when you call it;
- a trigger runs automatically when its event occurs;
- therefore, a trigger cannot be started with `EXEC`.

For `trg_City_Insert`, the event is an `INSERT` on `dbo.City`.

So the only way to make this trigger run is to perform an `INSERT` on that table.

---

## Check your understanding

1. Which table is `trg_City_Insert` attached to?
2. What event fires it?
3. What caused the row to appear in `ActivityLog`?
4. Why does `EXEC dbo.trg_City_Insert` fail?

<details>
<summary>Show answers</summary>

1. `dbo.City`.
2. `INSERT`.
3. The `INSERT` into `City` fired the trigger automatically.
4. Triggers are not invoked like stored procedures. They execute because their configured event occurred.

</details>

---

# Section 3 – The `inserted` and `deleted` tables

A useful trigger usually needs to know **which rows caused it to fire**.

For example, if a new city is inserted, the trigger may need to know its ID and name.

SQL Server provides this information through two special tables available inside DML triggers:

- `inserted`
- `deleted`

There is no `updated` table.

Their contents depend on the DML event:

| Event | `inserted` | `deleted` |
|---|---|---|
| `INSERT` | new rows | empty |
| `DELETE` | empty | old rows |
| `UPDATE` | new versions | old versions |

A simple way to remember this is:

```mermaid
flowchart LR
    A["INSERT"] --> B["inserted<br/>new rows"]

    C["DELETE"] --> D["deleted<br/>old rows"]

    E["UPDATE"] --> F["deleted<br/>old versions"]
    E --> G["inserted<br/>new versions"]
```

For an `UPDATE`, both versions are available:

```text
deleted  -> values before UPDATE
inserted -> values after UPDATE
```

> [!IMPORTANT]
> Despite their names, `inserted` and `deleted` are **tables**, not individual rows. They can contain one row or many rows. We will examine this in detail in the next section.

These tables exist only while the trigger is running.

You can read from them inside a trigger:

```sql
SELECT *
FROM inserted;
```

but you cannot query them as normal tables outside a trigger.

---

## Improving the INSERT trigger

The first trigger only recorded that *something* was inserted.

Now that we know about `inserted`, we can log the actual inserted data:

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_Insert
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO ActivityLog (Message)
    SELECT
        'City inserted: ID='
        + CAST(IDCity AS nvarchar(10))
        + ', Name='
        + Name
    FROM inserted;
END
GO
```

The important part is:

```sql
FROM inserted;
```

The trigger does not need to search the `City` table to find out what was inserted. SQL Server already provides the affected rows through `inserted`.

```mermaid
flowchart LR
    A["INSERT INTO City"] --> B["inserted"]
    B --> C["Trigger reads<br/>inserted"]
    C --> D["ActivityLog"]
```

> [!NOTE]
> This trigger intentionally does not use `SET NOCOUNT ON`, so SQL Server displays the `(n rows affected)` messages. In practice, `SET NOCOUNT ON` is commonly used in triggers to suppress these unnecessary messages.

Test it:

```sql
INSERT INTO City (Name, StateID)
VALUES ('Karlovac', 1);

SELECT *
FROM ActivityLog
ORDER BY LoggedAt DESC;
```

The trigger reads the inserted row from `inserted` and uses its values to create the log message.

In the next section, we will see what happens when a single statement inserts **more than one row**.

---

# Section 4 – Triggers fire once per statement

This is one of the most important trigger rules.

> [!IMPORTANT]
> **A trigger fires once per statement, not once per row.** Other database systems may support row-level triggers. For example, Oracle can execute a trigger once for each affected row using FOR EACH ROW

Consider:

```sql
INSERT INTO City (Name, StateID)
VALUES
    ('Pula',    1),
    ('Sisak',    1),
    ('Bjelovar', 1);
```

This is:

- one `INSERT` statement;
- three inserted rows;
- one trigger execution;
- three rows inside `inserted`.

Because our trigger uses:

```sql
INSERT INTO ActivityLog (Message)
SELECT ...
FROM inserted;
```

it correctly writes three log rows.

This is a **set-based trigger**.

### The dangerous pattern

Avoid trigger code that assumes `inserted` contains exactly one row.

For example:

```sql
DECLARE @CityID int;

SELECT @CityID = IDCity
FROM inserted;
```

If several rows are present, the variable is assigned multiple times and only one value remains.
Which row supplies the final value is not something the trigger should rely on.

Even worse:

```sql
SET @CityID = (
    SELECT IDCity
    FROM inserted
);
```

fails when `inserted` contains more than one row.

> [!IMPORTANT]
> **Rule:** Always design triggers as if `inserted` and `deleted` may contain many rows.

---

## Check your understanding

1. If one `INSERT` statement inserts 100 rows, how many times does the trigger fire?
2. How many rows can `inserted` contain?
3. Why is `INSERT INTO log SELECT ... FROM inserted` a good trigger pattern?
4. Why is loading one value from `inserted` into a scalar variable dangerous?

<details>
<summary>Show answers</summary>

1. Once.
2. 100 rows in this example.
3. It is set-based and naturally handles one row or many rows.
4. Because a trigger statement may affect multiple rows, so `inserted` is not guaranteed to contain only one row.

</details>

---

# Section 5 – UPDATE: old and new values

An `UPDATE` is the most interesting trigger event because SQL Server gives us access to **both versions of every affected row**.

For an `UPDATE`:

```text
deleted  = old values
inserted = new values
```

There is no `updated` table.

The old version of the row is available in `deleted`, and the new version is available in `inserted`.

---

## First demonstration – both tables contain rows

Create a temporary trigger that counts the rows in `inserted` and `deleted`:

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_UpdateDemo
ON dbo.City
AFTER UPDATE
AS
BEGIN
    INSERT INTO ActivityLog (Message)
    VALUES (
        'inserted rows: '
        + CAST((SELECT COUNT(*) FROM inserted) AS nvarchar(10))
        + ' | deleted rows: '
        + CAST((SELECT COUNT(*) FROM deleted) AS nvarchar(10))
    );
END
GO
```

Now update one city:

```sql
UPDATE City
SET Name = 'Zagreb Updated'
WHERE Name = 'Zagreb';
```

Check the log:

```sql
SELECT *
FROM ActivityLog
ORDER BY LoggedAt DESC;
```

The log should contain:

```text
inserted rows: 1 | deleted rows: 1
```

Why are both tables populated?

Because SQL Server keeps both versions of the updated row:

```mermaid
flowchart LR
    A["deleted<br/><b>Old values</b><br/>Name = Zagreb"]
    B["UPDATE"]
    C["inserted<br/><b>New values</b><br/>Name = Zagreb Updated"]

    A --> B --> C
```

So for an `UPDATE`:

* `deleted` contains the row **before** the change;
* `inserted` contains the row **after** the change.

Now remove the temporary demonstration trigger:

```sql
DROP TRIGGER dbo.trg_City_UpdateDemo;
GO
```

---

## Comparing the old and new values

Knowing that both versions exist is useful because we can compare them.

To match the old version of a row with its new version, join `deleted` and `inserted` using the primary key:

```sql
FROM inserted AS i
JOIN deleted AS d
    ON d.IDCity = i.IDCity
```

Now we can create a trigger that records actual city name changes:

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_LogRename
ON dbo.City
AFTER UPDATE
AS
BEGIN
    INSERT INTO ActivityLog (Message)
    SELECT
        'City renamed from "'
        + d.Name
        + '" to "'
        + i.Name
        + '"'
    FROM inserted AS i
    JOIN deleted AS d
        ON d.IDCity = i.IDCity
    WHERE d.Name <> i.Name;
END
GO
```

The important parts are:

```sql
d.Name
```

the old value from `deleted`, and:

```sql
i.Name
```

the new value from `inserted`.

The condition:

```sql
WHERE d.Name <> i.Name
```

ensures that we log only rows where the name actually changed.

---

## Test the trigger

Run an update:

```sql
UPDATE City
SET Name = 'Zagreb'
WHERE Name = 'Zagreb Updated';
```

Then check the log:

```sql
SELECT *
FROM ActivityLog
ORDER BY LoggedAt DESC;
```

You should see a message similar to:

```text
City renamed from "Zagreb Updated" to "Zagreb"
```

The trigger did not need the application to send the old value.

SQL Server already provided both versions through `deleted` and `inserted`.

---

## Multi-row UPDATE

The same trigger also works when one statement updates several rows.

For example:

```sql
INSERT INTO City (Name, StateID)
VALUES
    ('Update Test 1', 1),
    ('Update Test 2', 1);

UPDATE City
SET Name = Name + ' Updated'
WHERE Name IN ('Update Test 1', 'Update Test 2');
```

The trigger still fires only **once**, but:

* `deleted` contains all old versions of the affected rows;
* `inserted` contains all new versions;
* the join matches each old row with its corresponding new row.

This is why trigger logic should be written as a **set-based operation** rather than assuming that only one row was updated.

---

## NULL-safe comparison

A simple comparison such as:

```sql
WHERE d.Name <> i.Name
```

works when `Name` cannot contain `NULL`.

If a column allows `NULL`, remember that comparisons with `NULL` do not return `TRUE` in the usual way.

For a nullable column, a more complete comparison is:

```sql
WHERE
       d.Name <> i.Name
    OR (d.Name IS NULL AND i.Name IS NOT NULL)
    OR (d.Name IS NOT NULL AND i.Name IS NULL);
```

For the examples in this lab, the simpler form is enough when the column is known to be non-nullable.

---

## Check your understanding

1. What does `deleted` contain during an `UPDATE`?
2. What does `inserted` contain during an `UPDATE`?
3. Why do we join `inserted` and `deleted` using the primary key?
4. Why do we use `WHERE d.Name <> i.Name`?
5. If one `UPDATE` changes 20 rows, how many times does the trigger fire?

<details>
<summary>Show answers</summary>

1. The old versions of the affected rows.
2. The new versions of the affected rows.
3. To match each row before the update with the same row after the update.
4. To keep only rows where the value actually changed.
5. Once. `inserted` and `deleted` can each contain 20 rows.

</details>

---

# Section 6 – DELETE: old values only

For a `DELETE`, SQL Server gives us access to the rows that are being removed through the `deleted` special table.

For a `DELETE`:

```text
deleted  = deleted rows
inserted = empty
```

Conceptually:

```mermaid
flowchart LR
    A["Row in City<br/>Name = DeleteMe"]
    B["DELETE"]
    C["Row removed from City"]
    D["deleted<br/><b>Old values available to trigger</b>"]

    A --> B
    B --> C
    B --> D
```

The important idea is that the row may be gone from the table, but its old values are still available inside the trigger through `deleted`.

---

## First DELETE trigger

Create a trigger that logs deleted cities:

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_Delete
ON dbo.City
AFTER DELETE
AS
BEGIN
    INSERT INTO ActivityLog (Message)
    SELECT
        'City deleted: ID='
        + CAST(IDCity AS nvarchar(10))
        + ', Name='
        + Name
    FROM deleted;
END
GO
```

Now delete a city:

```sql
INSERT INTO City (Name, StateID)
VALUES ('DeleteMe', 1);

DELETE FROM City
WHERE Name = 'DeleteMe';
```

Check the log:

```sql
SELECT *
FROM ActivityLog
ORDER BY LoggedAt DESC;
```

The row no longer exists in `City`, but the trigger was still able to read its old values from `deleted`.

---

## Multi-row DELETE

The same trigger also works when one statement deletes several rows:

```sql
INSERT INTO City (Name, StateID)
VALUES
    ('Delete Test 1', 1),
    ('Delete Test 2', 1),
    ('Delete Test 3', 1);

DELETE FROM City
WHERE Name IN ('Delete Test 1', 'Delete Test 2', 'Delete Test 3');
```

The trigger fires only **once**, but `deleted` contains every row removed by that statement.

Because the trigger uses:

```sql
INSERT INTO ActivityLog (Message)
SELECT ...
FROM deleted;
```

it correctly handles one row or many rows.

---

## INSERT, UPDATE, DELETE compared

| Event    | `inserted`   | `deleted`    |
| -------- | ------------ | ------------ |
| `INSERT` | new rows     | empty        |
| `UPDATE` | new versions | old versions |
| `DELETE` | empty        | deleted rows |

This table is one of the most important things to remember when working with DML triggers.

---

## Check your understanding

1. Which special table contains rows during a `DELETE`?
2. What does `inserted` contain during a `DELETE`?
3. Can a DELETE trigger still read the values of a row after it has been deleted?
4. If one `DELETE` statement removes 20 rows, how many times does the trigger fire?

<details>
<summary>Show answers</summary>

1. `deleted`.
2. It is empty.
3. Yes. The old values are available through `deleted` while the trigger is executing.
4. Once. `deleted` can contain all 20 rows.

</details>

---

# Section 7 – The UPDATE() function

Inside an `INSERT` or `UPDATE` trigger, SQL Server provides:

```sql
UPDATE(ColumnName)
```

It returns true when the column was part of the triggering statement.

Example:

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_StateChange
ON dbo.City
AFTER UPDATE
AS
BEGIN
    IF UPDATE(StateID)
    BEGIN
        INSERT INTO ActivityLog (Message)
        VALUES ('StateID was included in the UPDATE statement.');
    END
END
GO
```

Test it:

```sql
UPDATE City
SET Name = 'Test'
WHERE IDCity = 1;
```

No `StateID` was mentioned.

Now:

```sql
UPDATE City
SET StateID = 1
WHERE IDCity = 1;
```

`UPDATE(StateID)` returns true.

### Important distinction

`UPDATE(StateID)` answers:

> Was `StateID` included in the `SET` clause?

It does **not** answer:

> Did the value actually change?

For example:

```sql
UPDATE City
SET StateID = StateID
WHERE IDCity = 1;
```

still makes:

```sql
UPDATE(StateID)
```

return true.

To detect a real value change, compare `inserted` and `deleted`.

> [!NOTE]
> SQL Server does not provide matching `INSERT()` or `DELETE()` functions.
>
> `UPDATE(column)` is a special trigger function used to check whether a column was targeted by an `INSERT` or `UPDATE` statement.


---

## Check your understanding

1. What does `inserted` contain after an `UPDATE`?
2. What does `deleted` contain after an `UPDATE`?
3. What does `UPDATE(StateID)` tell us?
4. Does `UPDATE(StateID)` prove that the value changed?

<details>
<summary>Show answers</summary>

1. The new versions of the affected rows.
2. The old versions of the affected rows.
3. That `StateID` was included in the triggering `INSERT` or `UPDATE` statement.
4. No. The column may have been assigned the same value it already had.

</details>

---

# Section 8 – One trigger for multiple events

A single trigger can react to more than one DML event.

For example:

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_All
ON dbo.City
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    -- trigger body
END
GO
```

This trigger fires when an `INSERT`, `UPDATE`, or `DELETE` occurs on `dbo.City`.

---

## How do we know which event occurred?

We can use the contents of `inserted` and `deleted`.

| Event | `inserted` | `deleted` |
|---|---|---|
| `INSERT` | contains rows | empty |
| `UPDATE` | contains rows | contains rows |
| `DELETE` | empty | contains rows |

This gives us a simple pattern for detecting the event.

---

## Example

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_All
ON dbo.City
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    IF EXISTS (SELECT 1 FROM inserted)
       AND NOT EXISTS (SELECT 1 FROM deleted)
    BEGIN
        PRINT 'INSERT';
    END
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        AND EXISTS (SELECT 1 FROM deleted)
    BEGIN
        PRINT 'UPDATE';
    END
    ELSE IF NOT EXISTS (SELECT 1 FROM inserted)
        AND EXISTS (SELECT 1 FROM deleted)
    BEGIN
        PRINT 'DELETE';
    END
END
GO
```

Now test all three events:

```sql
-- INSERT
INSERT INTO City (Name, StateID)
VALUES ('Test City', 1);

-- UPDATE
UPDATE City
SET Name = 'Updated Test City'
WHERE Name = 'Test City';

-- DELETE
DELETE FROM City
WHERE Name = 'Updated Test City';
```

The same trigger fires for all three statements.

The trigger determines which event occurred by checking whether `inserted` and `deleted` contain rows.

---

## How the detection works

```text
INSERT
inserted = rows
deleted  = empty

UPDATE
inserted = rows
deleted  = rows

DELETE
inserted = empty
deleted  = rows
```

```mermaid
flowchart TD
    A["DML event on City"]
    B{"inserted has rows?"}
    C{"deleted has rows?"}
    D{"deleted has rows?"}
    E["INSERT"]
    F["UPDATE"]
    G["DELETE"]

    A --> B
    B -->|Yes| C
    B -->|No| D

    C -->|No| E
    C -->|Yes| F

    D -->|Yes| G
```

---

## Important note

This technique works when the DML statement actually affects rows.

For example:

```sql
UPDATE City
SET Name = 'Something'
WHERE IDCity = -1;
```

If no row matches the `WHERE` condition, both `inserted` and `deleted` are empty.

Therefore, the special tables alone do not always tell us which statement was attempted when zero rows were affected.

For the examples in this lab, we will use statements that actually affect rows.

---

## Should one trigger always handle all events?

Not necessarily.

A multi-event trigger can be useful when several events share similar logic.

However, separate triggers can sometimes be easier to read and maintain.

For example:

```text
trg_City_Insert
trg_City_Update
trg_City_Delete
```

may be clearer than putting three unrelated responsibilities into one large trigger.

> [!TIP]
> Use a multi-event trigger when the logic belongs together.
>
> Do not combine events only because SQL Server allows it.

---

## Check your understanding

1. Can one trigger react to `INSERT`, `UPDATE`, and `DELETE`?
2. Which special tables contain rows during an `UPDATE`?
3. How can we detect an `INSERT` using `inserted` and `deleted`?
4. What happens if the DML statement affects zero rows?
5. Is one multi-event trigger always better than separate triggers?

<details>
<summary>Show answers</summary>

1. Yes. A trigger can list multiple events, for example `AFTER INSERT, UPDATE, DELETE`.
2. Both `inserted` and `deleted`.
3. `inserted` contains rows and `deleted` is empty.
4. Both special tables can be empty, so their contents alone may not identify which statement was attempted.
5. No. A multi-event trigger is useful when the logic is related. Separate triggers can be clearer when each event has a different responsibility.

</details>

---

# Section 9 – Managing triggers

## Disable a trigger

```sql
DISABLE TRIGGER dbo.trg_City_Insert
ON dbo.City;
```

Re-enable it with:

```sql
ENABLE TRIGGER dbo.trg_City_Insert
ON dbo.City;
```

This can be useful during carefully controlled maintenance or bulk loading.

However:

> [!WARNING]
> Anything the trigger normally enforces or records is also disabled while it is disabled.
>
> Never disable a trigger casually, and do not forget to re-enable it.

### Multiple triggers on the same event

SQL Server allows multiple triggers for the same event on the same table.

> [!WARNING]
> Do not assume that multiple triggers for the same event run in creation order. SQL Server lets you mark one trigger `FIRST` and one `LAST` for an event using `sp_settriggerorder`, but the order of the remaining triggers is not guaranteed.
>
> If your design depends heavily on trigger order, reconsider the design.

### Nested triggers

A trigger can execute a statement that fires another trigger.

```mermaid
flowchart LR
    A["INSERT into Table A"]
    B["Trigger A fires"]
    C["Trigger A inserts into Table B"]
    D["Trigger B fires automatically"]

    A --> B --> C --> D
```

This is called **trigger nesting**.

SQL Server supports up to 32 levels of nesting.

> [!WARNING]
> Deep trigger chains are difficult to reason about and are usually a sign that the design should be simplified.

---

# Section 10 – Real-world example: checking a business rule

## Example – Checking a business rule with a trigger

For this example, we will use a separate database so that the business-rule example is completely independent of the AdventureWorksENG database.

Create a new database:

```sql
CREATE DATABASE EmployeeDemo;
GO

USE EmployeeDemo;
GO
```

Suppose each employee belongs to an area, and each area has an allowed salary range.

First, create a table with the allowed ranges:

```sql
CREATE TABLE SalaryRange
(
    Area      nvarchar(50) PRIMARY KEY,
    MinSalary decimal(10,2) NOT NULL,
    MaxSalary decimal(10,2) NOT NULL
);
GO

INSERT INTO SalaryRange (Area, MinSalary, MaxSalary)
VALUES
    ('Electronics', 2000.00, 3000.00),
    ('Physics',     1200.00, 8500.00),
    ('Acting',      2000.00, 3000.00),
    ('IT',           500.00, 6000.00),
    ('Chemistry',   3500.00, 5000.00),
    ('Mathematics', 1000.00, 10000.00);
GO
```

Now create a simple employee table:

```sql
CREATE TABLE Employee
(
    IDEmployee int IDENTITY(1,1) PRIMARY KEY,
    Name       nvarchar(100) NOT NULL,
    Area       nvarchar(50) NOT NULL,
    Salary     decimal(10,2) NOT NULL
);
GO
```

The trigger checks every inserted or updated row against `SalaryRange`.

```sql
CREATE OR ALTER TRIGGER dbo.trg_Employee_CheckSalary
ON dbo.Employee
AFTER INSERT, UPDATE
AS
BEGIN
    IF EXISTS
    (
        SELECT 1
        FROM inserted AS i
        JOIN SalaryRange AS sr
            ON sr.Area = i.Area
        WHERE i.Salary < sr.MinSalary
           OR i.Salary > sr.MaxSalary
    )
    BEGIN
        PRINT 'Warning: salary is outside the allowed range.';
    END
END
GO
```

The important part is that the trigger checks the rows from `inserted` against another table:

```sql
FROM inserted AS i
JOIN SalaryRange AS sr
    ON sr.Area = i.Area
```

This allows the database to check a business rule that depends on data stored in another table.

### Test with a valid salary

```sql
INSERT INTO Employee (Name, Area, Salary)
VALUES ('Anna', 'IT', 2500.00);
GO
```

For `IT`, the allowed range is:

```text
500.00 – 6000.00
```

so no warning is printed.

### Test with an invalid salary

```sql
INSERT INTO Employee (Name, Area, Salary)
VALUES ('John', 'IT', 9000.00);
GO
```

The salary is above the allowed maximum, so the trigger prints:

```text
Warning: salary is outside the allowed range.
```
> [!NOTE]
> In a real system, detecting an invalid value would usually not be enough — we would want to **reject the entire change** and leave the database in a consistent state. This requires an understanding of transactions and error handling, which will be covered later in this course.
>
> For now, the trigger only prints a warning so that we can focus on the trigger logic itself.

### The same trigger also works for UPDATE

```sql
UPDATE Employee
SET Salary = 7000.00
WHERE Name = 'Anna';
GO
```

The trigger fires again because it is defined for both:

```sql
AFTER INSERT, UPDATE
```

### It also works with multiple rows

```sql
INSERT INTO Employee (Name, Area, Salary)
VALUES
    ('Alice', 'IT',          3000.00),
    ('Bob',   'Chemistry',   9000.00),
    ('Carol', 'Mathematics', 2500.00);
GO
```

The trigger still fires only **once**, but `inserted` contains all three rows.

The `EXISTS` condition finds that at least one row has a salary outside the allowed range.

> This is another example of why trigger logic should be written to work with **sets of rows**, not with a single row.

---

## Check your understanding

1. Why does the trigger join `inserted` with `SalaryRange` instead of comparing against a fixed number?
2. If an `INSERT` adds three employees and only one has an invalid salary, does the trigger still detect it?
3. Why is `EXISTS` a good choice here instead of checking every row individually?
4. Is printing a warning a realistic way to enforce this rule in production?

<details>
<summary>Show answers</summary>

1. The allowed range depends on the employee's `Area`, and that mapping is stored in another table, so the trigger must look it up per row instead of hardcoding a value.
2. Yes. `EXISTS` only needs one matching row among everything in `inserted` to trigger the warning.
3. `EXISTS` stops as soon as it finds one row outside the allowed range; it does not need to process every row individually like a scalar check would.
4. No. A real system would normally reject the change (for example, with `ROLLBACK` or `RAISERROR`) or log it properly instead of only printing a message.

</details>

---

# Section 11 – Real-world example: Maintaining inventory

Triggers are often useful when a change in one table must automatically cause a related change in another table.

A common real-world example is **inventory management**.

Suppose we have products in stock and we create invoice items when those products are sold.

We will use two simple tables:

- `Product` — stores products and the quantity currently available;
- `InvoiceItem` — stores products sold on invoices.

Maintaining inventory involves more than just selling a product.

Think about the following questions:

- What should happen to the stock when a new `InvoiceItem` is **inserted**?
- What should happen if an `InvoiceItem` is **deleted**?
- What should happen if the quantity of an existing `InvoiceItem` is **updated**?

The expected behavior is:

| Operation | Example | Inventory change |
|---|---|---|
| `INSERT` | Sell 3 keyboards | Stock decreases by 3 |
| `DELETE` | Remove a sale of 3 keyboards | Stock increases by 3 |
| `UPDATE` | Change quantity from 3 to 5 | Stock decreases by another 2 |

This is a good scenario for triggers because every change to `InvoiceItem` should automatically produce the corresponding change in inventory.

```mermaid
flowchart LR
    A["InvoiceItem"] --> B{"Operation"}

    B -->|"INSERT"| C["Decrease stock"]
    B -->|"DELETE"| D["Increase stock"]
    B -->|"UPDATE"| E["Adjust stock"]

    C --> F["Product.StockQuantity"]
    D --> F
    E --> F
```

---

## 11.1. Creating the tables

For this example, we will create a separate test database.

The AdventureWorksENG database already contains a `Product` table, so using a separate database keeps this example simple and independent from the existing database structure.

```sql
CREATE DATABASE InventoryDemo;
GO

USE InventoryDemo;
GO
```

First, create the `Product` table:

```sql
CREATE TABLE dbo.Product
(
    IDProduct     int PRIMARY KEY,
    Name          varchar(100) NOT NULL,
    StockQuantity int NOT NULL
);
GO
```

Now create the `InvoiceItem` table:

```sql
CREATE TABLE dbo.InvoiceItem
(
    IDInvoiceItem int IDENTITY(1,1) PRIMARY KEY,
    IDInvoice     int NOT NULL,
    IDProduct     int NOT NULL,
    Quantity      int NOT NULL,
    UnitPrice     decimal(10,2) NOT NULL,

    CONSTRAINT FK_InvoiceItem_Product
        FOREIGN KEY (IDProduct)
        REFERENCES dbo.Product(IDProduct)
);
GO
```

For this example, we do not need a complete `Invoice` table. `IDInvoice` is simply used to identify which invoice an item belongs to.

Insert several products:

```sql
INSERT INTO dbo.Product
    (IDProduct, Name, StockQuantity)
VALUES
    (10, 'Keyboard', 20),
    (20, 'Mouse', 35),
    (30, 'Monitor', 12),
    (40, 'USB-C Cable', 50);
GO
```

Check the initial inventory:

```sql
SELECT *
FROM dbo.Product
ORDER BY IDProduct;
GO
```

The result should be:

| IDProduct | Name | StockQuantity |
|---:|---|---:|
| 10 | Keyboard | 20 |
| 20 | Mouse | 35 |
| 30 | Monitor | 12 |
| 40 | USB-C Cable | 50 |

We are now ready to implement the inventory rules.

---

## 11.2. INSERT — selling a product

Suppose a customer buys **3 keyboards**.

The application creates an invoice item:

```sql
INSERT INTO dbo.InvoiceItem
    (IDInvoice, IDProduct, Quantity, UnitPrice)
VALUES
    (1001, 10, 3, 25.00);
GO
```

The inventory should automatically change from:

```text
20 keyboards
```

to:

```text
20 - 3 = 17 keyboards
```

```mermaid
flowchart LR
    A["INSERT InvoiceItem<br/>3 × Keyboard"] --> B["AFTER INSERT<br/>trigger"]
    B --> C["Product"]
    C --> D["Keyboard<br/>20 → 17"]
```

However, we have not created the trigger yet.

Remove the test row before continuing:

```sql
DELETE FROM dbo.InvoiceItem
WHERE IDInvoice = 1001;
GO
```

---

## 11.3. Creating the INSERT trigger

We can use an `AFTER INSERT` trigger to automatically decrease the inventory.

Remember that `inserted` can contain several rows, and several of those rows may refer to the same product.

Therefore, we first calculate the **total quantity sold for each product**:

```sql
SELECT
    IDProduct,
    SUM(Quantity) AS TotalQuantity
FROM inserted
GROUP BY IDProduct;
```

For example, if `inserted` contains:

| IDProduct | Quantity |
|---:|---:|
| 10 | 2 |
| 10 | 4 |
| 20 | 1 |

the query produces:

| IDProduct | TotalQuantity |
|---:|---:|
| 10 | 6 |
| 20 | 1 |

We can then join this result with `Product` and update the stock:

```sql
CREATE OR ALTER TRIGGER dbo.trg_InvoiceItem_Insert
ON dbo.InvoiceItem
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE p
    SET p.StockQuantity = p.StockQuantity - i.TotalQuantity
    FROM dbo.Product AS p
    JOIN
    (
        SELECT
            IDProduct,
            SUM(Quantity) AS TotalQuantity
        FROM inserted
        GROUP BY IDProduct
    ) AS i
        ON i.IDProduct = p.IDProduct;
END;
GO
```

> [!NOTE]
> `SET NOCOUNT ON` again — the same habit introduced earlier in this lab.

The trigger follows a simple pattern:

```mermaid
flowchart LR
    A["inserted"] --> B["GROUP BY<br/>IDProduct"]
    B --> C["SUM<br/>Quantity"]
    C --> D["JOIN with<br/>Product"]
    D --> E["Decrease<br/>StockQuantity"]
```

The important idea is:

1. calculate how much of each product was sold;
2. match those totals with the corresponding products;
3. subtract the quantities from stock.

---

## 11.4. Testing the INSERT trigger

Check the inventory before the sale:

```sql
SELECT *
FROM dbo.Product
ORDER BY IDProduct;
GO
```

Now sell 3 keyboards:

```sql
INSERT INTO dbo.InvoiceItem
    (IDInvoice, IDProduct, Quantity, UnitPrice)
VALUES
    (1001, 10, 3, 25.00);
GO
```

Check the inventory again:

```sql
SELECT *
FROM dbo.Product
ORDER BY IDProduct;
GO
```

The result should now be:

| IDProduct | Name | StockQuantity |
|---:|---|---:|
| 10 | Keyboard | **17** |
| 20 | Mouse | 35 |
| 30 | Monitor | 12 |
| 40 | USB-C Cable | 50 |

The application did not explicitly update `Product`.

It only inserted an `InvoiceItem`.

The trigger automatically updated the inventory.

---

## 11.5. Remember: `inserted` is a table

Our trigger must also work when one SQL statement inserts multiple invoice items.

For example:

```sql
INSERT INTO dbo.InvoiceItem
    (IDInvoice, IDProduct, Quantity, UnitPrice)
VALUES
    (1002, 10, 2, 25.00),
    (1002, 10, 4, 25.00),
    (1002, 20, 1, 15.00),
    (1002, 40, 5, 8.00);
GO
```

The `inserted` table conceptually contains:

| IDProduct | Quantity |
|---:|---:|
| 10 | 2 |
| 10 | 4 |
| 20 | 1 |
| 40 | 5 |

Remember:

> **A trigger executes once per statement, not once per row.**

Therefore, the trigger executes **once**, and `inserted` contains all four rows.

For product `10`, there are two rows:

```text
Keyboard: 2 + 4 = 6
```

The `GROUP BY` and `SUM()` inside the trigger turn the rows into:

| IDProduct | TotalQuantity |
|---:|---:|
| 10 | 6 |
| 20 | 1 |
| 40 | 5 |

The inventory changes are therefore:

| Product | Quantity sold | Inventory change |
|---|---:|---:|
| Keyboard | 6 | -6 |
| Mouse | 1 | -1 |
| USB-C Cable | 5 | -5 |

```mermaid
flowchart TD
    A["One INSERT statement"] --> B["inserted<br/>4 rows"]
    B --> C["GROUP BY IDProduct"]
    C --> D["SUM Quantity"]
    D --> E["UPDATE Product"]
```

Check the inventory:

```sql
SELECT *
FROM dbo.Product
ORDER BY IDProduct;
GO
```

The trigger correctly handles both single-row and multi-row inserts.

---

## 11.6. DELETE — returning products to stock

Now consider what happens when an invoice item is deleted.

When an `InvoiceItem` is inserted, its quantity is removed from stock.

Therefore, if the invoice item is deleted, that quantity should be **returned to stock**.

For a `DELETE` operation, SQL Server provides the deleted rows through the `deleted` table.

```mermaid
flowchart LR
    A["DELETE<br/>InvoiceItem"] --> B["deleted"]
    B --> C["AFTER DELETE<br/>trigger"]
    C --> D["Increase<br/>StockQuantity"]
```

The rule is the opposite of `INSERT`:

| Operation | Inventory calculation |
|---|---|
| `INSERT` | `StockQuantity - Quantity` |
| `DELETE` | `StockQuantity + Quantity` |

Again, `deleted` may contain several rows, including several rows for the same product.

Therefore, we use the same pattern:

```sql
CREATE OR ALTER TRIGGER dbo.trg_InvoiceItem_Delete
ON dbo.InvoiceItem
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE p
    SET p.StockQuantity = p.StockQuantity + d.TotalQuantity
    FROM dbo.Product AS p
    JOIN
    (
        SELECT
            IDProduct,
            SUM(Quantity) AS TotalQuantity
        FROM deleted
        GROUP BY IDProduct
    ) AS d
        ON d.IDProduct = p.IDProduct;
END;
GO
```

Notice how similar this trigger is to the `INSERT` trigger.

The main differences are:

```text
inserted  → deleted
-         → +
```

The pattern is still the same:

```mermaid
flowchart LR
    A["deleted"] --> B["GROUP BY<br/>IDProduct"]
    B --> C["SUM<br/>Quantity"]
    C --> D["JOIN with<br/>Product"]
    D --> E["Increase<br/>StockQuantity"]
```

### Testing the DELETE trigger

Check the invoice items:

```sql
SELECT *
FROM dbo.InvoiceItem
ORDER BY IDInvoiceItem;
GO
```

Now delete all items belonging to invoice `1002`:

```sql
DELETE FROM dbo.InvoiceItem
WHERE IDInvoice = 1002;
GO
```

This deletes several rows with a single statement.

The trigger executes once, but `deleted` contains all deleted rows.

The trigger groups them by product, calculates the total quantity for each product, and returns those quantities to stock.

Check the inventory:

```sql
SELECT *
FROM dbo.Product
ORDER BY IDProduct;
GO
```

---

## 11.7. UPDATE — changing the sold quantity

An `UPDATE` is slightly more interesting because SQL Server provides **both versions** of each affected row:

- `deleted` contains the **old values**;
- `inserted` contains the **new values**.

Suppose our invoice contains:

| IDInvoice | Product | Quantity |
|---:|---|---:|
| 1001 | Keyboard | 3 |

The customer actually bought 5 keyboards, so we correct the quantity:

```sql
UPDATE dbo.InvoiceItem
SET Quantity = 5
WHERE IDInvoice = 1001
  AND IDProduct = 10;
GO
```

During the trigger execution:

| Table | Product | Quantity |
|---|---|---:|
| `deleted` | Keyboard | **3** |
| `inserted` | Keyboard | **5** |

The stock should **not** be reduced by another 5.

The original 3 keyboards were already removed from stock.

We only need to account for the difference:

```text
5 - 3 = 2
```

Another way to think about it is:

```text
current stock
+ old quantity
- new quantity
= new stock
```

If the current stock is 17:

```text
17 + 3 - 5 = 15
```

```mermaid
flowchart LR
    A["Current stock<br/>17"] --> B["+ old quantity<br/>3"]
    B --> C["20"]
    C --> D["- new quantity<br/>5"]
    D --> E["New stock<br/>15"]
```

For simplicity, we assume that an update can change the **quantity**, but not the product itself.

---

## 11.8. Creating the UPDATE trigger

For an `UPDATE`, we first need to match the old and new versions of each invoice item.

We already used this pattern earlier in the lab:

```sql
FROM inserted AS i
JOIN deleted AS d
    ON d.IDInvoiceItem = i.IDInvoiceItem
```

The primary key connects the old and new version of the same row.

Now suppose one statement updates several invoice items.

We can calculate the total old and new quantities for each product:

```sql
SELECT
    i.IDProduct,
    SUM(d.Quantity) AS OldQuantity,
    SUM(i.Quantity) AS NewQuantity
FROM inserted AS i
JOIN deleted AS d
    ON d.IDInvoiceItem = i.IDInvoiceItem
GROUP BY i.IDProduct;
```

Conceptually, this could produce:

| IDProduct | OldQuantity | NewQuantity |
|---:|---:|---:|
| 10 | 5 | 8 |
| 20 | 2 | 3 |

We can then use those totals to update the inventory:

```sql
CREATE OR ALTER TRIGGER dbo.trg_InvoiceItem_Update
ON dbo.InvoiceItem
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE p
    SET p.StockQuantity =
        p.StockQuantity
        + u.OldQuantity
        - u.NewQuantity
    FROM dbo.Product AS p
    JOIN
    (
        SELECT
            i.IDProduct,
            SUM(d.Quantity) AS OldQuantity,
            SUM(i.Quantity) AS NewQuantity
        FROM inserted AS i
        JOIN deleted AS d
            ON d.IDInvoiceItem = i.IDInvoiceItem
        GROUP BY i.IDProduct
    ) AS u
        ON u.IDProduct = p.IDProduct;
END;
GO
```

The calculation is:

```text
StockQuantity + old quantity - new quantity
```

For our example:

```text
17 + 3 - 5 = 15
```

The complete process is:

```mermaid
flowchart LR
    A["deleted<br/>old rows"] --> C["JOIN by<br/>IDInvoiceItem"]
    B["inserted<br/>new rows"] --> C
    C --> D["GROUP BY<br/>IDProduct"]
    D --> E["SUM old and<br/>new quantities"]
    E --> F["UPDATE Product"]
```

This trigger is also set-based and can handle several updated invoice items in one statement.

### Testing the UPDATE trigger

Check the current invoice item:

```sql
SELECT *
FROM dbo.InvoiceItem
WHERE IDInvoice = 1001;
GO
```

Change the quantity:

```sql
UPDATE dbo.InvoiceItem
SET Quantity = 5
WHERE IDInvoice = 1001
  AND IDProduct = 10;
GO
```

Now check both the invoice item and the product:

```sql
SELECT *
FROM dbo.InvoiceItem
WHERE IDInvoice = 1001;
GO

SELECT *
FROM dbo.Product
WHERE IDProduct = 10;
GO
```

The invoice quantity should now be `5`, and the inventory should have been reduced by only the additional `2` keyboards.

---

## 11.9. Putting it all together

We now have three triggers maintaining the inventory:

| Operation on `InvoiceItem` | Data available | Inventory action |
|---|---|---|
| `INSERT` | `inserted` | Subtract new quantity |
| `DELETE` | `deleted` | Add old quantity |
| `UPDATE` | `deleted` + `inserted` | Add old quantity, subtract new quantity |

All three triggers follow the same general idea:

```mermaid
flowchart TD
    A["InvoiceItem changes"]

    A --> B["INSERT"]
    A --> C["DELETE"]
    A --> D["UPDATE"]

    B --> E["Aggregate inserted"]
    C --> F["Aggregate deleted"]
    D --> G["Match old and new<br/>then aggregate"]

    E --> H["UPDATE Product"]
    F --> H
    G --> H
```

The application modifies `InvoiceItem`.

The database automatically keeps `Product.StockQuantity` synchronized.

---

## 11.10. Why use a trigger here?

Without triggers, every application that sells a product would have to remember to perform two operations:

```mermaid
flowchart LR
    A["Application"] --> B["INSERT InvoiceItem"]
    A --> C["UPDATE Product"]
```

If another application, script, import process, or developer inserts an invoice item but forgets to update the inventory, the data becomes inconsistent.

With a trigger:

```mermaid
flowchart LR
    A["Application"] --> B["InvoiceItem"]
    B --> C["Trigger"]
    C --> D["Product"]
```

The inventory rule is implemented inside the database.

The same rule is applied regardless of whether the change comes from:

- an application;
- a stored procedure;
- an import process;
- a manually executed SQL statement.

> **Key idea:** A trigger can be useful when a data change must always cause another related data change.

---

## 11.11. A note about real inventory systems

This example is intentionally simplified.

A real inventory system would usually require additional rules and mechanisms, such as:

- preventing stock from becoming negative;
- handling cancelled invoices;
- handling product returns;
- supporting multiple warehouses;
- keeping a history of inventory movements;
- handling concurrent transactions.

For this lab, the important concept is simpler:

```mermaid
flowchart LR
    A["InvoiceItem<br/>changes"] --> B["Trigger"]
    B --> C["Inventory<br/>stays synchronized"]
```

This example also demonstrates why `inserted` and `deleted` must always be treated as **tables**, not as individual rows.

### Check your understanding

1. Why does the `INSERT` trigger subtract from `StockQuantity`, while the `DELETE` trigger adds to it?
2. Why does the `UPDATE` trigger need both `deleted` and `inserted`?
3. Why do the `INSERT` and `DELETE` triggers use `GROUP BY IDProduct` and `SUM(Quantity)`?
4. Why do we join `inserted` and `deleted` using `IDInvoiceItem` in the `UPDATE` trigger?
5. Would these triggers still work if one statement affected several invoice items?

<details>
<summary>Show answers</summary>

1. Selling a product removes it from stock, while removing a sale returns that quantity to stock.
2. `deleted` contains the old quantity and `inserted` contains the new quantity. The trigger must return the old quantity and subtract the new one.
3. One statement may affect several invoice items for the same product, so their quantities must first be combined.
4. `IDInvoiceItem` is the primary key and allows us to match each old row with its corresponding new row.
5. Yes. The triggers are written using set-based logic and aggregate all affected rows by product.

</details>

### Key takeaways

- Triggers can automatically maintain related data.
- `AFTER INSERT` can reduce inventory when products are sold.
- `AFTER DELETE` can restore inventory when an invoice item is removed.
- `AFTER UPDATE` can use both `deleted` and `inserted` to adjust inventory.
- `inserted` and `deleted` may contain multiple rows.
- `GROUP BY` and `SUM()` allow us to calculate the total change for each product.
- `JOIN` can connect the affected rows with the related `Product` rows.
- During an `UPDATE`, the primary key connects the old and new versions of the same row.
- Trigger logic should be written to handle sets of rows, not individual rows.

---

Before continuing with the AdventureWorksENG exercises, switch back to the original database:

```sql
USE AdventureWorksENG;
GO
```


## Preparation

Remove the demonstration triggers before starting the exercises:

```sql
DROP TRIGGER IF EXISTS dbo.trg_City_Insert;
DROP TRIGGER IF EXISTS dbo.trg_City_LogRename;
DROP TRIGGER IF EXISTS dbo.trg_City_Delete;
DROP TRIGGER IF EXISTS dbo.trg_City_StateChange;
DROP TRIGGER IF EXISTS dbo.trg_City_All;
GO
```

---

# Exercises

Try each exercise before opening the solution.

## Exercise 1 – First logging trigger

Create an `AFTER INSERT` trigger named `dbo.trg_City_LogInsert` on `dbo.City`.

Whenever a row is inserted into `City`, write:

```text
A city was inserted.
```

to `ActivityLog`.

Then insert one test city and check the log.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_LogInsert
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO ActivityLog (Message)
    VALUES ('A city was inserted.');
END
GO

INSERT INTO City (Name, StateID)
VALUES ('Pula', 1);

SELECT *
FROM ActivityLog
ORDER BY LoggedAt DESC;
```

</details>

---

## Exercise 2 – Log inserted rows

Modify `trg_City_LogInsert`.

Instead of a fixed message, write one log entry for every inserted city containing:

- `IDCity`;
- `Name`.

Then test it with a two-row `INSERT`.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_LogInsert
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO ActivityLog (Message)
    SELECT
        'City inserted: ID='
        + CAST(IDCity AS nvarchar(10))
        + ', Name='
        + Name
    FROM inserted;
END
GO

INSERT INTO City (Name, StateID)
VALUES
    ('Sisak',    1),
    ('Knin', 1);

SELECT *
FROM ActivityLog
ORDER BY LoggedAt DESC;
```

</details>

---

## Exercise 3 – Log renamed cities

Create an `AFTER UPDATE` trigger that logs every actual change to `City.Name`.

The message should contain the old and new names.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER TRIGGER dbo.trg_City_LogRename
ON dbo.City
AFTER UPDATE
AS
BEGIN
    INSERT INTO ActivityLog (Message)
    SELECT
        'City renamed from "'
        + d.Name
        + '" to "'
        + i.Name
        + '"'
    FROM inserted AS i
    JOIN deleted AS d
        ON d.IDCity = i.IDCity
    WHERE d.Name <> i.Name;
END
GO
```

</details>

---

## Exercise 4 – Multi-row safety

Look at this trigger:

```sql
CREATE OR ALTER TRIGGER dbo.trg_BadExample
ON dbo.City
AFTER INSERT
AS
BEGIN
    DECLARE @CityID int;

    SELECT @CityID = IDCity
    FROM inserted;

    INSERT INTO ActivityLog (Message)
    VALUES (
        'Inserted city ID='
        + CAST(@CityID AS nvarchar(10))
    );
END
GO
```

Now imagine:

```sql
INSERT INTO City (Name, StateID)
VALUES
    ('City A', 1),
    ('City B', 1),
    ('City C', 1);
```

Questions:

1. How many times does the trigger fire?
2. How many rows are in `inserted`?
3. How many log rows does the trigger create?
4. What is wrong with this design?
5. Rewrite it correctly.

<details>
<summary>Show solution</summary>

The trigger fires **once**.

`inserted` contains **three rows**.

The trigger creates only **one** log row because the scalar variable can hold only one `IDCity`.

A correct set-based version is:

```sql
CREATE OR ALTER TRIGGER dbo.trg_BadExample
ON dbo.City
AFTER INSERT
AS
BEGIN
    INSERT INTO ActivityLog (Message)
    SELECT
        'Inserted city ID='
        + CAST(IDCity AS nvarchar(10))
    FROM inserted;
END
GO
```

</details>

---

# Cleanup

```sql
DROP TRIGGER IF EXISTS dbo.trg_City_Insert;
DROP TRIGGER IF EXISTS dbo.trg_City_LogInsert;
DROP TRIGGER IF EXISTS dbo.trg_City_LogRename;
DROP TRIGGER IF EXISTS dbo.trg_City_StateChange;
DROP TRIGGER IF EXISTS dbo.trg_BadExample;
DROP TRIGGER IF EXISTS dbo.trg_City_Delete;
DROP TRIGGER IF EXISTS dbo.trg_City_All;
GO
```

If `ActivityLog` was created only for this lab:

```sql
DROP TABLE IF EXISTS ActivityLog;
DROP TABLE IF EXISTS SalaryRange;
DROP TABLE IF EXISTS Employee;

GO
```

---

# What you should know after this lab

The most important patterns are:

```sql
CREATE OR ALTER TRIGGER dbo.trg_Name
ON dbo.TableName
AFTER INSERT
AS
BEGIN
    ...
END
GO
```

```sql
SELECT *
FROM inserted;
```

```sql
SELECT *
FROM deleted;
```

```sql
SELECT ...
FROM inserted AS i
JOIN deleted AS d
    ON d.PrimaryKey = i.PrimaryKey;
```

And the most important rule:

> [!IMPORTANT]
> **A trigger fires once per statement, not once per row.**
>
> Therefore: always write trigger logic to handle sets of rows.

---

## Additional practice

More trigger exercises, including auditing, multi-row logic, and a debugging exercise, are available in [Trigger Exercises](../exercises/triggers.md).

---

# Where to go next

Triggers execute automatically.

In the next lab, **Stored Procedures**, the model changes:

- a stored procedure is called explicitly;
- it can accept parameters;
- it can contain procedural logic;
- it can return data to the caller.

Triggers react to events.

Stored procedures are invoked on demand.
