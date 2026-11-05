# Lab 06 – Indexes in SQL Server

> [!TIP]
> How to use this lab
>
> Your instructor will demonstrate the main concepts and the indexing process during the laboratory session.
>
> You are not expected to memorize every detail or complete every section during class. Use this manual to follow the demonstrations, explore the SQL examples independently, and review the explanations at your own pace.
>
> You can also return to the exercises and detailed explanations after the laboratory session.

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
- **Tree depth:** the number of edges from the root to a leaf. In our diagrams, the root is at Level 0, so a leaf at Level 3 has a depth of 3. In database documentation, index depth may also be expressed as the number of levels, including the root and leaf levels.

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

1. At the root page. In a single-page index, that page is also the leaf.
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

This is a simplified redrawing of the actual plan measured on one computer (the reference results above) — same operators and row counts, laid out for readability. Your plan may differ from this reference example. Focus on the access methods, row counts, and amount of work performed rather than expecting an identical plan shape. Icon style and layout may also differ by SSMS version.

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

<details>
<summary>Show reference results from one computer</summary>

| Metric | Value |
|---|---|
| `SalesOrder` logical reads | 57,266 |
| `SalesOrderItem` logical reads | 198,439 |
| `Product` logical reads | 161 |
| CPU time | 13.25 s |
| Elapsed time | 14.1 s |

Logical reads remain very similar to the heap baseline (57,143 / 198,020 / 161, ~14.7 s CPU / ~18.1 s elapsed). Creating the clustered indexes changed the storage structure, but both large tables are still read in full. The total logical-read counts alone do not identify which pages account for the small difference.

</details>

## 8.2 Create an index for the `SalesOrder` date filter

In the previous step, we created clustered primary keys on `SalesOrder` and `SalesOrderItem`.

However, the execution plan still showed large scans because the clustered indexes did not directly support the query's filtering and joining conditions.

Let's address the first problem: **finding orders for a specific date**.

### Why index OrderDate?

Our main query filters orders using:

```sql
WHERE so.OrderDate >= '20250601'
  AND so.OrderDate < '20250602'
```

Without a suitable index, SQL Server must examine a large number of rows to identify the orders within this date range.

We can improve this by creating a nonclustered index on `OrderDate`.

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrder_OrderDate
ON dbo.SalesOrder (OrderDate);
GO
```

The index organizes entries by `OrderDate`, allowing SQL Server to navigate directly to the relevant range instead of scanning the entire clustered index.

### Run the main query again

Execute **exactly the same query from Section 6.2**, with Actual Execution Plan enabled.

![Execution plan after creating the OrderDate index](../images/lab06/execution-plan-after-orderdate.svg)

Compare the new execution plan with the previous one.

In our reference execution plan:

| Table | After clustered PK | After OrderDate index |
|---|---|---|
| `SalesOrder` | Clustered Index Scan | **Index Seek** |
| `SalesOrderItem` | Clustered Index Scan | Clustered Index Scan |
| Main join | Hash Match | Hash Match |

The most important change is the access to `SalesOrder`.

Before creating the index, SQL Server examined approximately **10 million rows** to find 5,477 orders.

After creating the index, it can locate the relevant date range through an **Index Seek**, examining approximately **5,477 matching index entries**.

### Inspect the Index Seek operator

In SSMS:

1. Select the `Index Seek` operator for `IX_SalesOrder_OrderDate`.
2. Press **F4** to open its Properties.
3. Find the **Seek Predicates** property.

You should see a condition corresponding to the requested `OrderDate` range.

Unlike the previous scan, SQL Server can use the index's ordered keys to locate the beginning of the range and read the matching entries.

Compare **Actual Number of Rows Read** and **Actual Number of Rows**. In our reference plan, these values are approximately equal because the seek reads the relevant entries.

> [!IMPORTANT]
> **An Index Seek does not necessarily retrieve only one row.**
>
> It can efficiently locate a range of values and return many matching rows without scanning the entire index.

### What problem remains?

Although we have improved access to `SalesOrder`, the execution plan still contains a large `Clustered Index Scan` on `SalesOrderItem`.

SQL Server still processes approximately **40 million order items** to find those belonging to the selected orders.

The new `OrderDate` index helps SQL Server find orders, but it does not provide an efficient way to locate their items.

This demonstrates an important principle:

**An index can improve one part of an execution plan without solving every performance problem in the query.**

In the next section, we will create an index on `SalesOrderItem(SalesOrderId)` to address the remaining large scan.

### Check your understanding

**Why did the new index eliminate the SalesOrder scan but not the SalesOrderItem scan?**

<details>
<summary>Show answer</summary>

The new index is created on `SalesOrder(OrderDate)`, so it helps SQL Server find orders matching the requested date range.

However, `SalesOrderItem` is a separate table. Its rows are not organized by `SalesOrderId` in a suitable nonclustered index yet.

SQL Server still needs to scan the large order-item table to find the matching items.

</details>

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


## 8.3 Create an index for the `SalesOrderItem` join

In the previous step, we created an index on `SalesOrder(OrderDate)`, allowing SQL Server to efficiently find the 5,477 orders for the selected date.

However, the execution plan still showed a large scan of approximately **40 million rows** in `SalesOrderItem`.

Let's address this problem by creating an index on the column used to join order items with their orders.

### Create the nonclustered index

Our query joins the tables using:

```sql
soi.SalesOrderId = so.SalesOrderId
```

We can support this operation with a nonclustered index:

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrderItem_SalesOrderId
ON dbo.SalesOrderItem (SalesOrderId);
GO
```

The index organizes order-item entries by `SalesOrderId`.

This allows SQL Server to efficiently locate the items belonging to a particular order without scanning the entire `SalesOrderItem` table.

### Run the main query again

Execute **the same main query from Section 6.2**, with Actual Execution Plan enabled.

![Execution plan after creating the SalesOrderId index](../images/lab06/execution-plan-after-salesorderid.svg)

Compare this execution plan with the previous one.

In our reference execution plan:

| Operation | Before this index | After this index |
|---|---|---|
| `SalesOrder` access | Index Seek | Index Seek |
| `SalesOrderItem` access | Clustered Index Scan | **Index Seek** |
| Main order-item join | Hash Match | **Nested Loops** |
| Order items retrieved | 21,908 matching rows after the join | 21,908 matching index entries |
| Additional clustered index accesses | Not needed for the scan | **21,908** |

This is a major improvement.

Instead of scanning all 40 million order items, SQL Server performs approximately **5,477 index seeks**, one for each selected order, retrieving a total of **21,908 matching order items**.

However, the new plan also introduces additional work.

### Why are additional clustered index accesses needed?

The new nonclustered index contains `SalesOrderId` as its search key.

However, our query also needs other columns from `SalesOrderItem`:

- `ProductId` – to join with the `Product` table.
- `Quantity` – to calculate the number of items sold and revenue.
- `UnitPrice` – to calculate revenue.

These columns are not stored in our narrow nonclustered index.

Therefore, after finding the matching index entries, SQL Server must retrieve the missing columns from the clustered index.

In our reference execution plan, this requires approximately **21,908 additional clustered index accesses**.

> [!IMPORTANT]
> **An index can efficiently locate matching rows without containing all the data required by the query.**
>
> When additional columns are needed, SQL Server may have to retrieve them from the underlying table.

### Inspect the additional data retrieval

In the Actual Execution Plan, locate the additional `Clustered Index Seek` on `PK_SalesOrderItem`.

Inspect its Properties and identify:

- **Object:** `PK_SalesOrderItem`.
- **Number of Executions:** approximately 21,908.
- **Output List:** the additional columns required by the query.

Notice that this operator is executed repeatedly, once for each matching order item in our reference plan.

This operation is conceptually similar to a **Key Lookup**, where SQL Server uses the clustered key obtained from a nonclustered index to retrieve missing columns.

A small number of additional lookups may be inexpensive. However, thousands of repeated accesses can become a significant part of the query's total work.

### A smaller example

To observe this behavior more clearly, execute:

```sql
SELECT ProductId, Quantity, UnitPrice
FROM dbo.SalesOrderItem
WHERE SalesOrderId = 1;
GO
```

The nonclustered index helps SQL Server find the matching order items, but it does not contain the three selected columns.

Depending on the optimizer's choice, the execution plan may show an `Index Seek` followed by a `Key Lookup (Clustered)`.

Inspect the operators and compare the number of executions.

> [!NOTE]
> A Key Lookup is not guaranteed for every query. SQL Server may choose a different access path depending on the estimated cost.

### Check your understanding

**Why does SQL Server perform additional clustered index accesses even though it already found the matching order items using the nonclustered index?**

<details>
<summary>Show answer</summary>

The nonclustered index contains the `SalesOrderId` key and the clustered-key row locator, but it does not contain all the columns required by the query.

SQL Server uses the nonclustered index to find matching order items, then accesses the clustered index to retrieve the missing columns.

In the next section, we will modify the index so that these additional accesses are no longer necessary.

</details>

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

This is already a dramatic speedup — Nested Loops with 5,477 cheap seeks beats a 40-million-row `Hash Match` input by a wide margin, even with an additional clustered index access for each of the 21,908 matching rows. `SalesOrderItem`'s logical reads (106,449) are still far higher than they need to be, though: each lookup costs extra page accesses that a covering index can avoid entirely — the point of Section 8.4.

</details>

## 8.4 Recreate the order-item index with `INCLUDE`

In the previous step, we created a nonclustered index on `SalesOrderItem(SalesOrderId)`.

This eliminated the expensive scan of 40 million order items. However, the execution plan still showed approximately **21,908 additional clustered index accesses** to retrieve columns missing from the nonclustered index.

Can we avoid these additional accesses?

Yes. We can extend the nonclustered index with **included columns**.

### What are included columns?

A nonclustered index can contain two types of explicitly defined columns:

- **Key columns:** determine the logical ordering of index entries and can be used to efficiently locate specific values or ranges.
- **Included columns:** store additional values at the leaf level without becoming part of the index's search key.

For our query, we need the following columns from `SalesOrderItem`:

| Column | Purpose | Index role |
|---|---|---|
| `SalesOrderId` | Find items belonging to selected orders | Key |
| `ProductId` | Join order items with products | Included |
| `Quantity` | Calculate items sold and revenue | Included |
| `UnitPrice` | Calculate revenue | Included |

By including the additional columns, SQL Server can retrieve all the required values directly from the nonclustered index.

### Recreate the index

First, remove the existing narrow index:

```sql
DROP INDEX IX_SalesOrderItem_SalesOrderId
ON dbo.SalesOrderItem;
GO
```

Now create it again with the additional columns:

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrderItem_SalesOrderId
ON dbo.SalesOrderItem (SalesOrderId)
INCLUDE (ProductId, Quantity, UnitPrice);
GO
```

Notice that only `SalesOrderId` is the index key.

The included columns are stored at the leaf level, but they do not change the logical ordering of the index.

### Run the main query again

Execute **exactly the same query from Section 6.2**, with Actual Execution Plan enabled.

![Execution plan after adding INCLUDE columns](../images/lab06/execution-plan-after-include.svg)

Compare this plan with the previous one, before adding `INCLUDE`.

| Operation | Without `INCLUDE` | With `INCLUDE` |
|---|---|---|
| `SalesOrder` access | Index Seek | Index Seek |
| `SalesOrderItem` access | Index Seek | Index Seek |
| Order-item index seeks | 5,477 | 5,477 |
| Matching order items | 21,908 | 21,908 |
| Additional clustered row fetches | **21,908** | **0** |
| Main order-item join | Nested Loops | Nested Loops |

The important difference is that **the additional clustered index accesses have disappeared**.

The nonclustered index now contains all the columns required from `SalesOrderItem`, so SQL Server no longer needs to retrieve them from the clustered index.

### What is a covering index?

An index is called a **covering index** when it contains all the columns required by a particular query, allowing SQL Server to satisfy that part of the query without additional row lookups.

Our index:

```sql
ON dbo.SalesOrderItem (SalesOrderId)
INCLUDE (ProductId, Quantity, UnitPrice)
```

is covering for the `SalesOrderItem` portion of the main query.

> [!IMPORTANT]
> **Covering is a property of an index relative to a query.**
>
> The same index may cover one query but not another query that requires additional columns.

### What about the clustered key?

There is one more detail worth understanding.

Our `SalesOrderItem` table has a clustered primary key on `SalesOrderItemId`.

In a nonclustered index on a clustered table, SQL Server also makes the clustered key available as a **row locator**.

Therefore, our nonclustered index effectively provides:

| Column | Role |
|---|---|
| `SalesOrderId` | Explicit index key |
| `ProductId` | Included column |
| `Quantity` | Included column |
| `UnitPrice` | Included column |
| `SalesOrderItemId` | Implicit clustered-key row locator |

We did not need to explicitly include `SalesOrderItemId`.

The same principle explains why our earlier index on `SalesOrder(OrderDate)` did not require `INCLUDE (SalesOrderId)`: `SalesOrderId` was already the clustered key of that table.

### The complete optimization process

We have now completed all five stages of our indexing demonstration.

The following table summarizes how SQL Server's access strategy changed as we introduced new indexes.

| Stage | `SalesOrder` access | `SalesOrderItem` access | Additional clustered row fetches |
|---|---|---|---|
| 1. Before indexing | Table Scan | Table Scan | — |
| 2. After clustered primary keys | Clustered Index Scan | Clustered Index Scan | — |
| 3. After `OrderDate` index | **Index Seek** | Clustered Index Scan | — |
| 4. After `SalesOrderId` index | Index Seek | **Index Seek** | **21,908** |
| 5. After `INCLUDE` | Index Seek | Index Seek | **0** |

Throughout all five stages:

- **The SQL query remained unchanged.**
- **The number of matching orders remained approximately 5,477.**
- **The number of matching order items remained approximately 21,908.**

What changed was **how SQL Server accessed and processed the data**.

Each new index introduced an access path that allowed the optimizer to choose a different execution strategy.

> [!IMPORTANT]
> **Creating indexes does not change which rows a query should return. It changes how SQL Server can find and process those rows.**
>
> A useful index allows SQL Server to avoid unnecessary work, but it does not guarantee that every query will use it.

### Are included columns always a good idea?

Not necessarily.

Included columns make an index wider, which can increase storage requirements and the work needed to maintain it during `INSERT`, `UPDATE`, and `DELETE` operations.

They should be selected based on the columns required by important queries rather than added automatically.

### Check your understanding

**Why did adding `INCLUDE (ProductId, Quantity, UnitPrice)` eliminate the additional clustered index accesses?**

<details>
<summary>Show answer</summary>

The nonclustered index now contains all the columns required from `SalesOrderItem`.

SQL Server can locate matching order items using `SalesOrderId` and retrieve `ProductId`, `Quantity`, and `UnitPrice` directly from the index's leaf level.

There is no longer a need to access the clustered index to retrieve these values.

</details>

---

We have now seen how different indexes change the execution plan. In the next section, we will compare **logical reads, CPU time, and elapsed time** to measure how much performance actually improved.

---

# 9. Performance comparison and analysis

In Section 8, we gradually introduced indexes and observed how each change affected the execution plan.

We started with expensive scans of millions of rows and ended with a more efficient execution strategy using targeted index seeks and a covering index.

However, **a better-looking execution plan does not automatically mean a faster query**. We need to measure the actual performance to understand how much work SQL Server performs.

In this section, we will compare three important metrics:

- **Logical reads** – how many page accesses SQL Server performs through the buffer pool.
- **CPU time** – how much processor time is spent executing the query.
- **Elapsed time** – how much time passes from the beginning to the end of query execution.

By comparing these measurements before and after indexing, we can evaluate the actual benefits of our indexes.

> [!IMPORTANT]
> **The goal of indexing is not simply to replace Scans with Seeks.**
>
> The goal is to reduce unnecessary work and improve query performance.

## 9.1 Understanding performance metrics

In Section 6.1, we enabled two SQL Server options:

```sql
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
```

These commands provide information about the work SQL Server performs when executing a query.

Let's examine the most important measurements before comparing our results.

### Logical reads

A **logical read** occurs when SQL Server accesses a data or index page through the buffer pool.

As we learned in Lab 05, SQL Server stores data in **8 KB pages**.

For example, consider this simplified `STATISTICS IO` output:

```text
Table 'SalesOrder'.
Scan count 1, logical reads 57000,
physical reads 0, read-ahead reads 0.
```

This means SQL Server performed approximately **57,000 logical page reads** while accessing `SalesOrder`.

Since each page is 8 KB, this represents approximately:

**57,000 logical reads × 8 KB ≈ 445 MiB**

However, this does not necessarily mean that SQL Server transferred 445 MiB from disk.

The pages may already be cached in memory.

> [!IMPORTANT]
> **Logical reads are not the same as physical disk reads.**
>
> Logical reads measure page accesses through the buffer pool, including pages already cached in memory.
>
> A query can perform many logical reads even when physical disk reads are zero.

### Physical reads and read-ahead reads

The `STATISTICS IO` output may also include:

| Metric | Meaning |
|---|---|
| `physical reads` | Pages read from storage because they were not already available in the buffer pool. |
| `read-ahead reads` | Pages SQL Server reads into memory in advance because it expects to need them. |

For this lab, we will focus primarily on **logical reads**, because they help us understand how much page-access work different execution plans perform.

### CPU time and elapsed time

`STATISTICS TIME` provides two important measurements.

A simplified example:

```text
SQL Server Execution Times:
   CPU time = 1200 ms,
   elapsed time = 1500 ms.
```

| Metric | Meaning |
|---|---|
| CPU time | Total processor time consumed while executing the query. |
| Elapsed time | Total wall-clock time taken to execute the query, including time spent waiting. |

In this example, the query used approximately 1.2 seconds of CPU time and finished after 1.5 seconds.

These values are not always similar.

For example, a query may spend time waiting for I/O operations, locks, or other resources. In a parallel execution plan, CPU time can also exceed elapsed time because multiple workers execute simultaneously.

### Why do we need all three measurements?

Each metric tells us something different:

- **Logical reads** help us understand the amount of page-access work.
- **CPU time** helps us understand processor usage.
- **Elapsed time** tells us how long the query actually took.

A query can become faster without reducing all three measurements by the same percentage.

For example, a different execution plan may reduce elapsed time through parallel execution while still processing a large amount of data.

> [!TIP]
> When comparing execution plans, do not look only at elapsed time.
>
> Compare logical reads, CPU time, and elapsed time together. Also remember that caching, concurrent activity, and execution settings can affect the results.

### Check your understanding

**A query reports 50,000 logical reads but zero physical reads. Does this mean SQL Server did not access any data pages?**

<details>
<summary>Show answer</summary>

No.

SQL Server accessed data or index pages approximately 50,000 times through the buffer pool.

The zero physical reads indicate that no demand page reads from storage were reported. The required pages may already have been cached in memory.

Logical reads measure page accesses, not necessarily physical disk operations.

</details>

## 9.2 Comparing performance before and after indexing

We have now seen how indexes changed the execution plan. Let's measure how much these changes improved query performance.

The following approximate results summarize the original lab demonstration on **SQL Server Express**. They are representative measurements from demonstration runs, rather than exact copies of every measurement in Sections 7 and 8. For example, the detailed baseline in Section 7 reports 18.1 seconds; the rounded comparison below uses approximately 17 seconds. Use measurements from your own runs when calculating your improvement.

The same SQL query was executed before and after creating the indexes.

### Reference measurements

| Metric | Before indexing | After indexing |
|---|---:|---:|
| `SalesOrder` logical reads | ~57,000 | ~15 |
| `SalesOrderItem` logical reads | ~198,000 | ~54,000 |
| Total logical reads (two large tables) | ~255,000 | ~54,015 |
| Elapsed time | ~17 s | ~0.5 s |

These are approximate reference measurements. Your results may differ depending on hardware, caching, SQL Server configuration, and other factors.

### How much did logical I/O decrease?

Before indexing, SQL Server performed approximately **255,000 logical reads** across the two large tables.

After indexing, this decreased to approximately **54,015 logical reads**.

We can calculate the reduction:

```math
\mathrm{Reduction} = \frac{255{,}000 - 54{,}015}{255{,}000} \times 100
```

```math
\boxed{\mathrm{Logical\text{-}read\ reduction} \approx 78.8\%}
```


This means the optimized query performs approximately **79% fewer logical page accesses** across these two tables.

Notice that the reduction is not identical for both tables:

- `SalesOrder` logical reads decreased from approximately 57,000 to only 15.
- `SalesOrderItem` logical reads decreased from approximately 198,000 to 54,000.

Although the large scans have disappeared, repeated index seeks still require page accesses.

**An Index Seek is efficient, but it is not free.**

### How much faster is the query?

The original execution took approximately **17 seconds**.

After indexing, the same query completed in approximately **0.5 seconds**.

We can calculate the speedup:

```math
\mathrm{Speedup} = \frac{\mathrm{Before\ elapsed\ time}}{\mathrm{After\ elapsed\ time}}
```

```math
\mathrm{Speedup} = \frac{17}{0.5} = 34
```


The query completed approximately **34 times faster** in this reference test.

This is a significant improvement, even though the SQL statement and the number of matching rows remained unchanged.

### Why did elapsed time improve more than logical reads?

Logical reads decreased by approximately 79%, while elapsed time improved by a factor of about 34.

These measurements describe different aspects of query execution.

The optimized plan avoids scanning millions of unrelated rows and uses more targeted access paths. This can reduce CPU processing, memory work, and other execution costs in addition to page accesses.

However, elapsed time is also affected by caching, waiting, parallelism, and system load.

Therefore, **the reduction in logical reads and the reduction in elapsed time do not have to be proportional**.

### Check your understanding

**Why does the optimized query still perform approximately 54,000 logical reads on `SalesOrderItem`, even though it no longer scans all 40 million rows?**

<details>
<summary>Show answer</summary>

The optimized plan uses repeated index seeks to find the order items belonging to the selected orders.

Each seek requires accessing index pages, including navigation and leaf pages.

Although these operations are much more targeted than scanning the entire table, their logical reads accumulate across thousands of seeks.

Therefore, eliminating a large scan does not mean eliminating all page-access work.

</details>

## 9.3 SQL Server editions and parallel execution

So far, we have focused on how indexes improve query performance by reducing unnecessary data access.

However, **the same query can perform differently depending on the SQL Server edition, configuration, and available hardware**.

In the original lab demonstration, the same database and query were tested on SQL Server Express and Developer editions running on the same computer.

### Reference measurements

| Metric | SQL Server Express | Developer / Enterprise |
|---|---:|---:|
| Execution before indexing | Serial | Parallel |
| Elapsed time before indexing | ~17 s | ~1.3 s |
| Elapsed time after indexing | ~0.5 s | ~0.17 s |
| Speedup from indexing | ~34× | ~8× |

These values are reference measurements from a particular test environment. They are not guaranteed results for every SQL Server installation.

### What is parallel execution?

SQL Server can sometimes divide the work of a query among multiple CPU workers.

There are two common execution approaches:

- **Serial execution:** the query uses a single worker for its execution.
- **Parallel execution:** parts of the query are processed by multiple workers simultaneously.

For example, when scanning a large table, a parallel plan may allow several workers to process different portions of the data.

This can reduce the elapsed time needed to complete the query.

However, **parallel execution does not necessarily reduce the total amount of work performed**. It may simply distribute the work across multiple CPU workers.

### Why was the difference larger before indexing?

Before indexing, the query had to process very large inputs, including approximately 40 million order items.

In the reference Developer/Enterprise test, parallel execution helped distribute this work across multiple CPU workers.

As a result, the query completed much faster than in the reference Express test, even before creating the indexes.

After indexing, both editions benefited from more efficient access paths. The query needed to process far less unnecessary data, so the difference in elapsed time between the two environments became smaller.

### CPU time vs. elapsed time

Remember the distinction from Section 9.1:

- **CPU time** measures the processor time consumed by the query.
- **Elapsed time** measures how long the query takes to finish.

In a parallel plan, several workers can consume CPU time simultaneously.

For example, a query might consume 4 seconds of total CPU time but finish in 1.5 seconds of elapsed time.

This is possible because multiple workers perform parts of the work concurrently.

> [!IMPORTANT]
> **Parallel execution can make an inefficient query finish faster, but it does not automatically make the query more efficient.**
>
> Good indexing reduces unnecessary data access. Parallel execution can distribute the remaining work across multiple CPU workers.

### Check your understanding

**Why did the reference Developer/Enterprise instance execute the query much faster than Express before indexing, even though both processed the same data?**

<details>
<summary>Show answer</summary>

The reference Developer/Enterprise instance used a parallel execution plan, allowing multiple CPU workers to process parts of the query simultaneously.

The Express instance used a serial plan in this test.

Parallelism reduced elapsed time, but the query still had to process large amounts of data.

After indexing, both instances benefited from more efficient access paths, reducing unnecessary work.

</details>

## 9.4 Performance analysis exercise

We have now completed the indexing demonstration and examined how the execution plan and query performance changed.

In this exercise, you will use the **five execution plans** from Sections 7 and 8, together with your `STATISTICS IO` and `STATISTICS TIME` results.

Your goal is to explain not only **which plan is faster, but why**.

### Part 1 – Analyze the execution plans

Review the five stages of our demonstration:

1. Before indexing.
2. After creating clustered primary keys.
3. After creating the `OrderDate` index.
4. After creating the `SalesOrderId` index.
5. After adding the `INCLUDE` columns.

Answer the following questions:

1. Why did creating clustered primary keys not eliminate the large scans?
2. Which index first allowed SQL Server to avoid scanning the entire `SalesOrder` table?
3. Which index eliminated the large `SalesOrderItem` scan?
4. Why did the narrow `SalesOrderId` index introduce additional clustered index accesses?
5. What changed after adding `INCLUDE (ProductId, Quantity, UnitPrice)`?
6. Why did the `Product` scan remain in the optimized plan?
7. Why did the join strategy change from `Hash Match` to `Nested Loops`?
8. Why is an `Index Seek` not always better than an `Index Scan` or `Table Scan`?

<details>
<summary>Show discussion points</summary>

1. The clustered keys did not directly support filtering by `OrderDate` or locating order items by `SalesOrderId`.
2. `IX_SalesOrder_OrderDate` enabled efficient access to the requested date range.
3. `IX_SalesOrderItem_SalesOrderId` enabled SQL Server to locate order items using the join key.
4. The narrow index did not contain `ProductId`, `Quantity`, and `UnitPrice`, so SQL Server needed additional clustered index accesses.
5. The index became covering for the order-item portion of the query, eliminating the additional clustered row fetches.
6. Scanning the relatively small `Product` table could still be cheaper than performing many individual seeks.
7. The new index made repeated seeks on the inner input efficient, making `Nested Loops` attractive.
8. A seek may still process many rows or require repeated lookups. A scan can be more efficient when a large proportion of the data is needed.

</details>

### Part 2 – Analyze the performance measurements

Use the results you recorded with `STATISTICS IO` and `STATISTICS TIME`.

Answer the following questions:

1. How much did the logical reads decrease for `SalesOrder`?
2. How much did the logical reads decrease for `SalesOrderItem`?
3. What was the overall percentage reduction in logical reads across these two tables?
4. How many times faster was the query after indexing?
5. Why did elapsed time improve by a different percentage than logical reads?
6. Why can the same query have different execution times on SQL Server Express and Developer editions?

<details>
<summary>Show reference answers</summary>

Using the approximate reference measurements from Section 9.2:

1. `SalesOrder`: from 57,000 to 15 logical reads — approximately **99.97% reduction**.
2. `SalesOrderItem`: from 198,000 to 54,000 logical reads — approximately **72.7% reduction**.
3. Combined logical reads decreased from approximately 255,000 to 54,015 — approximately **78.8% reduction**.
4. Elapsed time decreased from approximately 17 seconds to 0.5 seconds — approximately **34× speedup**.
5. Logical reads measure page accesses, while elapsed time also depends on CPU processing, waiting, caching, and execution strategy.
6. Different editions and configurations may use different execution plans, resource limits, and degrees of parallelism.

Your own results may differ from these reference values.

</details>

### Final question

**What is the most important lesson from this indexing demonstration?**

<details>
<summary>Show discussion</summary>

The most important lesson is that **effective indexing is about supporting the way queries access data**.

Creating indexes on arbitrary columns does not guarantee better performance.

By choosing index keys that support filtering and joining, and including additional columns when necessary, we allowed SQL Server to avoid processing millions of unnecessary rows.

The execution plan and performance measurements confirmed the improvement.

</details>

---


# 10. Index design principles

## 10.1 Composite indexes and column order

So far, we have created indexes on individual columns, such as `OrderDate` and `SalesOrderId`.

However, many queries filter or sort data using **more than one column**.

A **composite index** is an index that uses two or more columns as its key.

The order of these columns is important because it determines how the index entries are organized and which search patterns the index can efficiently support.

### How are composite index keys organized?

Consider an index on:

```sql
(CustomerId, OrderDate)
```

The index entries are logically ordered:

1. First by `CustomerId`.
2. Within each `CustomerId`, by `OrderDate`.

For example:

| CustomerId | OrderDate |
|---:|---|
| 100 | 2025-01-05 |
| 100 | 2025-02-12 |
| 100 | 2025-04-20 |
| 200 | 2025-01-10 |
| 200 | 2025-03-15 |
| 300 | 2025-02-01 |

Notice that all orders for the same customer are grouped together, and within each customer, the orders are sorted by date.

This makes it efficient to find orders for a particular customer, optionally restricted to a date range.

However, the index is **not globally sorted by `OrderDate`**. Dates are sorted only within each `CustomerId` group.

### Create the composite index

Execute:

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrder_CustomerId_OrderDate
ON dbo.SalesOrder (CustomerId, OrderDate);
GO
```

Now compare the following queries with Actual Execution Plan enabled.

**Query A – Leading key only**

```sql
SELECT SalesOrderId, CustomerId, OrderDate
FROM dbo.SalesOrder
WHERE CustomerId = 500;
GO
```

SQL Server can use the leading key `CustomerId` to locate the matching entries.

**Query B – Leading key and second key**

```sql
SELECT SalesOrderId, CustomerId, OrderDate
FROM dbo.SalesOrder
WHERE CustomerId = 500
  AND OrderDate >= '20250101';
GO
```

SQL Server can use the equality condition on `CustomerId` and the range condition on `OrderDate` to efficiently locate matching entries.

**Query C – Second key only**

```sql
SELECT SalesOrderId, CustomerId, OrderDate
FROM dbo.SalesOrder
WHERE OrderDate >= '20250101';
GO
```

This query does not filter by the leading key, `CustomerId`.

Therefore, SQL Server generally cannot use this composite index to directly seek to one continuous date range across all customers.

It may scan the index or choose another available index, such as `IX_SalesOrder_OrderDate`, which we created earlier.

### Compare the execution plans

For each query, inspect the access operator and its **Seek Predicates**.

| Query | Predicate | Expected use of the composite index |
|---|---|---|
| A | `CustomerId = 500` | Seek using the leading key |
| B | `CustomerId = 500 AND OrderDate >= ...` | Seek using both key columns |
| C | `OrderDate >= ...` | No efficient date-only seek using this composite index |

> [!IMPORTANT]
> **The order of columns in a composite index matters.**
>
> An index on `(CustomerId, OrderDate)` is not equivalent to an index on `(OrderDate, CustomerId)`.
>
> Reordering conditions in the `WHERE` clause does not change the index's key order.

### Check your understanding

**Would an index on `(OrderDate, CustomerId)` be equally efficient for finding all orders belonging to `CustomerId = 500`?**

<details>
<summary>Show answer</summary>

Not necessarily.

With `OrderDate` as the leading key, the index is organized primarily by date. Orders for customer 500 may be spread across many different date ranges.

An index on `(CustomerId, OrderDate)` is generally better suited for queries that filter by `CustomerId` alone.

However, `(OrderDate, CustomerId)` may be more useful for queries that primarily filter by date.

The best column order depends on the queries the index needs to support.

</details>

## 10.2 Selectivity

When designing an index, an important consideration is **selectivity**.

Selectivity describes how effectively a search condition reduces the number of rows that need to be processed.

For example, imagine a table containing one million orders:

| Status | Number of orders |
|---|---:|
| Completed | 900,000 |
| Processing | 90,000 |
| Review | 10,000 |

If we search for `Status = 'Completed'`, the query matches **90% of the table**.

However, searching for `Status = 'Review'` matches only **1% of the table**.

The second condition is much more selective because it returns a smaller proportion of the rows.

> [!NOTE]
> These numbers are illustrative. We will now examine the actual distribution of values in our `SalesOrder` table.

### Examine the data distribution

First, find out how frequently each status occurs:

```sql
SELECT Status, COUNT(*) AS NumberOfOrders
FROM dbo.SalesOrder
GROUP BY Status
ORDER BY NumberOfOrders DESC;
GO
```

Examine the results.

Which status occurs most frequently? Which is the rarest?

The distribution matters because SQL Server estimates how many rows a query will return and uses that information when choosing an execution plan.

### Create an index on Status

Now create a nonclustered index:

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrder_Status
ON dbo.SalesOrder (Status);
GO
```

The index organizes its entries by `Status`, allowing SQL Server to locate rows with a particular status.

However, **having an index does not guarantee that SQL Server will use it for every status value**.

### Compare two queries

Enable Actual Execution Plan and execute:

**Query A – Completed status**

```sql
SELECT SalesOrderId, Status
FROM dbo.SalesOrder
WHERE Status = 'Completed';
GO
```

**Query B – Review status**

```sql
SELECT SalesOrderId, Status
FROM dbo.SalesOrder
WHERE Status = 'Review';
GO
```

Both queries filter on the same indexed column. Use the distribution query above to check how frequently these values actually occur. If other values are more suitable, replace the literals with the most frequent and least frequent status values in your data. If the frequencies are similar, expect little difference due to selectivity alone.

These queries are covered by `IX_SalesOrder_Status` because `SalesOrderId` is the clustered key and is already available in the nonclustered index. Both queries may therefore use an Index Seek, even when one returns many rows. Compare the number of rows and logical reads; do not expect different operator types.

Compare their execution plans and `STATISTICS IO` results.

Pay attention to:

- **Access operator:** Does SQL Server use an `Index Seek` or an `Index Scan`?
- **Actual Number of Rows:** How many rows does each query return?
- **Logical reads:** How much page-access work does each query perform?

> [!IMPORTANT]
> **An index is often most beneficial when a query needs only a small portion of the table.**
>
> When a query returns a large proportion of the rows, a scan may be more efficient, especially if additional columns must be retrieved from the table.

### Selectivity vs. number of distinct values

A column with only a few different values is sometimes described as having **low cardinality**.

For example, `Status` might contain only `Completed`, `Processing`, and `Review`.

However, this does not automatically make an index on `Status` useless.

If `Review` occurs in only 1% of the rows, searching for that value can still be highly selective.

The important distinction is:

- **Cardinality:** how many distinct values a column contains (in this context).
- **Selectivity:** how narrowly a particular search condition filters the rows.

### Check your understanding

**Why might an index on `Status` be useful for `Status = 'Review'`, even though the column contains only a few distinct values?**

<details>
<summary>Show answer</summary>

Because `Review` may occur in only a small percentage of the table.

An index allows SQL Server to locate the matching entries without examining every row.

The usefulness of an index depends not only on the number of distinct values but also on their distribution and the columns required by the query.

</details>

## 10.3 Included columns and index width

In Section 8.4, we created a covering index on `SalesOrderItem`:

```sql
CREATE NONCLUSTERED INDEX IX_SalesOrderItem_SalesOrderId
ON dbo.SalesOrderItem (SalesOrderId)
INCLUDE (ProductId, Quantity, UnitPrice);
```

This allowed SQL Server to retrieve all the required columns directly from the nonclustered index, eliminating thousands of additional clustered index accesses.

However, **adding more columns to an index is not always beneficial**.

### Why does index width matter?

As we learned in Lab 05, SQL Server stores index data in **8 KB pages**.

When an index contains more columns, its leaf-level entries generally become wider.

This has several consequences:

- **Fewer entries per page:** wider entries reduce the number of index records that fit into an 8 KB page.
- **More pages:** the index may require more pages to store the same number of entries.
- **More I/O:** reading a larger portion of the index may require more page accesses.
- **More maintenance:** inserting or updating indexed values can require additional work.

For example, consider a simplified index with one million entries:

| Average entry size | Entries per page (approx.) | Pages needed (approx.) |
|---|---:|---:|
| 20 bytes | 400 | 2,500 |
| 40 bytes | 200 | 5,000 |
| 80 bytes | 100 | 10,000 |

These figures are illustrative and ignore page headers, record overhead, free space, and other internal structures.

The important observation is that **doubling the size of index entries can approximately double the number of leaf pages required**.

### Finding the right balance

A narrow index uses less storage and may require fewer page reads, but it might not contain all the columns required by a query.

A wider covering index can eliminate additional lookups, but it requires more storage and maintenance.

The best choice depends on the workload.

> [!IMPORTANT]
> **A covering index is not necessarily the best index for every situation.**
>
> Add included columns when the benefit of avoiding additional data lookups justifies the extra storage and maintenance cost.

### Check your understanding

**Why might a wider covering index be faster for one query but less efficient for the database overall?**

<details>
<summary>Show answer</summary>

A covering index can improve a query by providing all required columns without additional lookups.

However, wider index entries require more storage pages and can increase the work needed for data modifications.

The index may improve frequently executed queries while increasing storage and maintenance costs for the overall workload.

</details>

---

# 11. Inserts, page splits, and maintenance

So far, we have focused on how indexes help SQL Server find data efficiently.

However, database tables are not static. New rows are inserted, existing rows are updated, and rows are deleted.

**Every index must remain consistent with the data it represents.**

This means that indexes improve certain read operations, but they also introduce additional work when data changes.

## 11.1 Inserting entries into a B+ tree

As we learned earlier, SQL Server stores index entries in **8 KB pages**.

The entries at the leaf level are logically ordered by their index keys.

When a new row is inserted, SQL Server must place its index entry in the correct position according to the key.

Two situations are possible:

- **Enough free space:** the new entry can be inserted into the existing page.
- **Not enough free space:** SQL Server may need to split the page to make room for the new entry.

A page split can also require changes to separator keys and pointers in the upper levels of the B+ tree.

### Example: Inserting new keys

The following diagram illustrates the insertion of three new keys: `58`, `60`, and `75`.

![Step-by-step insertion into a simplified B+ tree](../images/lab06/bplus-tree-insert-steps.svg)

Follow the changes in the diagram:

1. **Initial state:** the B+ tree contains existing keys, with some available space in its pages.
2. **Insert 58:** the new key is placed in its correct position. A leaf page split requires an update to the parent structure.
3. **Insert 60:** another insertion changes the leaf-level structure, but the overall tree height remains unchanged.
4. **Insert 75:** additional splitting propagates upward, eventually creating a new root and increasing the height of the tree.

> [!IMPORTANT]
> **A page split does not always increase the height of a B+ tree.**
>
> The tree grows in height only when splitting propagates all the way to the root and a new root is required.

### Final B+ tree

The following diagram shows the resulting structure after all three insertions.

![Final B+ tree after the insertions](../images/lab06/bplus-tree-after-insert.svg)

Notice that:

- All leaf pages remain at the same depth.
- The index entries remain logically ordered by key.
- Separator keys and child pointers have been updated.
- The tree now has an additional level.

This illustrates how a B+ tree maintains its balanced structure even as new entries are inserted.

## 11.2 Inserting rows into a clustered index

In a **clustered index**, the leaf level contains the actual table rows.

Therefore, inserting a new row may require SQL Server to reorganize the data rows stored in the leaf pages.

The next diagram illustrates this process.

![Insertion into a clustered index](../images/lab06/clustered-index-insert.svg)

The same basic B+ tree principles apply:

- New rows must be placed according to the clustered key's logical order.
- If the target leaf page has enough free space, the row can be inserted there.
- If there is insufficient space, a page split may be necessary.
- Changes to the leaf pages may require updates to the upper index levels.

The key difference is that **clustered index leaf pages contain complete data rows**, not just nonclustered index entries.

This means that splitting a clustered index leaf page involves redistributing actual table rows.

## 11.3 Why do indexes require maintenance?

Every additional index must be updated when relevant data changes.

For example:

- **INSERT:** SQL Server adds entries to the indexes associated with the new row.
- **DELETE:** SQL Server must remove or logically delete the corresponding index entries.
- **UPDATE:** SQL Server may need to modify index entries, especially when indexed key or included column values change.

These operations require additional CPU, memory, logging, and page modifications.

### Page splits and fragmentation

Page splits can also contribute to **index fragmentation**.

In simplified terms, fragmentation occurs when the physical organization of index pages becomes less efficient for certain access patterns.

For example, logically neighboring leaf pages may no longer be stored close together in the physical file.

This can increase the cost of reading large ranges of index pages, particularly when physical I/O is involved.

However, fragmentation does not automatically mean that every query will become slower.

> [!NOTE]
> SQL Server provides index maintenance operations such as `ALTER INDEX ... REORGANIZE` and `ALTER INDEX ... REBUILD`.
>
> These operations can help address certain index maintenance issues, but they should not be performed automatically without considering actual performance, page counts, fragmentation, and workload requirements.

## 11.4 The cost of additional indexes

Indexes are useful because they can reduce the amount of data SQL Server must examine when executing queries.

However, they also consume storage and increase the work required for data modifications.

| Benefit | Cost |
|---|---|
| Faster access to selected rows | Additional storage space |
| Efficient range searches | Extra work during INSERT, UPDATE, and DELETE |
| Reduced need for large scans | Possible page splits and fragmentation |
| Covering indexes can avoid lookups | Wider indexes require more pages |

The goal is not to create as many indexes as possible.

**The goal is to create indexes that provide the greatest benefit for the database workload.**

### Check your understanding

**Why can adding more indexes improve SELECT queries but make INSERT operations more expensive?**

<details>
<summary>Show answer</summary>

Additional indexes provide more access paths that SQL Server can use to locate data efficiently.

However, when a new row is inserted, SQL Server must also maintain the corresponding entries in each affected index.

This requires additional page modifications, logging, and potentially page splits.

Therefore, more indexes can improve read performance while increasing the cost of data modifications.

</details>

---

# 12. Practical checklist – Designing useful indexes

Before creating an index, consider how the database will use it.

An index should support **real query patterns**, not simply exist because a column appears in a table.

Use the following checklist when evaluating a new index.

| Step | Question | Why it matters |
|---|---|---|
| 1. Identify the query | Which queries are slow or frequently executed? | Focus on queries where optimization provides a meaningful benefit. |
| 2. Examine search conditions | Which columns appear in `WHERE` and `JOIN` conditions? | These columns are potential candidates for index keys. |
| 3. Choose key columns | Does the index have the appropriate leading key and column order? | Key order determines which search patterns the index can efficiently support. |
| 4. Consider required columns | Which additional columns are returned, calculated, or aggregated? | Included columns may eliminate expensive additional lookups. |
| 5. Evaluate selectivity | How many rows does the query need compared with the total table size? | A selective predicate may benefit from an index seek, while a scan can be cheaper for large result sets. |
| 6. Check existing indexes | Does another index already support the query? | Avoid creating unnecessary or overlapping indexes. |
| 7. Consider maintenance costs | How frequently are rows inserted, updated, or deleted? | Additional indexes require storage and increase data modification costs. |
| 8. Measure the result | Did logical reads, CPU time, or elapsed time improve? | Use actual execution plans and measurements to verify the benefit. |

> [!IMPORTANT]
> **A good index is designed for a query, not just for a column.**
>
> The goal is to reduce unnecessary work while keeping storage and maintenance costs reasonable.

### A practical approach

When investigating a slow query, follow this process:

1. **Analyze** the SQL statement and its Actual Execution Plan.
2. **Identify** expensive operations and unnecessary data access.
3. **Design** an index that supports the query's filtering, joining, or ordering requirements.
4. **Test** the query again using the same SQL statement.
5. **Compare** logical reads, CPU time, and elapsed time.
6. **Evaluate** whether the performance improvement justifies the additional index.

Remember that an `Index Seek` is not automatically better than a `Scan`. The best execution strategy depends on the amount of data required and the available access paths.

**Always measure the results instead of assuming that a new index will improve performance.**

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

Check the **Object** property to identify which index SQL Server actually used. Query A may use the separate `IX_SalesOrder_OrderDate` index created earlier; that does not mean the composite index supports an efficient seek on `OrderDate` alone.

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

1. Which relevant indexes already exist, including `IX_SalesOrder_Status` from Section 10.2 and `IX_SalesOrder_Status_OrderDate` if you completed Exercise 1?
2. Can an existing index support both the filter and the requested sort order?
3. Is it better to create a new index, replace an overlapping index, or do nothing?

<details>
<summary>Show solution</summary>

If you completed Exercise 1, `IX_SalesOrder_Status_OrderDate` already covers this query. With `Status` fixed by the equality condition, SQL Server can read the relevant `OrderDate DESC` range backward to satisfy `ORDER BY OrderDate` in ascending order. No new index is needed for this exercise.

If you skipped Exercise 1, `IX_SalesOrder_Status` supports the filter, but not ordering by `OrderDate` within the same `Status`. An index on `(Status, OrderDate)` can support both. It overlaps with the status-only index, so consider **replacing** the earlier index instead of maintaining both. In a real system, inspect the entire workload before making this change.

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
