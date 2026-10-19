# Index Exercises

These exercises build on [Lab 06 – Indexes](../labs/lab06-indexes.md) and use `AdventureWorksENG` — the same database the midterm is written against — instead of `IndexLab`.

`AdventureWorksENG` is much smaller than `IndexLab` (hundreds to low tens-of-thousands of rows per table here, versus tens of millions there). That has one consequence worth stating up front:

> [!IMPORTANT]
> On a table this size, SQL Server sometimes chooses a plain scan even where a "correct" index exists — and that can be the right choice (Lab 06, Section 26). Exercise 4 below produces exactly that outcome for real. The point of these exercises is not to force a dramatic `Scan → Seek` flip like the `IndexLab` demo. It is to practice **designing** the right index for a given query, and correctly **reasoning** about execution plans, column order, and coverage — skills that transfer regardless of table size.

Every number quoted in this file (`logical reads`, row counts, which color is rarest, ...) was measured directly against this course's `AdventureWorksENG` — the same fixed dataset you have. Every exercise therefore uses literal values instead of looking an ID up first; you do not need a `DECLARE` block to reproduce any of this.

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

`Color` can have very few distinct values and still be a good index candidate, as long as the distribution is skewed — a rare value stays highly selective even when the column overall has few distinct values. This also shows, concretely, the Lab 06 Section 26 point: SQL Server choosing a scan is not automatically wrong.

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
