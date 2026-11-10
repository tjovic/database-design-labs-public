# Physical Storage Exercises

These exercises build on [Lab 05 – Physical Storage](../labs/lab05-physical-storage.md). **Part A** (Exercises 1–4) uses `AdventureWorksENG` — the same database the midterm is written against. **Part B** (Exercises 5–8) contains page calculations and two exercises on the lab's `IndexLab` database.

In Part A, `AdventureWorksENG` is much smaller than `IndexLab`, which is exactly the point: `State` has 3 rows, `Product` has 504, and `Customer` has 19,972. That range lets you see, on real tables of very different sizes, the same two questions Lab 05 asks about `Category`, `Product`, and `Customer`: how many pages does a table use, and what determines the physical order of rows on those pages?

Every number quoted in Part A (page counts, page IDs, record lengths, row IDs) was measured directly against this course's fixed `AdventureWorksENG` dataset. Your own page IDs will differ — page allocation is instance-specific — but row counts, record lengths, and which row comes before or after another should match, since those come from the data itself, not from allocation order.

> [!WARNING]
> `DBCC IND` and `DBCC PAGE` are **undocumented diagnostic commands** (same note as Lab 05). Use them only for learning in this training database.

These exercises are read-only: `DBCC IND` and `DBCC PAGE` only inspect existing pages. No setup or cleanup is required, and nothing here creates objects or modifies data.

## Setup

```sql
USE AdventureWorksENG;
GO

DBCC TRACEON(3604);
GO
```

Run `DBCC TRACEON(3604)` again if you open a new query window — it only applies to the current session.

---

# Part A – `AdventureWorksENG`

## Exercise 1 — The `State` table [BEGINNER]

`State` is the smallest table in this database — a good warm-up before moving to larger tables.

```sql
DBCC IND('AdventureWorksENG', 'dbo.State', -1);
GO
```

Answer:

1. On how many pages are the data from `State` stored (`PageType = 1`)?
2. What are the `PageFID` and `PagePID` of that page?
3. Using `DBCC PAGE('AdventureWorksENG', file_id, page_id, 3) WITH TABLERESULTS;` on that page, what is the length (in bytes) of the first, second, and third row?
4. By which column are the rows on the page arranged?
5. Find the row for `'Germany'`. What are the rows immediately before and after it?

<details>
<summary>Hint</summary>

`State` has a `PRIMARY KEY CLUSTERED (IDState)`, so its data pages belong to a clustered index — not a heap — and the physical row order follows the clustering key, not alphabetical order. For question 5, look up `IDState` for `'Germany'` first, then check which rows have the neighboring `IDState` values.

</details>

<details>
<summary>Solution</summary>

1. **1** data page (`DBCC IND` returns 2 rows total: one IAM page and one data page — there is no separate root page because one page is enough for the whole table).
2. `PageFID = 1`, `PagePID = 232`.
3. Row 1 (`Croatia`): **29 bytes**. Row 2 (`Germany`): **29 bytes**. Row 3 (`Italy`): **25 bytes**.
4. `IDState` — the clustering key. Row order on the page follows `IDState` ascending (1, 2, 3), not the alphabetical order of `Name`.
5. `'Germany'` has `IDState = 2`. The row before it is `'Croatia'` (`IDState = 1`); the row after it is `'Italy'` (`IDState = 3`) — based on `IDState`, not on alphabetical order.

</details>

---

## Exercise 2 — The `Product` table [INTERMEDIATE]

```sql
DBCC IND('AdventureWorksENG', 'dbo.Product', -1);
GO
```

Answer:

1. On how many data pages (`PageType = 1`) are `Product`'s 504 rows stored?
2. Write down the `PagePID` values of those data pages, in order.
3. Using `DBCC PAGE`, what is the length (in bytes) of the first, second, and third row in the table?
4. What is the `IDProduct` of the last row on the first data page? What is the `IDProduct` of the first row on the second data page?
5. What is the `IDProduct` of the last row on the second data page? What is the `IDProduct` of the first row on the third data page?
6. By which column are the rows on the pages arranged?

<details>
<summary>Hint</summary>

`DBCC IND` returns one row per allocated page, including the IAM page and — unlike `State` — a root page (`PageType = 2`). Filter for `PageType = 1` to find only the data (leaf) pages, and follow `PagePID` in the order `DBCC IND` lists them. For questions 4 and 5, open each page with `DBCC PAGE` and look at the `IDProduct` column of the first and last slot.

</details>

<details>
<summary>Solution</summary>

1. **6** data pages (out of 8 total allocated pages: 1 IAM page, 1 root page, 6 leaf/data pages).
2. In order: `576`, `578`, `579`, `580`, `581`, `582`. (`577` is the root page, `PageType = 2` — not a data page.)
3. Row 1 (`IDProduct = 1`): **75 bytes**. Row 2 (`IDProduct = 2`): **69 bytes**. Row 3 (`IDProduct = 3`): **75 bytes**.
4. Last row on page `576`: `IDProduct = 425`. First row on page `578`: `IDProduct = 426`.
5. Last row on page `578`: `IDProduct = 706`. First row on page `579`: `IDProduct = 707`.
6. `IDProduct` — the clustering key. Notice in questions 4 and 5 that the key value increases by exactly 1 across the page boundary: the clustered index keeps rows in one continuous, gapless order even though they are split across physical pages.

</details>

**Bonus — why isn't every page equally full?** Row counts per page were not identical across the six pages (they ranged from 62 to 107). Why might that be, given that `Name`, `ProductNumber`, and `Color` are all variable-length columns?

<details>
<summary>Think about it</summary>

Rows with longer `Name`, `ProductNumber`, or `Color` values take up more bytes, so a page holding several "wide" products fits fewer rows than a page holding mostly "narrow" ones — the same point Lab 05 makes about `Customer`'s variable record sizes, just visible here on a real, smaller table.

</details>

---

## Exercise 3 — The `Customer` table, without listing every page [INTERMEDIATE]

`Customer` has 19,972 rows — few enough that `DBCC IND` is still readable, but large enough to make the point of Lab 05's `SalesOrder` exercise: for a genuinely large table, listing every page by hand does not scale.

### a) Using `DBCC IND` directly

```sql
DBCC IND('AdventureWorksENG', 'dbo.Customer', -1);
GO
```

Answer:

1. Approximately how many data pages (`PageType = 1`) does `Customer` use?
2. What are the first five data-page `PagePID` values?
3. Using `DBCC PAGE` on the first data page, how many rows does it hold?
4. What is the length (in bytes) of the first, second, and third row on that page?

<details>
<summary>Solution for (a)</summary>

1. **338** data pages.
2. `584`, `586`, `587`, `588`, `589` (note the gap between `584` and `586` — the root page occupies `585`'s position in `PagePID` order, even though it is not part of the leaf chain).
3. **61** rows.
4. Row 1: **131 bytes**. Row 2: **135 bytes**. Row 3: **125 bytes**.

</details>

### b) Getting the same page count without listing every page

`Customer`'s 338 pages are still printable, but a table with millions of rows would produce an unusably long result — the exact problem Lab 05 raises for `SalesOrder`, which has tens of millions of rows. Use the documented `sys.dm_db_partition_stats` view instead:

```sql
SELECT
    i.name AS IndexName,
    i.index_id,
    SUM(ps.row_count) AS [RowCount],
    SUM(ps.in_row_data_page_count) AS InRowDataPages,
    SUM(ps.used_page_count) AS UsedPages
FROM sys.dm_db_partition_stats AS ps
JOIN sys.indexes AS i
    ON i.object_id = ps.object_id
   AND i.index_id = ps.index_id
WHERE ps.object_id = OBJECT_ID('dbo.Customer')
  AND i.index_id IN (0, 1)
GROUP BY i.name, i.index_id;
```

Answer:

1. Does `InRowDataPages` match the data-page count you found with `DBCC IND` in (a)?
2. Compute `[RowCount] / InRowDataPages`. Does it match the row count you observed on one page in part (a), question 3?
3. Why is this view better suited to a table with millions of rows than `DBCC IND`?

<details>
<summary>Solution for (b)</summary>

1. Yes — `InRowDataPages` should be **338**, matching the leaf-page count from `DBCC IND`.
2. `19,972 / 338 ≈ 59`, close to the 61 rows observed on the first page — an average, not an exact match, since some pages hold more or fewer rows depending on how much space their `FirstName`, `LastName`, `Email`, and `PhoneNumber` values use.
3. `sys.dm_db_partition_stats` returns one summary row per index instead of one row per page, so it stays fast and readable no matter how large the table is — exactly the reason Lab 05 uses it for `SalesOrder` instead of `DBCC IND`.

</details>

---

## Exercise 4 — From page count to logical reads [BEGINNER]

Exercises 1–3 counted pages using `DBCC IND` and `sys.dm_db_partition_stats`. This exercise connects that page count to what `STATISTICS IO` reports for an actual query — the same link Lab 05, Section 16 makes conceptually.

```sql
SET STATISTICS IO ON;

SELECT * FROM dbo.State;
SELECT * FROM dbo.Product;
SELECT * FROM dbo.Customer;

SET STATISTICS IO OFF;
```

For each table, look at the `logical reads` value on the **Messages** tab.

Answer:

1. For `State`, how does `logical reads` compare to the *total* number of pages `DBCC IND` listed in Exercise 1 (including the IAM page, not just the one data page)?
2. For `Product`, how does `logical reads` compare to the total page count from Exercise 2 — 6 data pages, 1 root page, and 1 IAM page?
3. For `Customer`, how does `logical reads` compare to the total page count implied by Exercise 3 — 338 data pages, 1 root page, and 1 IAM page?
4. Based on these three results, does `logical reads` count only the data (leaf) pages, or every page type SQL Server has to touch to satisfy the query?

<details>
<summary>Solution</summary>

1. `State`: **2** logical reads = 1 data page + 1 IAM page.
2. `Product`: **8** logical reads = 6 data pages + 1 root page + 1 IAM page.
3. `Customer`: **340** logical reads = 338 data pages + 1 root page + 1 IAM page.
4. Every page type. `logical reads` counts **every** page SQL Server accesses to answer the query — not just the leaf-level data pages. A full scan of a clustered table has to visit the IAM page to find the allocated extents, and in these three cases SQL Server also touched the root page on its way to the leaf level, even though the query itself did not need a seek. This is exactly why Lab 05 treats "how many pages does this table use" and "how many logical reads does this query cost" as closely related but not always identical questions — the second one depends on the access path the query actually takes, not just on the table's total page count.

</details>

---

# Part B – Page math and `IndexLab`

Exercises 5 and 6 are calculations; you need no database for them. Exercises 7 and 8 use the large `IndexLab` database from [Lab 05](../labs/lab05-physical-storage.md) and only read from it.

## Exercise 5 — Page math [BEGINNER]

A table contains **2,000,000 rows** and fits **40 rows per page**.

1. How many pages are required?
2. If wider rows reduce capacity to **25 rows per page**, how many pages are now required?
3. By what percentage does the number of pages increase?

<details>
<summary>Solution</summary>

1. `2,000,000 / 40 = 50,000 pages`.
2. `2,000,000 / 25 = 80,000 pages`.
3. `(80,000 - 50,000) / 50,000 × 100 = 60%`.

</details>

---

## Exercise 6 — Predict the effect of wider rows [BEGINNER]

A table contains **1,000,000 rows** and currently fits **16 rows per page**. After adding a populated variable-length column, it fits only **10 rows per page**.

1. How many pages were needed before the change?
2. How many pages are needed afterward?
3. What is the percentage increase?
4. What happens to the page-access cost of a full scan, assuming similar execution conditions?

<details>
<summary>Solution</summary>

1. `1,000,000 / 16 = 62,500 pages`.
2. `1,000,000 / 10 = 100,000 pages`.
3. `(100,000 - 62,500) / 62,500 × 100 = 60%`.
4. A scan generally needs to process more pages, increasing logical I/O and potentially physical I/O. Elapsed time is not determined by page count alone.

</details>

---

## Exercise 7 — Logical versus physical reads [BEGINNER]

In SSMS, execute the following batch **once**. It runs the same query twice. Compare the two outputs in the **Messages** tab:

```sql
USE IndexLab;
GO
SET STATISTICS IO ON;
GO
SELECT * FROM dbo.Product;
GO
SELECT * FROM dbo.Product;
GO
SET STATISTICS IO OFF;
GO
```

1. Record logical reads and physical reads for each execution.
2. Did the physical-read count change?
3. Why might both executions report zero physical reads?
4. Can you conclude that the query accessed zero pages if `physical reads = 0`?
5. Compare `logical reads` with the **159 data pages** you counted for `Product` in [Section 14 of Lab 05](../labs/lab05-physical-storage.md#14-guided-investigation--product-from-pages-to-query-performance). Are the two numbers the same? If not, why not?

> [!NOTE]
> Pages may have been cached before you started this exercise. Do not expect the first query to show a nonzero physical-read count. **Do not clear the SQL Server buffer pool** just to force a difference on a shared classroom server.

<details>
<summary>Solution</summary>

1. Values depend on the server and cache state.
2. They may differ: pages read from storage can remain cached for subsequent executions.
3. Another query or an earlier operation may already have loaded the required pages into memory.
4. No. Inspect **logical reads** to see page accesses in the buffer pool. Also consider `read-ahead reads` when studying storage activity.
5. Not necessarily. Our reference query reported **161 logical reads**, while `DBCC IND` listed **159 leaf-level data pages**. Logical reads count page accesses during execution, not distinct allocated pages. Additional or repeated page accesses can occur, so these counts need not match. The counts alone do not identify which additional page accesses occurred.

</details>

---

## Exercise 8 — Investigate `SalesOrder` without listing every page [INTERMEDIATE]

`SalesOrder` is much larger than the `IndexLab` tables inspected with `DBCC IND` in Lab 05. Producing an individual row for every allocated page could overwhelm the SSMS result window.

Instead, use the documented `sys.dm_db_partition_stats` view:

```sql
USE IndexLab;
GO

SELECT
    i.name AS IndexName,
    i.index_id,
    SUM(ps.row_count) AS [RowCount],
    SUM(ps.in_row_data_page_count) AS InRowDataPages,
    SUM(ps.used_page_count) AS UsedPages
FROM sys.dm_db_partition_stats AS ps
JOIN sys.indexes AS i
    ON i.object_id = ps.object_id
   AND i.index_id = ps.index_id
WHERE ps.object_id = OBJECT_ID('dbo.SalesOrder')
  AND i.index_id IN (0, 1)
GROUP BY i.name, i.index_id;
```

`row_count` is an approximate row count. `in_row_data_page_count` counts in-row data pages (leaf pages for a clustered index). `used_page_count` includes other pages allocated to that index or heap and can be higher.

1. What are the reported row count and in-row data page count?
2. Estimate the **average rows per in-row data page**.
3. Compare the estimate with the `IndexLab` tables `Category`, `Product`, and `Customer` from Lab 05.
4. Why is this query better suited to counting pages in a very large table than displaying `DBCC IND` output?

<details>
<summary>Solution</summary>

1. In the reference database: `RowCount` = 10,000,000 and `InRowDataPages` = 57,143. Because the data is generated deterministically, you should see the same values.
2. 10,000,000 / 57,143 ≈ **175 rows per page**. This is an average, not the exact occupancy of each page.
3. For comparison: `Product` has about 189 rows per page (30,000 / 159) and `Customer` about 137 (100,000 / 732). `Category` has 100 rows on its only page, but that page is only about 35% full ([Lab 05, Section 12](../labs/lab05-physical-storage.md#12-dbcc-page--look-inside-a-data-page)). Different row sizes and storage layouts lead to different page densities.
4. The system view returns summary counts without producing a huge row-by-row list of page identifiers. On SQL Server 2022 and later, this view requires `VIEW DATABASE PERFORMANCE STATE` and `VIEW SECURITY DEFINITION` on the database. Earlier SQL Server versions require `VIEW DATABASE STATE` and `VIEW DEFINITION`.

</details>

---

# Key takeaways

- A table's `PRIMARY KEY CLUSTERED` determines the physical row order on its data pages — not insertion order, not alphabetical order of a non-key column.
- `DBCC IND` lists every allocated page; filter on `PageType = 1` to find the actual data (leaf) pages, and exclude root/intermediate pages (`PageType = 2`) and the IAM page (`PageType = 10`).
- A clustered index's leaf-level key stays gapless across a page boundary — the last key on one page and the first key on the next are consecutive.
- Variable-length columns (`varchar`, `nvarchar`) cause different rows to occupy different numbers of bytes, so different pages of the same table can hold different numbers of rows.
- `DBCC IND` works for small and medium tables, but for a table with millions of rows, use a documented, summary-based view like `sys.dm_db_partition_stats` instead.
- `STATISTICS IO`'s `logical reads` counts every page type a query touches — data, root/intermediate, and IAM pages — not just leaf-level data pages.

## References

- [Lab 05 – Physical Storage](../labs/lab05-physical-storage.md)
- [Lab 05, Section 10 – Inspecting physical pages](../labs/lab05-physical-storage.md#10-inspecting-physical-pages)
- [Lab 05, Section 16 – From physical storage to query optimization](../labs/lab05-physical-storage.md#16-from-physical-storage-to-query-optimization)
