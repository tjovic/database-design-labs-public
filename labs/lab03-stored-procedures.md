# Lab 3 – Stored Procedures

**Database:** `AdventureWorksENG`

A stored procedure is a named program stored in the database. Unlike a view, which represents a query, a stored procedure can accept parameters, execute multiple SQL statements, modify data, and return information to the caller.

Stored procedures are especially useful when several SQL statements together represent a single database operation.

> [!IMPORTANT]
> **Core idea:** A stored procedure packages a database operation behind a name and parameters.

---

## Learning objectives

After completing this lab, you should be able to:

- explain when stored procedures are useful;
- create, execute, modify, and remove stored procedures;
- define and use input parameters;
- return values using result sets, output parameters, and `RETURN`;
- use several SQL statements to implement one logical database operation.

Start by selecting the training database:

```sql
USE AdventureWorksENG;
GO
```

> [!NOTE]
> **Prerequisites:** This lab assumes that you are already familiar with batches and `GO`, variables, `IF / ELSE`, `SCOPE_IDENTITY()`, and basic `CAST` expressions from Lab 00.

---

# Section 1 – What is a Stored Procedure?

A **stored procedure** is a named block of T-SQL code stored inside the database and executed explicitly by a user or an application.

A useful way to compare the database objects introduced so far is:

| Object | Main idea | How it is used |
|---|---|---|
| View | reusable query | queried with `SELECT` |
| Trigger | automatic reaction | executed automatically after an event |
| Stored procedure | callable database operation | executed with `EXEC` |

A procedure can contain multiple statements and can use variables, conditions, `SELECT`, `INSERT`, `UPDATE`, `DELETE`, and other T-SQL constructs.

```text
Views answer.
Triggers react.
Procedures do.
```

## Why use stored procedures?

Imagine that an application needs to transfer money from one account to another.

The operation may require several steps:

```text
Transfer money
    |
    +-- check the source account
    +-- check the destination account
    +-- validate the amount
    +-- subtract money from the source account
    +-- add money to the destination account
```

Without a stored procedure, some or all of these SQL statements may be issued separately by the application.

With a stored procedure, the application can request the complete operation with one call:

```sql
EXEC dbo.usp_TransferMoney
    @FromAccount = 100,
    @ToAccount   = 101,
    @Amount      = 3000;
```

The implementation remains inside the database.

This gives us several practical benefits.

### Encapsulation

The caller asks the database to perform an operation without having to know every SQL statement used to implement it.

```mermaid
flowchart TD
    A[Application] -->|EXEC dbo.usp_TransferMoney| P[Stored procedure]
    P --> V[Validation]
    P --> S[SELECT]
    P --> U1[UPDATE source account]
    P --> U2[UPDATE destination account]
    V --> T[(Tables)]
    S --> T
    U1 --> T
    U2 --> T
```

### Reusability

The same operation can be called repeatedly with different parameter values and from different applications.

### Fewer network round-trips

If an application sends several SQL statements one after another, each request and response may require communication between the application and SQL Server.

```mermaid
sequenceDiagram
    participant A as Application
    participant DB as SQL Server

    A->>DB: SELECT source account
    DB-->>A: result
    A->>DB: SELECT destination account
    DB-->>A: result
    A->>DB: UPDATE source account
    DB-->>A: result
    A->>DB: UPDATE destination account
    DB-->>A: result
```

A procedure can execute those statements on the database server after a single call:

```mermaid
sequenceDiagram
    participant A as Application
    participant DB as SQL Server

    A->>DB: EXEC dbo.usp_TransferMoney
    activate DB
    Note right of DB: validation
    Note right of DB: SELECT / UPDATE / UPDATE
    DB-->>A: result
    deactivate DB
```

This can reduce network round-trips.

> [!IMPORTANT]
> A stored procedure is not automatically faster than equivalent SQL. The performance benefit here comes from reducing communication between the application and the database when one operation requires several statements.

### A database interface

Applications can call a well-defined database operation instead of directly implementing all of its SQL logic.

```mermaid
flowchart LR
    A[Application]

    subgraph DB["Database"]
        P[Stored Procedure]
        T[(Tables)]

        P --> T
    end

    A -->|"EXEC procedure"| P
```

This can also be useful for controlling how applications interact with data.

> **Key idea:** Think of a stored procedure as a **callable database operation**.

---

## Check your understanding

1. What is the main difference between a trigger and a stored procedure?
2. Why can a stored procedure reduce network round-trips?
3. Does putting a query inside a stored procedure automatically make the query faster?

<details>
<summary>Show answers</summary>

1. A trigger runs automatically in response to an event, while a stored procedure is explicitly called.
2. One procedure call can execute several SQL statements on the database server instead of requiring a separate application request for every statement.
3. No. A stored procedure does not automatically make equivalent SQL faster.

</details>

---

# Section 2 – Creating and Executing Procedures

The simplest stored procedure does not have any parameters.

## Example

```sql
CREATE OR ALTER PROCEDURE dbo.usp_ListStates
AS
BEGIN
    SELECT *
    FROM State;
END
GO
```

Execute the procedure with `EXEC`:

```sql
EXEC dbo.usp_ListStates;
```

`EXECUTE` is the full form of the same command:

```sql
EXECUTE dbo.usp_ListStates;
```

The result appears as a normal result set.

Notice that the procedure is **not** queried like a view:

```sql
-- This is not valid:
SELECT *
FROM dbo.usp_ListStates;
```

A view is queried. A procedure is executed.

## Modifying a procedure

`CREATE OR ALTER` is convenient because the same statement works whether the procedure already exists or not.

```sql
CREATE OR ALTER PROCEDURE dbo.usp_ListStates
AS
BEGIN
    SELECT *
    FROM State
    ORDER BY Name;
END
GO
```

Run it again:

```sql
EXEC dbo.usp_ListStates;
```

## Removing a procedure

```sql
DROP PROCEDURE IF EXISTS dbo.usp_ListStates;
GO
```

Dropping the procedure removes the procedure itself. It does not remove the underlying tables or data.

> [!TIP]
> Use `EXEC` to call a procedure. In this lab, use `CREATE OR ALTER` so that your procedure can easily be executed again while you are developing it.

---

## Check your understanding

1. Which statement executes a stored procedure?
2. Why is `CREATE OR ALTER` useful while developing a procedure?
3. Does dropping a procedure delete data from the tables it uses?

<details>
<summary>Show answers</summary>

1. `EXEC` or `EXECUTE`.
2. The same script can create a new procedure or modify an existing one.
3. No. It removes only the stored procedure.

</details>

---

# Section 3 – Input Parameters

A procedure becomes much more reusable when the caller can provide input values.

Parameters are declared after the procedure name and before `AS`.

## One input parameter

```sql
CREATE OR ALTER PROCEDURE dbo.usp_GetProduct
    @IDProduct int
AS
BEGIN
    SELECT *
    FROM Product
    WHERE IDProduct = @IDProduct;
END
GO
```

The parameter behaves like a variable inside the procedure.

Call the procedure:

```sql
EXEC dbo.usp_GetProduct @IDProduct = 1;
```

The value `1` is the **argument** supplied to the `@IDProduct` parameter.

You can also pass it positionally:

```sql
EXEC dbo.usp_GetProduct 1;
```

For procedures with several parameters, named arguments are usually easier to read and less error-prone.

## Multiple input parameters

```sql
CREATE OR ALTER PROCEDURE dbo.usp_ProductsByPrice
    @MinPrice money,
    @MaxPrice money
AS
BEGIN
    SELECT Name, PriceWithoutVAT
    FROM Product
    WHERE PriceWithoutVAT BETWEEN @MinPrice AND @MaxPrice
    ORDER BY PriceWithoutVAT;
END
GO
```

Call it using named arguments:

```sql
EXEC dbo.usp_ProductsByPrice
    @MinPrice = 100,
    @MaxPrice = 500;
```

When arguments are named, their order does not have to match the declaration:

```sql
EXEC dbo.usp_ProductsByPrice
    @MaxPrice = 500,
    @MinPrice = 100;
```

### Common mistake

> [!WARNING]
> Do not call a stored procedure like a function:

```sql
-- Incorrect:
EXEC dbo.usp_GetProduct(1);
```

Use:

```sql
EXEC dbo.usp_GetProduct @IDProduct = 1;
```

> **Key idea:** Input parameters make one procedure reusable for many different inputs.

---

## Check your understanding

1. Where are procedure parameters declared?
2. What is the difference between a parameter and an argument?
3. Why are named arguments useful when a procedure has several parameters?

<details>
<summary>Show answers</summary>

1. After the procedure name and before `AS`.
2. A parameter is declared by the procedure; an argument is the value supplied by the caller.
3. They make calls easier to read and make it clear which value belongs to which parameter.

</details>

---

# Section 4 – Returning Data

A stored procedure can send information back to its caller in several ways.

The three mechanisms used in this lab are:

| Need | Mechanism |
|---|---|
| Return rows | result set |
| Return one or more individual values | `OUTPUT` parameters |
| Return an integer status code | `RETURN` |

Understanding the difference between these mechanisms is important.

## Result sets

You have already used the simplest form:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_GetProduct
    @IDProduct int
AS
BEGIN
    SELECT *
    FROM Product
    WHERE IDProduct = @IDProduct;
END
GO
```

The `SELECT` produces a result set for the caller.

```sql
EXEC dbo.usp_GetProduct @IDProduct = 1;
```

Use a result set when the caller needs rows.

---

## Output parameters

An output parameter sends an individual value back to the caller.

```sql
CREATE OR ALTER PROCEDURE dbo.usp_GetProductColor
    @IDProduct int,
    @Color     nvarchar(15) OUTPUT
AS
BEGIN
    SELECT @Color = Color
    FROM Product
    WHERE IDProduct = @IDProduct;
END
GO
```

The caller must first declare a variable:

```sql
DECLARE @MyColor nvarchar(15);

EXEC dbo.usp_GetProductColor
    @IDProduct = 742,
    @Color     = @MyColor OUTPUT;

SELECT @MyColor AS ProductColor;
```

Notice that `OUTPUT` appears in **two places**:

```text
Procedure declaration  -> @Color nvarchar(15) OUTPUT
Procedure call         -> @Color = @MyColor OUTPUT
```

The caller needs a variable because the procedure needs somewhere to store the returned value.

### Common mistake

> [!WARNING]
> Forgetting `OUTPUT` in the call lets the procedure execute normally, but the returned value is silently lost.

```sql
DECLARE @MyColor nvarchar(15);

-- The procedure executes, but the value is not returned
-- to @MyColor because OUTPUT is missing in the call.
EXEC dbo.usp_GetProductColor
    @IDProduct = 1,
    @Color     = @MyColor;
```

---

## RETURN values

`RETURN` provides a different output channel.

A procedure can return one integer value, commonly used as a status code.

```sql
CREATE OR ALTER PROCEDURE dbo.usp_CheckCustomerExists
    @FirstName nvarchar(50),
    @LastName  nvarchar(50)
AS
BEGIN
    IF EXISTS
    (
        SELECT 1
        FROM Customer
        WHERE FirstName = @FirstName
          AND LastName = @LastName
    )
        RETURN 0;

    RETURN 1;
END
GO
```

Capture the return value:

```sql
DECLARE @Result int;

EXEC @Result = dbo.usp_CheckCustomerExists
    @FirstName = 'Ada',
    @LastName  = 'Lovelace';

SELECT @Result AS ReturnCode;
```

A common convention is:

```text
0       -> success
nonzero -> another status
```

> [!NOTE]
> **`RETURN` also immediately ends execution of the procedure.**

Do not use `RETURN` to return normal application data such as names, dates, or prices. Use a result set or an output parameter for those values.

> [!IMPORTANT]
> `OUTPUT` returns data. `RETURN` is normally used for an integer status code.

---

## Check your understanding

1. Which mechanism should you use to return a table of matching products?
2. Which mechanism can return a product color to a variable in the caller?
3. What data type can a procedure return using `RETURN`?
4. Where must the `OUTPUT` keyword appear?

<details>
<summary>Show answers</summary>

1. A result set.
2. An output parameter.
3. An integer.
4. In the procedure parameter declaration and in the `EXEC` call that receives the value.

</details>

---

# Section 5 – Putting It Together: Bank Transfer

The real value of stored procedures becomes clearer when one request requires several SQL statements.

Return to the example from the beginning of the lab:

> Transfer money from one bank account to another.

From the application's point of view, this should be **one operation**:

```sql
EXEC dbo.usp_TransferMoney
    @FromAccount = 100,
    @ToAccount   = 101,
    @Amount      = 3000;
```

The database, however, must perform several steps.

```mermaid
flowchart TD
    A[Receive transfer request] --> B{Source account exists?}
    B -- No --> R1[RETURN 1]
    B -- Yes --> C{Destination account exists?}
    C -- No --> R2[RETURN 2]
    C -- Yes --> D{Amount greater than 0?}
    D -- No --> R3[RETURN 3]
    D -- Yes --> E{Enough funds?}
    E -- No --> R4[RETURN 4]
    E -- Yes --> F[Subtract amount from source]
    F --> G[Add amount to destination]
    G --> R0[RETURN 0]
```

## Example data

For this example, create a small table that is independent of the rest of `AdventureWorksENG`:

```sql
CREATE TABLE BankAccount
(
    AccountNumber int PRIMARY KEY,
    Balance       decimal(10,2) NOT NULL
);
GO

INSERT INTO BankAccount (AccountNumber, Balance)
VALUES
    (100, 5000.00),
    (101, 2000.00);
GO
```

Check the initial balances:

```sql
SELECT *
FROM BankAccount;
```

Expected state:

| AccountNumber | Balance |
|---:|---:|
| 100 | 5000.00 |
| 101 | 2000.00 |

---

## The procedure

```sql
CREATE OR ALTER PROCEDURE dbo.usp_TransferMoney
    @FromAccount int,
    @ToAccount   int,
    @Amount      decimal(10,2)
AS
BEGIN
    -- Source account must exist
    IF NOT EXISTS
    (
        SELECT 1
        FROM BankAccount
        WHERE AccountNumber = @FromAccount
    )
        RETURN 1;

    -- Destination account must exist
    IF NOT EXISTS
    (
        SELECT 1
        FROM BankAccount
        WHERE AccountNumber = @ToAccount
    )
        RETURN 2;

    -- Transfer amount must be positive
    IF @Amount <= 0
        RETURN 3;

    -- Source account must have enough funds
    IF
    (
        SELECT Balance
        FROM BankAccount
        WHERE AccountNumber = @FromAccount
    ) < @Amount
        RETURN 4;

    UPDATE BankAccount
    SET Balance = Balance - @Amount
    WHERE AccountNumber = @FromAccount;

    UPDATE BankAccount
    SET Balance = Balance + @Amount
    WHERE AccountNumber = @ToAccount;

    RETURN 0;
END
GO
```

The return codes describe the outcome:

| Return code | Meaning |
|---:|---|
| `0` | transfer completed |
| `1` | source account does not exist |
| `2` | destination account does not exist |
| `3` | invalid amount |
| `4` | insufficient funds |

Notice the role of `RETURN`: it does not return account data. It reports the **status of the operation**.

---

## Execute the transfer

Capture the return value in a variable:

```sql
DECLARE @Result int;

EXEC @Result = dbo.usp_TransferMoney
    @FromAccount = 100,
    @ToAccount   = 101,
    @Amount      = 3000;

SELECT @Result AS ReturnCode;
```

If the transfer succeeds, the return code is `0`.

Check the balances:

```sql
SELECT *
FROM BankAccount;
```

Expected result:

| AccountNumber | Balance |
|---:|---:|
| 100 | 2000.00 |
| 101 | 5000.00 |

The application requested one operation, while the procedure performed validation and multiple SQL statements inside the database.

```mermaid
sequenceDiagram
    participant A as Application

    box rgb(225, 240, 255) SQL Server
        participant P as usp_TransferMoney
        participant T as BankAccount
    end

    A->>P: Transfer 3000 from 100 to 101
    P->>T: Check accounts and balance
    T-->>P: Data
    P->>T: UPDATE account 100
    P->>T: UPDATE account 101
    P-->>A: RETURN 0
```

This example demonstrates several reasons for using a stored procedure:

- **encapsulation** — the application requests a transfer without implementing every SQL statement;
- **reusability** — the same procedure works for different accounts and amounts;
- **validation** — invalid requests can be rejected before data is modified;
- **fewer network round-trips** — the application sends one procedure call instead of coordinating each SQL statement separately;
- **one logical database operation** — the related statements are grouped behind one meaningful name.

---

## Test an unsuccessful transfer

Account `100` now contains `2000.00`.

Try to transfer more than the available balance:

```sql
DECLARE @Result int;

EXEC @Result = dbo.usp_TransferMoney
    @FromAccount = 100,
    @ToAccount   = 101,
    @Amount      = 5000;

SELECT @Result AS ReturnCode;
```

The expected return code is:

```text
4 -> insufficient funds
```

Because the procedure returns before either `UPDATE`, the balances remain unchanged.

---

## One important problem remains

Consider what could happen during a valid transfer:

```mermaid
flowchart LR
    A[Subtract 3000 from account 100] -->|succeeds| B[First UPDATE completed]
    B --> C{Server continues running?}
    C -- Yes --> D[Add 3000 to account 101]
    D --> E[Transfer complete]
    C -- No --> F[Money removed from 100<br/>but not added to 101]
```

The two updates logically belong together.

What happens if the first `UPDATE` succeeds, but the server crashes or loses power before the second `UPDATE` is executed?

```text
Account 100: -3000  ✓

        ⚡ power failure

Account 101: +3000  ✗
```

Money has been removed from one account but has not been added to the other.

What we really want is:

```text
BOTH updates succeed
        OR
NEITHER update happens
```

This is exactly the problem that **transactions** solve.

Transactions are outside the scope of this lab, but this example shows why they are important when several data modifications form one logical operation.

> [!NOTE]
> A stored procedure can group several statements into one callable operation. A transaction guarantees that related changes succeed or fail together.

---

## Check your understanding

1. What does the stored procedure in this example encapsulate that the application would otherwise have to implement itself?
2. Why does `usp_TransferMoney` check both accounts and the balance before performing either `UPDATE`?
3. What does a `RETURN` code of `4` mean in this procedure, and does it change any data?
4. Why doesn't the stored procedure alone guarantee that both updates succeed or fail together?

<details>
<summary>Show answers</summary>

1. The sequence of validations and the two related `UPDATE` statements that together make up one transfer operation.
2. So that an invalid request (missing account, invalid amount, insufficient funds) is rejected with a `RETURN` code before any data is modified.
3. Insufficient funds. No data is changed — the procedure returns before either `UPDATE` runs.
4. A stored procedure only groups statements behind one call; it does not by itself protect against a failure between the two `UPDATE` statements. That guarantee requires a transaction.

</details>

---

# Section 6 – Real-world example: Calculating a loyalty discount

Stored procedures are often used to implement **business rules**.

Consider a simple loyalty program.

When a customer is making a purchase, the application needs to determine whether the customer is eligible for a discount.

The discount depends on how much the customer spent during a specified period:

| Total spent | Discount |
|---:|---:|
| Less than €500 | 0% |
| €500 – €999.99 | 5% |
| €1,000 – €1,999.99 | 10% |
| €2,000 or more | 15% |

The application provides:

- the customer,
- the beginning of the period,
- the end of the period.

The stored procedure calculates the customer's total spending and returns the appropriate discount percentage.

```mermaid
flowchart LR
    A["Application"] -->|"Customer ID<br/>Date from<br/>Date to"| B["Stored procedure"]
    B --> C["Calculate total spending"]
    C --> D["Determine discount"]
    D -->|"OUTPUT parameter"| A
```

This example demonstrates three different ways of working with values inside a stored procedure:

| Value | Type | Purpose |
|---|---|---|
| `@CustomerID` | Input parameter | Customer to check |
| `@DateFrom` | Input parameter | Beginning of the period |
| `@DateTo` | Input parameter | End of the period |
| `@TotalSpent` | Local variable | Stores the calculated spending |
| `@DiscountPercent` | Output parameter | Returns the discount to the caller |

---

### Calculating the customer's spending

First, let's calculate how much customer `100` spent during 2003:

```sql
USE AdventureWorksENG;
GO
```

```sql
SELECT SUM(ii.TotalPrice)
FROM Invoice i
JOIN InvoiceItem ii
    ON ii.InvoiceID = i.IDInvoice
WHERE i.CustomerID = 100
  AND i.InvoiceDate >= '2003-01-01'
  AND i.InvoiceDate <= '2003-12-31';
```

The result is:

```text
1728.510000
```

According to our loyalty rules, this customer should receive a **10% discount**.

However, there is one small problem.

If the customer has no purchases during the selected period, `SUM()` returns `NULL`.

We want the total spending to be `0` instead:

```sql
SELECT COALESCE(SUM(ii.TotalPrice), 0)
FROM Invoice i
JOIN InvoiceItem ii
    ON ii.InvoiceID = i.IDInvoice
WHERE i.CustomerID = 100
  AND i.InvoiceDate >= '2003-01-01'
  AND i.InvoiceDate <= '2003-12-31';
```

Now we can use this calculation inside a stored procedure.

---

### Creating the procedure

```sql
CREATE OR ALTER PROCEDURE dbo.usp_GetLoyaltyDiscount
    @CustomerID int,
    @DateFrom date,
    @DateTo date,
    @DiscountPercent decimal(5,2) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @TotalSpent decimal(10,2);

    SELECT @TotalSpent =
        COALESCE(SUM(ii.TotalPrice), 0)
    FROM Invoice i
    JOIN InvoiceItem ii
        ON ii.InvoiceID = i.IDInvoice
    WHERE i.CustomerID = @CustomerID
      AND i.InvoiceDate >= @DateFrom
      AND i.InvoiceDate <= @DateTo;

    IF @TotalSpent >= 2000
        SET @DiscountPercent = 15;
    ELSE IF @TotalSpent >= 1000
        SET @DiscountPercent = 10;
    ELSE IF @TotalSpent >= 500
        SET @DiscountPercent = 5;
    ELSE
        SET @DiscountPercent = 0;
END;
GO
```

The procedure receives three **input parameters**:

```sql
@CustomerID int,
@DateFrom date,
@DateTo date,
```

These values come from the caller.

The procedure also declares a **local variable**:

```sql
DECLARE @TotalSpent decimal(10,2);
```

This variable exists only while the procedure is executing.

The query calculates the customer's spending and stores the result in that variable:

```sql
SELECT @TotalSpent =
    COALESCE(SUM(ii.TotalPrice), 0)
FROM Invoice i
JOIN InvoiceItem ii
    ON ii.InvoiceID = i.IDInvoice
WHERE i.CustomerID = @CustomerID
  AND i.InvoiceDate >= @DateFrom
  AND i.InvoiceDate <= @DateTo;
```

The procedure then applies the loyalty rules:

```sql
IF @TotalSpent >= 2000
    SET @DiscountPercent = 15;
ELSE IF @TotalSpent >= 1000
    SET @DiscountPercent = 10;
ELSE IF @TotalSpent >= 500
    SET @DiscountPercent = 5;
ELSE
    SET @DiscountPercent = 0;
```

```mermaid
flowchart TD
    A["Calculate @TotalSpent"] --> B{"@TotalSpent >= 2000?"}
    B -->|"Yes"| C["15%"]
    B -->|"No"| D{"@TotalSpent >= 1000?"}
    D -->|"Yes"| E["10%"]
    D -->|"No"| F{"@TotalSpent >= 500?"}
    F -->|"Yes"| G["5%"]
    F -->|"No"| H["0%"]
```

Finally, `@DiscountPercent` is an **OUTPUT parameter**:

```sql
@DiscountPercent decimal(5,2) OUTPUT
```

This allows the procedure to return the calculated discount to the caller.

---

### Calling the procedure

The caller first needs a variable that will receive the returned value:

```sql
DECLARE @Discount decimal(5,2);
```

We can then execute the procedure:

```sql
EXEC dbo.usp_GetLoyaltyDiscount
    @CustomerID = 100,
    @DateFrom = '2003-01-01',
    @DateTo = '2003-12-31',
    @DiscountPercent = @Discount OUTPUT;
```

Finally, we can inspect the returned value:

```sql
SELECT @Discount AS DiscountPercent;
```

The complete call is:

```sql
DECLARE @Discount decimal(5,2);

EXEC dbo.usp_GetLoyaltyDiscount
    @CustomerID = 100,
    @DateFrom = '2003-01-01',
    @DateTo = '2003-12-31',
    @DiscountPercent = @Discount OUTPUT;

SELECT @Discount AS DiscountPercent;
```

The result should be:

| DiscountPercent |
|---:|
| 10.00 |

The procedure calculated that customer `100` spent **€1,728.51** during the selected period and therefore returned a **10% discount**.

```mermaid
flowchart LR
    A["@CustomerID = 100<br/>@DateFrom = 2003-01-01<br/>@DateTo = 2003-12-31"] -->|"INPUT"| B["usp_GetLoyaltyDiscount"]
    B --> C["@TotalSpent<br/>1728.51"]
    C --> D["IF / ELSE"]
    D --> E["@DiscountPercent<br/>10%"]
    E -->|"OUTPUT"| F["Caller"]
```

---

### Input, local, and output values

It is important to understand the different roles of the values used in this example.

**Input parameters** bring values into the procedure:

```sql
@CustomerID
@DateFrom
@DateTo
```

A **local variable** stores an intermediate result inside the procedure:

```sql
@TotalSpent
```

An **OUTPUT parameter** sends a value back to the caller:

```sql
@DiscountPercent
```

Conceptually:

```mermaid
flowchart LR
    A["Input parameters"] --> B["Stored procedure"]
    B --> C["Local variable<br/>@TotalSpent"]
    C --> D["Business logic"]
    D --> E["OUTPUT parameter"]
```

### Check your understanding

1. Why does the procedure use `COALESCE(SUM(ii.TotalPrice), 0)` instead of just `SUM(ii.TotalPrice)`?
2. Why is `@TotalSpent` declared as a local variable instead of a parameter?
3. Why is `@DiscountPercent` declared as an `OUTPUT` parameter instead of being returned through a result set?
4. What would happen to the caller's variable if `OUTPUT` were omitted from the `EXEC` call?

<details>
<summary>Show answers</summary>

1. If the customer has no purchases in the period, `SUM()` returns `NULL`. `COALESCE` makes the total spending `0` instead, so the discount logic still works correctly.
2. `@TotalSpent` is not supplied by the caller — it is calculated inside the procedure from the input parameters, so it is a local variable rather than a parameter.
3. The result is a single value (a percentage), not a set of rows, so an `OUTPUT` parameter is the appropriate mechanism — the same distinction covered in Section 4.
4. The procedure would still calculate the discount internally, but the caller's variable would not receive the value — the same mistake shown in Section 4's "Common mistake".

</details>

### Key takeaways

- Stored procedures can implement business rules.
- Input parameters allow the caller to provide values to the procedure.
- Local variables can store intermediate results inside the procedure.
- `IF` and `ELSE` can be used to make decisions based on calculated values.
- An `OUTPUT` parameter allows a stored procedure to return a value to the caller.
- The caller must specify `OUTPUT` when receiving the value.
- A procedure can combine queries, variables, control flow, and parameters into a reusable database operation.

---

# Exercises

Try each exercise before opening the solution.

---

## Exercise 1 – Your First Procedure

Create a procedure named `dbo.usp_ListCategories`.

The procedure should:

- return all rows from `Category`;
- sort the result by category name.

Execute the procedure.

Then modify it so that the categories are sorted in descending order and execute it again.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_ListCategories
AS
BEGIN
    SELECT *
    FROM Category
    ORDER BY Name;
END
GO

EXEC dbo.usp_ListCategories;
GO

CREATE OR ALTER PROCEDURE dbo.usp_ListCategories
AS
BEGIN
    SELECT *
    FROM Category
    ORDER BY Name DESC;
END
GO

EXEC dbo.usp_ListCategories;
```

</details>

---

## Exercise 2 – Input Parameters

Create a procedure named `dbo.usp_CustomersByLastName`.

The procedure should:

- accept one parameter named `@LastNamePattern`;
- return `IDCustomer`, `FirstName`, `LastName`, and `Email`;
- find customers whose last name matches the supplied `LIKE` pattern;
- sort the result by `LastName` and `FirstName`.

Test it with:

```sql
EXEC dbo.usp_CustomersByLastName
    @LastNamePattern = 'S%';
```

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_CustomersByLastName
    @LastNamePattern nvarchar(50)
AS
BEGIN
    SELECT
        IDCustomer,
        FirstName,
        LastName,
        Email
    FROM Customer
    WHERE LastName LIKE @LastNamePattern
    ORDER BY LastName, FirstName;
END
GO

EXEC dbo.usp_CustomersByLastName
    @LastNamePattern = 'S%';
```

</details>

---

## Exercise 3 – A Complete Database Operation

Create a procedure named `dbo.usp_InsertCityInState`.

It should accept:

```text
@StateName
@CityName
```

The procedure must:

1. find the state by name;
2. store its ID in a variable;
3. insert the state if it does not exist;
4. use `SCOPE_IDENTITY()` to obtain the new state ID;
5. insert the city using the correct `StateID`.

Test the procedure with two calls:

```text
State: Canada, City: Toronto
State: Canada, City: Vancouver
```

Finally, verify that `Canada` exists only once in `State` and that both cities reference it.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertCityInState
    @StateName nvarchar(50),
    @CityName  nvarchar(50)
AS
BEGIN
    DECLARE @StateID int;

    SELECT @StateID = IDState
    FROM State
    WHERE Name = @StateName;

    IF @StateID IS NULL
    BEGIN
        INSERT INTO State (Name)
        VALUES (@StateName);

        SET @StateID = SCOPE_IDENTITY();
    END

    INSERT INTO City (Name, StateID)
    VALUES (@CityName, @StateID);
END
GO

EXEC dbo.usp_InsertCityInState
    @StateName = 'Canada',
    @CityName  = 'Toronto';

EXEC dbo.usp_InsertCityInState
    @StateName = 'Canada',
    @CityName  = 'Vancouver';

SELECT
    s.Name AS State,
    c.Name AS City
FROM City AS c
JOIN State AS s
    ON s.IDState = c.StateID
WHERE s.Name = 'Canada';

SELECT COUNT(*) AS CanadaRowCount
FROM State
WHERE Name = 'Canada';
```

</details>

---

## Exercise 4 – Find the Bug

Assume the following procedure already exists:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_GetProductColor
    @IDProduct int,
    @Color     nvarchar(15) OUTPUT
AS
BEGIN
    SELECT @Color = Color
    FROM Product
    WHERE IDProduct = @IDProduct;
END
GO
```

A developer calls it like this:

```sql
DECLARE @Color nvarchar(15);

EXEC dbo.usp_GetProductColor
    @IDProduct = 1,
    @Color     = @Color;

SELECT @Color AS ProductColor;
```

The procedure executes, but `@Color` does not contain the value returned by the procedure.

Questions:

1. What is wrong with the call?
2. Where must `OUTPUT` appear?
3. Correct the call.

<details>
<summary>Show solution</summary>

The caller forgot the `OUTPUT` keyword.

It must appear both in the procedure declaration and in the call when the caller wants to receive the modified value.

```sql
DECLARE @Color nvarchar(15);

EXEC dbo.usp_GetProductColor
    @IDProduct = 1,
    @Color     = @Color OUTPUT;

SELECT @Color AS ProductColor;
```

</details>

---

## Exercise 5 — Find customers and return the number of matches

A stored procedure can return both:

- A **result set**, such as a list of customers.
- Additional values through **`OUTPUT` parameters**, such as the number of customers found.

### Your task

Create a stored procedure named `dbo.usp_FindCustomersByLastName` with the following parameters:

| Parameter | Type | Purpose |
|---|---|---|
| `@LastNamePattern` | `nvarchar(100)` | Pattern used to filter customer last names with `LIKE` |
| `@CustomerCount` | `int OUTPUT` | Number of customers returned |

The procedure must:

1. Use `SET NOCOUNT ON`.
2. Return `IDCustomer`, `FirstName`, and `LastName` from the `Customer` table.
3. Filter customers using `LastName LIKE @LastNamePattern`.
4. Sort the results by `LastName`, `FirstName`, and `IDCustomer`.
5. Return the number of matching customers through `@CustomerCount`.

Use **`@@ROWCOUNT`** to obtain the number of rows returned by the query.

### Examples of search patterns

| Pattern | Meaning |
|---|---|
| `N'A%'` | Last names beginning with A |
| `N'%son'` | Last names ending with son |
| `N'%son%'` | Last names containing son |
| `N'%'` | All non-NULL last names |

> [!TIP]
> The caller supplies the complete search pattern, including any wildcard characters. The procedure does not add `%` automatically.

### Test your procedure

```sql
DECLARE @Count int;

EXEC dbo.usp_FindCustomersByLastName
    @LastNamePattern = N'%son%',
    @CustomerCount = @Count OUTPUT;

SELECT @Count AS MatchingCustomers;
GO
```

Try other patterns and compare the returned customers with the value of `MatchingCustomers`.

### Questions

1. What is the difference between the result set and the `OUTPUT` parameter?
2. Why must `OUTPUT` also appear in the procedure call?
3. What should `@CustomerCount` contain if no customers match?
4. Does `SET NOCOUNT ON` prevent `@@ROWCOUNT` from being updated?

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_FindCustomersByLastName
    @LastNamePattern nvarchar(100),
    @CustomerCount int OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        IDCustomer,
        FirstName,
        LastName
    FROM dbo.Customer
    WHERE LastName LIKE @LastNamePattern
    ORDER BY
        LastName,
        FirstName,
        IDCustomer;

    -- Capture the row count immediately after the query.
    SET @CustomerCount = @@ROWCOUNT;
END;
GO
```
</details>

### Example call

```sql
DECLARE @Count int;

EXEC dbo.usp_FindCustomersByLastName
    @LastNamePattern = N'A%',
    @CustomerCount = @Count OUTPUT;

SELECT @Count AS MatchingCustomers;
GO
```

SSMS displays two result grids:

1. The customers returned by the procedure.
2. The count displayed by the caller's `SELECT`.

If no customers match, the first result set is empty and `@CustomerCount` is `0`.

> [!IMPORTANT]
> `@@ROWCOUNT` describes the most recent statement. Capture its value immediately after the query, because subsequent statements can change or reset it.

> [!NOTE]
> `SET NOCOUNT ON` suppresses row-count messages such as `(5 rows affected)`. It does **not** prevent `@@ROWCOUNT` from being updated, and it does not hide query results.


---

## Exercise 6 — Validate a card number using the Luhn algorithm

In this exercise, you will combine input validation, `OUTPUT` parameters, variables, conditions, and a `WHILE` loop to solve a practical problem.

### Background

The **Luhn algorithm**, also called the **modulus 10 algorithm**, checks whether a numerical identifier has a valid checksum. It helps detect common typing errors.

It is used for credit and debit card numbers and for the check digit of **IMEI numbers**, which identify mobile devices. [stripe.com](https://stripe.com/resources/more/how-to-use-the-luhn-algorithm-a-guide-in-applications-for-businesses)

The final digit is called the **check digit**. It is calculated from the preceding digits.

> [!NOTE]
> Check digits are used in many identification systems.
>
> For example, the Croatian **OIB** includes a check digit calculated using **ISO 7064 MOD 11,10**. A Croatian **student card number (iksica)** also includes a check digit, in addition to the JMBAG contained within it. [regos.hr](https://regos.hr/app/uploads/2018/07/KONTROLA-OIB-a.pdf)
>
> These systems share the same idea: calculating a check value from the other digits helps detect typing errors. However, **different identifiers may use different algorithms**. The Luhn algorithm cannot be used to validate every identification number.

> [!IMPORTANT]
> Passing the Luhn check does **not** prove that a card exists, is active, or has sufficient funds. The algorithm checks only the checksum. It is not an encryption or authentication mechanism.

### How the algorithm works

Process the complete number, including its check digit:

1. Start with the **rightmost digit**.
2. Moving left, **double every second digit**, beginning with the second digit from the right.
3. If a doubled value is greater than `9`, subtract `9`.
4. Add all the resulting values.
5. The checksum is valid if the total is divisible by `10`.

Consider the demonstration sequence `12345674`:

| Step | Digits from left to right |
|---|---|
| Original digits | 1, 2, 3, 4, 5, 6, 7, 4 |
| Double every second digit from the right | 2, 2, 6, 4, 10, 6, 14, 4 |
| Subtract 9 from values greater than 9 | 2, 2, 6, 4, 1, 6, 5, 4 |

The total is:

```text
2 + 2 + 6 + 4 + 1 + 6 + 5 + 4 = 30
30 % 10 = 0
```

Therefore, this sequence passes the Luhn check.

> [!NOTE]
> This short sequence demonstrates the calculation. It is not a payment card number.

### Your task

Create a stored procedure named `dbo.usp_ValidateCardNumber` with these parameters:

| Parameter | Type | Purpose |
|---|---|---|
| `@CardNumber` | `varchar(100)` | Number to check |
| `@IsValid` | `bit OUTPUT` | Result: `1` if the input meets the exercise rules and passes the checksum; otherwise `0` |

Apply the following rules:

1. Use `SET NOCOUNT ON`.
2. Set `@IsValid` to `0` at the beginning.
3. Reject `NULL`.
4. Accept **exactly 16 characters**, all of which must be digits from `0` to `9`. Reject spaces, letters, and punctuation.
5. Use a `WHILE` loop to implement the Luhn algorithm.
6. Set `@IsValid` to `1` only if the input meets these rules and its checksum is valid.

> [!NOTE]
> The 16-digit requirement is a simplification for this exercise. The Luhn algorithm itself is not restricted to 16-digit numbers.

Store the input as text because it is an **identifier**, not a numerical quantity. Convert individual digits to `int` only when performing calculations.

### Hints

You can use the following T-SQL features:

| Feature | Purpose |
|---|---|
| `IF` and `RETURN` | Reject invalid input and exit the procedure |
| `DATALENGTH(@CardNumber)` | Check the input length, including trailing spaces |
| `LIKE '%[^0-9]%'` | Detect a character outside the digit range |
| `SUBSTRING(@CardNumber, @Position, 1)` | Extract one digit |
| `CAST(... AS int)` | Convert the extracted digit to an integer |
| `WHILE` | Process the digits one at a time |
| `%` | Calculate the remainder after division |

For the accepted ASCII digits in this `varchar` parameter, each character occupies one byte.

Check the input **before** converting its characters to integers.

### Test your procedure

Use the following published test card number: [docs.stripe.com](https://docs.stripe.com/testing?numbers-or-method-or-token=tokens)

```sql
DECLARE @Result bit;

EXEC dbo.usp_ValidateCardNumber
    @CardNumber = '4242424242424242',
    @IsValid = @Result OUTPUT;

SELECT @Result AS IsValid;
-- Expected: 1
GO
```

Change the last digit and test again:

```sql
DECLARE @Result bit;

EXEC dbo.usp_ValidateCardNumber
    @CardNumber = '4242424242424241',
    @IsValid = @Result OUTPUT;

SELECT @Result AS IsValid;
-- Expected: 0
GO
```

Also verify these cases:

| Input | Expected result | Reason |
|---|---:|---|
| `NULL` | 0 | Missing input |
| `''` | 0 | Empty input |
| `'4242'` | 0 | Incorrect length |
| `'424242424242424A'` | 0 | Contains a letter |
| `'4242 4242 4242 4242'` | 0 | Contains spaces |
| `'424242424242424 '` | 0 | Contains a trailing space |

> [!WARNING]
> Use only the supplied test values or invented demonstration sequences. Do not use real payment card data.

### Questions

1. Why does this procedure use a `varchar` parameter?
2. Why is the rightmost digit not doubled?
3. What does `@Total % 10 = 0` check?
4. Why must the caller also specify `OUTPUT`?
5. Can a number pass the Luhn check even if no corresponding card exists?

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_ValidateCardNumber
    @CardNumber varchar(100),
    @IsValid bit OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SET @IsValid = 0;

    -------------------------------------------------------
    -- Validate the input
    -------------------------------------------------------
    IF @CardNumber IS NULL
        RETURN;

    IF DATALENGTH(@CardNumber) <> 16
        RETURN;

    -- Reject input containing non-digit characters.
    IF @CardNumber LIKE '%[^0-9]%'
        RETURN;

    -------------------------------------------------------
    -- Calculate the Luhn checksum
    -------------------------------------------------------
    DECLARE @Position int = 16;
    DECLARE @Digit int;
    DECLARE @Total int = 0;
    DECLARE @ShouldDouble bit = 0;

    WHILE @Position >= 1
    BEGIN
        SET @Digit = CAST(
            SUBSTRING(@CardNumber, @Position, 1) AS int
        );

        IF @ShouldDouble = 1
        BEGIN
            SET @Digit = @Digit * 2;

            IF @Digit > 9
                SET @Digit = @Digit - 9;
        END;

        SET @Total = @Total + @Digit;

        -- Alternate between keeping and doubling a digit.
        IF @ShouldDouble = 0
            SET @ShouldDouble = 1;
        ELSE
            SET @ShouldDouble = 0;

        SET @Position = @Position - 1;
    END;

    -------------------------------------------------------
    -- Return the result through the OUTPUT parameter
    -------------------------------------------------------
    IF @Total % 10 = 0
        SET @IsValid = 1;
END;
GO
```

### Understanding the solution

- `@IsValid` starts at `0`, so every early `RETURN` produces an invalid result.
- `DATALENGTH` counts trailing spaces, which `LEN` would ignore.
- `LIKE '%[^0-9]%'` checks for characters outside the digit range.
- `@Position` starts at `16`, so the loop processes the number from right to left.
- `@ShouldDouble` starts at `0`, because the rightmost digit—the check digit—is **not doubled**.
- After each iteration, `@ShouldDouble` switches between `0` and `1`.
- `@Total % 10 = 0` checks whether the final sum is divisible by `10`.

</details>

> [!NOTE]
> A sequence containing sixteen zeros also passes these rules and the Luhn checksum. This illustrates why a checksum alone cannot confirm that a payment card number is actually issued or usable.

> [!TIP]
> [Lab 4, Section 9](lab04-functions.md#section-9--composing-a-function-with-a-procedure-and-a-trigger) moves this same Luhn calculation into a scalar function, then reuses it from this procedure, from a query over every row of `CreditCard`, and from a trigger that rejects an invalid `CardNumber` on `INSERT`/`UPDATE`.


---

## Challenge – Choosing the Right Output

Create a procedure named `dbo.usp_GetProductInfo`.

It should:

- accept `@IDProduct`;
- return the product row as a result set;
- return the product price through an output parameter named `@Price`;
- return `0` if the product exists;
- return `1` if the product does not exist.

Before writing the procedure, decide why each output mechanism is appropriate for its purpose.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_GetProductInfo
    @IDProduct int,
    @Price     money OUTPUT
AS
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM Product
        WHERE IDProduct = @IDProduct
    )
        RETURN 1;

    SELECT @Price = PriceWithoutVAT
    FROM Product
    WHERE IDProduct = @IDProduct;

    SELECT *
    FROM Product
    WHERE IDProduct = @IDProduct;

    RETURN 0;
END
GO

DECLARE @Price money;
DECLARE @Result int;

EXEC @Result = dbo.usp_GetProductInfo
    @IDProduct = 1,
    @Price     = @Price OUTPUT;

SELECT
    @Price AS Price,
    @Result AS ReturnCode;
```

The result set is appropriate for the product row, the output parameter returns an individual data value, and `RETURN` communicates the status of the operation.

</details>

---

# Cleanup

Remove the procedures and test data created during the lab.

```sql
DROP PROCEDURE IF EXISTS dbo.usp_ListStates;
DROP PROCEDURE IF EXISTS dbo.usp_GetProduct;
DROP PROCEDURE IF EXISTS dbo.usp_ProductsByPrice;
DROP PROCEDURE IF EXISTS dbo.usp_GetProductColor;
DROP PROCEDURE IF EXISTS dbo.usp_CheckCustomerExists;
DROP PROCEDURE IF EXISTS dbo.usp_ListCategories;
DROP PROCEDURE IF EXISTS dbo.usp_CustomersByLastName;
DROP PROCEDURE IF EXISTS dbo.usp_GetProductInfo;
DROP PROCEDURE IF EXISTS dbo.usp_InsertCityInState;
DROP PROCEDURE IF EXISTS dbo.usp_TransferMoney;
DROP PROCEDURE IF EXISTS dbo.usp_GetLoyaltyDiscount;
DROP PROCEDURE IF EXISTS dbo.usp_ValidateCardNumber;
GO
```

Remove only the test rows created in this lab:

```sql
DELETE FROM City
WHERE Name IN ('Osaka', 'Tokyo', 'Toronto', 'Vancouver');

DELETE FROM State
WHERE Name IN ('Japan', 'Canada');
GO

DROP TABLE IF EXISTS BankAccount;
GO
```

> [!TIP]
> Keep cleanup targeted to objects and rows created during the lab.

---

# What You Should Know After This Lab

The most important ideas are:

```mermaid
flowchart LR
    I[Input parameters] --> P[Stored Procedure]
    P --> R[Result set]
    P --> O[OUTPUT parameters]
    P --> RC[RETURN status code]
    P --> T[(Tables)]
```

```text
Stored Procedure
    -> a named, callable database operation
```

```text
Input parameters
    -> send values into the procedure
```

```text
Result set
    -> returns rows
```

```text
OUTPUT parameter
    -> returns individual values
```

```text
RETURN
    -> returns an integer status code
```

And remember:

> **Views answer. Triggers react. Procedures do.**

A stored procedure is particularly useful when **one logical database operation requires several SQL statements**.

It can also reduce **network round-trips** by allowing those statements to execute on the database server after a single procedure call.

---

## Additional practice

More stored procedure exercises, covering input parameters, output values, and return status codes, are available in [Stored Procedure Exercises](../exercises/procedures.md).

---

# Where to Go Next

In the next lab, **Functions**, we will look at another type of reusable code stored inside the database.

Unlike stored procedures, functions are designed to return a value and can be used as part of SQL expressions and queries.

You will learn about:

- scalar functions;
- table-valued functions;
- using user-defined functions inside SQL statements.
