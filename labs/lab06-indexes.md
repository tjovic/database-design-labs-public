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

Imagine a library with thousands of books. If books are not arranged by author, finding a particular book could require inspecting many shelves.

**Before computerized library catalogs became common, libraries used alphabetical card catalogs.** Each card contained information about a book, including its location on the shelves.

By searching the catalog, a librarian could quickly find where a book was stored without examining every shelf.

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

> [!NOTE]
> **Is using an index always faster?**
>
> Not necessarily. Imagine that a librarian needs to find just one book. Using the catalog is much faster than checking every shelf.
>
> But what if the librarian needs to examine almost every book in the library? In that case, searching the catalog and following individual shelf references may involve more work than simply going through the shelves.
>
> SQL Server faces a similar decision. For a query that returns only a small number of rows, using an index may be very efficient. However, when a query needs a large portion of a table, scanning the data may be more efficient.
>
> SQL Server's **query optimizer** evaluates different execution strategies and chooses the one with the lowest estimated cost. We will investigate these decisions later when analyzing execution plans.

**Think about it:** If a library already has an author catalog, why might it also need a title catalog?

<details>
<summary>Show answer</summary>

People search for books in different ways. Sometimes they know the author, but sometimes they only know the title.

An author catalog is organized by author names, so it is not efficient for searching by title alone. A separate title catalog allows books to be found quickly by title.

Similarly, a database can have **multiple indexes on the same table**, each supporting different search patterns without duplicating the actual data rows.

</details>

### From library catalogs to database indexes

The library catalog helps us understand **why an index is useful**. However, there is another important question:

**How can a database efficiently search an index containing millions of entries?**

A simple alphabetical list would still require searching through many entries. We need a structure that allows the database engine to quickly narrow down the search to a small part of the index.

SQL Server uses a tree-based structure for this purpose.

In the next section, we will first learn the basic terminology of trees and then explore how a **B+ tree** organizes index entries for efficient searching.

---

# 2. Trees and the B+ tree

## 2.1 Tree terminology

A tree is a hierarchy of nodes connected by links. Database rowstore indexes use a balanced B+ tree-like organization in which nodes correspond conceptually to **index pages**.

![Tree terminology, levels and depth](../images/lab06/tree-terminology-levels.svg)

- **Root:** the entry point to the tree.
- **Internal (intermediate) nodes:** contain separator keys and links to child pages.
- **Leaf level:** the bottom level containing index entries (or full rows for clustered indexes).
- **Tree depth:** he number of edges from the root to a leaf. In our diagrams, the root is at Level 0, so a leaf at Level 3 has a depth of 3. In database documentation, index depth may also be expressed as the number of levels, including the root and leaf levels.

An index may consist of a single page; it does not always need three levels. The examples below intentionally use three levels so that navigation is visible.

## 2.2 Why balanced trees?

![Balanced and unbalanced trees](../images/lab06/tree-balanced-vs-unbalanced.svg)

For a B+ tree, **all leaves are at the same depth**. Therefore, finding any key requires traversing approximately the same number of levels. Because each internal page can direct the search to many child pages, even a large index can have relatively few levels.

> [!NOTE]
> “All leaves are at the same depth” describes the B+ tree property illustrated here, not every possible definition of a balanced tree.

## 2.3 Keys, pointers, and leaf pages

Now that we understand the basic structure of a tree, let's see how a B+ tree helps a database find information.
A B+ tree organizes data using **keys** and **pointers**.

### Keys

A **key** is a value used to organize and search the index.
For example, imagine a table containing information about library members. Each member has a unique `MemberID`.
If we create an index on `MemberID`, the index organizes its entries by these values.
Unlike a simple list, a B+ tree does not require searching through all index entries one by one.

### Pointers

A **pointer** tells the database engine where to continue searching.
In the upper levels of a B+ tree, pointers lead to pages at the next level.
The database engine uses key values to decide which pointer to follow.
This process repeats until the search reaches the leaf level.

**The important idea is that the database does not need to visit every branch of the tree.** It follows only the branch that can contain the requested key.

### Leaf pages

The **leaf level** is the bottom level of the B+ tree.
Leaf pages contain index entries arranged in logical key order.

What these entries contain depends on the type of index:

- In a **nonclustered index**, leaf entries contain index keys, row locators, and possibly additional columns.
- In a **clustered index**, leaf pages contain the actual table rows.

We will explore this difference in Sections 3 and 4.

### Linked leaf pages

Leaf pages are also linked to neighboring leaf pages.
This is particularly useful for **range queries**, where the database needs multiple consecutive key values rather than just one.
Instead of starting a completely new tree search for every matching key, SQL Server can locate the beginning of a range and continue reading the relevant leaf pages.

### Free space in index pages

In the following diagrams, some nodes contain empty slots.
These empty slots are a simplified way to illustrate that an index page may have free space available for new entries.

In SQL Server, index pages are 8 KB in size, and their actual capacity depends on the size of the stored records. Empty slots in our diagrams are not a literal representation of SQL Server's internal page format.

If an index page does not have enough space for a new entry, SQL Server may need to perform a **page split**. We will explore this later in the lab.

> [!TIP]
> Remember these three concepts:
>
> - **Keys** help determine where to search.
> - **Pointers** lead to the next page.
> - **Leaf pages** contain the information needed to locate or retrieve the data.
>
> In the next section, we will follow a real example and search for `MemberID = 61`.

---

# 3. Heap tables and nonclustered indexes

## 3.1 What is a heap?

Before exploring how a nonclustered index works, we first need to understand how SQL Server stores table rows **without a clustered index**.

A **heap** is a table that does not have a clustered index.

As we learned in Lab 05, SQL Server stores table data in **8 KB pages**. A heap also uses these data pages, but its rows are not organized in a logical order defined by a clustered key.

Consider a simple `Member` table containing member IDs, first names, and last names.

![Heap table data storage](../images/lab06/heap-table-storage.svg)

Notice that the rows are **not arranged by `MemberID`**. For example, a row with a larger ID may appear on an earlier page than a row with a smaller ID.

This is perfectly valid. A heap does not require rows to be stored in any particular key order.

### How does SQL Server locate a row in a heap?

Each heap row has a physical location identified by a **RID (Row Identifier)**.

A RID consists of three components:

| Component | Meaning |
|---|---|
| File ID | Identifies the database file |
| Page ID | Identifies the page within that file |
| Slot ID | Identifies the row slot within the page |

Together, these values allow SQL Server to locate a particular row.

However, knowing that a row has a physical location is not the same as knowing **which location contains a particular `MemberID`**.

### What happens when we search without an index?

Suppose we want to find one member:

```sql
SELECT *
FROM dbo.Member
WHERE MemberID = 61;
```

If no suitable index exists, SQL Server may need to perform a **Table Scan**.

This means reading the heap's data pages and examining rows to find those that satisfy the condition.

For a small table, this may be inexpensive. But for a table containing millions of rows, scanning many pages can require substantial I/O work.

> [!NOTE]
> A heap does not guarantee that rows will be returned in any particular order. Neither does a clustered index. If a query requires a specific result order, use `ORDER BY`.

### Can we search a heap efficiently?

Yes. We can create a **nonclustered index** on `MemberID` without changing the heap into a clustered table.

The index provides an ordered search structure, while the actual data rows remain in the heap.

**This is what we will explore in the next section.**

## 3.2 A nonclustered index on a heap

In the previous section, we saw that a heap stores rows without organizing them by a clustered key.

If we want to find a particular member using `MemberID`, SQL Server may have to scan many data pages.

**Can we make searching faster without reorganizing the actual table?**

Yes. We can create a **nonclustered index** on `MemberID`.

A nonclustered index is a separate structure that organizes index entries by their key values. In a heap table, each index entry also contains a **RID (Row Identifier)** that identifies the corresponding data row.

This gives us two separate structures:

- **Nonclustered index:** stores ordered keys and information needed to locate rows.
- **Heap:** stores the actual data rows, which are not organized by the index key.

### Understanding the diagram

![B+ tree navigation and row lookups in a nonclustered index on a heap](../images/lab06/bplus-tree-search.svg)

The diagram illustrates a nonclustered index on `MemberID`.
Let's identify its main components.

**1. Root level**

The root is the starting point of the search.
It contains separator keys and pointers that direct the search to the appropriate branch of the tree.
The root does not need to contain every `MemberID`. Its purpose is to help SQL Server decide where to search next.

**2. Intermediate level**

Intermediate pages further divide the possible key values into smaller ranges.
Each page contains separator keys and pointers to child pages.
By following the appropriate pointer, SQL Server can eliminate entire branches of the tree without examining their entries.

**3. Leaf level**

The leaf level contains the actual nonclustered index entries, organized in key order.
In our example, each entry contains:

- The indexed key (`MemberID`).
- A RID that identifies the corresponding row in the heap.

Notice that the leaf pages are connected by horizontal pointers. These connections allow SQL Server to continue reading consecutive index entries.

**4. Heap data pages**

At the bottom of the diagram, the data pages contain the actual member records.
Unlike the index entries, the heap rows are not organized by `MemberID`.
The orange arrows illustrate how the RID values in the index refer to rows stored in these pages.

**5. Empty spaces**

Some index pages contain empty slots.
These are conceptual representations of available page capacity. They help us understand that new keys may be inserted into existing pages.
Real SQL Server index pages have an 8 KB layout, and their capacity depends on the size of the stored records.

### Finding MemberID = 61

Suppose we execute the following query:

```sql
-- Illustrative example (Member is not part of IndexLab)
SELECT *
FROM dbo.Member
WHERE MemberID = 61;
```

SQL Server can use the nonclustered index to locate the requested member.

**Step 1 – Start at the root**

The search starts at the root page, which contains the separator key `43`.
We are searching for `61`.
Because `61 >= 43`, we follow the right pointer.
There is no need to examine the left subtree because it contains smaller key values.

**Step 2 – Follow the intermediate pointer**

The next index page contains the separator keys `56` and `73`.
Our value falls into this range:

`56 <= 61 < 73`

Therefore, we follow the middle pointer.
Again, we eliminate the other branches without reading their leaf pages.

**Step 3 – Find the entry at the leaf level**

We reach a leaf page containing the keys `56` and `61`.
The entry for `61` contains a RID that identifies the location of the corresponding member row.
At this point, SQL Server has found the matching **index entry**, but it may not yet have all the columns requested by the query.

**Step 4 – Retrieve the actual row**

Our query uses `SELECT *`, so SQL Server needs the complete member row.
If the nonclustered index does not contain all the required columns, SQL Server follows the RID to the corresponding heap data page.
This additional operation is called a **RID Lookup**.

The important distinction is:

- **Index Seek:** locates the matching index entry.
- **RID Lookup:** retrieves missing columns from the actual heap row.

> [!IMPORTANT]
> A RID Lookup is not always required.
>
> If the nonclustered index already contains all columns needed by the query, SQL Server can return the result directly from the index.
>
> Such an index is called a **covering index**. We will explore covering indexes and `INCLUDE` columns later in the lab.

### Searching for a range of values

Indexes are useful not only when searching for a single value.

Consider this query:

```sql
-- Illustrative example (Member is not part of IndexLab)
SELECT *
FROM dbo.Member
WHERE MemberID BETWEEN 40 AND 70;
```

SQL Server can use the index to locate the beginning of the range.
Because leaf pages are logically ordered and linked to their neighbors, the engine can continue reading subsequent index entries until it reaches the end of the requested range.
This avoids starting a completely new tree search for every individual key.
However, because this query uses `SELECT *`, SQL Server may also need additional heap lookups for the matching rows.

If the range contains a large portion of the table, the optimizer may decide that a Table Scan is more efficient.

> [!NOTE]
> A nonclustered index is not limited to heap tables.
>
> When a table has a clustered index, a nonclustered index generally uses the **clustered key** as its row locator instead of a heap RID.
>
> If additional columns must be retrieved from the clustered index, SQL Server may use a **Key Lookup** instead of a RID Lookup.

### Check your understanding

1. Why are the index entries ordered while the heap rows are not?
2. Why does the root contain only separator keys rather than every `MemberID`?
3. What happens when we search for `MemberID = 61`?
4. What is the difference between Index Seek and RID Lookup?
5. Why are the leaf pages linked?
6. When can SQL Server avoid a RID Lookup?

<details>
<summary>Show answers</summary>

1. A nonclustered index organizes entries by its key, independently of the heap's row organization.
2. Separator keys guide the search into the correct subtree without storing every key at the root.
3. SQL Server navigates through the appropriate index pages, finds key 61, and retrieves the heap row if additional columns are required.
4. Index Seek locates index entries; RID Lookup retrieves missing data from a heap row.
5. Linked leaf pages support efficient traversal of consecutive key ranges.
6. When the index contains all columns required by the query.

</details>

## 3.3 Why is an index so efficient?

The previous example showed **how** SQL Server finds `MemberID = 61`. But why is navigating a B+ tree so much better than searching a large heap?

Imagine a table with **1,000,000 rows**. For a simplified calculation, assume that a data page holds 100 rows, a leaf index page holds 100 index entries, and each internal index page can point to 100 child pages.

![Full heap scan versus B+ tree index seek](../images/lab06/bplus-tree-efficiency.svg)

**Without a useful index**, finding one row may require scanning approximately:

```text
1,000,000 rows / 100 rows per data page = 10,000 data pages
```

**With a nonclustered index on a heap**, the index can have a three-level structure:

| Level | Approximate pages in that level | What happens during one seek? |
|---|---:|---|
| Root | 1 | Read the root page. |
| Intermediate | 100 | Follow one pointer to the relevant intermediate page. |
| Leaf | 10,000 | Follow one pointer to the relevant leaf page and find the key. |
| Heap data | 10,000 | Use the RID to access the page containing the row, if necessary. |

Only **one page at each index level** is needed along the search path, followed by **one heap data page** to retrieve a row not covered by the index. In this illustrative model, that is **about 4 page accesses instead of examining 10,000 data pages**.

> [!IMPORTANT]
> The power of a B+ tree comes from **fan-out**: each navigation page directs the search toward many possible pages. The engine follows one relevant path rather than reading every page.

> [!NOTE]
> This is a simplified comparison for finding **one matching row**. The page capacities are assumptions, not fixed SQL Server values. Logical page accesses are not the same as physical disk I/O; many pages may already be in memory. A range query returning many rows may favor a scan, and an index does not guarantee a particular execution plan or speedup.

**Check your understanding:** Why does adding millions of index entries not necessarily add many new levels to a B+ tree?

<details>
<summary>Show answer</summary>

Because an internal page can point to many child pages. Each extra level greatly increases the number of entries the tree can represent, so tree depth grows slowly compared with the number of indexed rows.

</details>

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

This is the main practical part of the lab. We will execute **the same SQL query before and after adding indexes**, inspect both actual execution plans, and measure the work performed by SQL Server. The goal is to explain *why* a plan becomes faster, not simply to observe that its elapsed time decreases.

The `IndexLab` reference database contains approximately **10 million** rows in `SalesOrder`, **40 million** rows in `SalesOrderItem`, and **30,000** products. These figures are large enough to make inefficient access paths visible.

> [!NOTE]
> **Don't have `IndexLab` yet?** It is created in [Lab 05, Section 2 – Create the `IndexLab` database](lab05-physical-storage.md#2-create-the-indexlab-database) using the [IndexLab setup script](setup/index-lab-data-setup.md). This lab does not repeat that setup — it assumes the database already exists in its freshly generated state (heaps, no indexes beyond what the script creates).

> [!IMPORTANT]
> Complete the steps **in order**, using the database in its prepared initial state. Later sections create indexes that change the execution plan. If you already created these indexes in a previous attempt, restore the prepared lab state before repeating the *before indexes* measurement.

## 6.1 Prepare SSMS and collect useful measurements

Open a new query window in SSMS and select the database:

```sql
USE IndexLab;
GO

SET STATISTICS IO ON;
SET STATISTICS TIME ON;
GO
```

Enable **Query → Include Actual Execution Plan**, or press `Ctrl + M` before executing the query. After execution inspect the **Results**, **Messages**, and **Execution Plan** tabs.

| Instrument | What to look for | Why it matters |
|---|---|---|
| Actual Execution Plan | Operators, row counts, estimates, joins, warnings | Shows how SQL Server executed the query |
| `STATISTICS IO` | Logical reads, scan count, physical/read-ahead reads | Shows the data-access work performed |
| `STATISTICS TIME` | CPU time and elapsed time | Helps distinguish CPU work from total duration |
| Operator Properties | Predicate, Seek Predicates, Estimated/Actual rows, Number of Rows Read | Explains whether rows were found efficiently |

**Logical reads** count 8 KB pages read from the buffer pool (including pages previously cached); they are *not* the same thing as physical disk reads. A query can perform many logical reads even when physical reads are near zero. Conversely, timing can vary with buffer cache, CPU availability, concurrent activity, and the selected plan.

> [!TIP]
> Hover over an execution-plan operator for its tooltip. For more detailed properties, click the operator and press **F4** (or right-click → **Properties**). In the plan, pay attention to **the arrows between operators**: thicker arrows usually represent larger row flows.

> [!NOTE]
> Reference timings come from the original lab's measurements on one computer running SQL Server 2025 (build 17.0.1135.8), 31 GB RAM, with separate Express and Developer instances. Your own numbers may be very different. Record your results; do not try to reproduce the exact timings.

## 6.2 Run the baseline query before adding indexes

The query calculates the number of sold items and revenue per product category for one day, then orders categories by revenue:

```sql
SELECT
    p.CategoryId,
    SUM(soi.Quantity) AS ItemsSold,
    SUM(CAST(soi.Quantity AS decimal(18,2)) * soi.UnitPrice) AS Revenue
FROM dbo.SalesOrder AS so
JOIN dbo.SalesOrderItem AS soi
    ON soi.SalesOrderId = so.SalesOrderId
JOIN dbo.Product AS p
    ON p.ProductId = soi.ProductId
WHERE so.OrderDate >= '20250601'
  AND so.OrderDate <  '20250602'
GROUP BY p.CategoryId
ORDER BY Revenue DESC;
GO
```

Read the SQL statement before you execute it:

1. `WHERE so.OrderDate ...` restricts sales orders to **one day**.
2. The first `JOIN` finds the order items belonging to those orders.
3. The second `JOIN` obtains each product's `CategoryId`.
4. `Quantity * UnitPrice` calculates the value of each line.
5. `GROUP BY` calculates the totals for each category.
6. `ORDER BY Revenue DESC` sorts the final category totals.

This query is useful because it combines **filtering, joining, calculation, aggregation, and sorting**. Different plan operators can be linked directly to parts of the SQL statement.

In the reference Express instance, the baseline execution took approximately **15–17 seconds**. Do not focus on the time alone — Section 7 explains how to read the plan behind this number.

---

# 7. Investigate the execution plan before indexing

Keep the **Execution Plan** tab from the query you ran in Section 6.2 open — Sections 7.2 through 7.7 walk through that specific plan, operator by operator. If you closed it or ran anything else in between, re-run the Section 6.2 query with Actual Execution Plan enabled before continuing.

Record your own values now, before changing any index — you will compare them against the "after indexes" numbers in Section 9. The table below shows reference values measured on one SQL Server 2025 Express instance (`IndexLab` in its freshly generated state — heaps, no indexes beyond the setup script), so you can check your own results against them:

| Metric | Before indexes (reference) |
|---|---|
| Elapsed time | **18.1 s** |
| CPU time | **14.7 s** |
| `SalesOrder` logical reads | **57,143** |
| `SalesOrderItem` logical reads | **198,020** |
| `Product` logical reads | **161** |
| Access operator for `SalesOrder` | `Table Scan` (heap), with the `OrderDate` predicate applied during the scan — **5,477** rows returned out of 10,000,000 |
| Access operator for `SalesOrderItem` | `Table Scan` (heap) — all **40,000,000** rows scanned, **21,908** rows survive the join |
| Access operator for `Product` | `Clustered Index Scan` on `PK_Product` — all 30,000 rows scanned |
| Main join operator(s) | Two `Hash Match (Inner Join)` operators — one for `SalesOrder`/`SalesOrderItem`, one for the result joined with `Product` |
| Aggregation / sort | `Hash Match (Aggregate)` for `GROUP BY`, then `Sort` for `ORDER BY Revenue DESC` |

> [!NOTE]
> SQL Server Express has resource and parallelism limitations. The original lab's reference query used serial execution in Express. On instances using parallel execution, the sum of CPU time across workers can be larger than elapsed time. The observed plan depends on edition, configuration, statistics, and data distribution; neither serial execution nor a particular operator is guaranteed for every installation. Elapsed and CPU time will vary most with your hardware; row counts and logical reads should be close to the reference values, since they come from the same generated dataset and an unindexed heap scan.

The "Access operator" and "Main join operator" rows name things Section 7.1 has not introduced yet — that is intentional. Look at your own plan now (even informally), then come back and compare it with the vocabulary from 7.1 onward.

![Execution plan before indexing: two Table Scans feeding two Hash Match joins, a Hash Match Aggregate, and a Sort](../images/lab06/execution-plan-before.svg)

This is a simplified redrawing of the actual plan measured on one computer (the reference results above) — same operators and row counts, laid out for readability. Your own plan's exact shape should match; icon style and layout will differ by SSMS version.

Execution plans are often explained by reading **from right to left**, beginning with operators that access tables or indexes. This is a useful convention, but follow the **data-flow arrows** when tracing individual branches: a plan is a tree of operations, not simply a linear list.

## 7.1 Learn the essential plan operators

An execution plan consists of **operators**, each representing an operation performed by SQL Server.

Some operators retrieve data from tables or indexes. Others join rows, calculate values, group results, or sort data.

The following table introduces the most important operators you will encounter in this lab.

| Operator | What it does |
|---|---|
| `Table Scan` | Reads rows from a **heap** (a table without a clustered index). SQL Server examines the rows to find those matching the query conditions. If there is no suitable index, it may need to read the entire table. |
| `Clustered Index Scan` | Reads data from the **leaf level of a clustered index**, where the actual table rows are stored. It may read many or all rows, even when the query needs only a small number of them. |
| `Index Scan` | Reads entries from a **nonclustered index**. Because an index may contain fewer and narrower columns than the table, scanning it can require less work than scanning the complete table. |
| `Index Seek` | Uses the **ordered index keys** to navigate directly to a specific value or range of values. This can avoid reading large parts of the index that are not relevant to the query. |
| `RID Lookup` | Uses a **Row Identifier (RID)** obtained from a nonclustered index to retrieve additional columns from a heap row. It is needed when the index does not contain all the required data. |
| `Key Lookup` | Retrieves additional columns from a **clustered index** after a nonclustered index has identified matching rows. It can become expensive when repeated for many rows. |
| `Nested Loops` | Takes rows from one input (the **outer input**) and repeatedly accesses another input (the **inner input**). It is often efficient when relatively few outer rows can quickly find matching inner rows using an index. |
| `Hash Match (Inner Join)` | Builds a **hash table** from one input and uses it to find matching rows from another input. It is often useful when joining large datasets without suitable indexes for repeated seeks. |
| `Hash Match (Aggregate)` | Uses a hash table to **group rows by one or more values** and calculate aggregates such as `SUM`, `COUNT`, or `AVG`. It does not require the input rows to be sorted by the grouping columns. |
| `Compute Scalar` | Defines a **calculated expression**, such as multiplication, addition, or data type conversion. For example, it may calculate `Quantity * UnitPrice` for each order item. |
| `Sort` | Arranges rows according to one or more columns or expressions. It is commonly used for `ORDER BY`, but may also be needed by other operations that require sorted input. |

> [!IMPORTANT]
> **An Index Seek is not always better than a Scan.**
>
> A seek is useful when SQL Server needs a relatively small portion of the data. However, when a query requires many rows, scanning the table or index may be more efficient than performing many separate index lookups.
>
> The goal is not to eliminate every scan, but to **reduce unnecessary work**.

## 7.2 Investigate the `SalesOrder` scan

Let's start with the `SalesOrder` table.

Our query contains the following filter:

```sql
WHERE so.OrderDate >= '20250601'
  AND so.OrderDate <  '20250602'
```

This condition selects orders from **June 1, 2025**.

Notice that we use a range rather than comparing the date with a single value. This also works correctly when `OrderDate` contains a time component.

### Why does SQL Server scan the table?

The `SalesOrder` table contains approximately **10 million rows**, but only about **5,477 rows** match the selected date in our reference dataset.

Without a suitable index on `OrderDate`, SQL Server cannot directly locate the matching date range through an index seek.

In our initial execution plan, it therefore performs a **Table Scan**.

This means SQL Server examines the heap's data pages to find rows satisfying the filter.

### Inspect the Table Scan operator

In the Actual Execution Plan:

1. Find the `Table Scan` operator for `dbo.SalesOrder`.
2. Click the operator and press **F4** to open Properties.
3. Find the following values:

| Property | Reference value | Meaning |
|---|---:|---|
| Actual Number of Rows Read | 10,000,000 | Rows examined by the operator |
| Actual Number of Rows | 5,477 | Rows returned after filtering |
| Predicate | `OrderDate` range | Condition used to filter rows |

The exact property names may vary slightly depending on the SQL Server version.

**What does this tell us?**

SQL Server examines **10 million rows to return only 5,477**.
That means approximately **99.95% of the examined rows do not match the filter**.
This is the main inefficiency we want to address.

### Rows are not pages

Remember from Lab 05 that SQL Server stores data in **8 KB pages**.
The values above describe rows, not the number of pages read.

To measure page access, look at the `STATISTICS IO` output in the **Messages** tab.

For example, the original reference measurement reported approximately 57,000 logical reads for `SalesOrder`.

These are logical page accesses through the buffer pool, not necessarily physical disk reads.

> [!IMPORTANT]
> A query can return only a few rows while still reading a very large amount of data.
>
> **The number of rows returned does not tell us how much work SQL Server performed to find them.**

## 7.3 Investigate the `SalesOrderItem` scan — the main bottleneck

We have seen that SQL Server examines 10 million rows in `SalesOrder` to find approximately 5,477 orders for the selected date.

However, finding the orders is only the first part of the query.

We also need to find **all order items belonging to those orders**.

### How are orders and order items connected?

The query uses the following join condition:

```sql
soi.SalesOrderId = so.SalesOrderId
```

Each order can contain multiple order items. The `SalesOrderId` column in `SalesOrderItem` identifies the order to which each item belongs.

In our reference dataset:

| Description | Number of rows |
|---|---:|
| Total orders in `SalesOrder` | 10,000,000 |
| Orders matching the selected date | 5,477 |
| Total rows in `SalesOrderItem` | 40,000,000 |
| Order items belonging to the selected orders | 21,908 |

The query needs only 21,908 order items, but the `SalesOrderItem` table contains **40 million rows**.

### Why does SQL Server scan SalesOrderItem?

At this stage, there is no suitable index on `SalesOrderItem(SalesOrderId)`.

Although SQL Server knows the `SalesOrderId` values of the selected orders, it has no efficient index-based way to locate the corresponding order items.

In our initial execution plan, SQL Server therefore performs a **Table Scan** on `SalesOrderItem`.

The scan reads the order-item data and supplies rows to the join operator.

The join then identifies which items belong to the selected orders.

> [!IMPORTANT]
> **A JOIN condition does not automatically provide an efficient way to locate matching rows.**
>
> Without a suitable index, SQL Server may need to process a very large input even when only a small number of rows are relevant.

### Inspect the Table Scan operator

In the Actual Execution Plan:

1. Find the `Table Scan` operator for `dbo.SalesOrderItem`.
2. Select the operator and press **F4** to open Properties.
3. Examine the following values:

| Property | Reference value | Meaning |
|---|---:|---|
| Actual Number of Rows | 40,000,000 | Rows produced by the scan |
| Actual Number of Rows Read | 40,000,000 | Rows examined by the scan |
| Predicate | None | The scan does not filter rows by the selected order IDs |

Notice the difference compared with the `SalesOrder` scan.

For `SalesOrder`, the date condition filters 10 million examined rows down to 5,477.

For `SalesOrderItem`, the scan produces **all 40 million rows**. The filtering to matching orders happens later, during the join.

### What about logical reads?

Look at the `STATISTICS IO` output in the Messages tab.

In the original reference measurement, `SalesOrderItem` required approximately **198,000 logical reads**.

Remember that a logical read represents an 8 KB page access through the buffer pool.

This is a large amount of work, even when most pages are already cached in memory.

Compare the two large tables:

| Table | Logical reads (approximately) |
|---|---:|
| `SalesOrder` | 57,000 |
| `SalesOrderItem` | 198,000 |

The order-item table requires substantially more page accesses.

This helps explain why it is the main bottleneck in our initial execution plan.


## 7.4 Why `Hash Match (Inner Join)` may be chosen

In our initial execution plan, SQL Server uses **Hash Match (Inner Join)** to connect the selected orders with their order items.

A Hash Join works in two main phases:

1. **Build phase:** SQL Server reads one input and builds a hash table in memory using the join key.
2. **Probe phase:** SQL Server reads the other input and uses the hash table to find matching rows.

In our example, SQL Server can build a hash table from the approximately **5,477 selected orders** and use it to match rows from the much larger `SalesOrderItem` input.

This avoids comparing every order item with every selected order.

### Why is Hash Match useful here?

Without an index on `SalesOrderItem(SalesOrderId)`, SQL Server cannot efficiently locate the items belonging to each order.

A Hash Join allows SQL Server to process the large input and find matching rows without repeatedly scanning the entire table for each order.

However, **the Hash Join does not eliminate the expensive scan of 40 million order items**.

> [!IMPORTANT]
> **Hash Match is not a bad operator.** It is often an efficient choice for joining large datasets.
>
> In our example, the main performance problem is the amount of data that must be read, not the join algorithm itself.

### Inspect the Hash Match operator

In the Actual Execution Plan, find the `Hash Match (Inner Join)` connecting `SalesOrder` and `SalesOrderItem`.

Open its Properties and examine the join condition and the number of rows flowing through the operator.

In our reference plan, the join produces approximately **21,908 matching order items**.

*Note: The build/probe description is simplified. The actual input roles depend on the execution plan.*


## 7.5 Why scanning `Product` may be fine

Our query also joins the `Product` table, which contains approximately **30,000 rows**.

In the reference execution plan, SQL Server uses a **Clustered Index Scan** to read the `Product` table.

Although the table has a clustered index, SQL Server may still choose to scan it rather than perform individual index seeks.

Why?

Because scanning a relatively small table can be more efficient than performing many separate lookups, especially when a large proportion of its rows is needed.

**Compare the scans in the execution plan:**

- `SalesOrder`: approximately 10 million rows examined.
- `SalesOrderItem`: approximately 40 million rows examined.
- `Product`: approximately 30,000 rows examined.

All three operators read rows, but the amount of work is very different.

> [!TIP]
> **A Scan is not necessarily a performance problem.**
>
> Do not try to eliminate every scan in an execution plan. Focus on operations that read or process unnecessarily large amounts of data.

### Think about it

**Why might scanning 30,000 products be more efficient than performing thousands of individual index seeks?**

<details>
<summary>Show answer</summary>

A scan can read the required pages sequentially, while many individual seeks may involve repeated index navigation and page accesses.

When a large proportion of the table is needed, scanning it may require less total work.

The optimizer compares the estimated costs of these alternatives.

</details>

## 7.6 `Compute Scalar`, aggregation, and sorting

After joining the tables, SQL Server still needs to **calculate revenue, group the results by product category, and sort the final output**.

Let's examine the operators responsible for these operations.

### Compute Scalar

The `Compute Scalar` operator defines calculated expressions.

In our query, each order item's revenue is calculated using:

```sql
CAST(soi.Quantity AS decimal(18,2)) * soi.UnitPrice
```

In the execution plan, select the `Compute Scalar` operator and inspect its **Defined Values** property.

You should find an expression corresponding to this calculation.

> [!NOTE]
> SQL Server may defer the actual evaluation of scalar expressions until another operator needs their values. Therefore, `Compute Scalar` does not necessarily mean that every calculation is performed immediately at that point in the plan.

### Hash Match (Aggregate)

Our query groups the results by product category:

```sql
GROUP BY p.CategoryId
```

The `Hash Match (Aggregate)` operator groups rows with the same `CategoryId` and calculates aggregate values such as `SUM`.

In our reference execution plan:

- Approximately **21,908 order items** contribute to the aggregation.
- The operator produces **100 groups**, one for each product category represented in the result.

Notice that the number of output rows is much smaller than the number of input rows.

**This is the purpose of aggregation:** many individual rows are combined into a smaller number of summary rows.

### Sort

Finally, the query sorts the aggregated results:

```sql
ORDER BY Revenue DESC
```

The `Sort` operator arranges the category totals from highest to lowest revenue.

In the execution plan, inspect the **Order By** property to see which expression determines the sorting order.

Because the aggregation produces only approximately **100 rows**, this final sort is relatively small compared with the earlier scans of millions of rows.

> [!NOTE]
> SQL Server does not always use these exact operators for calculations, grouping, or sorting. The optimizer chooses a physical execution strategy based on the query, available indexes, estimated row counts, and other factors.


## 7.7 Missing Index recommendations

A green missing-index suggestion may appear above the graphical plan. It may resemble:

```sql
-- Illustrative recommendation only, not a command to execute now
CREATE NONCLUSTERED INDEX ...
ON dbo.SalesOrder (OrderDate)
INCLUDE (SalesOrderId);
```

This recommendation is based on the optimizer's view of a **particular query**, not on the complete database workload. It does not fully account for existing overlapping indexes, maintenance overhead, storage costs, or other queries.

> [!WARNING]
> **Do not create suggested indexes yet.** We will add indexes deliberately in Section 8. After introducing a clustered primary key on `SalesOrderId`, its clustered key is already available as the row locator in the nonclustered `OrderDate` index. Explicit `INCLUDE (SalesOrderId)` is unnecessary in that design.

## Check your understanding

1. What is the difference between **rows read**, **rows returned**, and **logical reads**?
2. Why can scanning 10 million orders return only 5,477 relevant orders?
3. Why is `SalesOrderItem` the main bottleneck, despite having a join predicate?
4. Why might `Hash Match` be a reasonable join strategy before adding indexes?
5. Why is a scan of `Product` not necessarily a problem?
6. Which SQL clauses correspond to `Compute Scalar`, `Hash Match (Aggregate)`, and `Sort`?
7. Why should you not blindly create every Missing Index recommendation?

<details>
<summary>Show answers</summary>

1. Rows read are examined by an access operator; rows returned pass its filter; logical reads count 8 KB page accesses through the buffer pool.
2. The date filter is selective, but without a suitable index the engine may still inspect the whole heap to find the matches.
3. The join key is not indexed for the needed access pattern, so the engine may process a 40-million-row input for roughly 21,908 matching items.
4. It can efficiently match large unsorted inputs when no suitable repeated seek path exists.
5. Its table is much smaller; the overall cost of the scan can be low.
6. Arithmetic expression; `GROUP BY` and aggregates; `ORDER BY`.
7. Suggestions are query-specific and may overlap indexes or add unnecessary write and storage costs.

</details>

---

# 8. Create indexes and observe the changing plan

## 8.1 Create clustered primary keys

Until now, `SalesOrder` and `SalesOrderItem` have been stored as **heaps**, without clustered indexes.

We will now create a clustered primary key on each table.

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

### What changes when we create a clustered index?

Creating a clustered index changes how the table's rows are organized.

- The table is no longer a heap.
- The actual data rows become the **leaf level of the clustered index**.
- The rows are logically organized by the clustered key.
- SQL Server creates the necessary root and intermediate index pages for navigating the tree.

Remember that the clustered index defines a **logical key order**, not necessarily the physical order of pages on disk.

> [!NOTE]
> Creating a clustered index on a large heap can be an expensive operation because SQL Server must build the new index structure and organize the existing rows.

### Inspect the new indexes

In SSMS Object Explorer, expand the **Indexes** nodes under `SalesOrder` and `SalesOrderItem`.

Verify that the following indexes exist:

- `PK_SalesOrder` – clustered index on `SalesOrderId`.
- `PK_SalesOrderItem` – clustered index on `SalesOrderItemId`.

### Run the main query again

Execute **exactly the same query from Section 6.2**, with Actual Execution Plan enabled.

Compare the new plan with the original one.

![Execution plan after creating clustered primary keys](../images/lab06/execution-plan-after-clustered-pk.svg)

In our reference execution plan, the access operators change:

| Table | Before | After clustered PK |
|---|---|---|
| `SalesOrder` | Table Scan | Clustered Index Scan |
| `SalesOrderItem` | Table Scan | Clustered Index Scan |
| `Product` | Clustered Index Scan | Clustered Index Scan |

However, the important observation is that **the large scans remain**.

SQL Server still examines approximately:

- **10 million** rows from `SalesOrder`.
- **40 million** rows from `SalesOrderItem`.

The optimizer also continues to use `Hash Match` to join the large inputs.

### Why didn't the clustered indexes solve the problem?

The clustered indexes organize rows by:

- `SalesOrder.SalesOrderId`
- `SalesOrderItem.SalesOrderItemId`

However, our query uses different columns for filtering and joining:

```sql
WHERE so.OrderDate >= '20250601'
  AND so.OrderDate < '20250602'
```

```sql
soi.SalesOrderId = so.SalesOrderId
```

The clustered index on `SalesOrderId` does not provide an efficient way to locate orders by `OrderDate`.

Similarly, the clustered index on `SalesOrderItemId` does not provide an efficient way to locate order items by their `SalesOrderId`.

The indexes are useful for searches using their clustered keys, but they do not directly support the access patterns required by our query.

> [!IMPORTANT]
> **Creating an index does not automatically make every query faster.**
>
> An index is most useful when its key columns support the query's filtering, joining, or ordering requirements.

### Check your understanding

**Why does SQL Server still scan both large tables even after creating clustered primary keys?**

<details>
<summary>Show answer</summary>

Because the clustered indexes are organized by `SalesOrderId` and `SalesOrderItemId`, while our query filters orders by `OrderDate` and finds order items using `SalesOrderId`.

These access patterns are not efficiently supported by the new clustered indexes.

In the next sections, we will create nonclustered indexes specifically designed for these operations.

</details>

## 8.2 Create an index for the `SalesOrder` date filter

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrder_OrderDate
ON dbo.SalesOrder (OrderDate);
GO
```

The index key is `OrderDate` because the query's filter is a date range. `SalesOrderId` is the clustered key and is therefore already available as the nonclustered index's row locator. This makes the index sufficient to obtain the order IDs needed by the join without explicitly adding `SalesOrderId` to `INCLUDE`.

**Inspect:** expand the index in SSMS and check its key column. Remember the difference between the indexed **key** and an **implicit clustered-key locator**.

![Execution plan after the OrderDate index: SalesOrder switches to an Index Seek reading only 5,477 rows, while SalesOrderItem is still fully scanned](../images/lab06/execution-plan-after-orderdate.svg)

Rerun the main query and compare: `SalesOrder` now shows an `Index Seek` on `IX_SalesOrder_OrderDate`, reading only the 5,477 matching rows instead of 10 million. `SalesOrderItem` is unaffected — it has no useful index yet, so it is still fully scanned. The join itself may still be a `Hash Match`, since one of its two inputs is still enormous.

<details>
<summary>Show reference results from one computer</summary>

| Metric | Before `IX_SalesOrder_OrderDate` | After `IX_SalesOrder_OrderDate` |
|---|---:|---:|
| `SalesOrder` logical reads | 57,266 | **15** |
| `SalesOrderItem` logical reads | 198,439 | 198,439 (unchanged) |
| `Product` logical reads | 161 | 161 (unchanged) |
| CPU time | 13.25 s | 12.05 s |
| Elapsed time | 14.1 s | 13.1 s |

`SalesOrder`'s logical reads collapse from 57,266 to 15 — a seek through a handful of index pages instead of a full table read. The overall query is only modestly faster so far, because `SalesOrderItem` — the much larger table — is still scanned in full; that is the next bottleneck to address.

</details>

## 8.3 Create the order-item index *without* included columns

First create a narrow index on the join column:

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrderItem_SalesOrderId
ON dbo.SalesOrderItem (SalesOrderId);
GO
```

Run this isolated query with the Actual Execution Plan enabled:

```sql
SELECT ProductId, Quantity, UnitPrice
FROM dbo.SalesOrderItem
WHERE SalesOrderId = 1;
GO
```

The index helps SQL Server find rows matching `SalesOrderId`, but does **not** contain the requested `ProductId`, `Quantity`, and `UnitPrice` values. The optimizer may therefore choose an **Index Seek** followed by a **Key Lookup** in `PK_SalesOrderItem`.

In the plan, inspect the following:

- **Index Seek:** its Object should reference `IX_SalesOrderItem_SalesOrderId`; inspect its Seek Predicates.
- **Key Lookup (Clustered):** its Object should reference `PK_SalesOrderItem`; inspect Output List and number of executions.
- **Nested Loops:** it may connect the seek and lookup; repeated lookups can become expensive for many matching rows.

A Key Lookup is not automatically slow for a few rows. It can become costly when repeated thousands of times. The optimizer may instead choose a scan when lookups are estimated to be too expensive.

> [!NOTE]
> A lookup is **not guaranteed** for this particular `SalesOrderId` on every dataset or version. If the optimizer selects a different access path, use the plan properties to explain the choice. Do not force an index unless you are explicitly studying the effect of a forced plan.

**Optional — see the same Key Lookup at full scale.** Rerun the **main query from Section 6.2** with this narrow index still in place (before creating the `INCLUDE` version in 8.4):

![Execution plan with the narrow SalesOrderId index and no INCLUDE: both large tables use an Index Seek, but a Nested Loops + Clustered Index Seek lookup runs once per matching order item](../images/lab06/execution-plan-after-salesorderid.svg)

Both `SalesOrder` and `SalesOrderItem` now use an `Index Seek`, but `SalesOrderItem`'s seek is immediately followed by a `Clustered Index Seek` lookup into `PK_SalesOrderItem` — run once per matching row. For the isolated single-order query above, that was one lookup; for the full query, it is **21,908** lookups, one per order item. This is the same `Key Lookup` pattern, just visible at the scale the main query actually operates at.

<details>
<summary>Show reference results from one computer</summary>

| Metric | After `IX_SalesOrder_OrderDate` only | After narrow `IX_SalesOrderItem_SalesOrderId` (no `INCLUDE`) |
|---|---:|---:|
| `SalesOrder` logical reads | 15 | 15 (unchanged) |
| `SalesOrderItem` logical reads | 198,439 | **106,449** |
| `SalesOrderItem` scan count | 1 | **5,477** (one seek per matching order) |
| `Product` logical reads | 161 | 161 (unchanged) |
| CPU time | 12.05 s | **0.28 s** |
| Elapsed time | 13.1 s | **0.76 s** |

This is already a dramatic speedup — Nested Loops with 5,477 cheap seeks beats a 40-million-row `Hash Match` input by a wide margin, even with a `Key Lookup` on every one of the 21,908 matching rows. `SalesOrderItem`'s logical reads (106,449) are still far higher than they need to be, though: each lookup costs extra page accesses that a covering index can avoid entirely — the point of Section 8.4.

</details>

## 8.4 Recreate the order-item index with `INCLUDE`

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

Run the isolated query again. This index now contains everything required from `SalesOrderItem`, so a **Key Lookup is not needed** to obtain those three columns. Compare its plan with the previous one.

| Part of index | Columns | Role |
|---|---|---|
| Key | `SalesOrderId` | Locates matching order items through the B+ tree |
| Included | `ProductId`, `Quantity`, `UnitPrice` | Supplies required columns at leaf level |
| Implicit row locator | `SalesOrderItemId` | Clustered key needed to identify the complete row |

The main query needs these columns for joining `Product` (`ProductId`) and calculating revenue (`Quantity`, `UnitPrice`). This index is **covering** for the `SalesOrderItem` portion of the query.

> [!IMPORTANT]
> `INCLUDE` columns are stored at the leaf level; they do not extend the sorted search key. An included column can still support a residual filter or be used in `GROUP BY` or calculations, but it does not have the same seek or sort-order benefits as a leading key column.

---

# 9. Re-run the baseline query and compare plans

Execute **exactly the same SELECT from Section 6.2**, with both `STATISTICS IO` and `STATISTICS TIME` still on and Actual Execution Plan enabled. Do not modify the `WHERE`, joins, grouping, or ordering.

## 9.1 Start with the access operators

The original plan may have scanned large portions of `SalesOrder` and `SalesOrderItem`. After creating the targeted indexes, inspect whether the optimizer can use:

- **Index Seek on `IX_SalesOrder_OrderDate`** to find the relevant date range.
- **Index Seek on `IX_SalesOrderItem_SalesOrderId`** to find items for the selected order IDs.
- **A join algorithm such as Nested Loops** to combine the relatively small outer input with repeated efficient inner seeks.

**In SSMS:** click each relevant seek and inspect **Seek Predicates**. For the date index you should see a date-range condition; for the item index you should see a condition on `SalesOrderId` (subject to the optimizer's chosen plan).

![Execution plan after the covering INCLUDE index: both large tables use an Index Seek with no Key Lookup, joined by Nested Loops](../images/lab06/execution-plan-after-include.svg)

Compare this with the [Section 7 "before" plan](#7-investigate-the-execution-plan-before-indexing): both `Table Scan` operators are gone, replaced by `Index Seek` operators that read only the matching rows, and the `Key Lookup` from Section 8.3 is gone too — `IX_SalesOrderItem_SalesOrderId`'s `INCLUDE` columns supply everything the query needs. The two `Hash Match (Inner Join)` operators have also become `Nested Loops`, now that the inner side of each join can be found with an efficient seek instead of a full scan.

<details>
<summary>Show reference results from one computer</summary>

| Metric | Before any indexes | After narrow index (8.3) | After `INCLUDE` (8.4, final) |
|---|---:|---:|---:|
| `SalesOrder` logical reads | 57,143 | 15 | 15 |
| `SalesOrderItem` logical reads | 198,020 | 106,449 | **32,710** |
| `Product` logical reads | 161 | 161 | 161 |
| CPU time | 14.7 s | 0.28 s | **0.11 s** |
| Elapsed time | 18.1 s | 0.76 s | **0.23 s** |

Removing the `Key Lookup` cuts `SalesOrderItem`'s logical reads by roughly two-thirds again (106,449 → 32,710), and elapsed time drops from the full heap scan's 18.1 s to 0.23 s — about an **80× speedup** on this computer. The row counts (5,477 orders, 21,908 order items, 100 category groups) never changed; only the access paths did.

</details>

## 9.2 Why `Nested Loops` can become attractive

A simplified mental model of a nested-loops join is:

```text
for each matching order:
    seek its matching order items using SalesOrderId
```

Before indexing, repeated scans of `SalesOrderItem` would be unacceptably expensive. With an index on `SalesOrderId`, the inner input can be found through efficient index navigation. This can make Nested Loops cheaper than building or probing a hash join over an enormous item-table scan.

In the actual plan, compare the outer input's row count with the inner seek's **Number of Executions** or related runtime counters. A small number of logical reads per seek can still add up when the seek is repeated thousands of times. This is why the optimized query may still report tens of thousands of logical reads for `SalesOrderItem`.

> [!NOTE]
> The optimizer may still prefer `Hash Match`, `Merge Join`, a different access order, or a parallel plan. Indexes make new strategies **available**; they do not guarantee a particular one.

## 9.3 Compare logical I/O, CPU, and elapsed time

The original lab recorded the following approximate reference values on SQL Server Express:

| Metric | Before indexes | After indexes |
|---|---:|---:|
| `SalesOrder` access | Table Scan | Index Seek |
| Relevant orders | ~5,477 | ~5,477 |
| `SalesOrderItem` access | Table Scan | Index Seek |
| Relevant order items | ~21,908 | ~21,908 |
| Large item input processed | ~40,000,000 rows | ~21,908 matching rows |
| Main join | Hash Match | Nested Loops |
| `SalesOrder` logical reads | ~57,000 | ~15 |
| `SalesOrderItem` logical reads | ~198,000 | ~54,000 |
| Elapsed time | ~17 s | ~0.5 s |

These are **reference measurements, not expected fixed answers**. The large reduction in work is the central observation. The number of matching records did not change, and the SQL statement did not change; **the physical access paths did**.

### Calculate your own improvement

Using the numbers you recorded in Section 7:

- **Speedup** = before elapsed time / after elapsed time.
- **Logical-read reduction (%)** = 100 × (before reads − after reads) / before reads.

Compare logical reads **per table**, not only total execution time. Note that a higher number of indexed seeks can produce many logical reads, even when the plan is much faster than the original large scans.

## 9.4 Editions and parallel execution

The original lab also compared Express with Developer/Enterprise on the same computer and data:

| Reference measurement | Express | Developer / Enterprise |
|---|---:|---:|
| Execution before indexes | Serial in reference test | Parallel in reference test |
| Elapsed before indexes | ~17 s | ~1.3 s |
| Elapsed after indexes | ~0.5 s | ~0.17 s |
| Approximate speedup due to indexes | ~33× | ~8× |

The difference illustrates why **hardware, configured parallelism, memory, and edition capabilities** influence observed timing. A parallel plan can reduce elapsed time by using multiple workers, but it does not eliminate unnecessary logical I/O caused by a poor access path. In your own results, do not infer the edition or degree of parallelism from elapsed time alone; inspect plan properties.

> [!IMPORTANT]
> **The indexes did not make SQL Server faster at processing 40 million irrelevant order items. They allowed the engine to avoid processing most of them.**

## 9.5 A structured plan-comparison exercise

Open the **before** and **after** execution plans (if necessary, save the `.sqlplan` files in SSMS for comparison). Answer these questions using the actual plan rather than guessing:

1. Which operator reads `SalesOrder` before indexing, and which operator reads it afterward?
2. Which `SalesOrderItem` access path is used in each plan?
3. Which join algorithm combines orders and items before and after indexing?
4. Where do the rows that reach the join come from? Compare estimates and actuals.
5. Did the scan of `Product` disappear? If not, does that automatically mean the plan is inefficient?
6. Which expressions are calculated by `Compute Scalar`, and which operators handle aggregation and sorting?
7. Did the logical reads for the two large tables drop? Which table shows the greatest relative improvement?
8. Are the reference numbers from the lab identical to yours? Explain why a difference is expected.

<details>
<summary>Show discussion points</summary>

1. In the original reference plan the `SalesOrder` heap was scanned; after adding the date index the plan used an Index Seek.
2. The original reference plan scanned the large order-item input; the new index supports seeks by `SalesOrderId`.
3. The reference changed from a Hash Match join to Nested Loops. Either choice can be reasonable for different inputs and indexes.
4. The join receives relevant orders and their matching items; indexes reduce the amount of unrelated data read. Inspect each student's actual row counts.
5. Not necessarily. A smaller `Product` scan may still be cheap.
6. The arithmetic expression, `GROUP BY`, and `ORDER BY` remain part of the query even when the access path changes. Exact physical operators may vary.
7. The original reference showed `SalesOrder` logical reads decreasing from roughly 57,000 to 15, and `SalesOrderItem` from roughly 198,000 to 54,000.
8. Hardware, caching, statistics, edition, parallelism, data distribution, and other workloads affect measurements and plans.

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

The following illustrations continue the nonclustered `MemberID` index from Section 3.2 (the same initial tree: keys 11, 19, 27, 43, 56, 61, 73, 79). Three new members are inserted one at a time, in this order:

```sql
-- Illustrative statements: not executed against IndexLab
INSERT INTO Member (MemberID, FirstName, LastName)
VALUES (58, 'Daniel', 'Hayes');

INSERT INTO Member (MemberID, FirstName, LastName)
VALUES (60, 'Ryan', 'Mitchell');

INSERT INTO Member (MemberID, FirstName, LastName)
VALUES (75, 'Olivia', 'Bennett');
```

Each `INSERT` adds one new key to the index — `MemberID` 58, then 60, then 75 — in the order shown above. The page capacities below are intentionally simplified so that the resulting splits are visible:

![Step-by-step insertion into a simplified B+ tree](../images/lab06/bplus-tree-insert-steps.svg)

Inserting 58 and 60 each cause one leaf split; inserting 75 causes a leaf split **and** a root split, growing the tree from 3 levels to 4:

![Final B+ tree after the insertions](../images/lab06/bplus-tree-after-insert.svg)

The next example repeats the same three insertions (58, 60, 75) against the **clustered** version of the index from Section 4, where leaf pages hold the data rows themselves rather than key/RID pairs:

![Insertion into a clustered index](../images/lab06/clustered-index-insert.svg)

> [!WARNING]
> These diagrams model a very small maximum number of entries per node. Real SQL Server pages are 8 KB and can hold variable numbers of records, depending on row size and available space. The drawings are **conceptual**, not physical page byte layouts.

> [!IMPORTANT]
> **Indexes are not free.** Every nonclustered index must be kept in sync with the table: each `INSERT`, `UPDATE`, or `DELETE` that touches an indexed column also writes to every index built on it, not just to the table itself. This is the cost side of the trade-off the rest of this lab has been measuring the benefit of — and it is the reason the checklist in Section 13 asks whether an index is actually needed before creating it.

That cost sits alongside the benefits measured earlier in this lab:

- Faster and more targeted reads for some access patterns.
- Additional storage for index pages.
- Extra writes and maintenance when indexed data changes.
- Possible page splits and fragmentation.

<details>
<summary>Show reference results from one computer</summary>

A single-row `INSERT` into `dbo.SalesOrder`, measured with `STATISTICS IO` on one SQL Server 2025 Express instance:

| Indexes on `SalesOrder` | Logical writes for one `INSERT` |
|---|---:|
| `PK_SalesOrder` (clustered) only | **3** |
| `PK_SalesOrder` + `IX_SalesOrder_OrderDate` | **6** |

Adding one nonclustered index **doubled** the logical writes for this insert — the clustered row itself still needs writing, plus a separate entry in the nonclustered index's own B+ tree. Every additional index on a frequently written table repeats this cost on every matching insert, update, or delete — and unlike a read, this work cannot be skipped just because the resulting index happens not to be useful for any query that runs.

</details>

Repeated page splits leave pages only partially full and scatter logically adjacent pages across the file, which is called **fragmentation**. You can inspect it with the same `sys.dm_db_index_physical_stats` call from Section 10 — its `avg_fragmentation_in_percent` column reports it directly. Two maintenance commands address it:

```sql
-- Reorders pages in place; an online, lower-impact operation
ALTER INDEX IX_SalesOrder_OrderDate ON dbo.SalesOrder REORGANIZE;
GO

-- Rebuilds the index from scratch; more thorough, but more resource-intensive
ALTER INDEX IX_SalesOrder_OrderDate ON dbo.SalesOrder REBUILD;
GO
```

`REORGANIZE` is generally used for lighter fragmentation, `REBUILD` for heavier fragmentation or to also update statistics with a full scan. Neither is “free”: both consume I/O and CPU, so they are normally scheduled as periodic maintenance rather than run reactively after every change.

Do not index every column automatically. Choose indexes that support important, frequent queries.

## Check your understanding

1. Why does reordering predicates in a query's `WHERE` clause not change which column should be the leading key of a composite index?
2. Why can a rare `Status` value be a good index candidate even when the column has few distinct values overall?
3. What is the difference between a key column and an included column in a nonclustered index?
4. What causes a page split, and what is its effect on index pages?
5. What is the difference between `ALTER INDEX ... REORGANIZE` and `ALTER INDEX ... REBUILD`?
6. Why isn't it a good idea to add an index for every column "just in case"?

<details>
<summary>Show answers</summary>

1. An index's key order is fixed when the index is created; the optimizer can only use a composite index's leading column(s) to seek, regardless of how the `WHERE` clause predicates happen to be written.
2. Selectivity depends on how many rows a specific value matches, not on how many distinct values the column has overall. A rare status value still filters out most rows, even if the column itself has only a handful of possible values.
3. A key column defines the index's sort order and can be used for seeking and ordering. An included column is stored only at the leaf level to help cover a query; it does not participate in the sort order or support a seek on its own.
4. A page split happens when a new or updated entry no longer fits on its current index page. SQL Server allocates a new page and redistributes entries, which can leave pages partially full and scatter logically adjacent pages, causing fragmentation.
5. `REORGANIZE` reorders existing pages in place and is a lighter, online operation suited to mild fragmentation. `REBUILD` recreates the index from scratch, which is more thorough (and can refresh statistics with a full scan) but is more resource-intensive.
6. Every additional index adds storage and must be maintained on every `INSERT`, `UPDATE`, or `DELETE` that touches its columns, so indexes should be chosen to support actual, frequent query patterns rather than added speculatively.

</details>

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

---

## Additional practice

More index exercises, using `AdventureWorksENG` instead of `IndexLab`, are available in [Index Exercises](../exercises/indexes.md).
