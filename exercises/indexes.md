# Index Exercises

These exercises build on [Lab 06 – Indexes](../labs/lab06-indexes.md) and use `AdventureWorksENG` — the same database the midterm is written against — instead of `IndexLab`.

`AdventureWorksENG` is much smaller than `IndexLab`. That has one consequence worth stating up front:

> [!IMPORTANT]
> On a small table, SQL Server may still choose a scan even after you create a "correct" index — and that can be the right choice (Lab 06, Section 26). The point of these exercises is not to force a dramatic `Scan → Seek` flip like the `IndexLab` demo. It is to practice **designing** the right index for a given query, and correctly **reasoning** about execution plans, column order, and coverage — skills that transfer regardless of table size.

Each exercise creates one real, physical index on an existing `AdventureWorksENG` table — unlike the trigger/procedure/function exercises, these are not new, isolated objects. Use the naming convention below and run the cleanup section when you are done, so you don't accumulate leftover indexes across study sessions.

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

## Exercise 1 — What `INCLUDE` actually buys you [BEGINNER]

This exercise walks through the full story in stages: a filter-only index, proof that it stops helping the moment the query needs one more column, and the fix. Watch **logical reads** in the Messages tab (`SET STATISTICS IO ON`, from Setup) at every step, not just the plan icons — on a table this small, the read count is often the clearer signal.

First, pick a `SubcategoryID` that has more than one product:

```sql
DECLARE @SubcategoryID int;

SELECT TOP (1) @SubcategoryID = SubcategoryID
FROM Product
WHERE SubcategoryID IS NOT NULL
GROUP BY SubcategoryID
HAVING COUNT(*) > 1;

SELECT @SubcategoryID AS SubcategoryID;
```

Use that same `@SubcategoryID` value as a literal in every query below.

**a) Baseline.** Run, with no index yet beyond the default clustered primary key:

```sql
SELECT IDProduct, SubcategoryID
FROM Product
WHERE SubcategoryID = 1; -- replace 1 with the ID you found above
```

Note the logical reads.

**b) Create an index on the filter column alone:**

```sql
CREATE NONCLUSTERED INDEX IX_Exercises_Product_SubcategoryID
ON Product (SubcategoryID);
GO
```

**c) Re-run the exact query from (a).** The logical reads should now be lower.

<details>
<summary>Why did this work without an `INCLUDE`?</summary>

The query only returns `IDProduct` and `SubcategoryID`. `SubcategoryID` is the index key. `IDProduct` is `Product`'s clustering key — and the clustering key is **always** present at the leaf level of every nonclustered index, because it is the row locator SQL Server uses to find the full row if it ever needs to. You never need to `INCLUDE` it explicitly; it is already there for free.

</details>

**d) Now add one more returned column**, still using the same index from (b):

```sql
SELECT IDProduct, SubcategoryID, Name
FROM Product
WHERE SubcategoryID = 1; -- same ID as before
```

Compare the logical reads with step (c). They should go back up — `Name` is neither the key nor included, so SQL Server must look each matching row up in the clustered index to fetch it.

**e) Fix it.** Design and create a nonclustered index that supports the query from (d) **and** returns the results sorted by `PriceWithoutVAT DESC`:

```sql
SELECT IDProduct, SubcategoryID, Name, PriceWithoutVAT
FROM Product
WHERE SubcategoryID = 1 -- same ID as before
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

Re-run the query from (e). Logical reads should drop again, and no `Sort` operator should be needed.

</details>

**f) Bonus — `INCLUDE` also covers extra filters, not just extra returned columns.** Using the index from (e), run:

```sql
SELECT IDProduct, SubcategoryID, Name, PriceWithoutVAT
FROM Product
WHERE SubcategoryID = 1 -- same ID as before
  AND Name LIKE N'A%'
ORDER BY PriceWithoutVAT DESC;
```

<details>
<summary>Why does this stay covered?</summary>

`Name` is physically present at the leaf level as an included column, so SQL Server can check `LIKE N'A%'` right there — as a **residual predicate** on the index itself — without a separate lookup to the clustered index. An included column is not just for the `SELECT` list; anything already sitting at the leaf can also be filtered on for free.

</details>

---

## Exercise 2 — Composite index column order [INTERMEDIATE]

Create this index:

```sql
CREATE NONCLUSTERED INDEX IX_Exercises_Invoice_CustomerID_InvoiceDate
ON Invoice (CustomerID, InvoiceDate);
GO
```

For each query below, decide whether it can use the index via a seek on the **full key**, a seek on just the **leading column**, or **not efficiently at all** — then check with an actual execution plan.

```sql
DECLARE @CustomerID int;

SELECT TOP (1) @CustomerID = CustomerID
FROM Invoice
GROUP BY CustomerID
HAVING COUNT(*) > 1;

-- A
SELECT * FROM Invoice WHERE InvoiceDate >= '20030101';

-- B
SELECT * FROM Invoice WHERE CustomerID = @CustomerID ORDER BY InvoiceDate;

-- C
SELECT * FROM Invoice
WHERE CustomerID = @CustomerID
  AND InvoiceDate >= '20030101'
  AND InvoiceDate <  '20040101';
```

<details>
<summary>Hint</summary>

The index is sorted first by `CustomerID`, then by `InvoiceDate` within each customer. Ask: does the query supply a value for the leading column?

</details>

<details>
<summary>Solution</summary>

- **A** — Not efficiently. `InvoiceDate` is not the leading key column, so the index cannot be seeked on it alone.
- **B** — Seek on the leading column (`CustomerID`). Because `InvoiceDate` is the second key column, that customer's rows are already stored in `InvoiceDate` order, so the `ORDER BY` may be satisfied without an extra `Sort`.
- **C** — Seek on the full key (`CustomerID` and `InvoiceDate` together) — the most selective of the three, and typically the cheapest, though on a small table the difference in cost from B may be negligible.

The written order of the predicates in the `WHERE` clause (B puts `CustomerID` first, but that wouldn't matter if it were written the other way around) never determines index key order — only the index definition does.

</details>

---

## Exercise 3 — Covering index design [INTERMEDIATE]

Run this query with the actual execution plan enabled:

```sql
DECLARE @InvoiceID int;

SELECT TOP (1) @InvoiceID = InvoiceID
FROM InvoiceItem;

SELECT
    ProductID,
    Quantity,
    TotalPrice
FROM InvoiceItem
WHERE InvoiceID = @InvoiceID;
```

Design a nonclustered index so this query does not need a `Key Lookup` back to the clustered index. Confirm with an actual execution plan.

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

`InvoiceID` is the key because the query filters on it. `ProductID`, `Quantity`, and `TotalPrice` are included because the query returns them but does not filter or sort by them — with all three present, every column the query needs is either the key or an included column, so no `Key Lookup` is required.

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

Pick the most common color from your distribution and the least common one, then run the same shape of query for each:

```sql
SELECT IDProduct, Name
FROM Product
WHERE Color = N'...'; -- try the most common, then the least common
```

Answer: for which of the two colors is this index more likely to be useful, and why?

<details>
<summary>Hint</summary>

Selectivity is about how much of the table matches one value — not about how many distinct values the column has overall.

</details>

<details>
<summary>Solution</summary>

The index is more attractive for the **least common** color: a seek returns only a handful of rows out of the whole table. For the **most common** color, a large share of all rows match — at that point scanning the table (or the index) may cost about the same as, or even more than, seeking plus looking up every matching row, so the optimizer may reasonably choose a scan instead.

`Color` can have very few distinct values and still be a good index candidate, as long as the distribution is skewed — a rare value stays highly selective even when the column overall has few distinct values.

</details>

**Bonus — covering a `GROUP BY` instead of a `WHERE`.** Covering isn't limited to filtered or sorted columns; a column used only in `GROUP BY` needs to be covered too:

```sql
SELECT
    SubcategoryID,
    Color,
    COUNT(*) AS NumberOfProducts
FROM Product
WHERE SubcategoryID = 1 -- use the same SubcategoryID as in Exercise 1
GROUP BY SubcategoryID, Color;
```

<details>
<summary>Think about it</summary>

Does `IX_Exercises_Product_SubcategoryID_Price` from Exercise 1 cover this query? It does not — `Color` is in neither its key nor its `INCLUDE` list, so SQL Server still needs a `Key Lookup` for every matching row before it can group by `Color`. The fix is the same idea as before: add `Color` to `INCLUDE` (or the key) of whichever index is meant to support this query.

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

1. `IX_Exercises_Invoice_CustomerID_InvoiceDate` (Exercise 2) exists on `Invoice (CustomerID, InvoiceDate)`, but this query filters and sorts by `InvoiceDate` **without** a `CustomerID` predicate — so that index's leading column does not help here.
2. A suggested index on `Invoice (InvoiceDate)` would not duplicate the Exercise 2 index — it serves a different access pattern (no customer filter at all).
3. In a real workload, the better choice is usually to evaluate whether this query pattern (all invoices in a date range, regardless of customer) is actually common enough to justify a new index, given that `IX_Exercises_Invoice_CustomerID_InvoiceDate` already exists for the customer-scoped case. Creating both means `Invoice` now has two overlapping nonclustered indexes on `InvoiceDate` in different roles — a reasonable call if both access patterns genuinely occur, but worth a deliberate decision rather than accepting every suggestion automatically.

</details>

---

# Cleanup

```sql
DROP INDEX IF EXISTS IX_Exercises_Product_SubcategoryID_Price ON Product;
DROP INDEX IF EXISTS IX_Exercises_Invoice_CustomerID_InvoiceDate ON Invoice;
DROP INDEX IF EXISTS IX_Exercises_InvoiceItem_InvoiceID ON InvoiceItem;
DROP INDEX IF EXISTS IX_Exercises_Product_Color ON Product;
GO
```

If you created the index suggested in Exercise 5, drop it the same way using the name you gave it.

> [!TIP]
> Run this cleanup before your next study session, or before the exam. Leftover indexes from earlier practice can change execution plans in ways that make a later exercise behave differently than described here.
