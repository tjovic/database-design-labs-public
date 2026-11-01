# Lab 06 – Indexes in SQL Server

> Database Design Laboratory  
> Student Lab Manual

---

# Learning goals

By the end of this lab, you should be able to:

- explain why an index can reduce unnecessary page reads;
- identify root, intermediate, and leaf levels in a balanced B+ tree;
- follow an index search and explain what happens when a key is inserted;
- distinguish a heap, a nonclustered index on a heap, and a clustered index;
- explain RID Lookup, Key Lookup, and the relationship between primary keys and indexes;
- interpret relevant operators in an Actual Execution Plan;
- compare query performance using `STATISTICS IO` and `STATISTICS TIME`;
- design useful nonclustered, composite, and covering indexes;
- explain selectivity, index maintenance, and the cost of additional indexes;
- inspect the depth and page usage of an index.

> [!NOTE]
> **Prerequisite:** Complete Lab 05 (Physical Storage) and create the `IndexLab` database using the lab's preparation scripts before starting the SQL exercises below. This lab assumes the reference data and table names from those scripts.

---

# 1. Why do we need indexes?

In Lab 05, we saw that SQL Server stores data in **8 KB pages**. The database engine reads pages, not individual rows directly from storage. If a query needs only a few rows from a very large table, reading many unrelated pages is wasted work.

Imagine a library with thousands of books. If books are not arranged by author, finding a particular title could require inspecting many shelves. Instead, the librarian uses an **alphabetical card catalog**. Each card identifies a book and points to its shelf.

![Library catalog organized alphabetically by author](../images/lab06/library-catalog.svg)

A typical search is:

1. Select the cabinet and drawer for the author's name.
2. Find the card in alphabetical order.
3. Read the shelf location.
4. Go to that shelf and retrieve the book.

**The catalog is separate from the books.** Its entries are ordered even if the books themselves are not. Another catalog could be organized by title instead of author, without moving any books.

This is the central idea of a database index: an additional structure helps locate relevant data without examining the whole table.

| Library | Database analogy |
|---|---|
| Book | Data row |
| Shelf | Data page or location (simplified) |
| Author's name on the card | Index key |
| Alphabetical catalog | Index structure |
| Reference to a shelf | Row locator |
| Search every shelf | Table/clustered index scan, depending on table structure |
| Search catalog then find book | Index seek, optionally followed by a lookup |

> [!IMPORTANT]
> A useful index can reduce I/O, but it does **not** guarantee that the optimizer will use it. For a query returning most rows, a scan can still be cheaper.

**Think about it:** If a library already has an author catalog, why might it also need a title catalog?

---

# 2. Trees and the B+ tree

## 2.1 Tree terminology

A tree is a hierarchy of nodes connected by links. Database rowstore indexes use a balanced B+ tree-like organization in which nodes correspond conceptually to **index pages**.

![Tree terminology, levels and depth](../images/lab06/tree-terminology-levels.svg)

- **Root:** the entry point to the tree.
- **Internal (intermediate) nodes:** contain separator keys and links to child pages.
- **Leaf level:** the bottom level containing index entries (or full rows for clustered indexes).
- **Tree depth:** the number of levels to traverse from root to leaves (counting conventions vary).

An index may consist of a single page; it does not always need three levels. The examples below intentionally use three levels so that navigation is visible.

## 2.2 Why balanced trees?

![Balanced and unbalanced trees](../images/lab06/tree-balanced-vs-unbalanced.svg)

For a B+ tree, **all leaves are at the same depth**. Therefore, finding any key requires traversing approximately the same number of levels. Because each internal page can direct the search to many child pages, even a large index can have relatively few levels.

> [!NOTE]
> “All leaves are at the same depth” describes the B+ tree property illustrated here, not every possible definition of a balanced tree.

## 2.3 Keys, pointers, and leaf pages

An internal page holds **separator keys** and child pointers. These keys divide the search space into ranges. For example, a separator `43` can direct keys smaller than 43 to the left and keys greater than or equal to 43 to the right.

At the leaf level, entries are logically ordered by key. The leaf pages also have links to adjacent leaf pages. That is useful when a query asks for a **range**, such as all keys between 40 and 70.

The rectangular empty slots in our diagrams show **available capacity**, not literal SQL Server page formatting. Actual SQL Server pages use an 8 KB structure with variable-length records and a slot array. Free space is measured in bytes; a new entry may fit without changing the tree, or a full page may need to split.

> [!TIP]
> Think of a B+ tree as a *navigation structure*, not as an arithmetic formula students need to implement. We will focus on how SQL Server uses it.

---

# 3. Heap tables and nonclustered indexes

## 3.1 What is a heap?

A **heap** is a SQL Server table without a clustered index. Its rows are stored in data pages but are not logically ordered by a clustered key.

![Heap table data storage](../images/lab06/heap-table-storage.svg)

The diagram illustrates several pages containing rows in no particular order by `MemberID`. A row's location can be described by a **RID (Row Identifier)**: *File ID, Page ID, Slot ID*.

> [!NOTE]
> A heap is not the same thing as a randomly ordered query result. Without `ORDER BY`, SQL does not guarantee output order for *any* table, including one with a clustered index.

## 3.2 A nonclustered index on a heap

Suppose we create a nonclustered index on `MemberID`. The index has sorted keys and stores a **RID locator** for each corresponding heap row. The heap data pages remain separate from the index.

![B+ tree navigation and row lookups in a nonclustered index on a heap](../images/lab06/bplus-tree-search.svg)

The black pointers lead from parent pages to child pages, the leaf entries carry key/row-location information, and the horizontal links connect neighboring leaf pages. The colored arrows to data pages are conceptual references to the underlying rows.

### Finding `MemberID = 61`

Consider this illustrative query (the `Member` table is used only for the diagram, not as part of `IndexLab`):

```sql
SELECT *
FROM dbo.Member
WHERE MemberID = 61;
```

Follow the path in the image:

1. **Root:** compare 61 with 43. Since `61 >= 43`, take the right pointer.
2. **Intermediate level:** compare 61 with 56 and 73. Since `56 <= 61 < 73`, take the middle pointer.
3. **Leaf level:** locate the entry for key 61.
4. **Heap row:** use its RID to retrieve the complete row if the query needs columns not present in the index.

If the optimizer chooses this access path, the additional heap access appears in the plan as **RID Lookup**. If the index already contains everything needed, the extra lookup is unnecessary.

For a range query, the engine can locate the first key and continue through the linked leaf pages:

```sql
-- Illustrative query: not executed against IndexLab
SELECT *
FROM dbo.Member
WHERE MemberID BETWEEN 40 AND 70;
```

> [!IMPORTANT]
> **Nonclustered index ≠ heap-only index.** A nonclustered index can also be created on a table that has a clustered index. In that case its row locator is generally the **clustered key**, not a heap RID. We will use this fact in the performance demo.

---

# 4. Clustered indexes

A **clustered index** also has root and intermediate pages, but its **leaf level contains the actual data rows**. The data rows are logically ordered by the clustered key. They are not stored in a second heap that must be reached through an RID.

![Clustered index search: actual table rows at the leaf level](../images/lab06/clustered-index-search.svg)

### Finding `MemberID = 61`

The search still follows the appropriate pointers from the root to a leaf page. But once the leaf entry for 61 is reached, **the full row is already there**.

| Characteristic | Nonclustered index on a heap | Clustered index |
|---|---|---|
| Root and internal pages | Navigation keys and page pointers | Navigation keys and page pointers |
| Leaf level | Index keys + RID row locators (and possibly included columns) | Actual table rows |
| Additional fetch for missing columns | RID Lookup | No extra lookup when the clustered index itself supplies the row |
| How many per table? | Multiple nonclustered indexes possible | Only one clustered index |

A table cannot store its entire rowset in two different clustered-key orders at the same time. That is why a SQL Server table has **at most one clustered index**.

> [!WARNING]
> A clustered index defines a **logical ordering** by key. It does not guarantee adjacent physical positions on disk, and it does not guarantee output ordering without `ORDER BY`.

## 4.1 Nonclustered indexes on clustered tables

In our practical demo, we will create clustered primary keys and then add nonclustered indexes. A nonclustered index on a clustered table generally uses the clustered key as the row locator. If more columns are required, SQL Server may use a **Key Lookup** into the clustered index.

For example, a nonclustered index on `SalesOrder(OrderDate)` can already make its clustered key `SalesOrderId` available. We do not need to explicitly `INCLUDE (SalesOrderId)` when `SalesOrderId` is the clustered key.

## Check your understanding

1. Where does a B+ tree search start?
2. Why are leaf pages linked?
3. What does a heap lack?
4. What is the difference between RID Lookup and Key Lookup?
5. Why can a table have only one clustered index?

<details>
<summary>Show answers</summary>

1. At the root page, unless the tree has only a single level.
2. They allow efficient traversal through neighboring key ranges.
3. A clustered index.
4. RID Lookup retrieves missing columns from a heap row via its RID; Key Lookup retrieves them from a clustered index using its clustering key.
5. The table's full rows form one clustered leaf-level organization.

</details>

---

# 5. Primary keys and indexes

A **primary key** is a logical constraint: values must be unique and non-NULL. SQL Server enforces it using a **unique index**. By default, if a table has no clustered index and you do not specify `NONCLUSTERED`, a primary key is created using a clustered index.

In this lab we will explicitly choose:

```sql
PRIMARY KEY CLUSTERED
```

This makes the physical design decision visible. A primary key is excellent for finding a row by its key, but it does not automatically make all other search patterns efficient.

---

# 6. Prepare the main performance demonstration

The `IndexLab` tables contain approximately 10 million sales orders and 40 million sales-order items in the reference dataset. This is large enough for poor access paths to be noticeable.

In SQL Server Management Studio (SSMS), open a query window:

```sql
USE IndexLab;
GO
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
GO
```

Enable **Query → Include Actual Execution Plan** (`Ctrl + M`).

- **Actual Execution Plan:** the operators chosen and observed row counts.
- **STATISTICS IO:** logical reads and other page-read metrics.
- **STATISTICS TIME:** CPU time and elapsed execution time.

> [!NOTE]
> Reference timings in the original lab came from a particular machine (SQL Server 2025, build 17.0.1135.8, 31 GB RAM, Developer and Express instances). Your timings will differ. Compare the *access paths, pages read, and overall direction of change* rather than requiring identical seconds.

## 6.1 Baseline query: before adding indexes

```sql
SELECT
    p.CategoryId,
    COUNT_BIG(*) AS ItemCount,
    SUM
    (
        CAST(soi.Quantity AS decimal(18,2))
        * soi.UnitPrice
    ) AS Revenue
FROM dbo.SalesOrder AS so
JOIN dbo.SalesOrderItem AS soi
    ON soi.SalesOrderId = so.SalesOrderId
JOIN dbo.Product AS p
    ON p.ProductId = soi.ProductId
WHERE so.OrderDate >= '20250601'
  AND so.OrderDate <  '20250602'
GROUP BY
    p.CategoryId
ORDER BY
    Revenue DESC;
GO
```

On the reference Express instance, the original run took roughly 15–17 seconds. Make a note of your own measurements **before** creating any indexes.

| Metric | Before | After |
|---|---|---|
| Elapsed time | Record your result | Later |
| Logical reads, SalesOrder | Record your result | Later |
| Logical reads, SalesOrderItem | Record your result | Later |
| Access operator for SalesOrder | Record your result | Later |
| Access operator for SalesOrderItem | Record your result | Later |
| Main join | Record your result | Later |

> [!TIP]
> Do not evaluate performance from elapsed time alone. A warm cache and concurrent load can influence timing; logical reads and access paths are usually more informative for this exercise.

---

# 7. Understand the execution plan before indexing

Execution plans generally show data flowing **from right to left**. Start at the access operators that read tables or indexes, then inspect joins and other operations.

| Operator | What it does |
|---|---|
| `Table Scan` | Reads rows from a heap |
| `Clustered Index Scan` | Scans a clustered index |
| `Index Scan` | Scans a nonclustered index |
| `Index Seek` | Navigates to a key or key range |
| `RID Lookup` | Fetches a heap row using its RID |
| `Key Lookup` | Fetches more columns from the clustered index |
| `Nested Loops` | Repeatedly matches inner-side rows to each outer row |
| `Hash Match` | Implements hash join or aggregate operations |
| `Compute Scalar` | Computes a scalar expression |
| `Sort` | Orders rows |

## 7.1 Why is SalesOrder expensive?

The `OrderDate` predicate matches roughly 5,477 rows in the reference sample out of approximately 10 million orders. Without an index starting with `OrderDate`, SQL Server cannot navigate directly to that date range.

Inspect **Actual Number of Rows**, **Estimated Number of Rows**, **Number of Rows Read**, and **Predicate** in the access operator properties.

## 7.2 Why is SalesOrderItem the main bottleneck?

The join uses:

```sql
soi.SalesOrderId = so.SalesOrderId
```

The reference dataset contains approximately 40 million order items, but only about 21,908 match the orders from the chosen day. Without an efficient index on `SalesOrderId`, a very large input may have to be scanned and joined.

## 7.3 Joins, aggregation, and sorting

A `Hash Match (Inner Join)` is a reasonable option for large inputs without efficient lookup paths. It is **not inherently bad**.

`Compute Scalar` may calculate:

```sql
CAST(soi.Quantity AS decimal(18,2)) * soi.UnitPrice
```

`Hash Match (Aggregate)` may implement `GROUP BY p.CategoryId`, and `Sort` may implement `ORDER BY Revenue DESC`.

The `Product` table contains only about 30,000 rows. A scan of this comparatively small table may be perfectly reasonable. **Seek is not always better than scan**; the optimizer estimates costs, not labels.

## 7.4 Missing Index recommendations

SSMS may show an index recommendation such as a key on `SalesOrder(OrderDate)`.

> [!WARNING]
> A missing-index recommendation is a **hint**, not a complete indexing strategy. Check existing indexes, other queries, write overhead, index width, and possible duplication before applying it.

## Check your understanding

1. Why can a query return only 5,477 rows yet read millions of input rows?
2. Why does an index on `SalesOrderId` help the order-item join?
3. Is a `Hash Match` always a performance problem?
4. Why may a scan of `Product` still be acceptable?

<details>
<summary>Show answers</summary>

1. Without a useful access path the engine must inspect many unrelated rows/pages to evaluate the filter.
2. It lets the engine find items for each relevant order instead of scanning the entire item table.
3. No, it may be the cheapest join algorithm for the available inputs.
4. Because a small scan may cost less than using an index plus additional lookups.

</details>

---

# 8. Create useful indexes

## 8.1 Create clustered primary keys

```sql
ALTER TABLE dbo.SalesOrder
ADD CONSTRAINT PK_SalesOrder
PRIMARY KEY CLUSTERED (SalesOrderId);
GO

ALTER TABLE dbo.SalesOrderItem
ADD CONSTRAINT PK_SalesOrderItem
PRIMARY KEY CLUSTERED (SalesOrderItemId);
GO
```

Refresh the **Indexes** folder in SSMS and confirm `PK_SalesOrder` and `PK_SalesOrderItem` exist.

These indexes organize the data by their ID columns. However, the baseline query filters orders by **OrderDate** and finds items by **SalesOrderId**. Primary keys alone do not fully address those two access patterns.

## 8.2 Nonclustered index for the order-date filter

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrder_OrderDate
ON dbo.SalesOrder (OrderDate);
GO
```

The key `OrderDate` supports the date-range predicate. Because `SalesOrderId` is the clustered key, SQL Server already carries it as the row locator in this nonclustered index; an explicit `INCLUDE (SalesOrderId)` is unnecessary.

## 8.3 Nonclustered index for the join: first without INCLUDE

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrderItem_SalesOrderId
ON dbo.SalesOrderItem (SalesOrderId);
GO
```

Use this isolated query to inspect the lookup:

```sql
SELECT ProductId, Quantity, UnitPrice
FROM dbo.SalesOrderItem
WHERE SalesOrderId = 1;
GO
```

The optimizer may choose an **Index Seek** plus **Key Lookup**. The seek finds order-item rows using `SalesOrderId`, but the nonclustered index does not have `ProductId`, `Quantity`, and `UnitPrice`. SQL Server can fetch those values from the clustered index.

> [!NOTE]
> An execution plan is cost-based. If SQL Server chooses a different plan on your instance, inspect row counts and costs rather than assuming the diagram is wrong.

## 8.4 Add the columns needed by the query

```sql
DROP INDEX IX_SalesOrderItem_SalesOrderId ON dbo.SalesOrderItem;
GO

CREATE NONCLUSTERED INDEX IX_SalesOrderItem_SalesOrderId
ON dbo.SalesOrderItem (SalesOrderId)
INCLUDE
(
    ProductId,
    Quantity,
    UnitPrice
);
GO
```

Run the isolated query again. It should now be covered by the nonclustered index and normally no longer need a Key Lookup.

- **Key column** `SalesOrderId`: supports the search/join.
- **Included columns** `ProductId`, `Quantity`, `UnitPrice`: provide additional data at leaf level, without becoming part of the index search key.

A **covering index** supplies all columns required from a table for a particular query. Included columns can also support filters evaluated as residual predicates, `GROUP BY`, and aggregate expressions; they are not limited to the `SELECT` list.

---

# 9. Run the baseline query again

Re-run **exactly the SQL statement from Section 6.1**. The SQL text is unchanged; only the available access paths have changed.

Now compare the actual plans, logical reads, and elapsed time.

The optimizer may choose a pattern involving an `Index Seek` on the date index, a join such as `Nested Loops`, and seeks into the indexed order items. Exact operators can vary with statistics, cardinalities, and cost estimates.

A simplified view of nested loops is:

```text
for each matching order:
    find matching order items using the SalesOrderId index
```

> [!IMPORTANT]
> An index can change the strategy of the **entire execution plan**, not just replace one access operator.

## Reference comparison

These are approximate results from the original lab on one SQL Server Express instance, not guaranteed targets:

| Metric | Before | After |
|---|---:|---:|
| SalesOrder access | Table Scan | Index Seek |
| Relevant orders | ~5,477 | ~5,477 |
| SalesOrderItem access | Table Scan | Index Seek |
| Large item input | ~40 million rows | ~21,908 relevant rows |
| Main join | Hash Match | Nested Loops |
| SalesOrderItem logical reads | ~198,000 | ~54,000 |
| SalesOrder logical reads | ~57,000 | ~15 |
| Elapsed time | ~17 s | ~0.5 s |

The point is not that SQL Server suddenly processes 40 million rows faster. **It avoids processing most of them.**

## Check your understanding

1. Why did clustered primary keys alone not solve the original query's main problem?
2. Why is `OrderDate` the key of one index and `SalesOrderId` the key of the other?
3. Which missing columns can cause a Key Lookup on the order-item index?
4. Did the query itself change before and after adding the indexes?

<details>
<summary>Show answers</summary>

1. The query filters by `OrderDate` and joins on `SalesOrderId`, not only by the primary-key values.
2. They correspond to the filter and the join access pattern.
3. `ProductId`, `Quantity`, and `UnitPrice` when they are not available in that index.
4. No; indexes changed the available access paths.

</details>

---

# 10. Inspect the physical index structure

Now connect the execution plan back to Lab 05. Every level of a disk-based rowstore B+ tree consists of **8 KB pages**. More pages and a deeper tree can mean more page access, although cache behavior and the chosen plan also matter.

You can inspect index metadata and physical characteristics. For example:

```sql
SELECT
    i.name AS IndexName,
    ips.index_type_desc AS IndexType,
    ips.index_level AS IndexLevel,
    ips.page_count AS PageCount,
    ips.record_count AS RecordCount,
    ips.avg_page_space_used_in_percent AS PageUsedPercent
FROM sys.dm_db_index_physical_stats
(
    DB_ID(),
    OBJECT_ID('dbo.SalesOrder'),
    NULL, NULL, 'DETAILED'
) AS ips
JOIN sys.indexes AS i
    ON i.object_id = ips.object_id
   AND i.index_id = ips.index_id
ORDER BY i.name, ips.index_level DESC;
GO
```

`index_level = 0` represents the leaf level, and larger values represent higher levels. The highest level is the root for that index/allocation-unit context. For very large indexes, `'DETAILED'` can be expensive; use it in this training database, not automatically on busy production systems.

> [!NOTE]
> `sys.dm_db_index_physical_stats` can return multiple rows for partitions or allocation units. Interpret its output in that context. For a quick summary, SQL Server also offers `sys.dm_db_index_physical_stats` with `'SAMPLED'` or `'LIMITED'`, but not every metric is available in every mode.

Observe how the page counts differ between the clustered primary-key index and the narrower nonclustered `OrderDate` index.

---

# 11. Index design principles

## 11.1 Composite indexes and column order

Create an index that supports searches starting with `CustomerId` and optionally narrowing by date:

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrder_CustomerId_OrderDate
ON dbo.SalesOrder (CustomerId, OrderDate);
GO
```

Compare these queries (enable Actual Execution Plan):

```sql
-- Leading key only
SELECT SalesOrderId, CustomerId, OrderDate
FROM dbo.SalesOrder
WHERE CustomerId = 500;
GO

-- Leading key followed by a range on the second key
SELECT SalesOrderId, CustomerId, OrderDate
FROM dbo.SalesOrder
WHERE CustomerId = 500
  AND OrderDate >= '20250101';
GO

-- Second key without the first
SELECT SalesOrderId, CustomerId, OrderDate
FROM dbo.SalesOrder
WHERE OrderDate >= '20250101';
GO
```

The first two patterns align with the leading key. The third does not provide `CustomerId`, so it generally cannot efficiently seek directly on `OrderDate` using this index alone. A scan may still use it for coverage.

> [!IMPORTANT]
> **Key column order matters.** Reordering predicates in the `WHERE` clause does not change an index's key order.

## 11.2 Selectivity

Inspect the values of `Status`:

```sql
SELECT Status, COUNT(*) AS NumberOfOrders
FROM dbo.SalesOrder
GROUP BY Status
ORDER BY NumberOfOrders DESC;
GO

CREATE NONCLUSTERED INDEX IX_SalesOrder_Status
ON dbo.SalesOrder (Status);
GO
```

Compare the plans:

```sql
SELECT SalesOrderId, Status
FROM dbo.SalesOrder
WHERE Status = 'Completed';
GO

SELECT SalesOrderId, Status
FROM dbo.SalesOrder
WHERE Status = 'Review';
GO
```

**Selectivity** describes how narrowly a predicate reduces the rows to be processed. A rare status may be a good index candidate even if the `Status` column has only a few distinct values. The optimizer considers the distribution of values and cost of alternative plans.

## 11.3 Included columns and index width

Our index on `SalesOrderItem(SalesOrderId) INCLUDE (ProductId, Quantity, UnitPrice)` is a covering index for the order-item portion of the main query. An included column supplies data but does not extend the ordered search key.

Avoid making every index wide “just in case”: wider indexes consume storage, take more maintenance work, and may require more page reads.

---

# 12. Inserts, page splits, and maintenance

Indexes use physical pages with finite capacity. If an insertion belongs in a page with enough free space, SQL Server can add the entry there. If the page cannot accommodate it, a **page split** may be required, moving entries between pages and updating parent pointers as necessary.

The following illustrations simplify page capacity intentionally so that the operations are visible:

![Step-by-step insertion into a simplified B+ tree](../images/lab06/bplus-tree-insert-steps.svg)

![Final B+ tree after the insertions](../images/lab06/bplus-tree-after-insert.svg)

The next example shows insertion in the clustered-index case, where leaf pages hold the data rows themselves:

![Insertion into a clustered index](../images/lab06/clustered-index-insert.svg)

> [!WARNING]
> These diagrams model a very small maximum number of entries per node. Real SQL Server pages are 8 KB and can hold variable numbers of records, depending on row size and available space. The drawings are **conceptual**, not physical page byte layouts.

Every additional index may also require work during `INSERT`, `UPDATE`, or `DELETE`. That creates a trade-off:

- Faster and more targeted reads for some access patterns.
- Additional storage for index pages.
- Extra writes and maintenance when indexed data changes.
- Possible page splits and fragmentation.

Do not index every column automatically. Choose indexes that support important, frequent queries.

---

# 13. Practical checklist

When deciding whether to add an index, ask:

1. Which columns appear in selective `WHERE` predicates or joins?
2. Does the index have an appropriate **leading key**?
3. Which columns need to be returned, grouped, or aggregated?
4. Could included columns avoid a costly lookup?
5. Is a scan actually cheaper because many rows are needed?
6. Is there already a similar index?
7. What is the storage and write-maintenance cost?
8. What do the **actual execution plan** and **STATISTICS IO** show?

> [!TIP]
> Do not optimize by operator name alone. Optimize the actual workload, focusing on work avoided and the total cost of access paths.

---

# Exercises

Try each exercise **before opening the solution**. Keep Actual Execution Plan enabled.

## Exercise 1 – Index for a filtered, sorted query

Run this query before creating a new index:

```sql
SELECT
    SalesOrderId,
    CustomerId,
    OrderDate,
    TotalAmount
FROM dbo.SalesOrder
WHERE Status = 'Processing'
ORDER BY OrderDate DESC;
```

Design and create a nonclustered index that supports the filter and sort. Explain the key column order and any included columns. Re-run the query to verify your result.

<details>
<summary>Show solution</summary>

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrder_Status_OrderDate
ON dbo.SalesOrder (Status, OrderDate DESC)
INCLUDE (CustomerId, TotalAmount);
GO
```

`Status` is the leading key because of the equality filter. `OrderDate DESC` follows it to support the requested order. `CustomerId` and `TotalAmount` are included to cover the selected data. `SalesOrderId` is already available as the clustered key.

</details>

---

## Exercise 2 – Composite index column order

The lab created `IX_SalesOrder_CustomerId_OrderDate` on `(CustomerId, OrderDate)`. For each query below, predict whether the index supports a seek on both key columns, a seek on the leading column, or no efficient seek on the search condition. Verify your prediction in the plan.

```sql
-- A
SELECT * FROM dbo.SalesOrder WHERE OrderDate >= '20250101';

-- B
SELECT * FROM dbo.SalesOrder WHERE CustomerId = 500 ORDER BY OrderDate;

-- C
SELECT * FROM dbo.SalesOrder
WHERE CustomerId = 500
  AND OrderDate >= '20250101'
  AND OrderDate <  '20250201';
```

<details>
<summary>Show solution</summary>

- **A:** no efficient seek on `OrderDate` alone using this index because the first key (`CustomerId`) is missing; the index can still be scanned.
- **B:** seek on `CustomerId`; rows for that customer are then in `OrderDate` order, potentially avoiding `Sort`.
- **C:** seek using the equality on `CustomerId` and the range on `OrderDate`.

An actual plan may vary due to the cost of `SELECT *` and possible lookups.

</details>

---

## Exercise 3 – Covering index design

Write and analyze a query that returns `ProductId`, `Quantity`, and `UnitPrice` for one `SalesOrderId`:

```sql
SELECT ProductId, Quantity, UnitPrice
FROM dbo.SalesOrderItem
WHERE SalesOrderId = 12345;
```

Confirm whether it needs a Key Lookup.

<details>
<summary>Show solution</summary>

The existing `IX_SalesOrderItem_SalesOrderId` index with `INCLUDE (ProductId, Quantity, UnitPrice)` covers the query. The engine should generally be able to use it without an extra Key Lookup.

</details>

---

## Exercise 4 – Evaluate a Missing Index suggestion

Run:

```sql
SELECT SalesOrderId, OrderDate
FROM dbo.SalesOrder
WHERE Status = 'Review'
ORDER BY OrderDate;
```

Before creating anything, consider:

1. Does a similar index already exist (`IX_SalesOrder_Status` from Section 11.2)?
2. Would an index on `(Status, OrderDate)` overlap with it?
3. Is it better to create a new index, replace the existing one, or do nothing?

<details>
<summary>Show solution</summary>

`IX_SalesOrder_Status` supports the filter, but not ordering by `OrderDate` within the same `Status`. An index on `(Status, OrderDate)` can support both. It overlaps with the previous index, so consider **replacing** the earlier index instead of maintaining both. In a real system, inspect the entire workload before making this change.

</details>

---

# Key takeaways

- SQL Server indexes use pages, and useful access paths can avoid unnecessary I/O.
- A B+ tree has navigation pages and a logically ordered leaf level.
- A **heap** has no clustered index.
- A nonclustered index on a heap uses **RID** locators; on a clustered table it generally uses the **clustered key** as the locator.
- A clustered index stores **complete rows in its leaf level**; a table can have only one.
- A primary key is a constraint enforced by a unique index; it does not replace all other indexes.
- `Index Seek`, `Index Scan`, `Hash Match`, and `Nested Loops` are access/processing choices, not labels for inherently good or bad plans.
- Composite key order, selectivity, and included columns determine which access patterns an index supports.
- Indexes cost space and maintenance as well as providing potential read benefits.
- Always validate an index against the **actual workload** using plans and I/O measurements.
