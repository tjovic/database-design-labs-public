# Lab 06 – Index Exercises

These exercises build on [Lab 06 – Indexes](../labs/lab06-indexes.md). **Part A** (Exercises 1–6) uses `AdventureWorksENG` — the same database the midterm is written against. **Part B** (Exercises 7–10) uses the lab's large `IndexLab` database.

For Part A, note that `AdventureWorksENG` is much smaller than `IndexLab` (hundreds to low tens-of-thousands of rows per table here, versus tens of millions there). That has one consequence worth stating up front:

> [!IMPORTANT]
> On a table this size, SQL Server sometimes chooses a plain scan even where a "correct" index exists — and that can be the right choice (Lab 06, Section 7.1). Exercise 4 below produces exactly that outcome for real. The point of these exercises is not to force a dramatic `Scan → Seek` flip like the `IndexLab` demo. It is to practice **designing** the right index for a given query, and correctly **reasoning** about execution plans, column order, and coverage — skills that transfer regardless of table size.

Every number quoted in Part A (`logical reads`, row counts, which color is rarest, ...) was measured directly against this course's `AdventureWorksENG` — the same fixed dataset you have. Every exercise therefore uses literal values instead of looking an ID up first; you do not need a `DECLARE` block to reproduce any of this.

Each Part A exercise creates one real, physical index on an existing `AdventureWorksENG` table — unlike the trigger/procedure/function exercises, these are not new, isolated objects. Use the naming convention below and run the cleanup section when you are done, so you don't accumulate leftover indexes across study sessions.

## Setup

```sql
USE AdventureWorksENG;
GO
```

Enable, as in Lab 06:

```text
Query → Include Actual Execution Plan   (or Ctrl+M)
```

```sql
SET STATISTICS IO ON;
GO
```

With this on, the **Messages** tab reports a line like:

```text
Table 'Product'. Scan count 1, logical reads 8, physical reads 0, ...
```

The number right after `logical reads` is what several exercises below ask you to compare before and after creating an index — on a small table, that number is often a clearer signal than whether the plan shows "Seek" or "Scan".

All indexes created here use the prefix `IX_Exercises_` so they are easy to find and remove.

---

# Part A – `AdventureWorksENG`

## Exercise 1 — What `INCLUDE` actually buys you [BEGINNER]

This exercise walks through the full story in stages: a filter-only index, proof that it stops helping the moment the query needs one more column, and the fix. Watch **logical reads** in the Messages tab (`SET STATISTICS IO ON`, from Setup) at every step, not just the plan icons — on a table this small, the read count is often the clearer signal. The numbers quoted below are what this exact query returns against this course's `AdventureWorksENG` — you should see the same ones.

We will use `SubcategoryID = 12` throughout, which has 28 products.

**a) Baseline.** Run, with no index yet beyond the default clustered primary key:

```sql
SELECT IDProduct, SubcategoryID
FROM Product
WHERE SubcategoryID = 12;
```

Expect `logical reads 8`.

**b) Create an index on the filter column alone:**

```sql
CREATE NONCLUSTERED INDEX IX_Exercises_Product_SubcategoryID
ON Product (SubcategoryID);
GO
```

**c) Re-run the exact query from (a).** Expect `logical reads 2`.

<details>
<summary>Why did this work without an `INCLUDE`?</summary>

The query only returns `IDProduct` and `SubcategoryID`. `SubcategoryID` is the index key. `IDProduct` is `Product`'s clustering key — and the clustering key is **always** present at the leaf level of every nonclustered index, because it is the row locator SQL Server uses to find the full row if it ever needs to. You never need to `INCLUDE` it explicitly; it is already there for free.

</details>

**d) Now add one more returned column**, still using the same index from (b):

```sql
SELECT IDProduct, SubcategoryID, Name
FROM Product
WHERE SubcategoryID = 12;
```

Expect `logical reads 8` again — back up from step (c). `Name` is neither the key nor included, so SQL Server must look each matching row up in the clustered index to fetch it.

**e) Fix it.** Design and create a nonclustered index that supports the query from (d) **and** returns the results sorted by `PriceWithoutVAT DESC`:

```sql
SELECT IDProduct, SubcategoryID, Name, PriceWithoutVAT
FROM Product
WHERE SubcategoryID = 12
ORDER BY PriceWithoutVAT DESC;
```

<details>
<summary>Hint for (e)</summary>

`SubcategoryID` is the filter, so it leads the key. The query also needs the matching rows in `PriceWithoutVAT DESC` order — put that in the key too, not just `INCLUDE`, so SQL Server can avoid a separate `Sort`. `Name` is returned but neither filtered nor sorted on, so it belongs in `INCLUDE`. `IDProduct` needs nothing — see (c).

</details>

<details>
<summary>Solution for (e)</summary>

```sql
DROP INDEX IF EXISTS IX_Exercises_Product_SubcategoryID ON Product;

CREATE NONCLUSTERED INDEX IX_Exercises_Product_SubcategoryID_Price
ON Product (SubcategoryID, PriceWithoutVAT DESC)
INCLUDE (Name);
GO
```

Re-run the query from (e). Expect `logical reads 2` again, and the plan should show a single `Index Seek, ORDERED FORWARD` — no `Key Lookup`, no separate `Sort`.

</details>

**f) Bonus — `INCLUDE` also covers extra filters, not just extra returned columns.** Using the index from (e), run:

```sql
SELECT IDProduct, SubcategoryID, Name, PriceWithoutVAT
FROM Product
WHERE SubcategoryID = 12
  AND Name LIKE N'HL%'
ORDER BY PriceWithoutVAT DESC;
```

Expect `logical reads 2` here too — unchanged from (e), even with the extra condition.

<details>
<summary>Why does this stay covered?</summary>

`Name` is physically present at the leaf level as an included column, so SQL Server can check `LIKE N'HL%'` right there — as a **residual predicate** on the index itself, visible in the plan as a `WHERE:` clause attached to the same `Index Seek` — without a separate lookup to the clustered index. An included column is not just for the `SELECT` list; anything already sitting at the leaf can also be filtered on for free.

</details>

---

## Exercise 2 — Composite index column order [INTERMEDIATE]

Create this index:

```sql
CREATE NONCLUSTERED INDEX IX_Exercises_Invoice_CustomerID_InvoiceDate
ON Invoice (CustomerID, InvoiceDate);
GO
```

For each query below, decide whether it can use the index via a seek on the **full key**, a seek on just the **leading column**, or **not efficiently at all** — then check with an actual execution plan. `CustomerID = 15194` has 28 invoices in this dataset.

```sql
-- A
SELECT * FROM Invoice WHERE InvoiceDate >= '20030101';

-- B
SELECT * FROM Invoice WHERE CustomerID = 15194 ORDER BY InvoiceDate;

-- C
SELECT * FROM Invoice
WHERE CustomerID = 15194
  AND InvoiceDate >= '20030101'
  AND InvoiceDate <  '20040101';
```

<details>
<summary>Hint</summary>

The index is sorted first by `CustomerID`, then by `InvoiceDate` within each customer. Ask: does the query supply a value for the leading column?

</details>

<details>
<summary>Solution</summary>

- **A** — Not efficiently. `InvoiceDate` is not the leading key column, so the plan shows a `Clustered Index Scan` with a residual predicate instead of a seek on this index.
- **B** — Seek on the leading column (`CustomerID`). Because `InvoiceDate` is the second key column, that customer's rows are already stored in `InvoiceDate` order, so the `ORDER BY` may be satisfied without an extra `Sort`.
- **C** — Seek on the full key (`CustomerID` and `InvoiceDate` together) — the most selective of the three, and typically the cheapest.

The written order of the predicates in the `WHERE` clause (B puts `CustomerID` first, but that wouldn't matter if it were written the other way around) never determines index key order — only the index definition does.

> [!NOTE]
> All three queries use `SELECT *`, so expect a `Key Lookup` after the seek in B and C regardless — this index only has `CustomerID` and `InvoiceDate`, and `SELECT *` needs every other column too. That lookup is a separate issue from the one this exercise is about (whether the *seek itself* can use the leading column, the full key, or neither); Exercise 3 is where covering comes in.

</details>

---

## Exercise 3 — Covering index design [INTERMEDIATE]

Run this query with the actual execution plan enabled — `InvoiceID = 51201` has 2 line items in this dataset:

```sql
SELECT
    ProductID,
    Quantity,
    TotalPrice
FROM InvoiceItem
WHERE InvoiceID = 51201;
```

Before creating anything, run it and note the logical reads (expect `logical reads 847` — `InvoiceItem` is the largest table here, and nothing indexes `InvoiceID` yet). Design a nonclustered index so this query does not need a `Key Lookup` back to the clustered index. Confirm with an actual execution plan.

<details>
<summary>Hint</summary>

The key supports the `WHERE` clause. Every column the `SELECT` list returns, that is not already the key, needs to be in `INCLUDE` for the index to fully cover the query.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE NONCLUSTERED INDEX IX_Exercises_InvoiceItem_InvoiceID
ON InvoiceItem (InvoiceID)
INCLUDE (ProductID, Quantity, TotalPrice);
GO
```

`InvoiceID` is the key because the query filters on it. `ProductID`, `Quantity`, and `TotalPrice` are included because the query returns them but does not filter or sort by them — with all three present, every column the query needs is either the key or an included column, so no `Key Lookup` is required. Re-run the query: `logical reads` should drop from 847 to 3, and the plan should show a single `Index Seek`.

</details>

---

## Exercise 4 — Selectivity [INTERMEDIATE]

Inspect the distribution of `Product.Color`:

```sql
SELECT
    Color,
    COUNT(*) AS NumberOfProducts
FROM Product
GROUP BY Color
ORDER BY NumberOfProducts DESC;
GO
```

Create an index on it:

```sql
CREATE NONCLUSTERED INDEX IX_Exercises_Product_Color
ON Product (Color);
GO
```

In this dataset, the most common actual color value is `Crna` (93 products out of 504), and the rarest is `Siva` (1 product) — run the same shape of query for each, with the actual execution plan enabled:

```sql
SELECT IDProduct, Name FROM Product WHERE Color = N'Crna'; -- most common
SELECT IDProduct, Name FROM Product WHERE Color = N'Siva'; -- rarest
```

Answer: for which of the two colors is this index more likely to be useful, and why?

<details>
<summary>Hint</summary>

Selectivity is about how much of the table matches one value — not about how many distinct values the column has overall.

</details>

<details>
<summary>Solution</summary>

For `Crna`, the plan is a plain `Clustered Index Scan` — the optimizer does not even use `IX_Exercises_Product_Color`. With 93 of 504 rows matching (about 18%), seeking the index and then looking up every one of those rows in the clustered index is not obviously cheaper than just scanning the table once, so SQL Server skips the new index entirely.

For `Siva`, the plan is `Index Seek` on `IX_Exercises_Product_Color`, then `Nested Loops` into a `Clustered Index Seek ... LOOKUP` for `Name` — one lookup, because only one row matches. The index is clearly worth using here.

`Color` can have very few distinct values and still be a good index candidate, as long as the distribution is skewed — a rare value stays highly selective even when the column overall has few distinct values. This also shows, concretely, the Lab 06 Section 7.1 point: SQL Server choosing a scan is not automatically wrong.

</details>

**Bonus — covering a `GROUP BY` instead of a `WHERE`.** Covering isn't limited to filtered or sorted columns; a column used only in `GROUP BY` needs to be covered too. Using `IX_Exercises_Product_SubcategoryID_Price` from Exercise 1 (key: `SubcategoryID`, `PriceWithoutVAT DESC`; included: `Name`):

```sql
SELECT
    SubcategoryID,
    Color,
    COUNT(*) AS NumberOfProducts
FROM Product
WHERE SubcategoryID = 12
GROUP BY SubcategoryID, Color;
```

<details>
<summary>Think about it</summary>

`Color` is in neither the key nor the `INCLUDE` list of `IX_Exercises_Product_SubcategoryID_Price`, so that index cannot fully support this `GROUP BY` — in practice, with only 28 matching rows, the optimizer here simply falls back to a plain `Clustered Index Scan` rather than seeking the nonclustered index and looking `Color` up row by row; on a larger table, a `Key Lookup` per row is the more typical shape of this same problem. Either way, the fix is the same idea as before: add `Color` to `INCLUDE` (or the key) of whichever index is meant to support this query.

</details>

---

## Exercise 5 — Evaluate a Missing Index suggestion [ADVANCED]

Run this query and inspect any "Missing Index" recommendation SQL Server offers:

```sql
SELECT
    c.FirstName,
    c.LastName,
    i.InvoiceNumber,
    i.InvoiceDate
FROM Customer AS c
JOIN Invoice AS i
    ON i.CustomerID = c.IDCustomer
WHERE i.InvoiceDate >= '20030101'
  AND i.InvoiceDate <  '20040101'
ORDER BY i.InvoiceDate;
```

Before creating anything, answer:

1. Does a similar index already exist from the earlier exercises in this file?
2. Would a newly suggested index overlap or duplicate an existing one?
3. Should you create a new index, extend an existing one, or do nothing? Justify your decision.

<details>
<summary>Solution</summary>

Without any index beyond the Exercise 2 one, the plan for this query is `Sort → Hash Match (Inner Join) → Clustered Index Scan (Invoice) / Clustered Index Scan (Customer)` — both tables scanned in full, then hashed together. SQL Server's missing-index feature suggests an index on `Invoice (InvoiceDate) INCLUDE (InvoiceNumber, CustomerID)`.

1. `IX_Exercises_Invoice_CustomerID_InvoiceDate` (Exercise 2) exists on `Invoice (CustomerID, InvoiceDate)`, but this query filters and sorts by `InvoiceDate` **without** a `CustomerID` predicate — so that index's leading column does not help here.
2. The suggested index on `Invoice (InvoiceDate)` would not duplicate the Exercise 2 index — it serves a different access pattern (no customer filter at all).
3. In a real workload, the better choice is usually to evaluate whether this query pattern (all invoices in a date range, regardless of customer) is actually common enough to justify a new index, given that `IX_Exercises_Invoice_CustomerID_InvoiceDate` already exists for the customer-scoped case. Creating both means `Invoice` now has two overlapping nonclustered indexes in different roles — a reasonable call if both access patterns genuinely occur, but worth a deliberate decision rather than accepting every suggestion automatically.

</details>

---

## Exercise 6 — The same pattern, on a different table [INTERMEDIATE]

Exercise 5's missing-index suggestion was `Invoice (InvoiceDate) INCLUDE (InvoiceNumber, CustomerID)`. This exercise builds that same shape of index by hand, one step at a time, on a simpler query — the same staged pattern as Exercise 1, but on `Invoice` instead of `Product`, so you can check whether you recognize the pattern on a table and columns you have not seen it applied to yet.

`InvoiceDate BETWEEN '20010702' AND '20010702 23:59:59'` matches exactly 4 rows in this dataset. Watch **logical reads** at every step.

**a) Baseline.** Run, with no index yet beyond the clustered primary key:

```sql
SELECT InvoiceDate
FROM Invoice
WHERE InvoiceDate BETWEEN '20010702' AND '20010702 23:59:59';
```

Expect `logical reads 202` — a full scan of `Invoice`.

**b) Create an index on the filter column alone:**

```sql
CREATE NONCLUSTERED INDEX IX_Exercises_Invoice_InvoiceDate
ON Invoice (InvoiceDate);
GO
```

**c) Re-run the query from (a).** Expect `logical reads 2`.

**d) Add the clustering key to the returned columns**, still using the index from (b):

```sql
SELECT IDInvoice, InvoiceDate
FROM Invoice
WHERE InvoiceDate BETWEEN '20010702' AND '20010702 23:59:59';
```

<details>
<summary>What do you expect, and why?</summary>

Still `logical reads 2`. `IDInvoice` is `Invoice`'s clustering key, and the clustering key is always present at the leaf level of every nonclustered index — the same reason this worked for free in Exercise 1(c).

</details>

**e) Now add one more returned column**, still using the same index:

```sql
SELECT IDInvoice, InvoiceNumber, InvoiceDate
FROM Invoice
WHERE InvoiceDate BETWEEN '20010702' AND '20010702 23:59:59';
```

What do you expect to happen to `logical reads`, and why?

<details>
<summary>Solution</summary>

`logical reads` rises to **10**. `InvoiceNumber` is neither the key nor included, so SQL Server must look each of the 4 matching rows up in the clustered index to fetch it — the same `Key Lookup` pattern as Exercise 1(d).

</details>

**f) Fix it.** Design and create a nonclustered index that supports the query from (e) without a `Key Lookup`.

<details>
<summary>Hint</summary>

The fix is the same shape as Exercise 1(e): keep the filter column as the key, and add the extra returned column with `INCLUDE`. You do not need to add `IDInvoice` — see (d).

</details>

<details>
<summary>Solution</summary>

```sql
DROP INDEX IF EXISTS IX_Exercises_Invoice_InvoiceDate ON Invoice;

CREATE NONCLUSTERED INDEX IX_Exercises_Invoice_InvoiceDate
ON Invoice (InvoiceDate)
INCLUDE (InvoiceNumber);
GO
```

Re-run the query from (e). Expect `logical reads 2` again, with a single `Index Seek` and no `Key Lookup`.

</details>

**g) Bonus — a residual filter on an included column.** Using the index from (f), run:

```sql
SELECT IDInvoice
FROM Invoice
WHERE InvoiceDate BETWEEN '20010702' AND '20010702 23:59:59'
  AND InvoiceNumber LIKE 'S%';
```

Expect `logical reads 2` — unchanged, for the same reason as Exercise 1(f): `InvoiceNumber` is already present at the leaf level, so SQL Server can evaluate `LIKE 'S%'` right there as a residual predicate. (All 4 matching invoice numbers happen to start with `SO`, so this particular filter does not reduce the row count — but it does not cost any extra reads either.)

**h) Bonus — why did Exercise 5 also suggest `CustomerID`?** Still using the index from (f), run:

```sql
SELECT CustomerID, COUNT(*) AS Cnt
FROM Invoice
WHERE InvoiceDate BETWEEN '20010702' AND '20010702 23:59:59'
GROUP BY CustomerID
ORDER BY Cnt DESC;
```

<details>
<summary>Think about it</summary>

`logical reads` rises back to **10** — `CustomerID` is in neither the key nor the `INCLUDE` list of this index, so it is not covered, the same gap as Exercise 4's `Color` case. This is exactly why Exercise 5's missing-index suggestion included `CustomerID` in its `INCLUDE` list: that query also joined on `CustomerID`, so the optimizer's suggestion was shaped by a different query than this one. A recommendation only covers the query that produced it — the general point Exercise 5 itself makes.

</details>

---

# Part B – `IndexLab`

Exercises 7–10 use the large `IndexLab` database from [Lab 06](../labs/lab06-indexes.md) instead of `AdventureWorksENG`. On a table with ten million rows, the effect of an index is easy to see in the execution plan and in `logical reads`.

> [!IMPORTANT]
> Do these exercises after Lab 06, in the same `IndexLab` database. They rely on the indexes the lab creates: `IX_SalesOrder_CustomerId_OrderDate`, `IX_SalesOrder_Status`, `IX_SalesOrder_Review_OrderDate`, and `IX_SalesOrderItem_SalesOrderId`.

Keep **Actual Execution Plan** enabled, and start with:

```sql
USE IndexLab;
GO
```

## Exercise 7 — Index for a filtered, sorted query [INTERMEDIATE]

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

> [!TIP]
> The query returns about one million rows. Displaying them in the SSMS results grid takes longer than executing the query itself, so before measuring, enable **Query → Query Options → Results → Grid → Discard results after execution**.

<details>
<summary>Solution</summary>

```sql
CREATE NONCLUSTERED INDEX IX_Exercises_SalesOrder_Status_OrderDate
ON dbo.SalesOrder (Status, OrderDate DESC)
INCLUDE (CustomerId, TotalAmount);
GO
```

`Status` is the leading key because of the equality filter. `OrderDate` follows it, so within one status the entries are already in date order and no `Sort` is needed. `CustomerId` and `TotalAmount` are included to cover the selected data. `SalesOrderId` is already available as the clustered key.

Declaring `OrderDate DESC` matches the requested order, but it is not required: SQL Server can read an ascending index backward just as well (Exercise 10 relies on exactly this). The direction of a key column matters when `ORDER BY` mixes directions, for example `ORDER BY Status ASC, OrderDate DESC` without an equality filter on `Status`.

Reference results:

| | Before the index | With `IX_Exercises_SalesOrder_Status_OrderDate` |
|---|---|---|
| Plan | `Clustered Index Scan` + `Sort` | `Index Seek`, no `Sort` |
| Logical reads | 57,266 | 5,462 |
| Elapsed time | about 4.9 s | about 0.5 s |

</details>

---

## Exercise 8 — Composite index column order [INTERMEDIATE]

Lab 06 created `IX_SalesOrder_CustomerId_OrderDate` on `(CustomerId, OrderDate)`. For each query below, predict whether the index supports a seek on both key columns, a seek on the leading column, or no efficient seek on the search condition. Verify your prediction in the plan.

```sql
-- A
SELECT * FROM dbo.SalesOrder WHERE OrderDate >= '20250101';

-- B
SELECT * FROM dbo.SalesOrder WHERE CustomerId = 501 ORDER BY OrderDate;

-- C
SELECT * FROM dbo.SalesOrder
WHERE CustomerId = 501
  AND OrderDate >= '20250101'
  AND OrderDate <  '20250201';
```

<details>
<summary>Solution</summary>

- **A:** no efficient seek on `OrderDate` alone using this index because the first key (`CustomerId`) is missing.
- **B:** seek on `CustomerId`; rows for that customer are then in `OrderDate` order, potentially avoiding `Sort`.
- **C:** seek using the equality on `CustomerId` and the range on `OrderDate`.

Check the **Object** property to identify which index SQL Server actually used. For Query A, the separate `IX_SalesOrder_OrderDate` index could locate the date range, but the condition matches roughly one fifth of the table (about 2 million rows) and `SELECT *` would require a lookup for each of them. Expect a `Clustered Index Scan` instead. Neither outcome means that the composite index supports an efficient seek on `OrderDate` alone.

For Queries B and C, `SELECT *` requires a Key Lookup for every matching order. An actual plan may vary due to these lookup costs.

</details>

---

## Exercise 9 — Covering index design [BEGINNER]

Write and analyze a query that returns `ProductId`, `Quantity`, and `UnitPrice` for one `SalesOrderId`:

```sql
SELECT ProductId, Quantity, UnitPrice
FROM dbo.SalesOrderItem
WHERE SalesOrderId = 12345;
```

Confirm whether it needs a Key Lookup.

<details>
<summary>Solution</summary>

The existing `IX_SalesOrderItem_SalesOrderId` index with `INCLUDE (ProductId, Quantity, UnitPrice)` covers the query. The engine should generally be able to use it without an extra Key Lookup.

</details>

---

## Exercise 10 — Evaluate a Missing Index suggestion [ADVANCED]

Run the following query with Actual Execution Plan enabled:

```sql
SELECT SalesOrderId, OrderDate
FROM dbo.SalesOrder
WHERE Status = 'Cancelled'
ORDER BY OrderDate;
```

If a Missing Index suggestion appears above the plan, look at it carefully before creating anything, and consider:

1. Which relevant indexes already exist, including `IX_SalesOrder_Status` from [Section 10.2](../labs/lab06-indexes.md#102-selectivity-and-statistics), the filtered index `IX_SalesOrder_Review_OrderDate` from [Section 10.4](../labs/lab06-indexes.md#104-filtered-indexes), and `IX_Exercises_SalesOrder_Status_OrderDate` if you completed Exercise 7?
2. Can an existing index support both the filter and the requested sort order?
3. Does the suggested index support both of them?
4. Is it better to create the suggested index, replace an overlapping index, or do nothing?

<details>
<summary>Solution</summary>

**The filtered index is not used.** `IX_SalesOrder_Review_OrderDate` contains only `Review` orders, so it cannot answer a query for `Cancelled` orders (see the limitations in [Section 10.4](../labs/lab06-indexes.md#104-filtered-indexes)).

**If you completed Exercise 7**, no suggestion appears. `IX_Exercises_SalesOrder_Status_OrderDate` already covers the query: with `Status` fixed by the equality condition, SQL Server reads the `Cancelled` part of the index backward (`Index Seek` with `ORDERED BACKWARD` in the plan properties) and returns the rows in ascending date order without a `Sort`. The reference run needed 3,751 logical reads. No new index is needed.

**If you skipped Exercise 7**, the reference plan uses a `Clustered Index Scan` followed by a `Sort` (57,266 logical reads), and SQL Server suggests an index similar to:

```sql
-- Missing Index suggestion (estimated impact about 41%)
CREATE NONCLUSTERED INDEX ...
ON dbo.SalesOrder (Status)
INCLUDE (OrderDate);
```

This suggestion has two weaknesses:

- `OrderDate` is only an included column, so it does not determine the order of the index. The index would find the cancelled orders, but the `Sort` would remain. Missing Index suggestions do not take `ORDER BY` into account.
- It is almost a duplicate of the existing `IX_SalesOrder_Status`, which has the same key.

A better design is an index on `(Status, OrderDate)`. It supports both the filter and the sort, and, following the leftmost-prefix rule from [Section 10.1](../labs/lab06-indexes.md#101-composite-indexes-and-column-order), it also supports every search on `Status` alone. It should therefore **replace** `IX_SalesOrder_Status` rather than be added next to it. In a real system, inspect the entire workload before making this change.

</details>

---

# Cleanup

```sql
DROP INDEX IF EXISTS IX_Exercises_Product_SubcategoryID_Price ON Product;
DROP INDEX IF EXISTS IX_Exercises_Invoice_CustomerID_InvoiceDate ON Invoice;
DROP INDEX IF EXISTS IX_Exercises_InvoiceItem_InvoiceID ON InvoiceItem;
DROP INDEX IF EXISTS IX_Exercises_Product_Color ON Product;
DROP INDEX IF EXISTS IX_Exercises_Invoice_InvoiceDate ON Invoice;
GO
```

If you created the index suggested in Exercise 5, drop it the same way using the name you gave it.

For Part B, remove the index created in Exercise 7 from `IndexLab`. The indexes created by Lab 06 itself stay in place:

```sql
USE IndexLab;
GO
DROP INDEX IF EXISTS IX_Exercises_SalesOrder_Status_OrderDate ON dbo.SalesOrder;
GO
USE AdventureWorksENG;
GO
```

> [!TIP]
> Run this cleanup before your next study session, or before the exam. Leftover indexes from earlier practice can change execution plans in ways that make a later exercise behave differently than described here.
