# Physical Storage Exercises

These exercises build on [Lab 05 – Physical Storage](../labs/lab05-physical-storage.md) and use `AdventureWorksENG` — the same database the midterm is written against — instead of `IndexLab`.

`AdventureWorksENG` is much smaller than `IndexLab`, which is exactly the point here: `State` has 3 rows, `Product` has 504, and `Customer` has 19,972. That range lets you see, on real tables of very different sizes, the same two questions Lab 05 asks about `Category`, `Product`, and `Customer`: how many pages does a table use, and what determines the physical order of rows on those pages?

Every number quoted in this file (page counts, page IDs, record lengths, row IDs) was measured directly against this course's fixed `AdventureWorksENG` dataset. Your own page IDs will differ — page allocation is instance-specific — but row counts, record lengths, and which row comes before or after another should match, since those come from the data itself, not from allocation order.

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

## Exercise 1 — The `State` table [BEGINNER]

`State` is the smallest table in this database — a good warm-up before moving to larger tables.

```sql
DBCC IND('AdventureWorksENG', 'dbo.State', -1);
GO
```

Answer:

a. On how many pages are the data from `State` stored (`PageType = 1`)?
b. What are the `PageFID` and `PagePID` of that page?
c. Using `DBCC PAGE('AdventureWorksENG', file_id, page_id, 3) WITH TABLERESULTS;` on that page, what is the length (in bytes) of the first, second, and third row?
d. By which column are the rows on the page arranged?
e. Find the row for `'Germany'`. What are the rows immediately before and after it?

<details>
<summary>Hint</summary>

`State` has a `PRIMARY KEY CLUSTERED (IDState)`, so its data pages belong to a clustered index — not a heap — and the physical row order follows the clustering key, not alphabetical order. For (e), look up `IDState` for `'Germany'` first, then check which rows have the neighboring `IDState` values.

</details>

<details>
<summary>Solution</summary>

a. **1** data page (`DBCC IND` returns 2 rows total: one IAM page and one data page — there is no separate root page because one page is enough for the whole table).
b. `PageFID = 1`, `PagePID = 232`.
c. Row 1 (`Croatia`): **29 bytes**. Row 2 (`Germany`): **29 bytes**. Row 3 (`Italy`): **25 bytes**.
d. `IDState` — the clustering key. Row order on the page follows `IDState` ascending (1, 2, 3), not the alphabetical order of `Name`.
e. `'Germany'` has `IDState = 2`. The row before it is `'Croatia'` (`IDState = 1`); the row after it is `'Italy'` (`IDState = 3`) — determined by `IDState`, not by the two country names' alphabetical relationship to `'Germany'`.

</details>

---

## Exercise 2 — The `Product` table [INTERMEDIATE]

```sql
DBCC IND('AdventureWorksENG', 'dbo.Product', -1);
GO
```

Answer:

a. On how many data pages (`PageType = 1`) are `Product`'s 504 rows stored?
b. Write down the `PagePID` values of those data pages, in order.
c. Using `DBCC PAGE`, what is the length (in bytes) of the first, second, and third row in the table?
d. What is the `IDProduct` of the last row on the first data page? What is the `IDProduct` of the first row on the second data page?
e. What is the `IDProduct` of the last row on the second data page? What is the `IDProduct` of the first row on the third data page?
f. By which column are the rows on the pages arranged?

<details>
<summary>Hint</summary>

`DBCC IND` returns one row per allocated page, including the IAM page and — unlike `State` — a root page (`PageType = 2`). Filter for `PageType = 1` to find only the data (leaf) pages, and follow `PagePID` in the order `DBCC IND` lists them. For (d) and (e), open each page with `DBCC PAGE` and look at the `IDProduct` column of the first and last slot.

</details>

<details>
<summary>Solution</summary>

a. **6** data pages (out of 8 total allocated pages: 1 IAM page, 1 root page, 6 leaf/data pages).
b. In order: `576`, `578`, `579`, `580`, `581`, `582`. (`577` is the root page, `PageType = 2` — not a data page.)
c. Row 1 (`IDProduct = 1`): **75 bytes**. Row 2 (`IDProduct = 2`): **69 bytes**. Row 3 (`IDProduct = 3`): **75 bytes**.
d. Last row on page `576`: `IDProduct = 425`. First row on page `578`: `IDProduct = 426`.
e. Last row on page `578`: `IDProduct = 706`. First row on page `579`: `IDProduct = 707`.
f. `IDProduct` — the clustering key. Notice in (d) and (e) that the key value increases by exactly 1 across the page boundary: the clustered index keeps rows in one continuous, gapless order even though they are split across physical pages.

</details>

**Reflect:** Row counts per page were not identical across the six pages (they ranged from 62 to 107). Why might that be, given that `Name`, `ProductNumber`, and `Color` are all variable-length columns?

<details>
<summary>Think about it</summary>

Rows with longer `Name`, `ProductNumber`, or `Color` values take up more bytes, so a page holding several "wide" products fits fewer rows than a page holding mostly "narrow" ones — the same point Lab 05 makes about `Customer`'s variable record sizes, just visible here on a real, smaller table.

</details>

---

## Exercise 3 — The `Customer` table, without listing every page [INTERMEDIATE]

`Customer` has 19,972 rows — few enough that `DBCC IND` is still readable, but large enough to make the point of Lab 05's `SalesOrder` exercise: for a genuinely large table, listing every page by hand does not scale.

**a) Use `DBCC IND` directly** for the first part of this exercise:

```sql
DBCC IND('AdventureWorksENG', 'dbo.Customer', -1);
GO
```

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

**b) Now get the same page count without listing every page.** `Customer`'s 338 pages are still printable, but a table with millions of rows would produce an unusably long result (this is the exact problem Lab 05 raises for `SalesOrder`, which has tens of millions of rows). Use the documented `sys.dm_db_partition_stats` view instead:

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

1. Does `InRowDataPages` match the data-page count you found with `DBCC IND` in (a)?
2. Compute `[RowCount] / InRowDataPages`. Does it match the row count you observed on one page in (a.3)?
3. Why is this view better suited to a table with millions of rows than `DBCC IND`?

<details>
<summary>Solution for (b)</summary>

1. Yes — `InRowDataPages` should be **338**, matching the leaf-page count from `DBCC IND`.
2. `19,972 / 338 ≈ 59`, close to the 61 rows observed on the first page — an average, not an exact match, since some pages hold more or fewer rows depending on how much space their `FirstName`, `LastName`, `Email`, and `PhoneNumber` values use.
3. `sys.dm_db_partition_stats` returns one summary row per index instead of one row per page, so it stays fast and readable no matter how large the table is — exactly the reason Lab 05 uses it for `SalesOrder` instead of `DBCC IND`.

</details>

---

# Key takeaways

- A table's `PRIMARY KEY CLUSTERED` determines the physical row order on its data pages — not insertion order, not alphabetical order of a non-key column.
- `DBCC IND` lists every allocated page; filter on `PageType = 1` to find the actual data (leaf) pages, and exclude root/intermediate pages (`PageType = 2`) and the IAM page (`PageType = 10`).
- A clustered index's leaf-level key stays gapless across a page boundary — the last key on one page and the first key on the next are consecutive.
- Variable-length columns (`varchar`, `nvarchar`) cause different rows to occupy different numbers of bytes, so different pages of the same table can hold different numbers of rows.
- `DBCC IND` works for small and medium tables, but for a table with millions of rows, use a documented, summary-based view like `sys.dm_db_partition_stats` instead.

## References

- [Lab 05 – Physical Storage](../labs/lab05-physical-storage.md)
- [Lab 05, Section 10 – Inspecting physical pages](../labs/lab05-physical-storage.md#10-inspecting-physical-pages)
- [Lab 05, Section 17 – Large tables and the problem we need to solve](../labs/lab05-physical-storage.md#17-large-tables-and-the-problem-we-need-to-solve)
