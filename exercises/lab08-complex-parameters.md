# Lab 08 – Complex Parameters Exercises

**Database:** `AdventureWorksENG`

These exercises build on [Lab 8 – Complex Parameters](../labs/lab08-complex-parameters.md). They are grouped by method: delimited strings, reading XML, building XML with `FOR XML PATH`, JSON, and Table-Valued Parameters. The last exercise asks you to choose the right method for several scenarios.

Several exercises insert or delete rows in `State`, `City`, `Customer`, and `Product`. Run them in order on a freshly restored `AdventureWorksENG` (see [About the database](../README.md#about-the-database)); the solutions do not remove what they create. To start over, restore the database again.

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

Test it with a list like `'1,2,316,9999,8888'` (where 9999 and 8888 don't exist).

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
EXEC dbo.usp_GetProductsByIDListWithValidation @IDList = '1,2,316,9999,8888';

-- Result set 1: Valid products (1, 2, 316)
-- Result set 2: Invalid IDs (8888, 9999)
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
- Remember: alias both the table and the column after `.nodes()` — `AS tbl(col)`.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertStatesBatch
    @States xml
AS
BEGIN
    INSERT INTO State (Name)
    SELECT
        tbl.col.value('@Name', 'nvarchar(50)')
    FROM @States.nodes('/States/State') AS tbl(col);
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

## Exercise 5 — XML: Read Element Text and Attributes [INTERMEDIATE]

Create a procedure `dbo.usp_InsertCitiesFromXml` that accepts an `xml` parameter of this shape:

```xml
<Cities>
    <City StateID="1">ZZ_TestCity1</City>
    <City StateID="1">ZZ_TestCity2</City>
    <City StateID="2">ZZ_TestCity3</City>
</Cities>
```

The city name is the **text** of each `City` element, and the state is an **attribute**.

The procedure must:

1. Accept `@Cities xml`.
2. Insert all cities into the `City` table with one `INSERT ... SELECT`.

Call it with the XML above and verify the inserted rows, including each city's state.

### Hints

- Read the element text with `.value('.', 'nvarchar(50)')`, as in Lab 8, Section 4.2, Step 3.
- Read the attribute with `.value('@StateID', 'int')`.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertCitiesFromXml
    @Cities xml
AS
BEGIN
    INSERT INTO City (Name, StateID)
    SELECT
        tbl.col.value('.', 'nvarchar(50)'),
        tbl.col.value('@StateID', 'int')
    FROM @Cities.nodes('/Cities/City') AS tbl(col);
END;
GO

-- Test
EXEC dbo.usp_InsertCitiesFromXml @Cities = N'
<Cities>
    <City StateID="1">ZZ_TestCity1</City>
    <City StateID="1">ZZ_TestCity2</City>
    <City StateID="2">ZZ_TestCity3</City>
</Cities>';

-- Verify
SELECT c.Name AS City, s.Name AS State
FROM City c
JOIN State s ON s.IDState = c.StateID
WHERE c.Name LIKE N'ZZ_TestCity%'
ORDER BY c.Name;
```

Expected result:

| City | State |
|---|---|
| ZZ_TestCity1 | Croatia |
| ZZ_TestCity2 | Croatia |
| ZZ_TestCity3 | Germany |

</details>

---

## Exercise 6 — XML with Nested Structure [INTERMEDIATE]

In Section 4.4 of Lab 8, we inserted an invoice and its items from one XML document. Here, we apply the same pattern to a department and its employees.

Write a procedure `dbo.usp_InsertDepartmentWithEmployees` that accepts an `xml` parameter of this shape:

```xml
<Department Name="Sales">
    <Employee FirstName="Alice" LastName="Anderson" />
    <Employee FirstName="Bob" LastName="Brown" />
</Department>
```

The procedure must:

1. Insert the department into a test table `dbo.TestDepartment`.
2. Insert each employee into a test table `dbo.TestEmployee`, linked to the department by a `DepartmentID`.
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

Call the procedure twice: once for `Sales` with the two employees above, and once for `Engineering` with one employee, Charlie Clark. Verify that every employee is linked to the correct department.

### Hints

- Read the department with `.nodes('/Department')` and the employees with `.nodes('/Department/Employee')`, as the procedure in Section 4.4 reads the invoice header and its items.
- Insert the department first and save `SCOPE_IDENTITY()` in a variable.
- Insert all employees with one `INSERT ... SELECT` that uses that variable.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertDepartmentWithEmployees
    @Department xml
AS
BEGIN
    DECLARE @DepartmentID int;

    -- Insert the department
    INSERT INTO dbo.TestDepartment (Name)
    SELECT tbl.col.value('@Name', 'nvarchar(50)')
    FROM @Department.nodes('/Department') AS tbl(col);

    SET @DepartmentID = SCOPE_IDENTITY();

    -- Insert all employees of this department
    INSERT INTO dbo.TestEmployee (DepartmentID, FirstName, LastName)
    SELECT
        @DepartmentID,
        tbl.col.value('@FirstName', 'nvarchar(50)'),
        tbl.col.value('@LastName', 'nvarchar(50)')
    FROM @Department.nodes('/Department/Employee') AS tbl(col);
END;
GO

-- Test
EXEC dbo.usp_InsertDepartmentWithEmployees @Department = N'
<Department Name="Sales">
    <Employee FirstName="Alice" LastName="Anderson" />
    <Employee FirstName="Bob" LastName="Brown" />
</Department>';

EXEC dbo.usp_InsertDepartmentWithEmployees @Department = N'
<Department Name="Engineering">
    <Employee FirstName="Charlie" LastName="Clark" />
</Department>';

-- Verify
SELECT d.Name AS Department, e.FirstName, e.LastName
FROM dbo.TestEmployee e
JOIN dbo.TestDepartment d ON d.DepartmentID = e.DepartmentID
ORDER BY d.Name, e.LastName;
```

Expected result:

| Department | FirstName | LastName |
|---|---|---|
| Engineering | Charlie | Clark |
| Sales | Alice | Anderson |
| Sales | Bob | Brown |

</details>

> [!NOTE]
> Each call inserts one department. To insert several departments in one call, the procedure would have to read every employee together with its own department, which needs XML techniques that Lab 8 does not cover.

---

## Exercise 7 — XML: Find or Create Related Records [ADVANCED]

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

- Use `.nodes('/Customer')` and `.value()` to read the attributes into variables with `SELECT @Variable = ...`.
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
    DECLARE @FirstName nvarchar(50);
    DECLARE @LastName nvarchar(50);
    DECLARE @CityName nvarchar(50);
    DECLARE @StateName nvarchar(50);
    DECLARE @StateID int;
    DECLARE @CityID int;
    DECLARE @CustomerID int;

    -- Read the customer's attributes
    SELECT
        @FirstName = tbl.col.value('@FirstName', 'nvarchar(50)'),
        @LastName = tbl.col.value('@LastName', 'nvarchar(50)'),
        @CityName = tbl.col.value('@City', 'nvarchar(50)'),
        @StateName = tbl.col.value('@State', 'nvarchar(50)')
    FROM @Customer.nodes('/Customer') AS tbl(col);

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

## Exercise 8 — FOR XML PATH: Build a Price List [INTERMEDIATE]

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

## Exercise 9 — Generating Nested XML with FOR XML PATH [ADVANCED]

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

# JSON

## Exercise 10 — JSON: Insert Customers from JSON [INTERMEDIATE]

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
        Email     nvarchar(50)  '$.Email'
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

## Exercise 11 — JSON: Insert a Parent and Its Children [INTERMEDIATE]

In Lab 8, Section 5.6, we inserted an invoice and its items from one JSON document. Here, the children are a simple array of names.

Create the test tables:

```sql
CREATE TABLE dbo.TestTeam
(
    TeamID int PRIMARY KEY IDENTITY,
    Name nvarchar(50)
);

CREATE TABLE dbo.TestMember
(
    MemberID int PRIMARY KEY IDENTITY,
    TeamID int,
    Name nvarchar(50)
);
GO
```

Write a procedure `dbo.usp_InsertTeamFromJson` that accepts an `nvarchar(max)` parameter of this shape:

```json
{
    "Team": "Blue",
    "Members": ["Ana", "Ivan", "Marko"]
}
```

The procedure must:

1. Insert the team into `dbo.TestTeam`.
2. Insert every member into `dbo.TestMember`, linked to the team by `TeamID`.

Call it twice: once for team `Blue` with the members above, and once for team `Red` with members `Petra` and `Luka`. Verify that every member is linked to the correct team.

### Hints

- Read the team name with `JSON_VALUE(@Json, '$.Team')`.
- Save `SCOPE_IDENTITY()` in a variable after inserting the team.
- `OPENJSON(@Json, '$.Members')` turns the array into rows. The elements are plain values, not objects, so read the `value` column, as in Lab 8, Section 5.3, Step 1.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertTeamFromJson
    @Json nvarchar(max)
AS
BEGIN
    DECLARE @TeamID int;

    -- Insert the team
    INSERT INTO dbo.TestTeam (Name)
    VALUES (JSON_VALUE(@Json, '$.Team'));

    SET @TeamID = SCOPE_IDENTITY();

    -- Insert all members of this team
    INSERT INTO dbo.TestMember (TeamID, Name)
    SELECT @TeamID, value
    FROM OPENJSON(@Json, '$.Members');
END;
GO

-- Test
EXEC dbo.usp_InsertTeamFromJson @Json = N'
{
    "Team": "Blue",
    "Members": ["Ana", "Ivan", "Marko"]
}';

EXEC dbo.usp_InsertTeamFromJson @Json = N'
{
    "Team": "Red",
    "Members": ["Petra", "Luka"]
}';

-- Verify
SELECT t.TeamID, t.Name AS Team, m.Name AS Member
FROM dbo.TestMember m
JOIN dbo.TestTeam t ON t.TeamID = m.TeamID
ORDER BY t.TeamID, m.Name;
```

Expected result:

| TeamID | Team | Member |
|---|---|---|
| 1 | Blue | Ana |
| 1 | Blue | Ivan |
| 1 | Blue | Marko |
| 2 | Red | Luka |
| 2 | Red | Petra |

</details>

---

## Exercise 12 — JSON: Delete by a List of IDs [INTERMEDIATE]

This exercise uses the tables and rows from the previous exercise.

Write a procedure `dbo.usp_DeleteTeamsFromJson` that accepts a JSON array of team IDs, such as `[1, 2]`, and deletes those teams **together with their members**.

The procedure must:

1. Accept `@TeamIDs nvarchar(max)`.
2. Delete the members of the listed teams first, then the teams themselves.
3. Use set-based `DELETE` statements, with no loop.

Call it with the ID of team `Blue` (`[1]` if you ran the previous exercise once) and verify that team `Blue` and its three members are gone, while team `Red` remains.

### Hints

- `OPENJSON(@TeamIDs)` returns one row per ID in the `value` column. The values are text, so convert them with `CAST(value AS int)`, just as with `STRING_SPLIT`.
- Delete the child rows (`TestMember`) before the parent rows (`TestTeam`).

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_DeleteTeamsFromJson
    @TeamIDs nvarchar(max)
AS
BEGIN
    -- Delete the members first
    DELETE FROM dbo.TestMember
    WHERE TeamID IN
    (
        SELECT CAST(value AS int)
        FROM OPENJSON(@TeamIDs)
    );

    -- Then delete the teams
    DELETE FROM dbo.TestTeam
    WHERE TeamID IN
    (
        SELECT CAST(value AS int)
        FROM OPENJSON(@TeamIDs)
    );
END;
GO

-- Test
EXEC dbo.usp_DeleteTeamsFromJson @TeamIDs = N'[1]';

-- Verify
SELECT t.Name AS Team, m.Name AS Member
FROM dbo.TestTeam t
LEFT JOIN dbo.TestMember m ON m.TeamID = t.TeamID
ORDER BY m.Name;
```

Expected result: only team `Red`, with `Luka` and `Petra`.

If deleting the teams failed after the members were deleted, the members would already be gone. [Lab 9](../labs/lab09-transactions.md) shows how a transaction makes both deletes succeed or fail together.

</details>

---

## Exercise 13 — FOR JSON PATH: Build a Product List [INTERMEDIATE]

Write a query (no procedure) that returns the five most expensive products as JSON of this shape:

```json
{
    "Products": [
        {
            "IDProduct": 749,
            "Name": "Road-150 Red, 62",
            "PriceWithoutVAT": 3578.2700,
            "Subcategory": {
                "ID": 2,
                "Name": "Road Bikes"
            }
        },
        ...
    ]
}
```

Order the products by `PriceWithoutVAT` descending, then by `IDProduct`.

### Hints

- Join `Product` with `Subcategory` to get the subcategory name.
- A dot in the alias creates a nested object: `[Subcategory.Name]`.
- Use `ROOT('Products')` to wrap the array.

<details>
<summary>Show solution</summary>

```sql
SELECT TOP 5
    p.IDProduct,
    p.Name,
    p.PriceWithoutVAT,
    s.IDSubcategory AS [Subcategory.ID],
    s.Name AS [Subcategory.Name]
FROM Product p
JOIN Subcategory s ON s.IDSubcategory = p.SubcategoryID
ORDER BY p.PriceWithoutVAT DESC, p.IDProduct
FOR JSON PATH, ROOT('Products');
```

Compare it with Exercise 9: JSON uses a dot in the alias where XML uses a slash.

</details>

---

# Table-Valued Parameters

## Exercise 14 — TVP Fundamentals [INTERMEDIATE]

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
INSERT INTO @ProductList (ID) VALUES (1), (2), (316);

EXEC dbo.usp_ListProductsByIDList @IDs = @ProductList;
```

</details>

---

## Exercise 15 — TVP: Insert Multiple Products [INTERMEDIATE]

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

# Choosing a method

## Exercise 16 — Choose the Right Method [INTERMEDIATE]

For each scenario below, decide which of the five methods from Lab 8 (client-side query, delimited string, XML, JSON, TVP) is most appropriate. Write one sentence defending your choice.

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

5. **Delimited string or TVP** — The 30 IDs form a flat list, as in Lab 8, Section 7.3, Scenario 1. If the GUI's platform supports TVPs (for example .NET), a TVP adds type safety.

</details>

---

# References

- [Lab 8 – Complex Parameters](../labs/lab08-complex-parameters.md) — all five methods: client-side query building (the anti-example), delimited strings, XML, JSON, and Table-Valued Parameters.
- **Microsoft Learn**: [STRING_SPLIT (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/string-split-transact-sql)
- **Microsoft Learn**: [Nodes() Method (xml Data Type)](https://learn.microsoft.com/en-us/sql/t-sql/xml/nodes-method-xml-data-type)
- **Microsoft Learn**: [FOR XML (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/xml/for-xml-sql-server)
- **Microsoft Learn**: [OPENJSON (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/openjson-transact-sql)
- **Microsoft Learn**: [Table-Valued Parameters](https://learn.microsoft.com/en-us/sql/relational-databases/tables/use-table-valued-parameters-database-engine)
