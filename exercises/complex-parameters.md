# Complex Parameters Exercises

**Database:** `AdventureWorksENG`

These exercises extend the material from [Lab 8 – Complex Parameters](../labs/lab08-complex-parameters.md). They cover delimited strings, XML, and scenarios where you must choose the right method for the job.

---

## Exercise 1 — Manual String Splitter [ADVANCED]

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

## Exercise 2 — XML with Nested Structure [INTERMEDIATE]

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

## Exercise 3 — Choose the Right Method [INTERMEDIATE]

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

## Exercise 4 — Delimited String with Validation [INTERMEDIATE]

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

## Exercise 5 — FOR XML PATH: Build a Price List [INTERMEDIATE]

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

# Cleanup

Remove any test procedures, functions, and tables created during these exercises. (Each exercise's solution already cleans up most of these inline; this is a safety net.)

```sql
DROP PROCEDURE IF EXISTS dbo.usp_InsertEmployeeHierarchy;
DROP PROCEDURE IF EXISTS dbo.usp_GetProductsByIDListWithValidation;
DROP FUNCTION IF EXISTS dbo.fn_SplitInts;
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
