# Lab 11 – Advanced Grouping and Window Functions

**Database:** `AdventureWorksENG`

Every lab so far has been about building a database — tables, procedures, indexes, transactions. The database is now built. It holds data. The question changes: not "how do I put data in", but "how do I ask hard questions of it"?

This lab answers two kinds of questions:

- **Part I – Advanced grouping.** A report with subtotals for every category and a grand total at the bottom. Writing that in plain SQL usually means several queries glued together with `UNION`. Three extensions to `GROUP BY` produce that shape in a single query.
- **Part II – Window functions.** Every product **and** its category's total on the same row, a ranking, or a running total that updates on every row. `GROUP BY` cannot do this, because it collapses the rows. A window function aggregates **without collapsing them**.

> [!IMPORTANT]
> **Core idea:** `GROUP BY` collapses rows into groups. `ROLLUP`, `CUBE`, and `GROUPING SETS` run several `GROUP BY`s at once and stack the results. A window function, `OVER (PARTITION BY ... ORDER BY ...)`, keeps every row and adds a column that summarizes the rows around it.

---

## Learning objectives

After completing this lab, you should be able to:

- explain the difference between a bare aggregate and `GROUP BY ()`, and why they only disagree on an empty input;
- use `ROLLUP` to produce subtotals up a hierarchy in one query;
- use `CUBE` to produce every combination of subtotals, and explain why it grows as `2^n`;
- use `GROUPING SETS` to choose exactly which grouping levels appear, including levels neither `ROLLUP` nor `CUBE` can produce alone;
- rewrite any `ROLLUP` or `CUBE` as an equivalent `GROUPING SETS` list;
- use `GROUPING()` to tell a "this column was rolled away" `NULL` apart from a real data `NULL`, and build a readable report label from it.
- describe the three parts of a window function's `OVER` clause, and which are mandatory for which function family;
- use `ROW_NUMBER`, `RANK`, `DENSE_RANK`, and `NTILE`, and explain how they treat ties differently;
- use `SUM`/`AVG`/`COUNT`/`MIN`/`MAX` with `OVER`, and explain why adding `ORDER BY` turns a constant into a running total;
- use `LAG` and `LEAD` to compare a row to its neighbors in an ordered partition;
- explain why `LAST_VALUE` needs an explicit frame, and write that frame correctly;
- choose between `ROWS` and `RANGE` framing, and write the four most common frame idioms.

---

# Part I – Advanced Grouping

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

```mermaid
flowchart TB
    subgraph R["ROLLUP(a, b, c) — a line"]
        direction TB
        R1["(a, b, c)"] --> R2["(a, b)"] --> R3["(a)"] --> R4["()"]
    end
    subgraph C["CUBE(a, b, c) — a lattice"]
        direction TB
        C1["(a, b, c)"] --> C2["(a, b)"] & C3["(a, c)"] & C4["(b, c)"]
        C2 --> C5["(a)"]
        C2 --> C6["(b)"]
        C3 --> C5
        C3 --> C7["(c)"]
        C4 --> C6
        C4 --> C7
        C5 --> C8["()"]
        C6 --> C8
        C7 --> C8
    end
```

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

# Part II – Window Functions

Part I produced subtotals and grand totals in one query — but every one of `ROLLUP`, `CUBE`, and `GROUPING SETS` *collapses* rows. Each group becomes one output row; the detail is gone. That's fine for a report. It's no help when you want to see every product **and** its category's total on the same row, or rank rows without losing the rows themselves, or compute a running total that updates on every row.

The tool built for exactly that is the window function. It aggregates across a set of rows **without collapsing them**.

# Section 6 – The Anatomy of a Window Function

## 6.1 The killer comparison

```sql
-- Grouped: one row per color, detail gone
SELECT Color, SUM(PriceWithoutVAT) AS ColorTotal
FROM Product
GROUP BY Color;
```

```sql
-- Windowed: every product, plus its color's total
SELECT Name, Color, PriceWithoutVAT,
       SUM(PriceWithoutVAT) OVER (PARTITION BY Color) AS ColorTotal
FROM Product;
```

Same aggregate, same partitioning by color. `GROUP BY` loses the individual rows. The window function keeps every row **and** adds the aggregate as an extra column, living on every row of the partition it applies to. Everything in this lab is a variation on that one pattern.

## 6.2 The shape of every window function

```
funcName(<args>)
OVER
(
    [ PARTITION BY <cols> ]
    [ ORDER BY <cols>
        [ frame ] ]
)
```

A function, the keyword `OVER`, and up to three optional pieces inside the parentheses: `PARTITION BY` slices the rows into independent strips; `ORDER BY` orders the rows within each strip; a frame (Section 10) defines a sliding window inside the ordered strip.

Which pieces you need depends on the function:

| Function family | `PARTITION BY` | `ORDER BY` | Frame |
|---|:---:|:---:|:---:|
| Ranking | optional | **mandatory** | n/a |
| Aggregate | optional | optional | optional |
| Analytical | optional | **mandatory** | optional |

A ranking function without `ORDER BY` makes no sense — ranked by what? Same for `LAG`/`LEAD`/`FIRST_VALUE` — "previous" and "first" are meaningless without an order. An aggregate *without* `ORDER BY` means "across the whole partition, same value on every row"; *with* `ORDER BY`, it means "up to and including this row" (Section 8).

## 6.3 Where it runs in the query

```mermaid
flowchart LR
    A["FROM / JOIN\nraw rows come in"] --> B["WHERE\nfilter rows"]
    B --> C["GROUP BY\ncollapse into groups\n(loses rows)"]
    C --> D["HAVING\nfilter the groups"]
    D --> E["SELECT\nwindow functions run here"]
    E --> F["ORDER BY\norder the final result"]
```

If a query has a `GROUP BY`, the window function sees the **aggregated** rows, not the original table — usually not what you want, since the whole point of a window function is to keep individual rows. Most window-function queries have no `GROUP BY` at all.

## 6.4 Check your understanding

1. What are the three optional pieces of an `OVER` clause?
2. Which piece is mandatory for a ranking function?
3. If a query has a `GROUP BY`, what rows does a window function in that query's `SELECT` see?

<details>
<summary>Show answers</summary>

1. `PARTITION BY` (slice into strips), `ORDER BY` (order within each strip), and a frame (a sliding window inside the ordered strip).
2. `ORDER BY`. `PARTITION BY` is optional.
3. The aggregated rows produced by `GROUP BY`, not the original rows — usually not what you want, since window functions exist to preserve individual rows.

</details>

---

# Section 7 – Ranking Functions

## 7.1 The four functions

```
ROW_NUMBER()    unique row number per partition (1, 2, 3, 4, ...)
RANK()          rank; ties share; then skip     (1, 2, 2, 4)
DENSE_RANK()    rank; ties share; no skip        (1, 2, 2, 3)
NTILE(n)        bucket rows into n groups
```

`ROW_NUMBER` breaks every tie arbitrarily — every row gets a unique number. `RANK` gives tied rows the same number, then skips ahead (two 2nd-place rows means the next is 4th). `DENSE_RANK` also shares the rank on a tie, but never skips. `NTILE(n)` buckets the rows into `n` roughly-equal groups — quartiles, deciles, percentiles.

## 7.2 Demo: all four side by side

```sql
SELECT
    p.Name,
    p.Color,
    p.PriceWithoutVAT,
    ROW_NUMBER() OVER (ORDER BY p.PriceWithoutVAT DESC) AS RN,
    RANK()       OVER (ORDER BY p.PriceWithoutVAT DESC) AS RK,
    DENSE_RANK() OVER (ORDER BY p.PriceWithoutVAT DESC) AS DR,
    NTILE(4)     OVER (ORDER BY p.PriceWithoutVAT DESC) AS Quartile
FROM Product p
WHERE p.PriceWithoutVAT > 0
ORDER BY p.PriceWithoutVAT DESC;
```

Look at the tied prices (there are several): `ROW_NUMBER` gives them consecutive numbers; `RANK` gives them the same number, then skips; `DENSE_RANK` gives them the same number, no skip; `NTILE(4)` assigns each row to one of four price-based quartiles.

## 7.3 Restarting per partition

```sql
SELECT
    p.Name,
    p.Color,
    p.PriceWithoutVAT,
    ROW_NUMBER() OVER (PARTITION BY p.Color
                       ORDER BY p.PriceWithoutVAT DESC) AS RankInColor
FROM Product p
WHERE p.Color IS NOT NULL
ORDER BY p.Color, p.PriceWithoutVAT DESC;
```

Adding `PARTITION BY p.Color` makes `RankInColor` restart at `1` for every new color — "the most expensive Crna product", "the most expensive Plava product", all in one query. The same pattern applies to `RANK`, `DENSE_RANK`, and `NTILE`.

## 7.4 When to use each

| Function | Use for |
|---|---|
| `ROW_NUMBER` | Pagination, de-duplication ("give me the first one") |
| `RANK` | Classical leaderboards |
| `DENSE_RANK` | Grouped-by-value listings ("top 5 distinct prices") |
| `NTILE(n)` | Percentiles, deciles, cohort analysis |

## 7.5 Check your understanding

1. What does `RANK` do differently from `ROW_NUMBER`?
2. What does `DENSE_RANK` do differently from `RANK`?
3. You want the top 3 rows per partition, and you don't want ties to give you more or fewer than 3. Which function do you use?

<details>
<summary>Show answers</summary>

1. `ROW_NUMBER` gives every row a unique number, breaking ties arbitrarily. `RANK` gives tied rows the same number and then skips the following numbers (`1, 2, 2, 4`).
2. `DENSE_RANK` also shares a rank across ties, but does not skip — the next distinct value gets the next integer (`1, 2, 2, 3`).
3. `ROW_NUMBER`, filtered to `<= 3` in an outer query — it guarantees exactly 3 rows per partition regardless of ties. `RANK` could return more or fewer than 3 if there's a tie at the boundary.

</details>

---

# Section 8 – Aggregate Window Functions and Running Totals

## 8.1 Two shapes

```
SUM(col) OVER (PARTITION BY x)              -- constant over each partition
SUM(col) OVER (PARTITION BY x ORDER BY y)   -- running total, resets per partition
```

The same aggregate functions you already know — `SUM`, `AVG`, `COUNT`, `MIN`, `MAX` — become window functions with `OVER`. Without `ORDER BY`, the aggregate is computed across the whole partition and every row sees the same value. With `ORDER BY`, it becomes a running total: each row sees the aggregate of every row up to and including itself, in the given order.

## 8.2 Demo: a grand total on every row

```sql
SELECT
    p.Name,
    p.PriceWithoutVAT,
    SUM(p.PriceWithoutVAT) OVER () AS TotalOfAllPrices
FROM Product p
WHERE p.PriceWithoutVAT > 0;
```

An empty `OVER ()` means no partition and no order — the window is the entire result set, so the same total appears on every row.

## 8.3 Demo: running total per year

```sql
SELECT
    i.InvoiceDate,
    ii.TotalPrice,
    SUM(ii.TotalPrice) OVER
    (
        PARTITION BY YEAR(i.InvoiceDate)
        ORDER BY i.InvoiceDate, i.IDInvoice
    ) AS RunningTotalThisYear
FROM InvoiceItem ii
JOIN Invoice i ON i.IDInvoice = ii.InvoiceID
ORDER BY i.InvoiceDate, i.IDInvoice;
```

The running total climbs as the rows go by in date order, then resets to zero on January 1st of the next year — because the partition is `YEAR(InvoiceDate)`, and a new year is a new partition. One query; no cursor needed for a running total ever again.

## 8.4 Why ORDER BY inside OVER produces a running total

The default frame when `ORDER BY` is present is:

```
RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

— "aggregate every row from the start of the partition up to and including this one." That is the running-total definition. Section 10 covers frames directly; for now, this explains why "aggregate + `ORDER BY`" behaves the way it does.

## 8.5 Check your understanding

1. What is the difference between `SUM(col) OVER ()` and `SUM(col) OVER (ORDER BY x)`?
2. What does `PARTITION BY YEAR(date) ORDER BY date` give you inside an aggregate window?
3. Why is a running total called "running"?

<details>
<summary>Show answers</summary>

1. Without `ORDER BY`, the aggregate is computed across the whole window — every row sees the same value. With `ORDER BY`, it's computed from the start of the partition up to and including each row — a running total.
2. A running total per calendar year, resetting every January 1st; each row shows the year-to-date total as of its own date.
3. The value grows monotonically as you move down the ordered rows — each row is a snapshot of the total "so far", the same shape as adding numbers on a calculator without pressing equals.

</details>

---

# Section 9 – Analytical Functions: LAG, LEAD, FIRST_VALUE, LAST_VALUE

## 9.1 The four functions

```
FIRST_VALUE(col)   value of col in the FIRST row of the window
LAST_VALUE(col)    value of col in the LAST row of the window    *
LAG(col, n)        value of col from n rows BEFORE the current row
LEAD(col, n)       value of col from n rows AFTER the current row

ORDER BY       mandatory — "first"/"last"/"previous"/"next" need an order
PARTITION BY   optional — restarts per partition

* LAST_VALUE has a default-frame trap. See 9.4.
```

`LAG` and `LEAD` are the two you will reach for most often: `LAG(col, 1)` is the value of `col` in the previous row; `LEAD(col, 1)` is the value in the next row.

## 9.2 Demo: LAG for a time-series diff

```sql
SELECT
    p.Name,
    p.PriceWithoutVAT,
    LAG(p.PriceWithoutVAT, 1) OVER (ORDER BY p.PriceWithoutVAT) AS PrevPrice,
    p.PriceWithoutVAT
      - LAG(p.PriceWithoutVAT, 1) OVER (ORDER BY p.PriceWithoutVAT) AS DeltaFromPrev
FROM Product p
WHERE p.PriceWithoutVAT > 0
ORDER BY p.PriceWithoutVAT;
```

`PrevPrice` is the previous product's price on every row; the first row's `PrevPrice` is `NULL`, because nothing precedes it — that's `LAG`'s default at the edge of a partition. `DeltaFromPrev` is how much more this product costs than the one before it. "Compare each row to the one before it" is one of the most common analytical patterns in real code.

## 9.3 LEAD: the mirror

```sql
SELECT
    p.Name,
    p.PriceWithoutVAT,
    LEAD(p.PriceWithoutVAT, 1) OVER (ORDER BY p.PriceWithoutVAT) AS NextPrice
FROM Product p
WHERE p.PriceWithoutVAT > 0
ORDER BY p.PriceWithoutVAT;
```

Same idea, mirrored: the last row's `NextPrice` is `NULL`, since nothing follows it. Common use: "when does the next event happen after this one" — timestamps, schedules, version history.

## 9.4 FIRST_VALUE and the LAST_VALUE trap

```sql
SELECT
    p.Name,
    p.PriceWithoutVAT,
    FIRST_VALUE(p.Name) OVER (ORDER BY p.PriceWithoutVAT) AS CheapestProduct
FROM Product p
WHERE p.PriceWithoutVAT > 0
ORDER BY p.PriceWithoutVAT;
```

Every row shows the name of the cheapest product — the first row of the ordered window. `LAST_VALUE` looks symmetric, but is not, with default settings:

```sql
SELECT
    p.Name, p.PriceWithoutVAT,
    LAST_VALUE(p.Name) OVER (ORDER BY p.PriceWithoutVAT) AS LastValueDefault
FROM Product p
WHERE p.PriceWithoutVAT > 0
ORDER BY p.PriceWithoutVAT;
```

`LastValueDefault` on every row turns out to equal that row's own `Name`. That is not "the last value in the partition" — it is "the last value seen so far". The default frame when `ORDER BY` is present is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` (Section 8.4), so "the last row of the window" is the current row itself.

The fix is an explicit frame covering the whole partition:

```sql
SELECT
    p.Name, p.PriceWithoutVAT,
    LAST_VALUE(p.Name) OVER
    (
        ORDER BY p.PriceWithoutVAT
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS ActuallyMostExpensive
FROM Product p
WHERE p.PriceWithoutVAT > 0
ORDER BY p.PriceWithoutVAT;
```

> [!IMPORTANT]
> Whenever you use `LAST_VALUE`, add the explicit `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` frame. Always.

## 9.5 Check your understanding

1. What does `LAG(col, 1)` return in the first row of a partition?
2. Give one real-world use for `LEAD`.
3. Why does `LAST_VALUE` need an explicit frame to behave as its name suggests?

<details>
<summary>Show answers</summary>

1. `NULL` — there is no previous row to reach back to. A third argument overrides this: `LAG(col, 1, 0)` returns `0` instead of `NULL` at the edge.
2. "When does the next event happen after this one" — time until the next login, order, or state change; also gap detection, by filtering on an abnormally large difference between a row and its `LEAD`.
3. The default frame with `ORDER BY` is `RANGE UNBOUNDED PRECEDING TO CURRENT ROW`, so "the last value in the window" is "the last value seen so far" — the current row. The fix is `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`.

</details>

---

# Section 10 – Frames

## 10.1 The third piece of OVER

A frame is a sliding window inside the ordered partition, used only by aggregate and analytical functions — ranking functions don't use frames.

```
ROWS  BETWEEN <start> AND <end>       -- row-count based
RANGE BETWEEN <start> AND <end>       -- value based on the ORDER BY column

Endpoints:
    UNBOUNDED PRECEDING     from the start of the partition
    N PRECEDING             N rows/values before the current one
    CURRENT ROW             this row
    N FOLLOWING             N rows/values ahead
    UNBOUNDED FOLLOWING     to the end of the partition
```

`ROWS` counts physical rows — predictable. `RANGE` uses the values in the `ORDER BY` column, so rows that tie on that value are all included together, which can surprise you. Rule of thumb: use `ROWS` unless you specifically need value-based semantics.

## 10.2 Four idioms worth memorizing

```
"The whole partition":
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING

"Moving window of size N+1 ending on this row":
    ROWS BETWEEN N PRECEDING AND CURRENT ROW

"Everything from here forward":
    ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING

"Everything up to but not including this row":
    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
```

Together these four cover most of what you'll write in real code.

## 10.3 Demo: a moving 3-item average

```sql
SELECT
    p.Name,
    p.PriceWithoutVAT,
    AVG(p.PriceWithoutVAT) OVER
    (
        ORDER BY p.PriceWithoutVAT
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS Moving3Avg
FROM Product p
WHERE p.PriceWithoutVAT > 0
ORDER BY p.PriceWithoutVAT;
```

The first row's window has just 1 row (nothing precedes it), so the average equals that row's own price. The second row's window has 2 rows; the third row onward, 3. This is the standard shape for smoothing a time series with a moving average.

## 10.4 The default frame, revisited

Recall from Section 8.4: when `ORDER BY` is present inside `OVER` with no explicit frame, the default is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. That default is why "aggregate + `ORDER BY`" gives a running total (Section 8), and why `LAST_VALUE` without an explicit frame looks broken (Section 9.4) — the frame ends at the current row, so "the last value" is the current row. Always be explicit when using `LAST_VALUE`.

## 10.5 Check your understanding

1. What is the difference between `ROWS` and `RANGE`?
2. Write the frame that means "the whole partition".
3. How do you turn a running average into a fixed-size moving average over the current row plus the previous four?

<details>
<summary>Show answers</summary>

1. `ROWS` counts physical rows — `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` is exactly 3 rows. `RANGE` uses the `ORDER BY` column's values, so tied rows are all included together, which can surprise you.
2. `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`.
3. Specify the frame explicitly: `AVG(col) OVER (ORDER BY x ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)` — a moving 5-item average (the current row plus 4 preceding).

</details>

---

# Section 11 – Common Mistakes and Final Review

## 11.1 Common mistakes

| Mistake | Why it matters | Better approach |
|---|---|---|
| Treating a `ROLLUP` `NULL` as always meaning "no data" | It can also mean "this column was rolled away" | Use `GROUPING(col)` to tell the two apart |
| Reaching for `CUBE` by default | Grows as `2^n`; most reports only need a hierarchy | Start with `ROLLUP`; escalate only if you need sideways combinations |
| Assuming `GROUPING SETS` always needs `ROLLUP` or `CUBE` first | `GROUPING SETS` is the general form, not an extension | List exactly the levels you want directly |
| Getting `ROLLUP` column order backwards | The order determines which column "rolls up" first | Put the most detailed column on the left |
| Forgetting `WHERE` before grouping sensitive columns | Subtotals then include rows you didn't mean to report on | Filter first, then apply `ROLLUP`/`CUBE`/`GROUPING SETS` |
| Using `LAST_VALUE` without an explicit frame | Default frame ends at the current row — you get the row itself, not the true last value | Always add `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` |
| Forgetting `ORDER BY` on a ranking or analytical function | The function has nothing to rank or reach relative to — syntax error or meaningless result | Treat `ORDER BY` as mandatory for ranking and analytical functions |
| Mixing a `GROUP BY` into a window-function query without meaning to | The window function sees aggregated rows, not the originals | Drop the `GROUP BY` unless you specifically want to window over aggregated groups |
| Expecting `RANK` to give exactly `N` rows per partition when filtering top-`N` | Ties can produce more or fewer than `N` | Use `ROW_NUMBER` when you need exactly `N`, `RANK`/`DENSE_RANK` when ties should matter |
| Assuming `RANGE` and `ROWS` always behave the same | They agree only when there are no ties on the `ORDER BY` column | Default to `ROWS` unless you have a specific reason for value-based framing |

## 11.2 Final questions

1. What does a window function do that `GROUP BY` — including `ROLLUP`, `CUBE`, and `GROUPING SETS` — cannot?
2. You need (a) a revenue report with a subtotal per country and a grand total, and (b) a list of every product with its color's total price on the same row. Which tool do you use for each?
3. Why can't a plain `WHERE Color IS NOT NULL` filter out a `ROLLUP` grand-total row?
4. What is the practical rule of thumb for choosing between `ROLLUP`, `CUBE`, and `GROUPING SETS`?
5. Name the three families of window functions.

<details>
<summary>Show answers</summary>

1. It aggregates across a set of rows without collapsing those rows — every input row survives, with an extra column summarizing its neighborhood. `GROUP BY` and its extensions always turn each group into one output row.
2. (a) `GROUP BY ROLLUP` (or `GROUPING SETS`) — the report needs one row per country plus a grand total, so collapsing is exactly right. (b) A window function, `SUM(...) OVER (PARTITION BY Color)` — every product must stay in the result.
3. The grand-total row's `Color` is `NULL` because the column was rolled away, not because of a `WHERE` filter applied before grouping — `WHERE` runs before `GROUP BY`, so it cannot see or remove a row that `GROUP BY ROLLUP` creates afterward.
4. `ROLLUP` for subtotals up a real hierarchy (most reports); `CUBE` only when you genuinely need every combination; `GROUPING SETS` when you want an exact, explicit list that neither of the other two can produce alone.
5. Ranking, aggregate, analytical.

</details>

---

# Key takeaways

- **`GROUP BY ()` is the grand-total idiom.** Identical to a bare aggregate except on an empty table.
- **`ROLLUP(a, b, c)` walks up the hierarchy.** Four grouping levels for three columns.
- **`CUBE(a, b, c)` explores every combination.** `2^n` levels — reach for it only when you need them all.
- **`GROUPING SETS` is the underlying primitive.** Every `ROLLUP` and `CUBE` can be rewritten as one; use it directly when you want exact control.
- **`NULL` in a grouped result has two meanings.** Use `GROUPING(col)` to tell "rolled away" apart from "really `NULL`", and a `CASE WHEN GROUPING(col) = 1 THEN 'ALL' ELSE col END` to make the report readable.
- **Window functions aggregate without collapsing.** Every input row survives; each gets one extra column summarizing its neighborhood.
- **The shape is always `func(...) OVER (PARTITION BY ... ORDER BY ... frame)`.** Three optional pieces, each with a specific job.
- **Three families.** Ranking (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`), aggregate (`SUM`/`AVG`/`COUNT`/`MIN`/`MAX` with `OVER`), analytical (`FIRST_VALUE`, `LAST_VALUE`, `LAG`, `LEAD`).
- **Aggregate + `ORDER BY` inside `OVER` = a running total**, reset at each partition boundary.
- **`LAG`/`LEAD` reach back and forward** — the two most-used analytical functions in real code.
- **`LAST_VALUE` needs an explicit frame.** Always write `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`.

Back to the opening questions: a report with subtotals and a grand total is what `ROLLUP`, `CUBE`, and `GROUPING SETS` produce — natively, in one query, with no `UNION` in sight. A row that must keep its detail **and** see an aggregate is what a window function produces: `GROUP BY Color` loses every row but the aggregate, while `SUM(...) OVER (PARTITION BY Color)` keeps every row and adds it.

**Looking ahead:** Between advanced grouping and window functions, you now have the two tools that cover almost every analytical query written outside specialized BI tools.

---

## Additional practice

Exercises for this lab are in [Advanced Grouping and Window Function Exercises](../exercises/lab11-grouping-and-window-functions.md).

---

# Additional Reading

The following topics extend the lab. They are not required for the exercises.

## A. GROUPING_ID()

`GROUPING(col)` reports whether one column was rolled away. `GROUPING_ID(col1, col2, ...)` packs the same information for *several* columns into a single integer bitmask — useful for filtering a multi-column `ROLLUP`/`CUBE` result down to one specific grouping level (e.g. "only the rows where exactly columns 1 and 3 were rolled away") without writing a `GROUPING()` call per column.

## B. Statistical Window Functions

`PERCENT_RANK()`, `CUME_DIST()`, and `PERCENTILE_CONT()`/`PERCENTILE_DISC()` compute relative standing and percentiles directly as window or aggregate functions — useful once `NTILE` stops being precise enough.
