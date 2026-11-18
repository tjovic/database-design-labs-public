# Lab 8 – Complex Parameters: Passing Collections to Procedures

**Database:** `AdventureWorksENG`

In Labs 3 and 4, we learned that stored procedures and functions package database operations behind a name. Every procedure and function we wrote accepted scalar parameters — one `int`, one `nvarchar`, one `money` at a time.

But what happens when you need to pass **many** values in a single call? How do you insert an invoice header together with twenty line items? How do you delete multiple rows by ID? How do you accept the output of a web API that sends JSON?

This lab compares five approaches to handling collections of data, starting with unsafe SQL concatenation and moving to delimited strings, XML, TVPs, and JSON. By the end, you will know how each approach works and which to consider in different situations.

> [!IMPORTANT]
> **Core idea:** A collection parameter is not a scalar. It needs structure. SQL Server provides multiple envelopes — some safer, some faster, some better suited to the format used by the application. This lab compares unsafe client-side SQL concatenation with four ways to pass collections or structured data: delimited strings, XML, Table-Valued Parameters, and JSON. TVPs pass typed relational rows; XML and JSON represent structured documents.

---

## Learning objectives

After completing this lab, you should be able to:

- identify the two classic collection-parameter problems: the 1:N insert and the batch key operation;
- explain the risks of unsafe SQL concatenation, the benefits of parameterization, and the overhead of separate database calls;
- pass a flat list of values as a delimited string and split them with `STRING_SPLIT`;
- pass hierarchical data as XML, shred it with `.nodes()` and `.value()`, and build it back with `FOR XML PATH`;
- use XML to pass items with several fields, and insert a parent row with its children from one XML document using `.value()`'s singleton syntax and `.nodes()`;
- define a table type with `CREATE TYPE ... AS TABLE` and pass tables as parameters using Table-Valued Parameters (TVPs);
- accept JSON data with `OPENJSON(@json) WITH (...)`, shred it into typed columns, and build JSON output with `FOR JSON PATH` and dotted aliases;
- insert a parent row and its children from a single nested JSON document, using `JSON_VALUE` and `OPENJSON` together;
- compare all five methods (client-side query, delimited string, XML, TVP, JSON) and know which to reach for in different situations.

---

> [!NOTE]
> **Prerequisites:** This lab assumes familiarity with:
>
> - **Stored procedures (Lab 3)** — how to create them, what `EXEC` does, what parameters are.
> - **Functions (Lab 4)** — scalar and table-valued functions.
> - **T-SQL programming (Lab 0)** — variables (Section 2), `IF/BEGIN/END` (Section 4), `WHILE` loops (Section 7), and inline type conversion (Section 6).
>
> XML and JSON formats are introduced inline as needed.

---

> [!NOTE]
> Run each insert example once, except where an exercise explicitly asks you to repeat a call. Repeating an insert may create duplicate rows or fail if a unique constraint prevents duplicates.

Start by selecting the training database:

```sql
USE AdventureWorksENG;
GO
```

---

# Section 1 – The Problem: Passing Multiple Values

In previous labs, we learned how to create stored procedures and pass values through parameters.

Consider this simple procedure:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_GetProduct
    @ProductID int
AS
BEGIN
    SELECT IDProduct, Name, PriceWithoutVAT
    FROM Product
    WHERE IDProduct = @ProductID;
END;
GO
```

We can call it by passing a single product ID:

```sql
EXEC dbo.usp_GetProduct @ProductID = 1;
```

This works because `@ProductID` is a **scalar parameter** — it contains one value.

But what if we want to pass several product IDs in a single procedure call?

For example, we might want to retrieve products **1, 2, and 3**.

We cannot simply pass a list to an `int` parameter:

```sql
-- This does not work
EXEC dbo.usp_GetProduct @ProductID = (1, 2, 3);
```

An `int` parameter expects one integer, not a collection of integers.

We need a way to pass **multiple values through a single parameter**.

This is the main problem we will solve in this lab.

## 1.1 Problem 1 – Working with Multiple IDs

Imagine an application that displays a list of products.

A user selects three products and clicks a button to display their details.

The application knows which products were selected:

```text
Selected product IDs: 1, 2, 3
```

One possible solution is to call the procedure three times:

```sql
EXEC dbo.usp_GetProduct @ProductID = 1;
EXEC dbo.usp_GetProduct @ProductID = 2;
EXEC dbo.usp_GetProduct @ProductID = 3;
```

This works, but the application must make three separate procedure calls.

What if the user selects 100 products?

A better approach would be to pass all selected IDs in **one procedure call** and let SQL Server process them together.

```mermaid
sequenceDiagram
    participant A as Application
    participant P as Stored Procedure
    participant T as Product Table

    A->>P: One procedure call with IDs: 1, 2, 3
    P->>T: SELECT products WHERE IDProduct IN (1, 2, 3)
    T-->>P: Matching product rows
    P-->>A: One result set containing all matches
```

This type of operation is called a **batch operation**.

The same concept applies when we want to update, delete, or retrieve multiple rows using a list of IDs.

> [!NOTE]
> A batch operation processes multiple items together. In SQL Server, we can often use a single set-based SQL statement instead of executing the same operation separately for each item.

## 1.2 Problem 2 – Inserting Related Data

Now consider a more complex example: creating an invoice.

An invoice consists of:

- **One invoice header** — customer, date, invoice number.
- **Multiple invoice items** — products, quantities, and prices.

For example:

**Invoice**

| IDInvoice | CustomerID | InvoiceDate |
|---|---|---|
| 101 | 5 | 2026-11-04 |

**InvoiceItem**

| InvoiceID | ProductID | Quantity | UnitPrice |
|---|---|---|---|
| 101 | 1 | 2 | 199.00 |
| 101 | 2 | 1 | 49.90 |
| 101 | 3 | 5 | 9.99 |

The application needs to send all this information to the database.

We could create separate procedures for inserting the invoice header and each invoice item.

However, this introduces several challenges:

1. The application must make multiple procedure calls.
2. The invoice ID must be passed to every invoice item.
3. If one insert fails, we must ensure that the invoice is not left incomplete.

Ideally, we want to send the entire invoice in **one procedure call**.

```mermaid
flowchart TD
    A["Application"] -->|"One call: header + all items"| B
    subgraph P["Stored Procedure"]
        B["Insert invoice header"] --> C["Get generated invoice ID"]
        C --> D["Insert all items using that ID"]
    end
    D --> E["Return new invoice ID"]
```

The procedure receives the invoice data, inserts the header, and uses its generated ID to link all items to the invoice.

> [!IMPORTANT]
> **One procedure call does not necessarily mean one SQL statement.**
>
> A procedure may execute several SQL statements. One call alone does not ensure that all changes succeed or fail together. In the next lab, we will use transactions to provide that behavior.


## 1.3 The Solution – Complex Parameters

Both examples have something in common.

We need to pass more than one value to a stored procedure:

- A **list of IDs**, such as `1, 2, 3`.
- A **collection of related records**, such as an invoice with multiple items.

These are examples of **complex parameters**.

Unlike scalar parameters, complex parameters can represent collections or structured data.

SQL Server provides several ways to handle this.

In this lab, we will explore five approaches:

| Method | Example | Main idea |
|---|---|---|
| Client-side query building | `WHERE IDProduct IN (1, 2, 3)` | Construct SQL in application code |
| Delimited string | `'1,2,3'` | Pass a string and split it into values |
| XML | `<IDs><ID>1</ID><ID>2</ID><ID>3</ID></IDs>` | Pass structured XML data |
| Table-Valued Parameter (TVP) | A table containing three ID rows | Pass a collection of typed rows |
| JSON | `[1, 2, 3]` | Pass structured JSON data |

All five approaches can represent the same list of product IDs, but they differ in how the data is prepared, transmitted, and processed.

Some approaches are safer, more efficient, or better suited to particular applications than others.

We will begin with SQL statements built by embedding values in application code, then explore parameterized alternatives.

By the end of this lab, you should understand **how to pass collections of data to stored procedures and how to choose an appropriate method for a given situation**.

---

# Section 2 – Method 1: Client-Side Query Building

In Section 1, the user selected products `1`, `2`, and `3`. One possible solution is to construct the SQL statement directly in the application.

## 2.1 Building SQL in Application Code

Consider the following Python example:

```python
product_ids = [1, 2, 3]

# Convert the IDs into the text "1,2,3"
id_list = ",".join(str(product_id) for product_id in product_ids)

# Insert that text into the SQL statement
sql = f"SELECT * FROM Product WHERE IDProduct IN ({id_list})"

# Send the SQL statement to the database
cursor.execute(sql)
```

The application generates this SQL statement:

```sql
SELECT *
FROM Product
WHERE IDProduct IN (1, 2, 3);
```

This example uses a fixed list of integers, so it contains no untrusted user input.

However, **building SQL by inserting untrusted values directly into the SQL text is dangerous**.

## 2.2 SQL Injection

SQL injection occurs when user-provided data becomes part of the SQL command itself.

Consider an application that searches for customers by first and last name:

```python
# UNSAFE — user input is inserted directly into SQL text
first_name = input("Enter first name: ")
last_name = input("Enter last name: ")

sql = (
    f"SELECT * FROM Customer "
    f"WHERE FirstName = '{first_name}' AND LastName = '{last_name}'"
)

cursor.execute(sql)
```

Now imagine the user enters:

```text
First name: Gustavo
Last name: Achong' OR 1=1 --
```

The application generates:

```sql
SELECT *
FROM Customer
WHERE FirstName = 'Gustavo' AND LastName = 'Achong' OR 1=1 --';
```

1. The first `'` closes the original string.
2. `OR 1=1` adds a condition that is always true.
3. `--` starts a comment, so SQL Server ignores the closing quote added by the application.

The query returns **all customers**. The user has changed the meaning of the SQL statement without changing the application code.

### The solution – Parameterized queries

Instead of inserting user input into SQL text, pass the values as parameters:

```python
sql = "SELECT * FROM Customer WHERE FirstName = ? AND LastName = ?"

cursor.execute(sql, (first_name, last_name))
```

The `?` placeholders mark where parameter values belong; the values are supplied separately. SQL Server now treats the input `Achong' OR 1=1 --` as **a value to search for**, not as SQL code.

> [!IMPORTANT]
> Do not put quotes around the `?` placeholders. The database driver handles parameter values.

> [!TIP]
> The optional [`Cyber Lab`](../demos/cyber-lab/) demo shows how an application should be designed to keep user input separate from SQL code.

## 2.3 Why Parameters Alone Are Not Enough

Parameters have one more benefit: when the query text stays the same and only the values change, SQL Server can **reuse the cached execution plan** instead of compiling a new one for every value.

However, a scalar parameter still carries only one value. As we saw in Section 1.1, retrieving 100 products with a parameterized query in a loop still requires **100 calls**:

| Approach | IDs per call | Number of calls |
|---|---|---|
| Parameterized query inside a loop | 1 | 100 |
| Pass a collection | 100 | 1 |

Each call waits for a response from the server, so the communication time adds up — especially when the application and database run on different servers.

## 2.4 The Better Approach

| Problem | Better approach |
|---|---|
| User input can change the SQL command | Pass values as parameters |
| Changing SQL text can reduce execution-plan reuse | Keep query text consistent and use parameters |
| Separate queries require many database calls | Send multiple values together |

We need both: values passed **as parameters**, and many values passed **in one call**. The remaining four methods from Section 1.3 do exactly that — each passes a collection through a single parameter.

We will begin with the simplest format: **delimited strings**.

---

# Section 3 – Method 2: Delimited String Parameters

In Section 1, we wanted to pass several product IDs to a stored procedure using a single parameter.

A simple solution is to combine the IDs into one string, separating them with commas:

```text
1,2,3
```

Instead of passing three separate integers, we pass **one string containing three values**.

Inside the stored procedure, SQL Server splits the string back into individual values.

This technique is called a **delimited string parameter**.

## 3.1 How It Works

Consider the following parameter:

```sql
DECLARE @IDList nvarchar(200) = N'1,2,3';
```

Although it contains three numbers, SQL Server sees it as a single string.

We need to convert it into a collection of values that can be used in a SQL query.

```mermaid
flowchart TD
    A["String parameter: 1,2,3"] --> B["STRING_SPLIT"]
    B --> C["Table with three rows"]
    C --> D["1"]
    C --> E["2"]
    C --> F["3"]
```

SQL Server provides a built-in function called **`STRING_SPLIT`** for this purpose.

## 3.2 The STRING_SPLIT Function

The `STRING_SPLIT` function divides a string into separate values using a specified delimiter.

Its basic syntax is:

```sql
STRING_SPLIT(string, separator)
```

For example:

```sql
SELECT value
FROM STRING_SPLIT('1,2,5,7,11', ',');
```

Result:

| value |
|---|
| 1 |
| 2 |
| 5 |
| 7 |
| 11 |

The function returns a table containing one column named `value`.

Each separated value becomes a row.

Notice that the values are returned as **strings**, even though they look like numbers.

To use them as integers, we can convert them:

```sql
SELECT CAST(value AS int) AS ProductID
FROM STRING_SPLIT('1,2,5,7,11', ',');
```

Now the result contains integer values that can be compared with integer columns in the database.

> [!NOTE]
> `STRING_SPLIT` is available in SQL Server 2016 and later, with database compatibility level 130 or higher.
>
> The function does not guarantee the order of returned rows. If order matters, it must be handled explicitly.

## 3.3 Using STRING_SPLIT in a Query

Let's return to our example from Section 1.

We want to retrieve products with IDs `1`, `2`, and `3`.

First, we can write a normal query:

```sql
SELECT IDProduct, Name, PriceWithoutVAT
FROM Product
WHERE IDProduct IN (1, 2, 3);
```

Now replace the hardcoded list with `STRING_SPLIT`:

```sql
DECLARE @IDList nvarchar(200) = N'1,2,3';

SELECT IDProduct, Name, PriceWithoutVAT
FROM Product
WHERE IDProduct IN
(
    SELECT CAST(value AS int)
    FROM STRING_SPLIT(@IDList, ',')
);
```

Let's examine the process:

1. `@IDList` contains the string `'1,2,3'`.
2. `STRING_SPLIT` separates it into three rows.
3. `CAST` converts each value into an integer.
4. The `IN` operator checks whether `IDProduct` matches any of these values.

The result is the same as the original query, but the list of IDs is now supplied through a variable.

This means we can use the same SQL statement with different lists of IDs.

## 3.4 Passing the List to a Stored Procedure

We can now create a stored procedure that accepts a list of product IDs.

```sql
CREATE OR ALTER PROCEDURE dbo.usp_GetProductsByIDList
    @IDList nvarchar(200)
AS
BEGIN
    SELECT IDProduct, Name, PriceWithoutVAT
    FROM Product
    WHERE IDProduct IN
    (
        SELECT CAST(value AS int)
        FROM STRING_SPLIT(@IDList, ',')
    );
END;
GO
```

Call the procedure:

```sql
EXEC dbo.usp_GetProductsByIDList
    @IDList = N'1,2,3';
```

We can also pass a different list without modifying the procedure:

```sql
EXEC dbo.usp_GetProductsByIDList
    @IDList = N'5,10,15,20';
```

**One parameter. Multiple IDs. One procedure call.**

This solves our first problem: passing a collection of simple values to a stored procedure.

## 3.5 Practical Example – Deleting Multiple Customers

Suppose a user selects three customers and clicks **Delete**.

The application can send their IDs as one comma-separated string. The procedure splits the string and deletes the matching customers using one `DELETE` statement.

### Step 1 – Create the procedure

```sql
CREATE OR ALTER PROCEDURE dbo.usp_DeleteCustomersByIDList
    @IDList nvarchar(200)
AS
BEGIN
    DELETE FROM Customer
    WHERE IDCustomer IN
    (
        SELECT CAST(value AS int)
        FROM STRING_SPLIT(@IDList, ',')
    );
END;
GO
```

### Step 2 – Check the selected customers

For this example, we use customers with IDs `55`, `56`, and `57`.

```sql
SELECT IDCustomer, FirstName, LastName
FROM Customer
WHERE IDCustomer IN (55, 56, 57);
```

> [!NOTE]
> Use the training database. The selected customers must not be referenced by invoices or other records, otherwise a foreign key constraint may prevent deletion.

### Step 3 – Delete the customers

Pass all three IDs through one parameter:

```sql
EXEC dbo.usp_DeleteCustomersByIDList
    @IDList = N'55,56,57';
```

`STRING_SPLIT` separates the string into three values, and `CAST` converts them into integers. The `DELETE` statement removes all matching customers.

### Step 4 – Verify the result

```sql
SELECT IDCustomer, FirstName, LastName
FROM Customer
WHERE IDCustomer IN (55, 56, 57);
```

The query should return no rows.

**Three customer IDs. One parameter. One procedure call.**

## 3.6 Limitations of Delimited Strings

Delimited strings are simple and convenient, but they have several limitations.

| Limitation | Explanation |
|---|---|
| No type safety | Values arrive as text and may require conversion. |
| Invalid values | A value such as `'1,ABC,3'` causes an error when converted to `int` using `CAST`. |
| Delimiter conflicts | A comma cannot safely separate values that may themselves contain commas without additional rules. |
| Limited structure | A string such as `'1,2,3'` represents a flat list, not a collection of records with multiple fields. |
| No guaranteed order | `STRING_SPLIT` does not guarantee that rows are returned in their original order. |

For example, consider an invoice containing several products.

Each invoice item needs multiple values:

| ProductID | Quantity | UnitPrice |
|---|---|---|
| 1 | 2 | 199.00 |
| 2 | 1 | 49.90 |
| 3 | 5 | 9.99 |

We could try to represent this information as a string:

```text
1,2,199.00;2,1,49.90;3,5,9.99
```

But now we need two delimiters:

- `;` to separate invoice items.
- `,` to separate fields within each item.

We would also need additional logic to extract and convert every value.

This quickly becomes difficult to maintain.

**Delimited strings work well for simple lists of values, but they are not ideal for structured data.**

In the next section, we will introduce **XML**, which allows us to represent more complex information using elements, attributes, and nested structures.

---

# Section 4 – Method 3: XML Parameters

In Section 3, we passed a list of IDs as a comma-separated string:

```text
1,2,3
```

This works well when each item is **one value**. But what if each item contains several values?

For example, we may want to insert several customers in one call. Each customer has a first name, a last name, and an email address. A comma-separated string cannot clearly show which value belongs to which field.

We need a format that can represent **structured data**. One solution is **XML (Extensible Markup Language)**.

> [!TIP]
> For a short introduction to both XML and JSON, see the [XML and JSON Primer](../XML-JSON-PRIMER.md).

## 4.1 What Is XML?

XML is a text-based format that describes data using **elements**, **attributes**, and **nested structures**.

```xml
<Customers>
    <Customer FirstName="Nina" LastName="Novak" Email="nina.novak@example.com" />
    <Customer FirstName="Ivan" LastName="Horvat" Email="ivan.horvat@example.com" />
</Customers>
```

The XML document contains:

- A root element: `<Customers>`.
- Two child elements: `<Customer>`.
- Three attributes for each customer: `FirstName`, `LastName`, and `Email`.

Unlike a comma-separated string, XML names every value, so it is clear what each value represents.

XML can also be **nested**. For example, a state can contain its cities:

```xml
<State>
    <Name>Norway</Name>
    <City Name="Oslo" />
    <City Name="Bergen" />
    <City Name="Trondheim" />
</State>
```

### Attributes vs. element text

XML can store a value in two ways:

| Form | Example | XQuery path |
|---|---|---|
| Attribute | `<City Name="Oslo" />` | `@Name` |
| Element text | `<Name>Norway</Name>` | `Name` |

Both forms contain one value. We will read both of them in this section.

SQL Server has a built-in `xml` data type for storing and processing XML documents.

## 4.2 Reading XML in SQL Server

SQL Server provides several methods for working with XML. In this lab, we will focus on two:

| Method | Purpose |
|---|---|
| `.nodes()` | Converts matching XML elements into rows |
| `.value()` | Extracts one value from an XML element or attribute and converts it to a SQL type |

### Step 1 – Convert XML elements into rows

We want one row for each `Customer` element:

```sql
DECLARE @Customers xml = N'
<Customers>
    <Customer FirstName="Nina" LastName="Novak" Email="nina.novak@example.com" />
    <Customer FirstName="Ivan" LastName="Horvat" Email="ivan.horvat@example.com" />
</Customers>';

SELECT
    c.node.query('.') AS CustomerXml
FROM @Customers.nodes('/Customers/Customer') AS c(node);
```

The expression `@Customers.nodes('/Customers/Customer')` selects every `Customer` element inside the root `Customers` element. The syntax `AS c(node)` names the resulting table and its XML column.

The result contains two rows, each holding one XML fragment:

| CustomerXml |
|---|
| `<Customer FirstName="Nina" LastName="Novak" Email="nina.novak@example.com" />` |
| `<Customer FirstName="Ivan" LastName="Horvat" Email="ivan.horvat@example.com" />` |

Here, `.query('.')` only displays the current node, so we can see what each row contains.

> [!NOTE]
> The path `/Customers/Customer` uses **XQuery**, a language for navigating XML:
>
> - `/Customers` — the root element.
> - `/Customers/Customer` — all `Customer` elements inside `Customers`.
> - `@FirstName` — the `FirstName` attribute.
> - `.` — the current XML node.

### Step 2 – Extract values using `.value()`

Instead of XML fragments, we usually want ordinary SQL values:

```sql
DECLARE @Customers xml = N'
<Customers>
    <Customer FirstName="Nina" LastName="Novak" Email="nina.novak@example.com" />
    <Customer FirstName="Ivan" LastName="Horvat" Email="ivan.horvat@example.com" />
</Customers>';

SELECT
    c.node.value('@FirstName', 'nvarchar(50)') AS FirstName,
    c.node.value('@LastName', 'nvarchar(50)') AS LastName,
    c.node.value('@Email', 'nvarchar(50)') AS Email
FROM @Customers.nodes('/Customers/Customer') AS c(node);
```

Result:

| FirstName | LastName | Email |
|---|---|---|
| Nina | Novak | nina.novak@example.com |
| Ivan | Horvat | ivan.horvat@example.com |

**The XML document has been converted into relational rows and columns.**

1. `.nodes('/Customers/Customer')` creates one row for each customer.
2. Each `.value()` reads one attribute from the current customer and converts it to `nvarchar(50)`.

This process is sometimes called **XML shredding**.

### The `[1]` rule

`.value()` always returns **exactly one** SQL value, so its path must select at most one item.

- An attribute such as `@FirstName` on the current node can exist only once, so no `[1]` is needed.
- An element can appear several times, so we must add `[1]` to select the first one: `(Name)[1]`.

When we read from the whole document instead of from a node returned by `.nodes()`, the path starts at the root:

```sql
DECLARE @State xml = N'<State><Name>Norway</Name></State>';

SELECT @State.value('(/State/Name)[1]', 'nvarchar(50)') AS StateName;
```

| StateName |
|---|
| Norway |

Without `[1]`, SQL Server reports that `.value()` requires a singleton.

## 4.3 Passing XML to a Stored Procedure

Now we can use XML as a stored procedure parameter. The following procedure inserts several customers, each with three fields, in one call.

### Step 1 – Create the procedure

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertCustomerBatch
    @Customers xml
AS
BEGIN
    INSERT INTO Customer (FirstName, LastName, Email)
    SELECT
        c.node.value('@FirstName', 'nvarchar(50)'),
        c.node.value('@LastName', 'nvarchar(50)'),
        c.node.value('@Email', 'nvarchar(50)')
    FROM @Customers.nodes('/Customers/Customer') AS c(node);
END;
GO
```

The procedure uses `INSERT INTO ... SELECT`. The XML parameter is converted into rows, and all customers are inserted with one SQL statement — no `WHILE` loop and no separate `INSERT` for each customer.

### Step 2 – Call the procedure

```sql
EXEC dbo.usp_InsertCustomerBatch
    @Customers = N'
<Customers>
    <Customer FirstName="Nina" LastName="Novak" Email="nina.novak@example.com" />
    <Customer FirstName="Ivan" LastName="Horvat" Email="ivan.horvat@example.com" />
    <Customer FirstName="Ana" LastName="Kovac" Email="ana.kovac@example.com" />
</Customers>';

-- Verify
SELECT IDCustomer, FirstName, LastName, Email
FROM Customer
WHERE Email IN (
    N'nina.novak@example.com',
    N'ivan.horvat@example.com',
    N'ana.kovac@example.com'
);
```

**Three customers. Three fields each. One XML parameter. One procedure call.**

## 4.4 Inserting a Parent and Its Children

In Section 1.2, we described the 1:N insert problem: one parent row together with several child rows. XML can carry both in one document.

We will insert a state together with its cities:

```xml
<State>
    <Name>Norway</Name>
    <City Name="Oslo" />
    <City Name="Bergen" />
    <City Name="Trondheim" />
</State>
```

The procedure inserts the state first, then uses its generated ID when inserting the cities.

### Step 1 – Create the procedure

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertStateWithCitiesFromXml
    @State xml
AS
BEGIN
    DECLARE @NewStateID int;

    -- Insert the state (one value: singleton syntax)
    INSERT INTO State (Name)
    VALUES (@State.value('(/State/Name)[1]', 'nvarchar(50)'));

    SET @NewStateID = SCOPE_IDENTITY();

    -- Insert all cities (many rows: .nodes())
    INSERT INTO City (Name, StateID)
    SELECT
        c.node.value('@Name', 'nvarchar(50)'),
        @NewStateID
    FROM @State.nodes('/State/City') AS c(node);

    SELECT @NewStateID AS NewStateID;
END;
GO
```

The procedure uses both reading styles:

- `@State.value('(/State/Name)[1]', ...)` reads **one value** from the document — the state name stored as element text.
- `@State.nodes('/State/City')` turns the **collection** of cities into rows, and `.value('@Name', ...)` reads each city's attribute.

### Step 2 – Call the procedure

```sql
EXEC dbo.usp_InsertStateWithCitiesFromXml
    @State = N'
<State>
    <Name>Norway</Name>
    <City Name="Oslo" />
    <City Name="Bergen" />
    <City Name="Trondheim" />
</State>';

-- Verify
SELECT
    s.IDState,
    s.Name AS StateName,
    c.IDCity,
    c.Name AS CityName
FROM State s
JOIN City c ON c.StateID = s.IDState
WHERE s.Name = N'Norway';
```

The procedure inserts one state and three related cities in a single call.

> [!NOTE]
> If inserting the cities fails, the state may remain in the database. In the next lab, we will use a transaction to keep these operations together.

## 4.5 Generating XML with FOR XML PATH

So far, we have received XML and converted it into SQL rows. SQL Server can also do the opposite: **convert query results into XML**. This is useful when an application or external system expects XML output.

```sql
SELECT
    c.IDCustomer AS [@IDCustomer],
    c.FirstName AS [FirstName],
    c.LastName AS [LastName],
    c.Email AS [Emails/Email]
FROM Customer c
WHERE c.IDCustomer <= 3
FOR XML PATH('Customer'), ROOT('Customers');
```

The result contains one `Customer` element for each row. The first one looks like this:

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

| SQL syntax | XML result |
|---|---|
| `[@IDCustomer]` | Creates an XML attribute |
| `[FirstName]` | Creates a child element |
| `[Emails/Email]` | Creates nested elements |
| `FOR XML PATH('Customer')` | Creates one `Customer` element per row |
| `ROOT('Customers')` | Wraps the result in a root element |

The `/` in a column alias such as `[Emails/Email]` creates nested elements. This is how we build nested XML structures directly from relational data.

## 4.6 Advantages and Limitations of XML

| Advantages | Limitations |
|---|---|
| Supports nested and hierarchical data | More verbose than simpler formats |
| Names every value, so items can have several fields | XML syntax and XQuery require additional learning |
| Built-in `xml` data type in SQL Server | XML processing introduces parsing overhead |
| Can convert XML into relational rows | A missing attribute or element silently becomes `NULL` |
| Supports XML input and output | May be unnecessary when simpler formats are sufficient |

XML remains useful when integrating with systems that already exchange XML documents, such as certain SOAP-based services.

> [!TIP]
> Additional practice: [Exercise 6 of the Complex Parameters Exercises](../exercises/lab08-complex-parameters.md#exercise-6--xml-find-or-create-related-records-advanced) demonstrates a more advanced XML procedure that finds or creates related records across multiple tables.

In the next section, we will explore **Table-Valued Parameters (TVPs)**, which allow us to pass collections of typed rows directly to stored procedures without converting them into XML or delimited strings.

---

# Section 5 – Method 4: Table-Valued Parameters (TVPs)

In the previous sections, we learned how to pass collections of data using delimited strings and XML.

Both approaches allow us to send multiple values through a single parameter.

However, they require SQL Server to extract values from text before using them as relational data.

What if we could pass a **table directly to a stored procedure**?

SQL Server supports exactly this through **Table-Valued Parameters (TVPs)**.

## 5.1 What Is a Table-Valued Parameter?

A Table-Valued Parameter allows a stored procedure to receive multiple rows and columns as one parameter.

Consider our familiar example: we want to retrieve products with IDs `1`, `2`, and `3`.

With a delimited string, we passed:

```sql
@IDList = N'1,2,3'
```

With XML, we could pass:

```xml
<IDs>
    <ID>1</ID>
    <ID>2</ID>
    <ID>3</ID>
</IDs>
```

With a TVP, we pass the values as a table:

| ID |
|---|
| 1 |
| 2 |
| 3 |

The stored procedure can use this table directly in SQL queries, including `SELECT`, `JOIN`, and `WHERE`.

There is no need for `STRING_SPLIT` or XML parsing.

> [!IMPORTANT]
> A TVP is a parameter whose value is a collection of typed rows.
>
> Unlike a scalar parameter, which contains one value, a TVP can contain many rows and multiple columns.

## 5.2 Defining a Table Type

Before using a TVP, we must define its structure.

SQL Server already provides built-in data types such as:

```sql
int
nvarchar(50)
date
money
```

But there is no built-in type representing a table with a column named `ID`.

We must create one.

### Step 1 – Create a user-defined table type

```sql
CREATE TYPE dbo.ProductIDList AS TABLE
(
    ID int PRIMARY KEY
);
GO
```

This statement creates a new table type named `dbo.ProductIDList`.

It defines the structure of a table containing one integer column.

The `PRIMARY KEY` ensures that the same ID cannot appear more than once in a value of this type.

> [!NOTE]
> `CREATE TYPE ... AS TABLE` defines a reusable table structure.
>
> It does not create a regular database table containing product IDs. Instead, it creates a type that can be used to declare table variables and procedure parameters.

### Step 2 – Declare a variable of this type

Now that the type exists, we can declare a variable:

```sql
DECLARE @MyIDs dbo.ProductIDList;
```

This creates a table variable based on our custom type.

We can insert rows into it:

```sql
DECLARE @MyIDs dbo.ProductIDList;

INSERT INTO @MyIDs (ID)
VALUES (1), (2), (3);

SELECT *
FROM @MyIDs;
```

Result:

| ID |
|---|
| 1 |
| 2 |
| 3 |

Notice that `@MyIDs` behaves like a table.

We can insert rows, query its contents, and use it in joins.

The important difference is that it is a **table variable**, not a permanent table stored under a name such as `dbo.Product`.

## 5.3 Passing a Table to a Stored Procedure

Now let's create a procedure that receives our table variable.

```sql
CREATE OR ALTER PROCEDURE dbo.usp_GetProductsByIDs
    @IDs dbo.ProductIDList READONLY
AS
BEGIN
    SELECT
        p.IDProduct,
        p.Name,
        p.PriceWithoutVAT
    FROM Product p
    INNER JOIN @IDs i ON i.ID = p.IDProduct;
END;
GO
```

Notice the parameter declaration:

```sql
@IDs dbo.ProductIDList READONLY
```

It contains three important parts:

| Part | Meaning |
|---|---|
| `@IDs` | Parameter name |
| `dbo.ProductIDList` | User-defined table type |
| `READONLY` | The procedure cannot modify the parameter |

Unlike ordinary scalar parameters, TVPs must be declared with `READONLY`.

### Calling the procedure

We can now pass our table variable to the procedure:

```sql
DECLARE @MyIDs dbo.ProductIDList;

INSERT INTO @MyIDs (ID)
VALUES (1), (2), (3);

EXEC dbo.usp_GetProductsByIDs
    @IDs = @MyIDs;
```

The procedure receives all three IDs and joins them with the `Product` table.

**Three IDs. One table parameter. One procedure call.**

The procedure can accept any number of IDs without changing its definition.

### Why READONLY?

Inside the procedure, we can read the TVP:

```sql
SELECT *
FROM @IDs;
```

However, we cannot modify it:

```sql
-- Not allowed inside a procedure
INSERT INTO @IDs (ID)
VALUES (4);
```

SQL Server requires TVPs to be read-only.

This means that the procedure can use the input data without changing the collection supplied by the caller.

If we need to modify the data, we can copy it into a local table variable or temporary table.

## 5.4 Practical Example – Inserting an Invoice with Multiple Items

Let's return to the invoice problem introduced in Section 1.

An invoice contains:

- One header with customer information, invoice date, and invoice number.
- Multiple items containing products, quantities, and prices.

We want to insert the entire invoice using **one stored procedure call**.

For this example, we will use:

- **Scalar parameters** for the invoice header.
- A **Table-Valued Parameter** for the invoice items.

The header contains a fixed number of values, while the number of items can vary.

### Step 1 – Define the table type

Each invoice item contains three values:

| ProductID | Quantity | UnitPrice |
|---|---|---|
| 1 | 2 | 199.00 |
| 2 | 1 | 49.90 |
| 3 | 5 | 9.99 |

Create a table type representing these items:

```sql
CREATE TYPE dbo.InvoiceLineInput AS TABLE
(
    ProductID int NOT NULL,
    Quantity int NOT NULL,
    UnitPrice money NOT NULL
);
GO
```

Unlike our earlier table type containing only IDs, this type represents **records with multiple columns**.

### Step 2 – Create the procedure

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InvoiceInsert
    @CustomerID int,
    @InvoiceDate date,
    @InvoiceNumber nvarchar(20),
    @Lines dbo.InvoiceLineInput READONLY
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @NewInvoiceID int;

    -- Insert the invoice header
    INSERT INTO Invoice (CustomerID, InvoiceDate, InvoiceNumber)
    VALUES (@CustomerID, @InvoiceDate, @InvoiceNumber);

    -- Get the generated invoice ID
    SET @NewInvoiceID = SCOPE_IDENTITY();

    -- Insert all invoice items
    INSERT INTO InvoiceItem
    (
        InvoiceID,
        ProductID,
        Quantity,
        InitialPrice,
        Discount,
        TotalPrice
    )
    SELECT
        @NewInvoiceID,
        ProductID,
        Quantity,
        UnitPrice,
        0,
        Quantity * UnitPrice
    FROM @Lines;

    -- Return the generated invoice ID
    SELECT @NewInvoiceID AS NewInvoiceID;
END;
GO
```

Let's examine the important parts.

**1. Scalar parameters**

```sql
@CustomerID int,
@InvoiceDate date,
@InvoiceNumber nvarchar(20)
```

These supply the values for the invoice header.

**2. Table-Valued Parameter**

```sql
@Lines dbo.InvoiceLineInput READONLY
```

This supplies all invoice items as typed rows.

**3. SCOPE_IDENTITY()**

```sql
SET @NewInvoiceID = SCOPE_IDENTITY();
```

This retrieves the ID generated when the invoice header was inserted.

Every item needs this ID to reference the same invoice.

**4. Set-based INSERT**

```sql
INSERT INTO InvoiceItem (...)
SELECT ...
FROM @Lines;
```

This inserts all invoice items using one SQL statement. The same `@NewInvoiceID` is assigned to every item.

We do not need a loop.

> [!NOTE]
> In this simplified example, `UnitPrice` becomes `InitialPrice`, `Discount` is set to `0`, and `TotalPrice` is calculated as `Quantity * UnitPrice`.
>
> The invoice number is supplied by the caller through a scalar parameter.

> [!IMPORTANT]
> One procedure call does not automatically make all statements succeed or fail together.
>
> If inserting the items fails, the invoice header may remain in the database. In the next lab, we will use a transaction to keep these operations together.

### Step 3 – Prepare the items and call the procedure

Declare a variable of our table type and fill it with three invoice items:

```sql
DECLARE @InvoiceLines dbo.InvoiceLineInput;

INSERT INTO @InvoiceLines (ProductID, Quantity, UnitPrice)
VALUES
    (1, 2, 199.00),
    (2, 1, 49.90),
    (3, 5, 9.99);

EXEC dbo.usp_InvoiceInsert
    @CustomerID = 1,
    @InvoiceDate = '2026-11-04',
    @InvoiceNumber = N'SO-TEST-001',
    @Lines = @InvoiceLines;
```

Run this entire block together so that `@InvoiceLines` remains in scope.

The procedure receives the header through three scalar parameters and all three items through one TVP.

The procedure returns the generated invoice ID.

### Step 4 – Verify the result

Find the invoice and its items using the invoice number supplied in the procedure call:

```sql
SELECT
    i.IDInvoice,
    i.InvoiceNumber,
    i.InvoiceDate,
    ii.ProductID,
    ii.Quantity,
    ii.InitialPrice,
    ii.TotalPrice
FROM Invoice i
JOIN InvoiceItem ii ON ii.InvoiceID = i.IDInvoice
WHERE i.InvoiceNumber = N'SO-TEST-001';
```

The result should contain three items linked to the same invoice.

> [!NOTE]
> Use an invoice number that does not already exist in the training database.

**One invoice header. Three items. One procedure call.**

## 5.5 Advantages and Limitations of TVPs

| Advantages | Limitations |
|---|---|
| Strong typing — columns have defined SQL data types | Requires a user-defined table type |
| Supports multiple rows and columns | TVP parameters must be `READONLY` |
| Can be used directly in joins and queries | Table types cannot be altered directly |
| Avoids parsing XML or delimited strings | Client applications must support sending TVPs |
| Useful for set-based operations | SQL Server does not maintain column statistics on TVPs |

TVPs are particularly useful when an application needs to pass a collection of relational records directly to SQL Server.

They are commonly used in SQL Server applications, including applications written in .NET.

However, TVPs do not always guarantee the fastest execution plan. SQL Server does not maintain statistics on TVP columns, which can affect optimization for larger collections.

For some workloads, copying TVP data into a temporary table may provide better query optimization.

> [!TIP]
> **When should you use a TVP?**
>
> Use a TVP when you need to pass multiple typed rows to a stored procedure and your database client supports Table-Valued Parameters.
>
> For example:
>
> - Retrieving multiple products by ID.
> - Updating many records in one operation.
> - Inserting multiple invoice items.
> - Passing structured data from a .NET application to SQL Server.

In the next section, we will explore **JSON parameters**, which are especially useful when applications already exchange data in JSON format, such as REST APIs and web applications.

---

# Section 6 – Method 5: JSON Parameters

In the previous sections, we learned how to pass collections of data using delimited strings, XML, and Table-Valued Parameters (TVPs).

These methods are useful when applications need to send multiple values to SQL Server.

However, modern web applications frequently exchange data using **JSON (JavaScript Object Notation)**.

JSON is widely used by REST APIs, web applications, and mobile applications because it is relatively simple, compact, and easy to process.

SQL Server can read JSON, convert it into relational rows, and generate JSON from query results.

In this section, we will learn how to use JSON as a stored procedure parameter.

## 6.1 What Is JSON?

JSON is a text-based format for representing structured data.

It supports objects, arrays, strings, numbers, Boolean values, and `null`.

Consider a customer represented as a JSON object:

```json
{
    "FirstName": "Alice",
    "LastName": "Anderson",
    "Email": "alice@example.com"
}
```

An **object** contains named properties and their values.

We can also represent multiple customers using a JSON array:

```json
[
    {
        "FirstName": "Alice",
        "LastName": "Anderson",
        "Email": "alice@example.com"
    },
    {
        "FirstName": "Bob",
        "LastName": "Brown",
        "Email": "bob@example.com"
    }
]
```

The square brackets `[]` represent an array, while curly brackets `{}` represent objects.

In this example, the array contains two customer objects.

> [!NOTE]
> In SQL Server 2016–2022, JSON is typically stored and passed as `nvarchar(max)`.
>
> SQL Server provides built-in functions for reading and generating JSON. The examples in this lab use these functions and are compatible with SQL Server 2016 or later, provided the database compatibility level supports `OPENJSON` (level 130 or higher).

## 6.2 Reading a Single Value – JSON_VALUE

Let's start with a simple JSON object.

```sql
DECLARE @Customer nvarchar(max) = N'
{
    "FirstName": "Alice",
    "LastName": "Anderson",
    "Email": "alice@example.com"
}';

SELECT
    JSON_VALUE(@Customer, '$.FirstName') AS FirstName,
    JSON_VALUE(@Customer, '$.LastName') AS LastName,
    JSON_VALUE(@Customer, '$.Email') AS Email;
```

Result:

| FirstName | LastName | Email |
|---|---|---|
| Alice | Anderson | alice@example.com |

The `JSON_VALUE` function extracts a single scalar value from a JSON document.

Its basic syntax is:

```sql
JSON_VALUE(json_expression, path)
```

The path tells SQL Server which property to read.

For example:

| JSON path | Meaning |
|---|---|
| `$` | Root of the JSON document |
| `$.FirstName` | Property `FirstName` |
| `$.Email` | Property `Email` |
| `$.Address.City` | Property `City` inside `Address` |

The `$` symbol represents the root of the JSON document, and dots are used to navigate through nested objects.

> [!IMPORTANT]
> `JSON_VALUE` extracts **one scalar value**.
>
> It is useful when we need a specific property, but it does not convert an entire JSON array into multiple SQL rows.

## 6.3 Converting JSON Arrays into Rows – OPENJSON

Now consider a JSON array containing several customers.

We want to convert the array into a normal SQL result set.

SQL Server provides the **`OPENJSON`** function for this purpose.

### Step 1 – Declare a JSON array

```sql
DECLARE @Customers nvarchar(max) = N'
[
    { "FirstName": "Ida", "LastName": "Ibsen", "Email": "ida@example.com" },
    { "FirstName": "Jonas", "LastName": "Jensen", "Email": "jonas@example.com" },
    { "FirstName": "Kari", "LastName": "Kristian", "Email": "kari@example.com" }
]';
```

### Step 2 – Read the array

Without specifying columns, `OPENJSON` returns three default columns:

```sql
DECLARE @IDs nvarchar(max) = N'[1, 2, 3]';

SELECT *
FROM OPENJSON(@IDs);
```

Result:

| key | value | type |
|---|---|---|
| 0 | 1 | 2 |
| 1 | 2 | 2 |
| 2 | 3 | 2 |

The columns represent:

- `key` — the array index, starting at zero.
- `value` — the value of the array element.
- `type` — a numeric code describing the JSON value type (`2` means number).

This is useful for simple arrays, but our customer objects contain multiple properties.

### Step 3 – Define columns with WITH

We can use `WITH (...)` to specify which properties should become SQL columns.

```sql
DECLARE @Customers nvarchar(max) = N'
[
    { "FirstName": "Ida", "LastName": "Ibsen", "Email": "ida@example.com" },
    { "FirstName": "Jonas", "LastName": "Jensen", "Email": "jonas@example.com" },
    { "FirstName": "Kari", "LastName": "Kristian", "Email": "kari@example.com" }
]';

SELECT *
FROM OPENJSON(@Customers)
WITH
(
    FirstName nvarchar(50) '$.FirstName',
    LastName  nvarchar(50) '$.LastName',
    Email     nvarchar(100) '$.Email'
);
```

Result:

| FirstName | LastName | Email |
|---|---|---|
| Ida | Ibsen | ida@example.com |
| Jonas | Jensen | jonas@example.com |
| Kari | Kristian | kari@example.com |

The `WITH` clause defines:

1. The SQL column name.
2. The SQL data type.
3. The JSON path containing the value.

For example:

```sql
FirstName nvarchar(50) '$.FirstName'
```

means: create a column named `FirstName`, convert its value to `nvarchar(50)`, and read it from the `FirstName` property.

**The JSON array has now become a relational result set.**

This process is similar to XML shredding using `.nodes()` and `.value()`.

## 6.4 Passing JSON to a Stored Procedure

Now we can use `OPENJSON` inside a stored procedure.

Our goal is to insert multiple customers using one JSON parameter.

### Step 1 – Create the procedure

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertCustomerBatchFromJson
    @JsonCustomers nvarchar(max)
AS
BEGIN
    INSERT INTO Customer (FirstName, LastName, Email)
    SELECT FirstName, LastName, Email
    FROM OPENJSON(@JsonCustomers)
    WITH
    (
        FirstName nvarchar(50) '$.FirstName',
        LastName  nvarchar(50) '$.LastName',
        Email     nvarchar(100) '$.Email'
    );
END;
GO
```

The procedure receives one string containing JSON data.

`OPENJSON` converts the array into rows, and `INSERT INTO ... SELECT` inserts all customers using one SQL statement.

### Step 2 – Call the procedure

```sql
EXEC dbo.usp_InsertCustomerBatchFromJson
    @JsonCustomers = N'
[
    {
        "FirstName": "Ruđer",
        "LastName": "Bošković",
        "Email": "rudjer.boskovic@example.com"
    },
    {
        "FirstName": "Janica",
        "LastName": "Kostelić",
        "Email": "janica.kostelic@example.com"
    }
]';

-- Verify the inserted customers
SELECT IDCustomer, FirstName, LastName, Email
FROM Customer
WHERE Email IN
(
    N'rudjer.boskovic@example.com',
    N'janica.kostelic@example.com'
);
```

**Two customers. One JSON parameter. One procedure call.**

The procedure can handle a larger array without changing its SQL code.

## 6.5 Working with Nested JSON

Real-world JSON documents often contain nested objects and arrays.

Consider an invoice with several line items:

```json
{
    "Invoice": {
        "CustomerID": 5,
        "InvoiceDate": "2026-11-04",
        "Lines": [
            { "ProductID": 1, "Quantity": 2, "UnitPrice": 199.00 },
            { "ProductID": 2, "Quantity": 1, "UnitPrice": 49.90 },
            { "ProductID": 3, "Quantity": 5, "UnitPrice": 9.99 }
        ]
    }
}
```

This document contains two levels of information:

- **Invoice header** — customer ID and invoice date.
- **Invoice lines** — an array of products, quantities, and prices.

We can read the header using `JSON_VALUE`.

```sql
DECLARE @Json nvarchar(max) = N'
{
    "Invoice": {
        "CustomerID": 5,
        "InvoiceDate": "2026-11-04",
        "Lines": [
            { "ProductID": 1, "Quantity": 2, "UnitPrice": 199.00 },
            { "ProductID": 2, "Quantity": 1, "UnitPrice": 49.90 },
            { "ProductID": 3, "Quantity": 5, "UnitPrice": 9.99 }
        ]
    }
}';

SELECT
    JSON_VALUE(@Json, '$.Invoice.CustomerID') AS CustomerID,
    JSON_VALUE(@Json, '$.Invoice.InvoiceDate') AS InvoiceDate;
```

But what about the `Lines` array?

We can use `OPENJSON` with a path pointing directly to that array:

```sql
SELECT *
FROM OPENJSON(@Json, '$.Invoice.Lines')
WITH
(
    ProductID int '$.ProductID',
    Quantity  int '$.Quantity',
    UnitPrice decimal(10,2) '$.UnitPrice'
);
```

Result:

| ProductID | Quantity | UnitPrice |
|---|---|---|
| 1 | 2 | 199.00 |
| 2 | 1 | 49.90 |
| 3 | 5 | 9.99 |

Notice the second argument:

```sql
'$.Invoice.Lines'
```

It tells SQL Server to start reading from the `Lines` array inside the `Invoice` object.

### Reading both levels with CROSS APPLY

> [!TIP]
> This is an optional advanced example. For the core lab, focus on reading the header with `JSON_VALUE` and the items with `OPENJSON`. Run the following query in the same batch as the declaration of `@Json`.

Sometimes we want to combine the invoice header and line items in one result.

We can use two `OPENJSON` operations connected by `CROSS APPLY`.

```sql
SELECT
    inv.CustomerID,
    inv.InvoiceDate,
    line.ProductID,
    line.Quantity,
    line.UnitPrice
FROM OPENJSON(@Json, '$.Invoice')
WITH
(
    CustomerID int '$.CustomerID',
    InvoiceDate date '$.InvoiceDate',
    LinesJson nvarchar(max) '$.Lines' AS JSON
) AS inv
CROSS APPLY OPENJSON(inv.LinesJson)
WITH
(
    ProductID int '$.ProductID',
    Quantity int '$.Quantity',
    UnitPrice decimal(10,2) '$.UnitPrice'
) AS line;
```

Result:

| CustomerID | InvoiceDate | ProductID | Quantity | UnitPrice |
|---|---|---|---|---|
| 5 | 2026-11-04 | 1 | 2 | 199.00 |
| 5 | 2026-11-04 | 2 | 1 | 49.90 |
| 5 | 2026-11-04 | 3 | 5 | 9.99 |

Let's break down the process:

1. The first `OPENJSON` reads the invoice header.
2. `AS JSON` preserves the nested `Lines` array as JSON text.
3. `CROSS APPLY` passes that array to the second `OPENJSON`.
4. The second `OPENJSON` converts each line item into a row.
5. The result combines the header values with each line item.

> [!NOTE]
> `CROSS APPLY` allows the right-hand expression to use values from the current row on the left.
>
> In this example, it processes the `LinesJson` array belonging to each invoice row.
>
> Also notice that the aliases `AS inv` and `AS line` appear **after** the `WITH (...)` clauses.

## 6.6 Inserting Related Records from JSON

We can also use JSON to insert a parent record together with its child records.

Consider a state containing several cities:

```json
{
    "StateName": "Sweden",
    "Cities": [
        "Stockholm",
        "Gothenburg",
        "Malmo"
    ]
}
```

We want to insert:

- One record into the `State` table.
- Three records into the `City` table, linked to the new state.

The procedure inserts the state first, then uses its generated ID when inserting the cities.

### Step 1 – Create the procedure

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InsertStateWithCities
    @Json nvarchar(max)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @NewStateID int;
    DECLARE @StateName nvarchar(50);

    SET @StateName = JSON_VALUE(@Json, '$.StateName');

    -- Insert the state
    INSERT INTO State (Name)
    VALUES (@StateName);

    SET @NewStateID = SCOPE_IDENTITY();

    -- Insert all cities
    INSERT INTO City (Name, StateID)
    SELECT value, @NewStateID
    FROM OPENJSON(@Json, '$.Cities');

    SELECT @NewStateID AS NewStateID;
END;
GO
```

The procedure uses:

- `JSON_VALUE` to extract the state name.
- `SCOPE_IDENTITY()` to retrieve the new state ID.
- `OPENJSON` to convert the city array into rows.

Notice that `OPENJSON` is used without `WITH` because the `Cities` array contains simple strings rather than objects.

### Step 2 – Call the procedure

```sql
EXEC dbo.usp_InsertStateWithCities
    @Json = N'
{
    "StateName": "Sweden",
    "Cities": [
        "Stockholm",
        "Gothenburg",
        "Malmo"
    ]
}';
```

Verify the inserted state and cities:

```sql
SELECT
    s.IDState,
    s.Name AS StateName,
    c.IDCity,
    c.Name AS CityName
FROM State s
JOIN City c ON c.StateID = s.IDState
WHERE s.Name = N'Sweden';
```

The procedure inserts one state and three related cities in a single call.

> [!NOTE]
> If inserting the cities fails, the state may remain in the database. In the next lab, we will use a transaction to keep these operations together.

This is the same parent-child pattern we previously used with XML and Table-Valued Parameters. The difference is that the data now arrives as JSON.

## 6.7 Generating JSON with FOR JSON PATH

So far, we have converted JSON into SQL rows.

SQL Server can also perform the opposite operation: convert query results into JSON.

This is useful when sending data to REST APIs or other applications that expect JSON.

Consider this query:

```sql
SELECT
    c.IDCustomer AS [Customer.IDCustomer],
    c.FirstName AS [Customer.FirstName],
    c.LastName AS [Customer.LastName],
    c.Email AS [Customer.Email]
FROM Customer c
WHERE c.IDCustomer < 5
FOR JSON PATH, ROOT('Customers');
```

The result has a structure similar to:

```json
{
    "Customers": [
        {
            "Customer": {
                "IDCustomer": 1,
                "FirstName": "Gustavo",
                "LastName": "Achong",
                "Email": "gustavo0@adventure-works.com"
            }
        }
    ]
}
```

The important parts are:

| SQL syntax | Purpose |
|---|---|
| `[Customer.IDCustomer]` | Creates a nested `Customer` object with an `IDCustomer` property |
| `[Customer.FirstName]` | Adds `FirstName` to the nested object |
| `FOR JSON PATH` | Converts query rows into JSON objects |
| `ROOT('Customers')` | Wraps the resulting array in a root object |

Notice that **dots in column aliases create nested JSON objects**.

For example:

```sql
c.Email AS [Customer.Contact.Email]
```

produces a structure like:

```json
{
    "Customer": {
        "Contact": {
            "Email": "alice@example.com"
        }
    }
}
```

This is similar to `FOR XML PATH`, but JSON uses dots instead of slashes to define nested structures.

## 6.8 Advantages and Limitations of JSON

| Advantages | Limitations |
|---|---|
| Widely used by web applications and REST APIs | JSON input must be parsed |
| Supports objects, arrays, and nested structures | Data types are checked during extraction and conversion |
| No custom table type is required | Missing properties may produce `NULL` |
| Can represent complex data in one parameter | Additional validation may be required |
| Supports both input and output | Large JSON documents introduce parsing overhead |

JSON is particularly useful when the application already works with JSON data.

For example, a REST API can receive a JSON request and pass the relevant document to a stored procedure.

However, JSON is not always the best choice.

When an application can pass typed relational rows directly to SQL Server, **Table-Valued Parameters may be more appropriate**.

> [!TIP]
> **Real-world example:** The optional [`OBP REST Demo`](../demos/obp-rest-demo/) demonstrates how a FastAPI application receives JSON through an HTTP request and uses a SQL Server stored procedure to insert an invoice with multiple items.

In the next section, we will compare all five approaches and discuss when each method is most appropriate.

---

# Section 7 – Choosing the Right Method

Throughout this lab, we explored five approaches to passing collections of data to SQL Server.

Each method solves a similar problem: **how to send multiple values or structured records to a stored procedure in a single call**.

However, the methods differ in how data is represented, processed, and validated.

The goal is not to memorize five different solutions. It is to understand **which method is appropriate for a particular situation**.

## 7.1 One List, Five Approaches

Let's return to the example from Section 1.

An application needs to retrieve products with IDs `1`, `2`, and `3`.

We can represent the same collection in several ways:

| Method | Example |
|---|---|
| Client-side query building | `WHERE IDProduct IN (1, 2, 3)` |
| Delimited string | `'1,2,3'` |
| XML | `<IDs><ID>1</ID><ID>2</ID><ID>3</ID></IDs>` |
| Table-Valued Parameter | A table containing three rows |
| JSON | `[1, 2, 3]` |

The values are identical. Only their representation changes.

For stored procedures, the corresponding parameter declarations are:

| Method | Parameter declaration |
|---|---|
| Client-side query building | No collection parameter; values are embedded in SQL text |
| Delimited string | `@IDList nvarchar(200)` |
| XML | `@IDs xml` |
| TVP | `@IDs dbo.ProductIDList READONLY` |
| JSON | `@Json nvarchar(max)` |

Delimited strings and JSON are both passed as text, but their contents have different structures. This lab uses `nvarchar(200)` for the ID lists and `nvarchar(max)` for JSON documents.

XML has its own SQL Server data type, while TVPs use a user-defined table type.

> [!NOTE]
> Client-side query building is included for comparison, but unsafe concatenation of user input into SQL statements should be avoided.
>
> Parameterized SQL can be generated dynamically when necessary. The important rule is to keep untrusted values separate from executable SQL code.

## 7.2 Comparing the Methods

The following table summarizes the main characteristics of each approach.

| Method | Data Structure | Type Safety | Main Advantage | Main Limitation |
|---|---|---|---|---|
| Client-side SQL concatenation | SQL text | None for concatenated values | Simple to construct | SQL injection risk with untrusted input |
| Delimited string | Flat list | Values arrive as text | Simple for lists of IDs | Requires splitting and conversion |
| XML | Hierarchical | XML type; extracted values require conversion | Supports complex nested structures | Verbose syntax and parsing overhead |
| TVP | Relational rows and columns | Strong | Typed data can be used directly in SQL | Requires a predefined table type |
| JSON | Objects and arrays | Values are converted during extraction | Natural format for web integration | Requires parsing and validation |

There is no single method that is always best.

The appropriate choice depends on:

- The structure of the data.
- The application sending the data.
- The need for type safety.
- The database operations being performed.
- Performance and integration requirements.

## 7.3 Common Use Cases

Let's examine four practical situations.

### Scenario 1 – A simple list of IDs

An application needs to retrieve several products.

Input:

```text
1,2,3,4,5
```

A delimited string can be sufficient:

```sql
EXEC dbo.usp_GetProductsByIDList
    @IDList = N'1,2,3,4,5';
```

The procedure uses `STRING_SPLIT` to convert the string into rows.

**Why?** The input is a simple list, and the format is easy to process.

If the client supports TVPs, a TVP is another good option, particularly when type safety is important.

### Scenario 2 – Inserting multiple invoice items

An application needs to insert an invoice containing several products.

Each item has:

- Product ID.
- Quantity.
- Unit price.

A **Table-Valued Parameter** is a natural choice when the client supports it.

The application passes the invoice items as typed rows, and the procedure can insert them using `INSERT INTO ... SELECT`.

**Why?** The data is already relational and contains multiple columns.

### Scenario 3 – Receiving data from a REST API

A web application sends a JSON document:

```json
{
    "CustomerID": 5,
    "Items": [
        { "ProductID": 1, "Quantity": 2 },
        { "ProductID": 2, "Quantity": 1 }
    ]
}
```

SQL Server can process this document using `JSON_VALUE` and `OPENJSON`.

**Why?** JSON is already the format used by the API.

Depending on the application architecture, the backend could also convert the JSON into a TVP before calling SQL Server.

Both designs are valid.

### Scenario 4 – Integration with an XML-based system

An external system sends:

```xml
<Products>
    <Product ID="1" Quantity="2" />
    <Product ID="2" Quantity="1" />
</Products>
```

A stored procedure can accept an `xml` parameter and use `.nodes()` and `.value()` to extract the data.

**Why?** The source system already uses XML, so SQL Server can process the existing format directly.

This is particularly useful when integrating with XML-based services and legacy systems.

## 7.4 How to Choose

Use the following decision diagram as a general guide.

```mermaid
flowchart TD
    A["Need to pass multiple values or records?"]
    A --> B{"What format does the source use?"}

    B -->|"XML"| C["Consider XML"]
    B -->|"JSON"| D{"Can the backend transform the data?"}
    B -->|"Typed rows"| E["Consider TVP"]
    B -->|"Simple text list"| F{"Only a flat list?"}

    D -->|"Yes"| G["JSON or TVP"]
    D -->|"No / direct JSON input"| H["Use JSON"]

    F -->|"Yes"| I["Delimited string or TVP"]
    F -->|"No"| J["Use a structured format"]
```

This diagram is a guideline, not a strict rule.

For example, a REST API may receive JSON, convert it into typed objects, and pass those objects to SQL Server using a TVP.

The choice depends on where data conversion should happen and how the application is designed.

## 7.5 Key Takeaways

The most important concepts from this lab are:

**1. Scalar parameters and collection parameters solve different problems.**

A scalar parameter represents one value. A collection parameter can represent multiple values or records.

**2. Avoid unsafe SQL concatenation.**

Use parameterized queries or properly defined stored procedure parameters to keep data separate from executable SQL code.

**3. Delimited strings are suitable for simple lists.**

Use `STRING_SPLIT` to convert the string into rows. Remember that values may require type conversion.

**4. XML supports structured and hierarchical data.**

Use `.nodes()` and `.value()` to extract data and `FOR XML PATH` to generate XML output.

**5. TVPs allow typed rows to be passed directly to procedures.**

Define a table type using `CREATE TYPE ... AS TABLE` and use it as a `READONLY` parameter.

**6. JSON is useful for modern application integration.**

Use `JSON_VALUE` for individual scalar values, `OPENJSON` for arrays and objects, and `FOR JSON PATH` to generate JSON output.

> [!IMPORTANT]
> **Remember the principle, not just the syntax.**
>
> When choosing a method, first consider the structure of the data and how it arrives at the database.
>
> A simple list, a collection of relational rows, and a nested document may require different approaches.

---

## Check your understanding

1. What is the 1:N insert problem, and why is it hard without collection parameters?
2. Why should untrusted values be passed as parameters, and why is a parameterized query in a loop still not enough for 100 IDs?
3. What does `STRING_SPLIT` return, and what type is the `value` column?
4. When you use XML, what does `@Name` mean in `.value('@Name', 'nvarchar(50)')`?
5. When you use `FOR XML PATH`, how do you create nested elements in the output?
6. Why is `READONLY` mandatory on TVP parameters, and what do you do if you need to modify the input?
7. In `OPENJSON(@Json, '$.Invoice')`, what does `'$.Invoice'` do?
8. How would you use `FOR JSON PATH` to build nested JSON with dotted aliases?
9. Compare TVP and JSON: when would you pick each one?

<details>
<summary>Show answers</summary>

1. **1:N insert** — An invoice header and its line items must be inserted together. A simple implementation using a separate procedure call for every row would require one call for the header and twenty calls for twenty items. A collection parameter allows one call to carry all items. Ensuring that all related inserts succeed or fail together is a separate concern, covered in the next lab.

2. **Parameters and round-trips** — Passing untrusted values as parameters keeps data separate from executable SQL code and lets SQL Server reuse the execution plan. But a scalar parameter carries one value, so 100 IDs still mean 100 calls. A collection parameter sends all IDs in one call.

3. **STRING_SPLIT returns** — With the two-argument syntax used in this lab, it returns a table with one column named `value`. The column is `nvarchar` if either input argument is `nvarchar` or `nchar`; otherwise it is `varchar`. For example, `STRING_SPLIT('1,2,5', ',')` returns three `varchar` values: `1`, `2`, and `5`. They are strings until converted to a numeric type.

4. **`@Name` in XML** — It reads an **attribute** named `Name` on the current node. To read a child element instead, use its name with `[1]`, for example `(Name)[1]`, as explained in Section 4.2.

5. **Nested elements in FOR XML PATH** — Use a **slash** in the column alias. `[Emails/Email]` produces `<Emails><Email>...</Email></Emails>`. (This is different from `FOR JSON PATH`, which uses **dots** instead of slashes for the same purpose — see question 8.)

6. **`READONLY` is required** — SQL Server requires TVPs to be input-only, read-only parameters. The procedure can query the rows but cannot insert, update, or delete rows in the parameter. If modifications are needed, copy the data into a local table variable or temporary table and modify the copy.

7. **`'$.Invoice'` in OPENJSON** — It sets the **starting point** for shredding. Instead of starting at the document root (`$`), start at the `Invoice` property. All column paths in the `WITH` clause are then relative to each row starting from that point.

8. **Dotted aliases in FOR JSON PATH** — Column aliases like `[Invoice.IDCustomer]` or `[Invoice.Lines.ProductID]` create nested objects. Each dot is one level of nesting. `[A.B.C]` produces `{ "A": { "B": { "C": ... } } }`.

9. **TVP** is a good choice for passing typed relational data when the database client supports it. **JSON** is useful when data already arrives in JSON format, particularly through web APIs. The best choice depends on the application architecture and workload.

</details>

---

# What You Should Know After This Lab

**Collection parameters are not scalars.** A scalar is one value. A collection is many. SQL Server provides multiple envelopes for different situations.

**Keep untrusted values separate from SQL code.** Use parameterized queries or properly implemented stored procedures. Dynamic SQL can be valid when values are passed as parameters rather than concatenated into the statement.

**Delimited strings suit simple flat lists.** Use `STRING_SPLIT` to produce rows and convert values as needed. Avoid this approach if values may contain the delimiter and no escaping rules are defined.

**XML handles nesting and structure.** Use `.nodes()` to shred, `.value()` to extract columns, `FOR XML PATH` to build it back. It is verbose on the wire but standard and self-documenting.

**Table-Valued Parameters (TVPs)** pass typed relational rows. Define a type with `CREATE TYPE ... AS TABLE`, then use it as a `READONLY` parameter. TVPs are a natural choice for calls between T-SQL procedures and for clients that support them, including .NET. Performance depends on the workload.

**JSON fits applications that already exchange JSON.** Use `OPENJSON ... WITH (...)` to extract typed rows and `FOR JSON PATH` with dotted aliases to generate nested objects. A backend can pass JSON to SQL Server or transform it into a TVP.

## The Complete Comparison

| Method | Use When | Why |
|--------|----------|-----|
| **Unsafe SQL concatenation** | Avoid embedding untrusted values in SQL text | Use parameterized statements instead. |
| **Delimited string** | Flat list of IDs, simplicity over type safety | Simple, small on wire. No structure needed. |
| **XML** | Hierarchical data; interop with XML systems | Standard, self-documenting. Verbose on wire. |
| **TVP** | Typed relational data; client supports TVPs | Strong typing, multiple columns, direct use in SQL. |
| **JSON** | Applications and services that already exchange JSON | Supports objects, arrays, and nested data without a custom table type. |

Use the decision flowchart in Section 7 as a guide. Consider TVPs for typed relational rows, JSON or XML when the source already uses those formats, and delimited strings for simple flat lists. Choose according to the client, data structure, and workload.

---

## Additional practice

Exercises for this lab are in [Complex Parameters Exercises](../exercises/lab08-complex-parameters.md), grouped by method: delimited strings, XML, `FOR XML PATH`, Table-Valued Parameters, and JSON.
