# Index Lab – Demo Database Setup

This script creates and populates the demo database used in the indexing lab.

The goal is to create a database large enough to make inefficient access paths clearly visible, while still being small enough to generate in a few minutes on a typical lab computer.

## What the script creates

The demo uses a simple sales model:

- `Customer`
- `Category`
- `Product`
- `SalesOrder`
- `SalesOrderItem`

The two large transactional tables are generated with:

- **10,000,000** rows in `SalesOrder`
- **40,000,000** rows in `SalesOrderItem`

The smaller tables have clustered primary keys. The two large tables are intentionally created as **heaps**.

This is not intended as an ideal production design. It is deliberate: the lab starts with inefficient physical access paths so that the effect of adding indexes can be measured.

## Database file sizes

The database is pre-sized to:

- data file: **4096 MB**
- transaction log: **512 MB**

Pre-sizing avoids repeated autogrowth while the data is being generated.

The database uses the `SIMPLE` recovery model because this is a disposable teaching database. Data is inserted in batches and `CHECKPOINT` is issued between batches so that transaction log space can be reused.

> On the machine used to prepare this lab, data generation took approximately two minutes. Actual time depends on CPU, storage, memory, and SQL Server configuration.

---

## Full setup script

> **Warning:** The script drops the existing `IndexLab` database if it already exists.

```sql
USE master;
GO

/* ============================================================
   1. Recreate the database
   ============================================================ */

IF DB_ID(N'IndexLab') IS NOT NULL
BEGIN
    ALTER DATABASE IndexLab
        SET SINGLE_USER
        WITH ROLLBACK IMMEDIATE;

    DROP DATABASE IndexLab;
END;
GO

CREATE DATABASE IndexLab;
GO

ALTER DATABASE IndexLab
SET RECOVERY SIMPLE;
GO

/*
    Pre-size the files so SQL Server does not need to repeatedly
    grow them while the demo data is being generated.

    Increasing the file size does NOT make queries slower by itself.
    It only reserves disk space in advance.
*/

ALTER DATABASE IndexLab
MODIFY FILE
(
    NAME = N'IndexLab',
    SIZE = 4096MB,
    FILEGROWTH = 512MB
);
GO

ALTER DATABASE IndexLab
MODIFY FILE
(
    NAME = N'IndexLab_log',
    SIZE = 512MB,
    FILEGROWTH = 128MB
);
GO

USE IndexLab;
GO


/* ============================================================
   2. Create the schema
   ============================================================ */

CREATE TABLE dbo.Category
(
    CategoryId   int         NOT NULL,
    CategoryName varchar(50) NOT NULL,

    CONSTRAINT PK_Category
        PRIMARY KEY CLUSTERED (CategoryId)
);
GO

CREATE TABLE dbo.Product
(
    ProductId    int           NOT NULL,
    ProductName  varchar(100)  NOT NULL,
    CategoryId   int           NOT NULL,
    ListPrice    decimal(10,2) NOT NULL,

    CONSTRAINT PK_Product
        PRIMARY KEY CLUSTERED (ProductId)
);
GO

CREATE TABLE dbo.Customer
(
    CustomerId int         NOT NULL,
    FirstName  varchar(30) NOT NULL,
    LastName   varchar(40) NOT NULL,
    City       varchar(50) NOT NULL,
    Segment    varchar(20) NOT NULL,

    CONSTRAINT PK_Customer
        PRIMARY KEY CLUSTERED (CustomerId)
);
GO

/*
    Intentionally created as a heap.
    Indexes will be added later during the lab.
*/
CREATE TABLE dbo.SalesOrder
(
    SalesOrderId bigint        NOT NULL,
    CustomerId   int           NOT NULL,
    OrderDate    date          NOT NULL,
    Status       varchar(12)   NOT NULL,
    TotalAmount  decimal(12,2) NOT NULL
);
GO

/*
    Intentionally created as a heap.
*/
CREATE TABLE dbo.SalesOrderItem
(
    SalesOrderItemId bigint        NOT NULL,
    SalesOrderId     bigint        NOT NULL,
    ProductId        int           NOT NULL,
    Quantity         smallint      NOT NULL,
    UnitPrice        decimal(10,2) NOT NULL
);
GO


/* ============================================================
   3. Create a helper Numbers table
   ============================================================ */

/*
    The Numbers table contains integers from 1 to 100,000.

    It allows the large tables to be populated using set-based
    INSERT statements instead of inserting rows one at a time.
*/

CREATE TABLE dbo.Numbers
(
    n int NOT NULL,

    CONSTRAINT PK_Numbers
        PRIMARY KEY CLUSTERED (n)
);
GO

WITH
E1(n) AS
(
    SELECT n
    FROM
    (
        VALUES
            (0),(1),(2),(3),(4),
            (5),(6),(7),(8),(9)
    ) AS d(n)
),
E2(n) AS
(
    SELECT 0
    FROM E1 AS a
    CROSS JOIN E1 AS b
),
E4(n) AS
(
    SELECT 0
    FROM E2 AS a
    CROSS JOIN E2 AS b
),
E5(n) AS
(
    SELECT 0
    FROM E4 AS a
    CROSS JOIN E1 AS b
),
N(n) AS
(
    SELECT
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL))
    FROM E5
)
INSERT INTO dbo.Numbers(n)
SELECT n
FROM N;
GO


/* ============================================================
   4. Generate categories
   ============================================================ */

INSERT INTO dbo.Category
(
    CategoryId,
    CategoryName
)
SELECT
    n,
    CONCAT('Category ', n)
FROM dbo.Numbers
WHERE n <= 100;
GO


/* ============================================================
   5. Generate products
   ============================================================ */

INSERT INTO dbo.Product
(
    ProductId,
    ProductName,
    CategoryId,
    ListPrice
)
SELECT
    n,
    CONCAT('Product ', n),
    1 + ((n * 37 + 11) % 100),
    CAST
    (
        5.00 + ((n * 73 + 17) % 50000) / 100.0
        AS decimal(10,2)
    )
FROM dbo.Numbers
WHERE n <= 30000;
GO


/* ============================================================
   6. Generate customers
   ============================================================ */

/*
    The generated data is intentionally not perfectly uniform.

    City distribution:
        Zagreb       ~35%
        Split        ~15%
        Rijeka       ~10%
        Osijek        ~8%
        Zadar         ~6%
        Other        ~26%

    Segment distribution:
        Retail       ~70%
        SMB          ~20%
        Enterprise   ~10%

    These distributions will be useful later when discussing
    selectivity and query optimization.
*/

INSERT INTO dbo.Customer
(
    CustomerId,
    FirstName,
    LastName,
    City,
    Segment
)
SELECT
    n,
    CONCAT('FirstName', 1 + ((n * 17) % 5000)),
    CONCAT('LastName', 1 + ((n * 31) % 10000)),

    CASE
        WHEN (n * 13) % 100 < 35 THEN 'Zagreb'
        WHEN (n * 13) % 100 < 50 THEN 'Split'
        WHEN (n * 13) % 100 < 60 THEN 'Rijeka'
        WHEN (n * 13) % 100 < 68 THEN 'Osijek'
        WHEN (n * 13) % 100 < 74 THEN 'Zadar'
        ELSE 'Other'
    END,

    CASE
        WHEN (n * 19) % 100 < 70 THEN 'Retail'
        WHEN (n * 19) % 100 < 90 THEN 'SMB'
        ELSE 'Enterprise'
    END
FROM dbo.Numbers
WHERE n <= 100000;
GO


/* ============================================================
   7. Generate 10 million sales orders
   ============================================================ */

/*
    Rows are inserted in batches of 100,000.

    Each INSERT statement is its own transaction.
    CHECKPOINT allows reusable transaction log space to be
    reclaimed while the database is in SIMPLE recovery mode.

    The data is intentionally skewed:
        - 60% of orders belong to the first 10,000 customers.
        - order statuses have different frequencies.
        - order dates are distributed across approximately
          five years.
*/

SET NOCOUNT ON;
GO

DECLARE
    @TotalRows     bigint = 10000000,
    @BatchSize     int    = 100000,
    @FirstId       bigint = 1,
    @RowsThisBatch int;

DECLARE @StartedAt datetime2 = SYSDATETIME();

WHILE @FirstId <= @TotalRows
BEGIN

    SET @RowsThisBatch =
        CASE
            WHEN @TotalRows - @FirstId + 1 > @BatchSize
                THEN @BatchSize
            ELSE CAST(@TotalRows - @FirstId + 1 AS int)
        END;

    INSERT INTO dbo.SalesOrder
    (
        SalesOrderId,
        CustomerId,
        OrderDate,
        Status,
        TotalAmount
    )
    SELECT
        o.SalesOrderId,

        CASE
            WHEN ((o.SalesOrderId * 37 + 11) % 100) < 60
                THEN 1 + ((o.SalesOrderId * 48271 + 17) % 10000)
            ELSE
                10001 + ((o.SalesOrderId * 69621 + 13) % 90000)
        END,

        DATEADD
        (
            day,
            CAST((o.SalesOrderId * 97 + 13) % 1826 AS int),
            CAST('20210101' AS date)
        ),

        CASE
            WHEN ((o.SalesOrderId * 31 + 7) % 100) < 80
                THEN 'Completed'
            WHEN ((o.SalesOrderId * 31 + 7) % 100) < 90
                THEN 'Processing'
            WHEN ((o.SalesOrderId * 31 + 7) % 100) < 97
                THEN 'Cancelled'
            ELSE 'Review'
        END,

        CAST
        (
            25 + ((o.SalesOrderId * 71 + 19) % 100000) / 100.0
            AS decimal(12,2)
        )

    FROM
    (
        SELECT
            @FirstId + CAST(n AS bigint) - 1 AS SalesOrderId
        FROM dbo.Numbers
        WHERE n <= @RowsThisBatch
    ) AS o;

    SET @FirstId += @RowsThisBatch;

    CHECKPOINT;

    IF (@FirstId - 1) % 1000000 = 0
    BEGIN
        PRINT CONCAT
        (
            'SalesOrder rows generated: ',
            FORMAT(@FirstId - 1, 'N0')
        );
    END;

END;

PRINT CONCAT
(
    'SalesOrder generation completed in ',
    DATEDIFF(second, @StartedAt, SYSDATETIME()),
    ' seconds.'
);
GO


/* ============================================================
   8. Generate 40 million sales order items
   ============================================================ */

/*
    Four order items are generated for every sales order.

    The table remains a heap and no index is created on
    SalesOrderId. This is intentional and will become important
    when joins are analyzed later in the lab.
*/

SET NOCOUNT ON;
GO

DECLARE
    @OrderCount      bigint = 10000000,
    @ItemsPerOrder   int    = 4,
    @TotalRows       bigint,
    @BatchSize       int    = 100000,
    @FirstId         bigint = 1,
    @RowsThisBatch   int;

SET @TotalRows = @OrderCount * @ItemsPerOrder;

DECLARE @StartedAt datetime2 = SYSDATETIME();

WHILE @FirstId <= @TotalRows
BEGIN

    SET @RowsThisBatch =
        CASE
            WHEN @TotalRows - @FirstId + 1 > @BatchSize
                THEN @BatchSize
            ELSE CAST(@TotalRows - @FirstId + 1 AS int)
        END;

    INSERT INTO dbo.SalesOrderItem
    (
        SalesOrderItemId,
        SalesOrderId,
        ProductId,
        Quantity,
        UnitPrice
    )
    SELECT
        i.SalesOrderItemId,
        ((i.SalesOrderItemId - 1) / @ItemsPerOrder) + 1,
        1 + ((i.SalesOrderItemId * 48271 + 17) % 30000),
        1 + ((i.SalesOrderItemId * 13 + 3) % 5),

        CAST
        (
            5 + ((i.SalesOrderItemId * 73 + 29) % 50000) / 100.0
            AS decimal(10,2)
        )

    FROM
    (
        SELECT
            @FirstId + CAST(n AS bigint) - 1 AS SalesOrderItemId
        FROM dbo.Numbers
        WHERE n <= @RowsThisBatch
    ) AS i;

    SET @FirstId += @RowsThisBatch;

    CHECKPOINT;

    IF (@FirstId - 1) % 5000000 = 0
    BEGIN
        PRINT CONCAT
        (
            'SalesOrderItem rows generated: ',
            FORMAT(@FirstId - 1, 'N0')
        );
    END;

END;

PRINT CONCAT
(
    'SalesOrderItem generation completed in ',
    DATEDIFF(second, @StartedAt, SYSDATETIME()),
    ' seconds.'
);
GO


/* ============================================================
   9. Verify row counts
   ============================================================ */

SELECT
    'Category' AS TableName,
    COUNT_BIG(*) AS [RowCount]
FROM dbo.Category

UNION ALL

SELECT
    'Product',
    COUNT_BIG(*)
FROM dbo.Product

UNION ALL

SELECT
    'Customer',
    COUNT_BIG(*)
FROM dbo.Customer

UNION ALL

SELECT
    'SalesOrder',
    COUNT_BIG(*)
FROM dbo.SalesOrder

UNION ALL

SELECT
    'SalesOrderItem',
    COUNT_BIG(*)
FROM dbo.SalesOrderItem;
GO


/* ============================================================
   10. Inspect table sizes
   ============================================================ */

SELECT
    t.name AS TableName,
    SUM(p.rows) AS [RowCount],

    CAST
    (
        SUM(a.total_pages) * 8.0 / 1024
        AS decimal(12,2)
    ) AS TotalSizeMB,

    CAST
    (
        SUM(a.used_pages) * 8.0 / 1024
        AS decimal(12,2)
    ) AS UsedSizeMB

FROM sys.tables AS t

JOIN sys.indexes AS i
    ON i.object_id = t.object_id

JOIN sys.partitions AS p
    ON p.object_id = i.object_id
   AND p.index_id = i.index_id

JOIN sys.allocation_units AS a
    ON a.container_id = p.partition_id

WHERE t.is_ms_shipped = 0

GROUP BY
    t.name

ORDER BY
    TotalSizeMB DESC;
GO


/* ============================================================
   11. Inspect database files
   ============================================================ */

SELECT
    name,
    type_desc,

    CAST
    (
        size * 8.0 / 1024
        AS decimal(12,2)
    ) AS SizeMB

FROM sys.database_files;
GO


PRINT 'IndexLab database setup completed.';
GO
```

---

## Expected result

The exact physical size may differ slightly between SQL Server installations, but a typical result is approximately:

| Table | Rows | Approx. used size |
|---|---:|---:|
| `SalesOrderItem` | 40,000,000 | 1.5 GB |
| `SalesOrder` | 10,000,000 | 0.45 GB |
| `Customer` | 100,000 | 6 MB |
| `Product` | 30,000 | 1.4 MB |
| `Category` | 100 | negligible |

The important point is not the database file size itself. The important point is the number of data pages SQL Server must process when an appropriate index does not exist.

The next part of the lab can use this database to compare:

- heap scans
- index seeks
- logical reads
- execution time
- join strategies
- the effect of adding indexes
