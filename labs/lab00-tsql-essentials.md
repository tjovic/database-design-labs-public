# Lab 0 – T-SQL Essentials

Database: AdventureWorksENG

Building blocks used across the whole course:

1. Batches and GO
2. Variables
3. IF / ELSE
4. SCOPE_IDENTITY()
5. Inline type conversion — CAST(int AS nvarchar(N))

These are prerequisites for Triggers (Lab 3), Stored Procedures (Lab 4), and Functions (Lab 5). Lab 8 (T-SQL Programming) picks up the full conversion story (CONVERT, FORMAT) plus CASE, WHILE, and TRY/CATCH.

```sql
USE AdventureWorksENG;
GO
```

## Section 1 – Batches and GO

A script is one file. A script contains one or more BATCHES. Each batch is compiled together and gets one execution plan. GO separates batches.

IMPORTANT RULES:

- Variables die at GO. State does not cross batches.
- CREATE VIEW / TRIGGER / PROCEDURE / FUNCTION must be alone in a batch.
- A batch failing does NOT stop the next batch.

THREE batches:

```sql
SELECT TOP 3 * FROM Customer;
GO

DECLARE @Name nvarchar(50);
SELECT @Name = FirstName
FROM Customer
WHERE IDCustomer = 1;
PRINT @Name;
GO

PRINT @Name;   -- ERROR: @Name was declared in the previous batch
```

### Independent batches — if one fails, the next still runs

DO NOT run this against real data — it's a thought experiment. Batch 2 fails at compile time, but batch 3 STILL runs the DELETE.

```sql
SELECT TOP 3 * FROM Customer;
SELECT TOP 3 * FROM Invoice;
GO
-- batch 1: works

SELECT TOP 3 * FROM Customer;
SELECT TOP 3 NonExistentColumn FROM Customer;
GO
-- batch 2: FAILS at compile time (invalid column)

DELETE FROM Invoice;
SELECT TOP 3 * FROM Invoice;
-- batch 3: STILL RUNS — batches are independent!
```

## Section 2 – Variables

Syntax: `DECLARE @name type;`
Prefix: variables always start with @

Assignment — three ways:

### 1. Direct with SET

```sql
DECLARE @FirstName nvarchar(50);
SET @FirstName = 'Ana';
PRINT @FirstName;
GO
```

### 2. From a scalar subquery

The subquery must return exactly ONE value (or you get an error).

```sql
DECLARE @TotalSold int;
SET @TotalSold = (SELECT SUM(Quantity) FROM InvoiceItem);
PRINT @TotalSold;
GO
```

### 3. From a SELECT — assign many variables at once

TRAP:

- If SELECT returns 0 rows → variables stay NULL
- If SELECT returns 1 row → OK
- If SELECT returns N rows → variables get the LAST row's values (order is unpredictable without ORDER BY!)

```sql
DECLARE @Name  nvarchar(50);
DECLARE @Color nvarchar(15);

SELECT
    @Name  = Name,
    @Color = Color
FROM Product
WHERE IDProduct = 1;

PRINT @Name;
PRINT @Color;
GO
```

## Section 3 – IF / ELSE

Syntax:

```
IF condition BEGIN ... END
ELSE IF condition BEGIN ... END
ELSE BEGIN ... END
```

TIP: Always use BEGIN...END even if a branch has only one statement. Adding a second statement later cannot silently break the logic.

```sql
DECLARE @CustomerCount int;
SELECT @CustomerCount = COUNT(*) FROM Customer;

IF @CustomerCount >= 20000
BEGIN
    PRINT 'We have more than 20000 customers.';
END
ELSE
BEGIN
    PRINT 'We are still under 20000 customers.';
END
GO
```

## Section 4 – SCOPE_IDENTITY()

After INSERT into a table with an identity column, SCOPE_IDENTITY() returns the newly generated value.

RULE: Capture SCOPE_IDENTITY() into a variable IMMEDIATELY after the INSERT. Any later INSERT that generates an identity resets what it returns.

Related functions to know but AVOID:

- @@IDENTITY — spans triggers and other scopes; risky
- IDENT_CURRENT(tbl) — spans sessions; risky in concurrent systems

Always prefer SCOPE_IDENTITY().

```sql
DECLARE @StateID int;

INSERT INTO State (Name) VALUES ('India');
SET @StateID = SCOPE_IDENTITY();

PRINT @StateID;

-- Now we can use that new ID to insert related rows atomically
INSERT INTO City (Name, StateID)
VALUES
    ('Agra',  @StateID),
    ('Delhi', @StateID);

SELECT * FROM City WHERE StateID = @StateID;

-- Cleanup
DELETE FROM City  WHERE StateID = @StateID;
DELETE FROM State WHERE IDState = @StateID;
GO
```

## Section 5 – Inline Type Conversion

T-SQL will NOT silently mix strings and numbers with the + operator. To concatenate an int (or any non-string value) with a string, you must convert it first.

Idiom used all over Labs 3, 4, 5:

```sql
PRINT 'Some message: ID = ' + CAST(@SomeInt AS nvarchar(10));
```

Lab 8 (T-SQL Programming) picks up the full story:

- CAST — the standard SQL conversion
- CONVERT — like CAST, plus a style code for dates
- FORMAT — .NET-style pattern strings (dd.MM.yyyy etc.)
- CASE, WHILE, TRY/CATCH

### The problem: mixed-type concatenation is an error

The following is illustrative and not meant to be run — uncomment it to see the error, then move on.

```sql
DECLARE @Count int = 42;
PRINT 'Row count: ' + @Count;
-- ERROR: Conversion failed when converting the varchar value ...
```

### The fix: CAST(value AS type)

```sql
DECLARE @Count int = 42;
PRINT 'Row count: ' + CAST(@Count AS nvarchar(10));     -- Row count: 42
GO
```

### Cousins to know but leave for Lab 8

```sql
CONVERT(nvarchar(10), GETDATE(), 121)
  -- date-time in yyyy-mm-dd hh:mi:ss.mmm

FORMAT(GETDATE(), 'dd.MM.yyyy')
  -- Croatian-style date via .NET-style patterns
  -- slower than CONVERT at scale
```

For everything Labs 3-5 need, CAST(int AS nvarchar(10)) covers it.

## Exercises

Try each exercise on your own first. Only look at the solution after you have attempted it.

### Exercise 1 – Variables from a table

Task: Declare @FirstName and @LastName. Assign them from the Customer table for IDCustomer = 1. Print both.

**Solution**

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

### Exercise 2 – The multi-row trap

Task: Modify Exercise 1 to load values from ALL customers (remove the WHERE). What values end up in @FirstName and @LastName? Explain why.

**Solution**

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

Explanation: The variables hold values from the LAST row returned by the query. Which row is "last" is not guaranteed without ORDER BY — it depends on the query plan the optimizer chose. Only use SELECT-into-variable when you are certain of at most one row.

### Exercise 3 – IF / ELSE

Task: Print 'Big database' if Customer has more than 20000 rows. Otherwise print 'Still growing'.

**Solution**

```sql
DECLARE @Count int;
SELECT @Count = COUNT(*) FROM Customer;

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

### Exercise 4 – SCOPE_IDENTITY()

Task: Insert a new state named 'India' into State. Capture the generated ID into a variable. Then insert two cities ('Agra' and 'Delhi') that both reference that state. Verify by selecting both cities. Clean up.

**Solution**

```sql
DECLARE @StateID int;

INSERT INTO State (Name) VALUES ('India');
SET @StateID = SCOPE_IDENTITY();

INSERT INTO City (Name, StateID)
VALUES
    ('Agra',  @StateID),
    ('Delhi', @StateID);

SELECT * FROM City WHERE StateID = @StateID;

-- Cleanup
DELETE FROM City  WHERE StateID = @StateID;
DELETE FROM State WHERE IDState = @StateID;
GO
```

## Cleanup

Removes any 'India' state and 'Agra'/'Delhi' cities that may have survived a partial run of the demo or Exercise 4 batches above.

```sql
DELETE FROM City  WHERE Name IN ('Agra', 'Delhi');
DELETE FROM State WHERE Name = 'India';
GO
```

## Where to Go Next

These five building blocks are used across the course:

- Lab 3 (Triggers) — Batches, Variables, IF/ELSE, and CAST(int AS nvarchar) for PRINT messages
- Lab 4 (Stored Procedures) — assumes all five
- Lab 5 (Functions) — assumes all five
- Lab 8 (T-SQL Programming) — picks up CONVERT, FORMAT, CASE, WHILE, TRY/CATCH — the full programming toolkit

If you struggle later, come back to this script.
