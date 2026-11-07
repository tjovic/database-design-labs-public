# Lab 11 – Advanced Grouping

**Database:** `AdventureWorksENG`

Every lab so far has been about building a database — tables, procedures, indexes, transactions. The database is now built. It holds data. The question changes: not "how do I put data in", but "how do I ask hard questions of it"?

Consider a spreadsheet report with subtotals for every category and a grand total at the bottom. Writing that in plain SQL usually means three separate queries glued together with `UNION`. This lab covers three extensions to `GROUP BY` that produce that shape in a single query.

> [!IMPORTANT]
> **Core idea:** `ROLLUP` walks up a hierarchy, `CUBE` explores every combination, `GROUPING SETS` lets you list exactly the levels you want. All three are variations on one underlying idea: running several `GROUP BY`s at once and stacking the results.

---

## Learning objectives

After completing this lab, you should be able to:

- explain the difference between a bare aggregate and `GROUP BY ()`, and why they only disagree on an empty input;
- use `ROLLUP` to produce subtotals up a hierarchy in one query;
- use `CUBE` to produce every combination of subtotals, and explain why it grows as `2^n`;
- use `GROUPING SETS` to choose exactly which grouping levels appear, including levels neither `ROLLUP` nor `CUBE` can produce alone;
- rewrite any `ROLLUP` or `CUBE` as an equivalent `GROUPING SETS` list;
- use `GROUPING()` to tell a "this column was rolled away" `NULL` apart from a real data `NULL`, and build a readable report label from it.

> [!NOTE]
> **Prerequisites:** comfort with `SELECT`, `JOIN`, `WHERE`, `ORDER BY`, `GROUP BY`, and the aggregate functions `SUM`, `COUNT`, `AVG`, `MIN`, `MAX`. No stored procedures, functions, or triggers are used in this lab — every example is a plain `SELECT`.

---

# Section 1 – The Grand Total Idiom

There are two ways to compute a grand total in SQL:

```sql
-- The bare aggregate
SELECT SUM(ii.TotalPrice) AS GrandTotal FROM InvoiceItem ii;

-- Group by nothing
SELECT SUM(ii.TotalPrice) AS GrandTotal FROM InvoiceItem ii GROUP BY ();
```

They return the same answer for a non-empty table. The difference only shows up on an empty input:

| Form | Over 0 rows |
|---|---|
| Bare aggregate | 1 result row, value `NULL` |
| `GROUP BY ()` | 0 result rows |

> [!NOTE]
> This distinction matters today because every subtotal row you are about to see from `ROLLUP` and `CUBE` is, conceptually, a `GROUP BY ()` applied to a subset of the rows. If "group by nothing means grand total" feels natural, `ROLLUP` and `CUBE` will too.

---

# Section 2 – ROLLUP: Walking Up the Hierarchy

## 2.1 The algorithm

`ROLLUP` takes a list of columns, ordered from most detailed (left) to least detailed (right), and groups repeatedly — dropping the rightmost column each time — until it reaches the grand total:

```
GROUP BY ROLLUP (a, b, c)

is equivalent to:

  GROUP BY (a, b, c)     -- full detail
  GROUP BY (a, b)        -- drop the rightmost column
  GROUP BY (a)           -- drop another
  GROUP BY ()            -- grand total
```

Four grouping levels for three columns: start on the left with everything, peel off the rightmost column, group again, repeat until you're grouping by nothing.

## 2.2 Demo: Country, City, and a grand total

```sql
SELECT
    s.Name AS Country,
    c.Name AS City,
    SUM(ii.TotalPrice) AS Revenue
FROM InvoiceItem ii
JOIN Invoice i ON i.IDInvoice = ii.InvoiceID
JOIN Customer cu ON cu.IDCustomer = i.CustomerID
JOIN City c ON c.IDCity = cu.CityID
JOIN State s ON s.IDState = c.StateID
GROUP BY ROLLUP (s.Name, c.Name)
ORDER BY s.Name, c.Name;
```

Three kinds of row come back:

| Row shape | Meaning |
|---|---|
| `Country` and `City` both filled in | Detail — revenue for that one city |
| `Country` filled in, `City` is `NULL` | Subtotal — revenue for that whole country |
| Both `Country` and `City` are `NULL` | Grand total — revenue across everything |

One query, three levels — exactly the shape a dashboard renders as a bold subtotal line above its detail rows, with the grand total at the bottom of the page.

## 2.3 The NULL warning

`NULL` in a `ROLLUP` result column can mean two different things:

1. This column was rolled away at this level (a subtotal or grand-total row), **or**
2. the underlying data in this row genuinely is `NULL`.

You cannot tell these apart from the value alone. Section 5 shows the fix.

## 2.4 Check your understanding

1. Describe the algorithm for `ROLLUP(a, b, c)` in your own words.
2. How many grouping levels does `ROLLUP(a, b, c)` produce?
3. What does a `NULL` in a `ROLLUP` result column mean?

<details>
<summary>Show answers</summary>

1. Group by the full column list, then repeatedly drop the rightmost column and group again, until no columns remain (the grand total).
2. Four: `(a, b, c)`, `(a, b)`, `(a)`, `()`.
3. Usually "this column was rolled away at this level" — but if the underlying data also contains `NULL`s, you cannot distinguish the two without `GROUPING()`.

</details>

---

# Section 3 – CUBE: Every Combination

## 3.1 The algorithm

`CUBE` has the same syntax as `ROLLUP`, but instead of walking a hierarchy in one direction, it produces every possible combination of the grouping columns:

```
GROUP BY CUBE (a, b, c)

is equivalent to:

  GROUP BY (a, b, c)
  GROUP BY (a, b)   GROUP BY (a, c)   GROUP BY (b, c)
  GROUP BY (a)      GROUP BY (b)      GROUP BY (c)
  GROUP BY ()

8 grouping levels for 3 columns. For n columns: 2^n levels.
```

`ROLLUP` with three columns gave four levels; `CUBE` gives eight. The difference is the "middle" combinations `CUBE` includes — group by `(b, c)` while skipping `a` entirely, group by just `b`, and so on. `ROLLUP` is a straight line up the hierarchy; `CUBE` is the entire lattice of combinations.

## 3.2 Demo: the same query, every combination

```sql
SELECT
    s.Name AS Country,
    c.Name AS City,
    SUM(ii.TotalPrice) AS Revenue
FROM InvoiceItem ii
JOIN Invoice i ON i.IDInvoice = ii.InvoiceID
JOIN Customer cu ON cu.IDCustomer = i.CustomerID
JOIN City c ON c.IDCity = cu.CityID
JOIN State s ON s.IDState = c.StateID
GROUP BY CUBE (s.Name, c.Name)
ORDER BY s.Name, c.Name;
```

Compared to Section 2.2's `ROLLUP` result, there are new rows where `Country` is `NULL` but `City` is filled in — "revenue for this city, across every country". `ROLLUP` never produces that shape, because it only ever walks up the hierarchy in one direction; `CUBE` gives you everything.

## 3.3 When to use CUBE — and when not

| Use CUBE when | Don't use CUBE when |
|---|---|
| You genuinely need every possible aggregation level (rare) | A `ROLLUP` would already give you what you need |
| Building a pivot table with fully interchangeable dimensions | You want only some combinations — use `GROUPING SETS` instead |
| | You have many columns: `CUBE` on 6 columns is 64 grouping levels |

> [!IMPORTANT]
> Reach for `ROLLUP` first. Escalate to `CUBE` only when you actually need the extra combinations.

## 3.4 Check your understanding

1. How many grouping levels does `CUBE(a, b, c, d)` produce?
2. What extra rows does `CUBE` give you compared to `ROLLUP` on the same columns?
3. When is `ROLLUP` enough, and `CUBE` unnecessary?

<details>
<summary>Show answers</summary>

1. `2^4 = 16`. Each additional column doubles the count.
2. Every combination that skips a "middle" column — for `(Country, City)`, that's the rows grouped by `City` alone, across all countries, which `ROLLUP` never produces.
3. Whenever the grouping columns form a genuine hierarchy (country contains city, year contains month) and you only need subtotals up that hierarchy, not sideways combinations — the vast majority of real reporting queries.

</details>

---

# Section 4 – GROUPING SETS: Pick Your Own

## 4.1 The general form

`GROUPING SETS` is the explicit, general form: you list exactly which grouping levels you want, nothing more:

```
GROUP BY GROUPING SETS
(
    (a, b),   -- this level
    (a),      -- and this one
    ()        -- and the grand total
)
```

`ROLLUP` and `CUBE` are shortcuts for specific `GROUPING SETS` lists:

```
GROUP BY ROLLUP(a, b)  ==  GROUP BY GROUPING SETS ((a, b), (a), ())
GROUP BY CUBE(a, b)    ==  GROUP BY GROUPING SETS ((a, b), (a), (b), ())
```

## 4.2 Demo: subtotals without the detail rows

```sql
SELECT
    s.Name AS Country,
    c.Name AS City,
    SUM(ii.TotalPrice) AS Revenue
FROM InvoiceItem ii
JOIN Invoice i ON i.IDInvoice = ii.InvoiceID
JOIN Customer cu ON cu.IDCustomer = i.CustomerID
JOIN City c ON c.IDCity = cu.CityID
JOIN State s ON s.IDState = c.StateID
GROUP BY GROUPING SETS
(
    (s.Name),   -- by country
    (c.Name),   -- by city (across all countries)
    ()          -- grand total
)
ORDER BY s.Name, c.Name;
```

The result has no `(Country, City)` detail rows at all — only per-country subtotals, per-city subtotals (across every country), and a grand total. Neither `ROLLUP` nor `CUBE` can produce this shape alone; both would include the detail rows. `GROUPING SETS` lets you skip them.

| Tool | Produces |
|---|---|
| `ROLLUP` | Subtotals up a hierarchy |
| `CUBE` | Every possible subtotal |
| `GROUPING SETS` | Exactly the levels you list |

## 4.3 Check your understanding

1. Rewrite `ROLLUP(a, b, c)` as a `GROUPING SETS` list.
2. Give one scenario where `GROUPING SETS` is the only tool that produces the shape you need.

<details>
<summary>Show answers</summary>

1. `GROUPING SETS ((a, b, c), (a, b), (a), ())`.
2. Revenue by country, revenue by city (across all countries), and a grand total — but *without* the `(country, city)` detail rows. Neither `ROLLUP` nor `CUBE` skips that intersection; `GROUPING SETS` lets you list exactly those four levels.

</details>

---

# Section 5 – Reading Multi-Level NULLs with GROUPING()

## 5.1 The trap

```sql
SELECT
    p.Color,
    COUNT(*) AS Products,
    SUM(ii.TotalPrice) AS Revenue
FROM Product p
JOIN InvoiceItem ii ON ii.ProductID = p.IDProduct
GROUP BY ROLLUP (p.Color);
```

Two rows in this result show `Color = NULL`: one is "products where the color is genuinely unrecorded in the data" (`Product` has 248 rows with `Color IS NULL`), the other is the `ROLLUP` grand-total row. Same value, two different meanings, and no way to tell them apart from the raw result.

## 5.2 The fix: GROUPING()

`GROUPING(col)` returns `1` if `col` was rolled away to produce the current row, and `0` otherwise:

```sql
SELECT
    CASE WHEN GROUPING(p.Color) = 1 THEN 'ALL'
         WHEN p.Color IS NULL       THEN '(no color)'
         ELSE p.Color
    END AS Color,
    GROUPING(p.Color) AS ColorIsGroupingNull,
    COUNT(*) AS Products,
    SUM(ii.TotalPrice) AS Revenue
FROM Product p
JOIN InvoiceItem ii ON ii.ProductID = p.IDProduct
GROUP BY ROLLUP (p.Color)
ORDER BY GROUPING(p.Color), p.Color;
```

Now the report is unambiguous: rows labeled `(no color)` are real data `NULL`s; the row labeled `ALL` is the `ROLLUP` grand total. The extra `ColorIsGroupingNull` column is shown here only to make the point — a production report would just display the labeled `Color`.

`ORDER BY GROUPING(p.Color)` pushes the grand-total row to the bottom, so detail rows come first, then subtotals, then the grand total — the order most reports expect.

## 5.3 Check your understanding

1. Give a scenario where a data `NULL` and a `ROLLUP` `NULL` are impossible to tell apart without `GROUPING()`.
2. What does `GROUPING(col)` return for a detail row where `col` genuinely is `NULL`?
3. Write the `ORDER BY` that puts subtotals below detail rows and the grand total at the bottom.

<details>
<summary>Show answers</summary>

1. `SELECT Color, SUM(...) FROM Product GROUP BY ROLLUP(Color)` where some products really have `Color = NULL`. The result has two rows with `Color = NULL` — one real, one the grand total — and the raw values alone don't distinguish them.
2. `0` — the row is still a genuine detail row, even though the column's value happens to be `NULL`.
3. `ORDER BY GROUPING(col), col` — sort by the grouping flag first (`0` for detail, `1` for rolled-away), then by the actual value. Extends to more columns by repeating the pattern for each one.

</details>

---

# Section 6 – Practice Exercises

## Exercise 1 — ROLLUP: the Adams and Simmons families

Using `ROLLUP`, count the invoices issued to customers named `Adams` or `Simmons`. Show subtotals per `(LastName, FirstName)`, per `LastName`, and a grand total for both families combined. Then answer: how many invoices in total went to the Adams family?

<details>
<summary>Show solution</summary>

```sql
SELECT
    c.LastName,
    c.FirstName,
    COUNT(*) AS Invoices
FROM Customer c
JOIN Invoice i ON i.CustomerID = c.IDCustomer
WHERE c.LastName IN ('Adams', 'Simmons')
GROUP BY ROLLUP (c.LastName, c.FirstName)
ORDER BY c.LastName, c.FirstName;
```

The Adams total is the row where `LastName = 'Adams'` and `FirstName IS NULL` — the `ROLLUP` subtotal for that family.

A common mistake: grouping by `(c.FirstName, c.LastName)` instead of `(c.LastName, c.FirstName)` — this changes which column rolls up first. Forgetting the `WHERE` clause would also give subtotals for every family, not just these two.

</details>

## Exercise 2 — ROLLUP: Rose and Lydia

Using `ROLLUP`, count invoices for customers whose **first name** is `Rose` or `Lydia`. Subtotals per `(FirstName, LastName)`, per `FirstName`, and a grand total. How many invoices went to the Lydias?

<details>
<summary>Show solution</summary>

```sql
SELECT
    c.FirstName,
    c.LastName,
    COUNT(*) AS Invoices
FROM Customer c
JOIN Invoice i ON i.CustomerID = c.IDCustomer
WHERE c.FirstName IN ('Rose', 'Lydia')
GROUP BY ROLLUP (c.FirstName, c.LastName)
ORDER BY c.FirstName, c.LastName;
```

The Lydia total is the row where `FirstName = 'Lydia'` and `LastName IS NULL`.

Compare with Exercise 1: there, `LastName` was the outer (leftmost) level; here, `FirstName` is. Order matters in `ROLLUP` — whichever column comes first is the one that gets a "grand total for that value" subtotal.

</details>

## Exercise 3 — CUBE: salespeople whose surname starts with 'A'

Using `CUBE`, count invoices for every salesperson whose `LastName` starts with `'A'`. Include per `(FirstName, LastName)`, per `FirstName`, per `LastName`, and a grand total.

<details>
<summary>Show solution</summary>

```sql
SELECT
    s.FirstName,
    s.LastName,
    COUNT(*) AS Invoices
FROM Salesman s
JOIN Invoice i ON i.SalesmanID = s.IDSalesman
WHERE s.LastName LIKE 'A%'
GROUP BY CUBE (s.FirstName, s.LastName)
ORDER BY s.LastName, s.FirstName;
```

Compare with what `ROLLUP` would give for the same query: the extra rows, where `FirstName` is `NULL` and `LastName` is filled in, are "per-surname across all first names" subtotals. `ROLLUP` would not produce those, because `LastName` is the second column in the list; `CUBE` gets them because it explores every combination.

</details>

## Exercise 4 — GROUPING SETS: revenue by name, by color, grand total

One query: revenue by product name, revenue by product color, and a grand total. Do **not** include the `(Name, Color)` detail rows. Exclude products with a `NULL` color.

<details>
<summary>Show solution</summary>

```sql
SELECT
    p.Name,
    p.Color,
    SUM(ii.TotalPrice) AS Revenue
FROM Product p
JOIN InvoiceItem ii ON ii.ProductID = p.IDProduct
WHERE p.Color IS NOT NULL
GROUP BY GROUPING SETS
(
    (p.Name),
    (p.Color),
    ()
)
ORDER BY p.Color, p.Name;
```

`(p.Name, p.Color)` is deliberately absent from the grouping sets list. Neither `ROLLUP` nor `CUBE` could produce this shape without also giving you the detail rows — `GROUPING SETS` is the only tool that cleanly cuts them out.

</details>

## Exercise 5 — Revenue by color, two ways

One query: revenue by product color, plus a grand total, excluding `NULL` colors. Solve it two ways — `ROLLUP` and `GROUPING SETS` — and confirm the results match.

<details>
<summary>Show solution</summary>

```sql
-- (a) ROLLUP
SELECT
    p.Color,
    SUM(ii.TotalPrice) AS Revenue
FROM Product p
JOIN InvoiceItem ii ON ii.ProductID = p.IDProduct
WHERE p.Color IS NOT NULL
GROUP BY ROLLUP (p.Color)
ORDER BY p.Color;

-- (b) GROUPING SETS
SELECT
    p.Color,
    SUM(ii.TotalPrice) AS Revenue
FROM Product p
JOIN InvoiceItem ii ON ii.ProductID = p.IDProduct
WHERE p.Color IS NOT NULL
GROUP BY GROUPING SETS ((p.Color), ())
ORDER BY p.Color;
```

Same result either way. When you only need one column plus a grand total, `ROLLUP` is the shortest to write. When you need more columns or want to skip levels, `GROUPING SETS` wins.

</details>

## Exercise 6 — Revenue by country and city, labeled

Report revenue by `(Country, City)`, then by `Country`, then a grand total — the classic `ROLLUP` shape. Use `GROUPING()` to label the subtotal rows cleanly.

<details>
<summary>Show solution</summary>

```sql
SELECT
    CASE WHEN GROUPING(s.Name) = 1 THEN 'ALL COUNTRIES' ELSE s.Name END AS Country,
    CASE WHEN GROUPING(c.Name) = 1 THEN 'ALL CITIES'    ELSE c.Name END AS City,
    SUM(ii.TotalPrice) AS Revenue
FROM InvoiceItem ii
JOIN Invoice i ON i.IDInvoice = ii.InvoiceID
JOIN Customer cu ON cu.IDCustomer = i.CustomerID
JOIN City c ON c.IDCity = cu.CityID
JOIN State s ON s.IDState = c.StateID
GROUP BY ROLLUP (s.Name, c.Name)
ORDER BY GROUPING(s.Name), s.Name, GROUPING(c.Name), c.Name;
```

This is the kind of query that ends up wrapped in a stored procedure and called directly by a dashboard — with the `GROUPING()` labels in place, the result is renderable with no post-processing needed in the application.

</details>

---

# Section 7 – Common Mistakes and Final Review

## 7.1 Common mistakes

| Mistake | Why it matters | Better approach |
|---|---|---|
| Treating a `ROLLUP` `NULL` as always meaning "no data" | It can also mean "this column was rolled away" | Use `GROUPING(col)` to tell the two apart |
| Reaching for `CUBE` by default | Grows as `2^n`; most reports only need a hierarchy | Start with `ROLLUP`; escalate only if you need sideways combinations |
| Assuming `GROUPING SETS` always needs `ROLLUP` or `CUBE` first | `GROUPING SETS` is the general form, not an extension | List exactly the levels you want directly |
| Getting `ROLLUP` column order backwards | The order determines which column "rolls up" first | Put the most detailed column on the left |
| Forgetting `WHERE` before grouping sensitive columns | Subtotals then include rows you didn't mean to report on | Filter first, then apply `ROLLUP`/`CUBE`/`GROUPING SETS` |

## 7.2 Final questions

1. What is the one-sentence difference between `ROLLUP` and `CUBE`?
2. How many grouping levels does `GROUPING SETS ((a,b), (a), ())` have, and what are they?
3. Why can't a plain `WHERE Color IS NOT NULL` filter out a `ROLLUP` grand-total row?
4. What is the practical rule of thumb for choosing between the three tools?

<details>
<summary>Show answers</summary>

1. `ROLLUP` produces subtotals up a hierarchy; `CUBE` produces every possible combination of the grouping columns.
2. Three: `(a, b)`, `(a)`, `()` — exactly the levels listed, no more, no fewer.
3. The grand-total row's `Color` is `NULL` because the column was rolled away, not because of a `WHERE` filter applied before grouping — `WHERE` runs before `GROUP BY`, so it cannot see or remove a row that `GROUP BY ROLLUP` creates afterward.
4. `ROLLUP` for subtotals up a real hierarchy (most reports); `CUBE` only when you genuinely need every combination; `GROUPING SETS` when you want an exact, explicit list that neither of the other two can produce alone.

</details>

## 7.3 Key takeaways

- **`GROUP BY ()` is the grand-total idiom.** Identical to a bare aggregate except on an empty table.
- **`ROLLUP(a, b, c)` walks up the hierarchy.** Four grouping levels for three columns.
- **`CUBE(a, b, c)` explores every combination.** `2^n` levels — reach for it only when you need them all.
- **`GROUPING SETS` is the underlying primitive.** Every `ROLLUP` and `CUBE` can be rewritten as one; use it directly when you want exact control.
- **`NULL` in a grouped result has two meanings.** Use `GROUPING(col)` to tell "rolled away" apart from "really `NULL`", and a `CASE WHEN GROUPING(col) = 1 THEN 'ALL' ELSE col END` to make the report readable.

Back to the opening question: a spreadsheet with subtotals for every category and a grand total at the bottom. That shape is exactly what `ROLLUP`, `CUBE`, and `GROUPING SETS` produce — natively, in one query, with no `UNION` in sight.

**Looking ahead:** `GROUP BY` and its extensions all *collapse* rows — every group becomes one output row. The next lab covers the opposite tool: aggregating across a set of rows *without* collapsing them.

---

# Additional Reading

The following topic extends the lab. It is not required for the main exercises.

## A. GROUPING_ID()

`GROUPING(col)` reports whether one column was rolled away. `GROUPING_ID(col1, col2, ...)` packs the same information for *several* columns into a single integer bitmask — useful for filtering a multi-column `ROLLUP`/`CUBE` result down to one specific grouping level (e.g. "only the rows where exactly columns 1 and 3 were rolled away") without writing a `GROUPING()` call per column. See [GROUPING_ID (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/grouping-id-transact-sql).

## B. References

- [GROUP BY (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-group-by-transact-sql)
- [ROLLUP, CUBE, GROUPING SETS — Using GROUP BY with ROLLUP, CUBE, and GROUPING SETS](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-group-by-transact-sql#using-group-by-with-rollup-cube-or-grouping-sets)
- [GROUPING (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/grouping-transact-sql)
- [GROUPING_ID (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/grouping-id-transact-sql)
