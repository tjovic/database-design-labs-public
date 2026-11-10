# Lab 08 – Complex Parameters Exercises

**Database:** `AdventureWorksENG`

These exercises build on [Lab 8 – Complex Parameters](../labs/lab08-complex-parameters.md). They are grouped by method: delimited strings, reading XML, building XML with `FOR XML PATH`, Table-Valued Parameters, and JSON. The last exercise asks you to choose the right method for several scenarios.

Several exercises insert or delete rows in `State`, `City`, `Customer`, and `Product`. Run them in a fresh copy of `AdventureWorksENG`, and recreate the database when you are done.

---

# Delimited strings

## Exercise 1 — Delimited String: Delete by Name List [INTERMEDIATE]

Create a procedure `dbo.usp_DeleteProductsByNameList` that takes one `nvarchar(max)` parameter — a comma-separated list of product names.

The procedure must:

1. Accept `@NameList nvarchar(max)`.
2. Delete all products whose name appears in the list.
3. Use `STRING_SPLIT` to split the list.

Insert three throwaway test products first (do not delete real `AdventureWorksENG` products — see the [database safety note](../exercises/README.md#database-safety-note)). Test the procedure against your own test products. Verify they are gone.

### Hints

- Use `STRING_SPLIT(@NameList, ',')` to get a table.
- Use `IN (SELECT value FROM STRING_SPLIT(...))` to match the names.
- Remember: `value` is `nvarchar`, and the `Product.Name` column is also `nvarchar`, so no `CAST` is needed.
- `Product.ProductNumber` and `Product.MinimumQuantityInStock` are `NOT NULL` — supply a value for each when inserting test rows.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_DeleteProductsByNameList
    @NameList nvarchar(max)
AS
BEGIN
    DELETE FROM dbo.Product
    WHERE Name IN
    (
        SELECT value
        FROM STRING_SPLIT(@NameList, ',')
    );
END
GO

-- Insert three throwaway test products — never delete real seed data
INSERT INTO Product (Name, ProductNumber, MinimumQuantityInStock, PriceWithoutVAT) VALUES
    (N'ZZ_TestProduct1', N'ZZTEST-001', 0, 9.99),
    (N'ZZ_TestProduct2', N'ZZTEST-002', 0, 9.99),
    (N'ZZ_TestProduct3', N'ZZTEST-003', 0, 9.99);

-- Test: delete all three test products in a single call
EXEC dbo.usp_DeleteProductsByNameList @NameList = N'ZZ_TestProduct1,ZZ_TestProduct2,ZZ_TestProduct3';

-- Verify they are gone
SELECT * FROM Product WHERE Name LIKE N'ZZ_TestProduct%';
```

</details>

---

## Exercise 2 — Delimited String with Validation [INTERMEDIATE]

Write a procedure `dbo.usp_GetProductsByIDListWithValidation` that:

1. Takes a comma-separated list of product IDs.
2. For each ID in the list, checks whether it exists in the `Product` table.
3. Returns two result sets:
   - **Valid products**: `IDProduct`, `Name`, `PriceWithoutVAT` for IDs that exist.
   - **Invalid IDs**: A list of IDs that were in the input but don't exist in the database.

Test it with a list like `'1,2,999,5,888'` (where 999 and 888 don't exist).

### Hints

- Split the input into a `@IDList` table variable.
- Use `LEFT JOIN` with `Product` to identify missing IDs.
- Return two separate result sets (two `SELECT` statements).

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_GetProductsByIDListWithValidation
    @IDList nvarchar(max)
AS
BEGIN
    DECLARE @IDs TABLE (ID int);

    INSERT INTO @IDs (ID)
    SELECT CAST(value AS int)
    FROM STRING_SPLIT(@IDList, ',');

    -- Valid products
    SELECT
        p.IDProduct,
        p.Name,
        p.PriceWithoutVAT
    FROM Product p
    INNER JOIN @IDs ids ON ids.ID = p.IDProduct
    ORDER BY p.IDProduct;

    -- Invalid IDs
    SELECT ids.ID AS InvalidID
    FROM @IDs ids
    LEFT JOIN Product p ON ids.ID = p.IDProduct
    WHERE p.IDProduct IS NULL
    ORDER BY ids.ID;
END
GO

-- Test
EXEC dbo.usp_GetProductsByIDListWithValidation @IDList = '1,2,999,5,888';

-- Result set 1: Valid products (1, 2, 5)
-- Result set 2: Invalid IDs (999, 888)

-- Cleanup
DROP PROCEDURE dbo.usp_GetProductsByIDListWithValidation;
```

</details>

---

## Exercise 3 — Manual String Splitter [ADVANCED]

In Lab 8, we used `STRING_SPLIT` — a built-in SQL Server function that does the work for us.

Here, we build a splitter from scratch using the fundamentals: `WHILE`, `CHARINDEX`, and `SUBSTRING`.

Write a **function** `dbo.fn_SplitInts` that:

1. Takes an `nvarchar(max)` string and a single-character separator.
2. Returns a table of `int` values — **without using `STRING_SPLIT`.**
3. Uses `WHILE`, `CHARINDEX`, and `SUBSTRING` to walk through the string.

Test your function against the built-in `STRING_SPLIT` for the input `'11,22,33,44'` with separator `,`. Both should return the same four values.

Reflect: how much code did you write to replicate one built-in function?

### Hints

- Start with `@Position = 1`.
- In each iteration, find the next separator with `CHARINDEX(@Separator, @Input, @Position)`.
- Extract the piece between separators using `SUBSTRING`.
- Convert to `int` with `CAST` and `INSERT` into the result table.
- Stop when `CHARINDEX` returns 0 (separator not found).

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER FUNCTION dbo.fn_SplitInts
(
    @Input nvarchar(max),
    @Separator nchar(1)
)
RETURNS @Result TABLE (Value int)
AS
BEGIN
    DECLARE @Position int = 1;
    DECLARE @NextPosition int;
    DECLARE @Piece nvarchar(max);

    WHILE @Position <= LEN(@Input)
    BEGIN
        -- Find the next separator
        SET @NextPosition = CHARINDEX(@Separator, @Input, @Position);

        -- If no separator found, we're at the end
        IF @NextPosition = 0
            SET @NextPosition = LEN(@Input) + 1;

        -- Extract the piece
        SET @Piece = SUBSTRING(@Input, @Position, @NextPosition - @Position);

        -- Insert it (skip empty pieces)
        IF LEN(@Piece) > 0
            INSERT INTO @Result (Value)
            VALUES (CAST(@Piece AS int));

        -- Move past the separator
        SET @Position = @NextPosition + 1;
    END

    RETURN;
END
GO

-- Test it
SELECT * FROM dbo.fn_SplitInts('11,22,33,44', ',');

-- Compare with STRING_SPLIT
SELECT CAST(value AS int) FROM STRING_SPLIT('11,22,33,44', ',');

-- Both should return the same values: 11, 22, 33, 44

-- Cleanup
DROP FUNCTION dbo.fn_SplitInts;
```

This demonstrates why built-in functions like `STRING_SPLIT` are valuable — you avoid writing this code every time. On older SQL Server versions (before 2016), you had to write something like this for every string-splitting task.

</details>

---

# XML

## Exercise 4 — XML: Insert a Batch of States [INTERMEDIATE]

Create a procedure `dbo.usp_InsertStatesBatch` that accepts an `xml` parameter of this shape:

```xml
<States>
    <State Name="NewCountry1" />
    <State Name="NewCountry2" />
    <State Name="NewCountry3" />
</States>
```

The procedure must:

1. Accept `@States xml`.
2. Insert all rows into the `State` table.
3. Use `.nodes()` and `.value()` to shred the XML.

Test it with at least three state names and verify the inserted rows.

### Hints

- Use `.nodes('/States/State')` to iterate over each `State` element.
- Use `.value('@Name', 'nvarchar(50)')` to extract the `Name` attribute.
- Remember: alias both the table and the column after `.nodes()` — `AS tbl(node)`.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertStatesBatch
    @States xml
AS
BEGIN
    INSERT INTO State (Name)
    SELECT
        tbl.node.value('@Name', 'nvarchar(50)')
    FROM @States.nodes('/States/State') AS tbl(node);
END
GO

-- Test
EXEC dbo.usp_InsertStatesBatch @States = N'
<States>
    <State Name="NewCountry1" />
    <State Name="NewCountry2" />
    <State Name="NewCountry3" />
</States>';

-- Verify
SELECT * FROM State WHERE Name LIKE N'NewCountry%';
```

</details>

---

## Exercise 5 — XML with Nested Structure [INTERMEDIATE]

In Lab 8, we built XML with simple elements. Here, we handle a more complex nested structure.

Write a procedure `dbo.usp_InsertEmployeeHierarchy` that accepts an `xml` parameter of this shape:

```xml
<Organization>
    <Department Name="Sales">
        <Employee FirstName="Alice" LastName="Anderson" />
        <Employee FirstName="Bob" LastName="Brown" />
    </Department>
    <Department Name="Engineering">
        <Employee FirstName="Charlie" LastName="Clark" />
    </Department>
</Organization>
```

The procedure must:

1. Insert each department into a test table `dbo.TestDepartment`.
2. Insert each employee into a test table `dbo.TestEmployee`, linked to the correct department by a `DepartmentID`.
3. Use `SCOPE_IDENTITY()` to link the rows.

Before testing, create the tables:

```sql
CREATE TABLE dbo.TestDepartment
(
    DepartmentID int PRIMARY KEY IDENTITY,
    Name nvarchar(50)
);

CREATE TABLE dbo.TestEmployee
(
    EmployeeID int PRIMARY KEY IDENTITY,
    DepartmentID int,
    FirstName nvarchar(50),
    LastName nvarchar(50)
);
GO
```

Test the procedure, verify the inserts, clean up the tables and procedure.

### Hints

- You need two `.nodes()` calls: one for departments, one for employees within each department.
- Use a `WHILE` loop or `INSERT ... SELECT` with an outer loop to process each department.
- For each department, capture the inserted identity and pass it to the employee insert.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertEmployeeHierarchy
    @Organization xml
AS
BEGIN
    DECLARE @DeptID int;
    DECLARE @DeptName nvarchar(50);

    -- Process each department
    DECLARE @Departments TABLE
    (
        DeptName nvarchar(50),
        EmployeeXml xml
    );

    INSERT INTO @Departments (DeptName, EmployeeXml)
    SELECT
        dept.node.value('@Name', 'nvarchar(50)'),
        dept.node.query('.')
    FROM @Organization.nodes('/Organization/Department') AS dept(node);

    -- For each department
    DECLARE dept_cursor CURSOR FOR
    SELECT DeptName, EmployeeXml FROM @Departments;

    OPEN dept_cursor;

    FETCH NEXT FROM dept_cursor INTO @DeptName, @Organization;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        -- Insert the department
        INSERT INTO dbo.TestDepartment (Name)
        VALUES (@DeptName);

        SET @DeptID = SCOPE_IDENTITY();

        -- Insert employees under this department
        INSERT INTO dbo.TestEmployee (DepartmentID, FirstName, LastName)
        SELECT
            @DeptID,
            emp.node.value('@FirstName', 'nvarchar(50)'),
            emp.node.value('@LastName', 'nvarchar(50)')
        FROM @Organization.nodes('/Department/Employee') AS emp(node);

        FETCH NEXT FROM dept_cursor INTO @DeptName, @Organization;
    END

    CLOSE dept_cursor;
    DEALLOCATE dept_cursor;
END
GO

-- Test
EXEC dbo.usp_InsertEmployeeHierarchy @Organization = N'
<Organization>
    <Department Name="Sales">
        <Employee FirstName="Alice" LastName="Anderson" />
        <Employee FirstName="Bob" LastName="Brown" />
    </Department>
    <Department Name="Engineering">
        <Employee FirstName="Charlie" LastName="Clark" />
    </Department>
</Organization>';

-- Verify
SELECT * FROM dbo.TestDepartment;
SELECT * FROM dbo.TestEmployee;

-- Cleanup
DROP PROCEDURE dbo.usp_InsertEmployeeHierarchy;
DROP TABLE dbo.TestEmployee;
DROP TABLE dbo.TestDepartment;
```

> [!NOTE]
> The cursor-based solution above is intentionally simple, not fast. For a production-quality version without a cursor, insert all departments first with `OUTPUT INSERTED.DepartmentID` into a table keyed by `Name`, then join that back to the original XML by department name to insert the employees in one set-based `INSERT ... SELECT`. The `OUTPUT` clause can only reference `INSERTED`/`DELETED` columns — not arbitrary expressions from the source `SELECT` — so the department name (not the raw XML fragment) is what you carry across the two inserts.

</details>

---

## Exercise 6 — XML: Find or Create Related Records [ADVANCED]

> [!TIP]
> Optional extension or homework: this exercise combines XML input with find-or-create logic across three related tables.

In previous exercises, we used XML to insert multiple records into a database.

Now consider a more realistic situation.

An application receives information about a customer, including their city and state. However, some of this information may already exist in the database.

We want to create a stored procedure that **inserts only the missing records**.

### The problem

Our database contains three related tables:

- `State` — stores states or countries.
- `City` — stores cities, each belonging to a state.
- `Customer` — stores customers, each optionally linked to a city.

The relationships are:

```mermaid
flowchart LR
    A["State"] -->|"1:N"| B["City"]
    B -->|"1:N"| C["Customer"]
```

The application sends the following XML document:

```xml
<Customer
    FirstName="Luka"
    LastName="Modric"
    City="Madrid"
    State="Spain" />
```

Before inserting the customer, the procedure must determine whether the state and city already exist.

For example:

- If `Spain` already exists, use its existing `IDState`.
- If `Madrid` already exists within `Spain`, use its existing `IDCity`.
- If the customer already exists, do not insert a duplicate.

### Requirements

Create a stored procedure named `dbo.usp_InsertCustomerWithLocation` that:

1. Accepts one parameter named `@Customer` of type `xml`.
2. Extracts `FirstName`, `LastName`, `City`, and `State` from the XML attributes.
3. Checks whether the state exists. If not, inserts it and retrieves its new ID.
4. Checks whether the city exists **within that state**. If not, inserts it and retrieves its new ID.
5. Checks whether the customer exists using their first and last name. If not, inserts the customer and links them to the city.
6. Returns the customer's ID, name, city, and state.

For this exercise, assume that the combination of first and last name uniquely identifies a customer. In a real application, a more reliable identifier would normally be required.

### Expected behavior

Call the procedure twice using the same XML:

```sql
EXEC dbo.usp_InsertCustomerWithLocation
    @Customer = N'
<Customer
    FirstName="Luka"
    LastName="Modric"
    City="Madrid"
    State="Spain" />';
```

After the first call, the required records should exist.

After the second call, no additional records should be inserted.

Both calls should return the same customer ID.

### Hints

- Use `.value()` to extract XML attributes.
- Use `SELECT @Variable = Column FROM Table` to find existing IDs.
- Use `IF @Variable IS NULL` to decide whether an insert is necessary.
- Use `SCOPE_IDENTITY()` to retrieve newly generated IDs.
- Check both `City.Name` and `City.StateID` when searching for an existing city.

> [!NOTE]
> The find-or-create pattern is not specific to XML. The same database logic can be used with scalar parameters, JSON, or Table-Valued Parameters.
>
> XML is simply the format used to pass the input data.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertCustomerWithLocation
    @Customer xml
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @FirstName nvarchar(50) =
        @Customer.value('(/Customer/@FirstName)[1]', 'nvarchar(50)');

    DECLARE @LastName nvarchar(50) =
        @Customer.value('(/Customer/@LastName)[1]', 'nvarchar(50)');

    DECLARE @CityName nvarchar(50) =
        @Customer.value('(/Customer/@City)[1]', 'nvarchar(50)');

    DECLARE @StateName nvarchar(50) =
        @Customer.value('(/Customer/@State)[1]', 'nvarchar(50)');

    DECLARE @StateID int;
    DECLARE @CityID int;
    DECLARE @CustomerID int;

    -- Step 1: Find or create the state
    SELECT @StateID = IDState
    FROM State
    WHERE Name = @StateName;

    IF @StateID IS NULL
    BEGIN
        INSERT INTO State (Name)
        VALUES (@StateName);

        SET @StateID = SCOPE_IDENTITY();
    END;

    -- Step 2: Find or create the city
    SELECT @CityID = IDCity
    FROM City
    WHERE Name = @CityName
      AND StateID = @StateID;

    IF @CityID IS NULL
    BEGIN
        INSERT INTO City (Name, StateID)
        VALUES (@CityName, @StateID);

        SET @CityID = SCOPE_IDENTITY();
    END;

    -- Step 3: Find or create the customer
    SELECT @CustomerID = IDCustomer
    FROM Customer
    WHERE FirstName = @FirstName
      AND LastName = @LastName;

    IF @CustomerID IS NULL
    BEGIN
        INSERT INTO Customer (FirstName, LastName, CityID)
        VALUES (@FirstName, @LastName, @CityID);

        SET @CustomerID = SCOPE_IDENTITY();
    END;

    -- Return customer information
    SELECT
        c.IDCustomer,
        c.FirstName,
        c.LastName,
        ci.Name AS CityName,
        s.Name AS StateName
    FROM Customer c
    LEFT JOIN City ci ON ci.IDCity = c.CityID
    LEFT JOIN State s ON s.IDState = ci.StateID
    WHERE c.IDCustomer = @CustomerID;

END;
GO
```

### Test the procedure

For an isolated test, use distinctive names that do not already exist in the training database.

```sql
-- First call
EXEC dbo.usp_InsertCustomerWithLocation
    @Customer = N'
<Customer
    FirstName="ZZ_TestLuka"
    LastName="ZZ_TestModric"
    City="ZZ_TestMadrid"
    State="ZZ_TestSpain" />';

-- Second call with identical data
EXEC dbo.usp_InsertCustomerWithLocation
    @Customer = N'
<Customer
    FirstName="ZZ_TestLuka"
    LastName="ZZ_TestModric"
    City="ZZ_TestMadrid"
    State="ZZ_TestSpain" />';
```

### Verify the results

```sql
SELECT COUNT(*) AS StateCount
FROM State
WHERE Name = N'ZZ_TestSpain';

SELECT COUNT(*) AS CityCount
FROM City c
JOIN State s ON s.IDState = c.StateID
WHERE c.Name = N'ZZ_TestMadrid'
  AND s.Name = N'ZZ_TestSpain';

SELECT COUNT(*) AS CustomerCount
FROM Customer
WHERE FirstName = N'ZZ_TestLuka'
  AND LastName = N'ZZ_TestModric';
```

Expected results:

| StateCount | CityCount | CustomerCount |
|---|---|---|
| 1 | 1 | 1 |

Running the procedure multiple times with the same input should not create additional records during this sequential test.

</details>

> [!IMPORTANT]
> **Real-world considerations**
>
> This simplified procedure assumes sequential execution in an isolated training database. Concurrent calls require appropriate unique constraints and concurrency control to prevent duplicates.
>
> If a later insert fails, earlier inserts may remain in the database. Transactions, covered in [Lab 9](../labs/lab09-transactions.md), allow related changes to succeed or fail together.

---

# Building XML with `FOR XML PATH`

## Exercise 7 — FOR XML PATH: Build a Price List [INTERMEDIATE]

Write a query (no procedure) that builds an XML price list from the `Product` table.

The output should be:

```xml
<PriceList>
    <Product ID="1" Name="..." Price="..." />
    <Product ID="2" Name="..." Price="..." />
    ...
</PriceList>
```

Include only products where `PriceWithoutVAT > 0`. Order by `PriceWithoutVAT` descending.

### Hints

- Use `FOR XML PATH('Product')` to wrap each row.
- Use `ROOT('PriceList')` to wrap the whole thing.
- Use column aliases with `[@ID]` for attributes.

<details>
<summary>Show solution</summary>

```sql
SELECT
    p.IDProduct       AS [@ID],
    p.Name            AS [@Name],
    p.PriceWithoutVAT AS [@Price]
FROM Product p
WHERE p.PriceWithoutVAT > 0
ORDER BY p.PriceWithoutVAT DESC
FOR XML PATH('Product'), ROOT('PriceList');
```

</details>

---

## Exercise 8 — Generating Nested XML with FOR XML PATH [ADVANCED]

Write a query (not a procedure) that:

1. Reads from `Customer` where `IDCustomer < 11`.
2. Produces XML of this shape:

```xml
<Customers>
    <Customer IDCustomer="1">
        <FirstName>Gustavo</FirstName>
        <LastName>Achong</LastName>
        <Emails>
            <Email>gustavo0@adventure-works.com</Email>
        </Emails>
    </Customer>
    ...
</Customers>
```

Use `FOR XML PATH` with slash-separated aliases to create the nested structure.

### Hints

- `[@IDCustomer]` in the `SELECT` becomes an XML attribute.
- `[FirstName]` becomes a simple element.
- `[Emails/Email]` with a slash creates a nested element.
- Use `FOR XML PATH('Customer'), ROOT('Customers')` to set the structure.

<details>
<summary>Show solution</summary>

```sql
SELECT
    c.IDCustomer      AS [@IDCustomer],
    c.FirstName       AS [FirstName],
    c.LastName        AS [LastName],
    c.Email           AS [Emails/Email]
FROM Customer c
WHERE c.IDCustomer < 11
FOR XML PATH('Customer'), ROOT('Customers');
```

Run it and inspect the XML. Notice:

- `[@IDCustomer]` became an attribute on the `<Customer>` element.
- `[FirstName]` and `[LastName]` became child elements.
- `[Emails/Email]` created a nested `<Emails>` container with an `<Email>` child inside.

</details>

---

# Table-Valued Parameters

## Exercise 9 — TVP Fundamentals [INTERMEDIATE]

Create a **table type** `dbo.ProductIDsExercise` with a single `int` column called `ID` (primary key).

Write a procedure `dbo.usp_ListProductsByIDList` that:

1. Accepts one `dbo.ProductIDsExercise READONLY` parameter.
2. Returns `IDProduct`, `Name`, and `PriceWithoutVAT` for all products in the list.
3. Joins the TVP against the `Product` table.

Call it with three product IDs and verify the results.

### Hints

- `CREATE TYPE ... AS TABLE` defines the type; `CREATE OR ALTER PROCEDURE` uses it as a parameter type.
- Remember `READONLY` is mandatory.
- After `DECLARE @List dbo.ProductIDsExercise;`, you can `INSERT INTO @List (ID) VALUES (...), (...);`

<details>
<summary>Show solution</summary>

```sql
CREATE TYPE dbo.ProductIDsExercise AS TABLE
(
    ID int PRIMARY KEY
);
GO

CREATE OR ALTER PROCEDURE dbo.usp_ListProductsByIDList
    @IDs dbo.ProductIDsExercise READONLY
AS
BEGIN
    SELECT
        p.IDProduct,
        p.Name,
        p.PriceWithoutVAT
    FROM Product p
    INNER JOIN @IDs ids ON ids.ID = p.IDProduct
    ORDER BY p.IDProduct;
END
GO

-- Test
DECLARE @ProductList dbo.ProductIDsExercise;
INSERT INTO @ProductList (ID) VALUES (1), (2), (5);

EXEC dbo.usp_ListProductsByIDList @IDs = @ProductList;
```

</details>

---

## Exercise 10 — TVP: Insert Multiple Products [INTERMEDIATE]

Create a **table type** `dbo.ProductInput` with columns `Name nvarchar(50)`, `ProductNumber nvarchar(25)`, and `PriceWithoutVAT money` (all `NOT NULL`).

Write a procedure `dbo.usp_InsertProducts` that:

1. Accepts one `dbo.ProductInput READONLY` parameter.
2. Inserts every row from it into the `Product` table.

Call it with at least two test products and verify they were inserted with a query.

### Hints

- `Product.MinimumQuantityInStock` is `NOT NULL` with no default — supply a value (e.g. `0`) in the `INSERT`, even though the TVP itself doesn't carry that column.
- Use a distinctive name prefix (e.g. `ZZ_Test`) to make your test products easy to find.

<details>
<summary>Show solution</summary>

```sql
CREATE TYPE dbo.ProductInput AS TABLE
(
    Name            nvarchar(50) NOT NULL,
    ProductNumber   nvarchar(25) NOT NULL,
    PriceWithoutVAT money        NOT NULL
);
GO

CREATE OR ALTER PROCEDURE dbo.usp_InsertProducts
    @Products dbo.ProductInput READONLY
AS
BEGIN
    INSERT INTO Product (Name, ProductNumber, MinimumQuantityInStock, PriceWithoutVAT)
    SELECT Name, ProductNumber, 0, PriceWithoutVAT
    FROM @Products;
END
GO

-- Test
DECLARE @NewProducts dbo.ProductInput;

INSERT INTO @NewProducts (Name, ProductNumber, PriceWithoutVAT) VALUES
    (N'ZZ_TestWidget1', N'ZZTEST-101', 19.99),
    (N'ZZ_TestWidget2', N'ZZTEST-102', 29.99);

EXEC dbo.usp_InsertProducts @Products = @NewProducts;

-- Verify
SELECT IDProduct, Name, ProductNumber, PriceWithoutVAT
FROM Product
WHERE Name LIKE N'ZZ_TestWidget%';
```

</details>

---

# JSON

## Exercise 11 — JSON: Insert Customers from JSON [INTERMEDIATE]

Write a procedure `dbo.usp_InsertCustomersFromJson` that:

1. Accepts an `nvarchar(max)` parameter containing JSON.
2. The JSON is an array of objects with `FirstName`, `LastName`, and `Email` fields.
3. Uses `OPENJSON ... WITH (...)` to shred the JSON into rows.
4. Inserts all rows into the `Customer` table.

Call it with at least two customers in JSON format and verify they were inserted.

### Hints

- JSON array: `[ { "FirstName": "...", ... }, { "FirstName": "...", ... } ]`
- `OPENJSON(@Json)` without a second argument shreds the root array.
- `WITH (FirstName nvarchar(50) '$.FirstName', ...)`  — column name, type, and path.
- Paths like `'$.FirstName'` mean "from the current row, read the FirstName property".

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertCustomersFromJson
    @JsonCustomers nvarchar(max)
AS
BEGIN
    INSERT INTO Customer (FirstName, LastName, Email)
    SELECT FirstName, LastName, Email
    FROM OPENJSON(@JsonCustomers)
    WITH
    (
        FirstName nvarchar(50)  '$.FirstName',
        LastName  nvarchar(50)  '$.LastName',
        Email     nvarchar(100) '$.Email'
    );
END
GO

-- Test
EXEC dbo.usp_InsertCustomersFromJson @JsonCustomers = N'
[
    { "FirstName": "Xavier", "LastName": "Xavier", "Email": "xavier@example.com" },
    { "FirstName": "Yolanda", "LastName": "Yates", "Email": "yolanda@example.com" }
]';

-- Verify
SELECT FirstName, LastName, Email
FROM Customer
WHERE Email IN ('xavier@example.com', 'yolanda@example.com');
```

</details>

---

# Choosing a method

## Exercise 12 — Choose the Right Method [INTERMEDIATE]

For each scenario below, decide which of the five methods from Lab 8 (client-side query, delimited string, XML, TVP, JSON) is most appropriate. Write one sentence defending your choice.

There is not one single "right" answer — the argument is what counts.

1. **A .NET desktop app with strongly-typed model classes needs to insert 500 rows.**

2. **A React frontend posts a new invoice via `fetch` with nested line items as JSON.**

3. **A nightly batch job running in SQL Agent needs to delete 1,000 rows by ID, reading the IDs from a text file.**

4. **An external partner sends daily sales reports over HTTP in a schema they defined, as a JSON payload.**

5. **An admin GUI lets a power user tick 30 rows in a grid and click "Archive".**

<details>
<summary>Show answers (one interpretation; others are valid)</summary>

1. **TVP** — .NET has first-class support for `DataTable`/`IEnumerable<T>`, and TVPs are type-safe and fast. Strongly-typed model classes map cleanly to a TVP type.

2. **JSON** — The client already speaks JSON (`fetch` sends it natively). Using JSON avoids translation overhead. The server shreds it with `OPENJSON`.

3. **Delimited string** — The IDs come from a text file as a flat list. No nesting needed. `STRING_SPLIT` to split, `IN (SELECT ...)` to match.

4. **JSON** — The partner is sending JSON over HTTP. Accept it as-is via `OPENJSON`. Zero translation overhead.

5. **TVP** — The admin GUI is C# or VB.NET (desktop). The 30 IDs form a natural collection that the GUI can package as a TVP.

</details>

---

# Cleanup

Remove the procedures, functions, table types, and test tables created during these exercises. Rows inserted into `State`, `City`, `Customer`, and `Product` are not removed here; recreate `AdventureWorksENG` to return to the original data.

```sql
DROP PROCEDURE IF EXISTS dbo.usp_DeleteProductsByNameList;
DROP PROCEDURE IF EXISTS dbo.usp_GetProductsByIDListWithValidation;
DROP FUNCTION IF EXISTS dbo.fn_SplitInts;
DROP PROCEDURE IF EXISTS dbo.usp_InsertStatesBatch;
DROP PROCEDURE IF EXISTS dbo.usp_InsertEmployeeHierarchy;
DROP PROCEDURE IF EXISTS dbo.usp_InsertCustomerWithLocation;
DROP PROCEDURE IF EXISTS dbo.usp_ListProductsByIDList;
DROP PROCEDURE IF EXISTS dbo.usp_InsertProducts;
DROP PROCEDURE IF EXISTS dbo.usp_InsertCustomersFromJson;
GO

-- Table types can be dropped only after the procedures that use them.
DROP TYPE IF EXISTS dbo.ProductIDsExercise;
DROP TYPE IF EXISTS dbo.ProductInput;
GO

DROP TABLE IF EXISTS dbo.TestEmployee;
DROP TABLE IF EXISTS dbo.TestDepartment;
GO
```

---

# References

- [Lab 8 – Complex Parameters](../labs/lab08-complex-parameters.md) — all five methods: client-side query building (the anti-example), delimited strings, XML, Table-Valued Parameters, and JSON.
- **Microsoft Learn**: [STRING_SPLIT (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/string-split-transact-sql)
- **Microsoft Learn**: [Nodes() Method (xml Data Type)](https://learn.microsoft.com/en-us/sql/t-sql/xml/nodes-method-xml-data-type)
- **Microsoft Learn**: [FOR XML (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/xml/for-xml-sql-server)
- **Microsoft Learn**: [OPENJSON (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/openjson-transact-sql)
- **Microsoft Learn**: [Table-Valued Parameters](https://learn.microsoft.com/en-us/sql/relational-databases/tables/use-table-valued-parameters-database-engine)
