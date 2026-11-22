# Lab 11 – Advanced Grouping and Window Function Exercises

**Database:** `AdventureWorksENG`

These exercises build on [Lab 11 – Advanced Grouping and Window Functions](../labs/lab11-grouping-and-window-functions.md) and use `AdventureWorksENG`. They are grouped like the lab: Part A practises `ROLLUP`, `CUBE`, `GROUPING SETS`, and `GROUPING()`; Parts B–D practise ranking functions, aggregate window functions with running totals and frames, and the analytical functions `LAG`, `LEAD`, and `FIRST_VALUE`. The last exercise combines several of them.

All exercises are plain `SELECT` statements, except Exercise 19, which creates a small table.

```sql
USE AdventureWorksENG;
GO
```

---

# Part A – Advanced grouping

## Exercise 1 — ROLLUP: the Adams and Simmons families [BEGINNER]

Using `ROLLUP`, count the invoices issued to customers named `Adams` or `Simmons`. Show subtotals per `(LastName, FirstName)`, per `LastName`, and a grand total for both families combined. Then answer: how many invoices in total went to the Adams family?

<details>
<summary>Hint</summary>

Join `Customer` to `Invoice`, filter the two last names, and group by `ROLLUP (LastName, FirstName)`. The family subtotal is the row where `FirstName` is `NULL`.

</details>

<details>
<summary>Solution</summary>

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

Expected result: the first row is the grand total, `314` invoices for both families. The Adams family has `134` invoices (the row `Adams` / `NULL`).

</details>

---

## Exercise 2 — ROLLUP: Rose and Lydia [BEGINNER]

Using `ROLLUP`, count invoices for customers whose **first name** is `Rose` or `Lydia`. Subtotals per `(FirstName, LastName)`, per `FirstName`, and a grand total. How many invoices went to the Lydias?

<details>
<summary>Hint</summary>

This time `FirstName` is the outer level, so it must come first in the `ROLLUP` list.

</details>

<details>
<summary>Solution</summary>

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

Expected result: `39` invoices in total, `29` of them for customers named Lydia (the row `Lydia` / `NULL`).

</details>

---

## Exercise 3 — CUBE: salespeople whose surname starts with 'A' [INTERMEDIATE]

Using `CUBE`, count invoices for every salesperson whose `LastName` starts with `'A'`. Include per `(FirstName, LastName)`, per `FirstName`, per `LastName`, and a grand total.

<details>
<summary>Hint</summary>

`CUBE (FirstName, LastName)` returns every combination: both columns, each column alone, and the grand total.

</details>

<details>
<summary>Solution</summary>

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

Expected result: 10 rows for three salespeople — Santi Ajello (`450`), Romano Arnolfi (`109`), and Marino Alessi (`48`) — with `607` invoices in total. Each salesperson appears in three rows: by first and last name together, by first name alone, and by last name alone.

</details>

---

## Exercise 4 — GROUPING SETS: revenue by name, by color, grand total [INTERMEDIATE]

One query: revenue by product name, revenue by product color, and a grand total. Do **not** include the `(Name, Color)` detail rows. Exclude products with a `NULL` color.

<details>
<summary>Hint</summary>

List exactly the three levels you want inside `GROUPING SETS`; the empty set `()` is the grand total.

</details>

<details>
<summary>Solution</summary>

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

Expected result: one row per product name, one row per color, and a grand total of about `108,747,062.49`. On name rows the color is `NULL`, on color rows the name is `NULL`.

</details>

---

## Exercise 5 — Revenue by color, two ways [INTERMEDIATE]

One query: revenue by product color, plus a grand total, excluding `NULL` colors. Solve it two ways — `ROLLUP` and `GROUPING SETS` — and confirm the results match.

<details>
<summary>Hint</summary>

`ROLLUP (Color)` is the same as `GROUPING SETS ((Color), ())`.

</details>

<details>
<summary>Solution</summary>

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

Expected result: both queries return the same 9 rows — 8 colors and a grand total of about `108,747,062.49` (the `NULL` row). `Crna` has the highest revenue, about `38.2` million.

</details>

---

## Exercise 6 — Revenue by country and city, labeled [ADVANCED]

Report revenue by `(Country, City)`, then by `Country`, then a grand total — the classic `ROLLUP` shape. Use `GROUPING()` to label the subtotal rows cleanly.

<details>
<summary>Hint</summary>

`GROUPING(col)` returns `1` on rows where that column was rolled away. Use it in a `CASE` for the label and in `ORDER BY` to place subtotals after their details. In this database, a country is a row of `State`.

</details>

<details>
<summary>Solution</summary>

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

Expected result: 16 rows — the cities of Croatia, Germany, and Italy, an `ALL CITIES` row after each country, and `ALL COUNTRIES` / `ALL CITIES` at the end. Croatia has the highest revenue, about `45.7` million.

</details>

---

## Exercise 7 — One report for the sales meeting [INTERMEDIATE]

For the sales meeting, management wants one table of revenue (`SUM(InvoiceItem.TotalPrice)`) by product category and invoice year. In the same table they also want:

- each category's total for all years;
- each year's total for all categories;
- the grand total.

Rows that are totals must be labeled (`ALL CATEGORIES`, `ALL YEARS`) instead of showing `NULL`, and they must come after the rows they summarize.

<details>
<summary>Hint 1</summary>

List the grouping levels the meeting needs: (category, year), (category), (year), and (). Which of `ROLLUP`, `CUBE`, or `GROUPING SETS` produces exactly these four levels with the shortest `GROUP BY`?

</details>

<details>
<summary>Hint 2</summary>

`CUBE (c.Name, YEAR(i.InvoiceDate))`. The year is a number, so convert it to text before putting `'ALL YEARS'` in the same column. `GROUPING()` takes the same expression as the `GROUP BY`.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    CASE WHEN GROUPING(c.Name) = 1 THEN 'ALL CATEGORIES'
         ELSE c.Name END AS Category,
    CASE WHEN GROUPING(YEAR(i.InvoiceDate)) = 1 THEN 'ALL YEARS'
         ELSE CAST(YEAR(i.InvoiceDate) AS varchar(4)) END AS InvoiceYear,
    SUM(ii.TotalPrice) AS Revenue
FROM InvoiceItem ii
JOIN Invoice i ON i.IDInvoice = ii.InvoiceID
JOIN Product p ON p.IDProduct = ii.ProductID
JOIN Subcategory s ON s.IDSubcategory = p.SubcategoryID
JOIN Category c ON c.IDCategory = s.CategoryID
GROUP BY CUBE (c.Name, YEAR(i.InvoiceDate))
ORDER BY
    GROUPING(c.Name), Category,
    GROUPING(YEAR(i.InvoiceDate)), InvoiceYear;
```

Expected result: 25 rows — 4 categories × 4 years, an `ALL YEARS` row for each category, an `ALL CATEGORIES` row for each year, and the grand total of about `109,846,381.40`. `Bicycles` brings in about `94.7` million of that.

`ROLLUP (c.Name, YEAR(...))` would miss the four "all categories in one year" rows: it only rolls up from right to left. `GROUPING SETS ((c.Name, YEAR(...)), (c.Name), (YEAR(...)), ())` gives the same result as `CUBE`, just longer.

</details>

---

## Exercise 8 — Choose the grouping [ADVANCED]

For each request, decide whether you would use `ROLLUP`, `CUBE`, or `GROUPING SETS`, and write only the `GROUP BY` clause. Then run the query for request 4.

1. Revenue by country and city, with a total for each country and a grand total.
2. Number of invoices by salesperson and year, with a total for each salesperson, a total for each year, and a grand total.
3. Number of products by color and, separately, by subcategory, with a grand total — but no rows for color and subcategory together.
4. Number of invoices by year and month, with a total for each year — but **no** grand total.

<details>
<summary>Hint</summary>

For each request, write down the grouping levels it needs, for example `(Country, City)`, `(Country)`, `()`. Then compare: `ROLLUP` gives the levels from left to right, `CUBE` gives every combination, and `GROUPING SETS` gives exactly the levels you list.

</details>

<details>
<summary>Solution</summary>

1. `ROLLUP` — the levels form a hierarchy:

    ```sql
    GROUP BY ROLLUP (s.Name, c.Name)
    ```

2. `CUBE` — every combination of the two columns:

    ```sql
    GROUP BY CUBE (sm.IDSalesman, YEAR(i.InvoiceDate))
    ```

3. `GROUPING SETS` — two independent levels and a grand total, without the combination:

    ```sql
    GROUP BY GROUPING SETS ((p.Color), (p.SubcategoryID), ())
    ```

    Watch out when you run it: products without a color and products without a subcategory also produce rows with `NULL` in both columns. Only `GROUPING()` tells you which `NULL` row is the grand total (`504` products), which one is "no color" (`248`), and which one is "no subcategory" (`209`).

4. `GROUPING SETS` — `ROLLUP` would add a grand total that the request does not want:

    ```sql
    SELECT
        YEAR(i.InvoiceDate) AS InvoiceYear,
        MONTH(i.InvoiceDate) AS InvoiceMonth,
        COUNT(*) AS Invoices
    FROM Invoice i
    GROUP BY GROUPING SETS
    (
        (YEAR(i.InvoiceDate), MONTH(i.InvoiceDate)),
        (YEAR(i.InvoiceDate))
    )
    ORDER BY InvoiceYear, GROUPING(MONTH(i.InvoiceDate)), InvoiceMonth;
    ```

    Expected result: 41 rows — 37 months from July 2001 to July 2004 and one total for each of the four years. 2003 has the most invoices, `12,443`.

</details>

# Part B – Ranking functions

## Exercise 9 — Row number by (LastName, FirstName) [BEGINNER]

List all customers ordered by `LastName` then `FirstName`. Add a row number based on the same ordering.

<details>
<summary>Hint</summary>

`ROW_NUMBER() OVER (ORDER BY ...)` numbers the rows in the order given inside `OVER`.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    c.IDCustomer, c.LastName, c.FirstName,
    ROW_NUMBER() OVER (ORDER BY c.LastName, c.FirstName) AS RN
FROM Customer c
ORDER BY c.LastName, c.FirstName;
```

Expected result: one row for each of the `19,972` customers. The first is Syed Abbas; customers with the same name, such as the three Kim Abercrombies, still get different numbers.

</details>

---

## Exercise 10 — Per-city row number [BEGINNER]

Same as Exercise 9, but the row number restarts for each city.

<details>
<summary>Hint</summary>

Add `PARTITION BY` to restart the numbering for every city.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    ci.Name AS City, c.LastName, c.FirstName,
    ROW_NUMBER() OVER (PARTITION BY ci.Name
                       ORDER BY c.LastName, c.FirstName) AS RankInCity
FROM Customer c
JOIN City ci ON ci.IDCity = c.CityID
ORDER BY ci.Name, c.LastName, c.FirstName;
```

`PARTITION BY` is the entire trick — everything else is identical to Exercise 9.

Expected result: the same `19,972` customers, but the numbering starts again at `1` in each city. Berlin comes first alphabetically, starting with Syed Abbas.

</details>

---

## Exercise 11 — Rank invoice items by quantity [BEGINNER]

Rank invoice items with the highest quantity first. Ties should share a rank (use `RANK`).

<details>
<summary>Hint</summary>

`RANK()` gives tied rows the same number and then skips numbers.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    ii.InvoiceID, ii.ProductID, ii.Quantity,
    RANK() OVER (ORDER BY ii.Quantity DESC) AS QuantityRank
FROM InvoiceItem ii
ORDER BY QuantityRank, ii.InvoiceID, ii.ProductID;
```

Expected result: one row for each of the `121,317` invoice items. The highest quantity is `44`. Two items share rank `3` with quantity `40`, so the next rank is `5`: `RANK` leaves a gap after a tie.

</details>

---

## Exercise 12 — Salesman 284's invoices, bucketed into groups of 3 [INTERMEDIATE]

Order salesman 284's invoices by date then invoice number. The first 3 are group 1, the next 3 are group 2, and so on.

<details>
<summary>Hint</summary>

Number the rows from 0 with `ROW_NUMBER() - 1`, then use integer division by 3.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    i.IDInvoice, i.InvoiceNumber, i.InvoiceDate,
    (ROW_NUMBER() OVER (ORDER BY i.InvoiceDate, i.InvoiceNumber) - 1) / 3 + 1
      AS BucketOf3
FROM Invoice i
WHERE i.SalesmanID = 284
ORDER BY i.InvoiceDate, i.InvoiceNumber;
```

`NTILE(n)` also looks tempting here, but it only works if you know `n` up front, and it distributes rows as evenly as possible across `n` buckets rather than making fixed-size buckets of 3. For "buckets of exactly 3 rows", the `ROW_NUMBER` plus integer-division trick is the direct tool.

Expected result: `39` invoices in `13` groups of 3. Group 1 holds the three invoices from 1 August 2002, and group 2 starts with `SO47969`.

</details>

---

## Exercise 13 — Best-selling colors [INTERMEDIATE]

Marketing wants to know which product colors sell best. Show each color with the total quantity sold (`SUM(InvoiceItem.Quantity)`) and its position, best-selling first. Show products without a color as `(no color)`. If two colors sold the same quantity, they share a position, and the next position is not skipped.

<details>
<summary>Hint 1</summary>

First write the `GROUP BY p.Color` query with the total. Then add the ranking column.

</details>

<details>
<summary>Hint 2</summary>

A window function can order by an aggregate: `DENSE_RANK() OVER (ORDER BY SUM(ii.Quantity) DESC)`. Window functions run after `GROUP BY` (Lab 11, Section 6.3).

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    ISNULL(p.Color, N'(no color)') AS Color,
    SUM(ii.Quantity) AS QuantitySold,
    DENSE_RANK() OVER (ORDER BY SUM(ii.Quantity) DESC) AS ColorRank
FROM InvoiceItem ii
JOIN Product p ON p.IDProduct = ii.ProductID
GROUP BY p.Color
ORDER BY ColorRank;
```

Expected result: 9 rows. `Crna` is first with `81,937`, `(no color)` is second with `48,289`, and `Srebrna/Crna` is last with `3,931`.

`RANK` or `ROW_NUMBER` would give the same numbers here, because no two colors have the same total.

</details>

---

# Part C – Aggregate window functions

## Exercise 14 — Running total of revenue per year [INTERMEDIATE]

Invoice items with a running total that resets every calendar year.

<details>
<summary>Hint</summary>

`SUM(...) OVER (PARTITION BY ... ORDER BY ...)` produces a running total; partition by the year of the invoice date.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    i.InvoiceDate, ii.TotalPrice,
    SUM(ii.TotalPrice) OVER
    (
        PARTITION BY YEAR(i.InvoiceDate)
        ORDER BY i.InvoiceDate, i.IDInvoice, ii.ProductID
    ) AS RunningRevenueThisYear
FROM InvoiceItem ii
JOIN Invoice i ON i.IDInvoice = ii.InvoiceID
ORDER BY i.InvoiceDate, i.IDInvoice, ii.ProductID;
```

Expected result: the running total starts again at the first invoice item of each year. The last row of 2001 shows the whole year's revenue, about `11,331,808.96`.

</details>

---

## Exercise 15 — Products with a count of same-color products [BEGINNER]

Every product, with a count of how many products share its color.

<details>
<summary>Hint</summary>

Without `ORDER BY` inside `OVER`, an aggregate window function returns the same value for the whole partition.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    p.Name, p.Color, p.PriceWithoutVAT,
    COUNT(*) OVER (PARTITION BY p.Color) AS ProductsInColor
FROM Product p
ORDER BY p.Color, p.Name;
```

No `ORDER BY` inside `OVER`, so `COUNT(*)` is computed across the whole partition — every product of a given color gets the same count. This is the "constant per partition" case from [Section 8.1 of Lab 11](../labs/lab11-grouping-and-window-functions.md#81-two-shapes).

Expected result: one row per product (504). Products without a color show `248` in `ProductsInColor`; black (`Crna`) products show `93`.

</details>

---

## Exercise 16 — Distance from the most expensive product [INTERMEDIATE]

For every product with a price greater than zero, show how much cheaper it is than the single most expensive product overall.

<details>
<summary>Hint</summary>

An empty `OVER ()` makes the whole result one window, so `MAX(...) OVER ()` is the overall maximum on every row.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    p.Name, p.PriceWithoutVAT,
    MAX(p.PriceWithoutVAT) OVER () - p.PriceWithoutVAT AS CheaperThanMaxBy
FROM Product p
WHERE p.PriceWithoutVAT > 0
ORDER BY CheaperThanMaxBy;
```

The empty `OVER ()` computes the `MAX` across the whole result; every row's `CheaperThanMaxBy` is `(global max) - (this row's price)`. The most expensive product's own row shows `0`.

Expected result: the five Road-150 Red bikes come first with `0.00`, because they are the most expensive (`3,578.27`).

</details>

---

## Exercise 17 — Smooth out the price jumps [INTERMEDIATE]

A chart of touring bike prices (`SubcategoryID = 3`, cheapest first) jumps sharply between models. To draw a smoother line, show each bike's price next to the average price of that bike, the 2 bikes before it, and the 2 bikes after it.

<details>
<summary>Hint 1</summary>

The third part of `OVER` is the frame (Lab 11, Section 10): `ROWS BETWEEN ... PRECEDING AND ... FOLLOWING`.

</details>

<details>
<summary>Hint 2</summary>

Many bikes have the same price. Add `IDProduct` to the `ORDER BY` inside `OVER`, so that "the previous 2 rows" always means the same rows.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    p.Name,
    p.PriceWithoutVAT,
    AVG(p.PriceWithoutVAT) OVER (
        ORDER BY p.PriceWithoutVAT, p.IDProduct
        ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
    ) AS MovingAvg
FROM Product p
WHERE p.SubcategoryID = 3
ORDER BY p.PriceWithoutVAT, p.IDProduct;
```

Expected result: 22 rows. While the window contains only `742.35` prices, the average is also `742.35`. Where the price jumps to `1214.85`, the average starts to rise a few rows early (`836.85`, `931.35`, ...), because the window already sees the more expensive bikes after the current one. At the first and last rows the window is smaller: there are no rows before the first one.

</details>

---

# Part D – Analytical functions

## Exercise 18 — Delta from the previous product [INTERMEDIATE]

Products with a price greater than zero, cheapest first. Show how much more expensive each one is than the previous.

<details>
<summary>Hint</summary>

`LAG(column, 1) OVER (ORDER BY ...)` returns the value from the previous row in that order.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    p.Name, p.PriceWithoutVAT,
    p.PriceWithoutVAT - LAG(p.PriceWithoutVAT, 1) OVER (ORDER BY p.PriceWithoutVAT)
      AS DeltaFromPrev
FROM Product p
WHERE p.PriceWithoutVAT > 0
ORDER BY p.PriceWithoutVAT;
```

Expected result: `304` products. The first row, Patch Kit/8 Patches (`2.29`), has `NULL` in `DeltaFromPrev`: there is no previous product. Products with the same price as the one before show `0.00`.

</details>

---

## Exercise 19 — A train schedule with LEAD [INTERMEDIATE]

Create a small table and show, next to each station, how many minutes until the next station's departure.

<details>
<summary>Hint</summary>

`LEAD` returns the value from the next row; `DATEDIFF(minute, ...)` turns two `time` values into minutes.

</details>

<details>
<summary>Solution</summary>

```sql
DROP TABLE IF EXISTS dbo.Lab12TrainSchedule;
GO

CREATE TABLE dbo.Lab12TrainSchedule
(
    IDStation int IDENTITY(1, 1) PRIMARY KEY,
    Station   nvarchar(50) NOT NULL,
    Departure time         NOT NULL
);
GO

INSERT INTO dbo.Lab12TrainSchedule (Station, Departure)
VALUES
    (N'Zagreb',    '11:00'),
    (N'Dugo Selo', '11:35'),
    (N'Kutina',    '13:15'),
    (N'Novska',    '13:45');

SELECT
    s.IDStation, s.Station, s.Departure,
    LEAD(s.Departure, 1) OVER (ORDER BY s.Departure) AS NextDeparture,
    DATEDIFF(minute,
             s.Departure,
             LEAD(s.Departure, 1) OVER (ORDER BY s.Departure)) AS MinutesToNext
FROM dbo.Lab12TrainSchedule s
ORDER BY s.Departure;
```

The last row's `MinutesToNext` is `NULL` — there is no next station. This is the same shape you'd use for "how long is each concert set", "how long between website events", or "how long between server heartbeats" — any time-series diff.

</details>

---

## Exercise 20 — How long has the customer been with us? [INTERMEDIATE]

For customers `1` and `2`, show every invoice with its date, the date of that customer's **first** invoice, and how many days have passed since then.

<details>
<summary>Hint 1</summary>

`FIRST_VALUE(column) OVER (PARTITION BY ... ORDER BY ...)` returns the value from the first row of each partition (Lab 11, Section 9.4).

</details>

<details>
<summary>Hint 2</summary>

Partition by customer and order by date. `DATEDIFF(day, first, current)` gives the number of days.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    i.CustomerID,
    i.InvoiceNumber,
    i.InvoiceDate,
    FIRST_VALUE(i.InvoiceDate) OVER (
        PARTITION BY i.CustomerID
        ORDER BY i.InvoiceDate, i.IDInvoice
    ) AS FirstInvoiceDate,
    DATEDIFF(day,
        FIRST_VALUE(i.InvoiceDate) OVER (
            PARTITION BY i.CustomerID
            ORDER BY i.InvoiceDate, i.IDInvoice
        ),
        i.InvoiceDate) AS DaysSinceFirst
FROM Invoice i
WHERE i.CustomerID IN (1, 2)
ORDER BY i.CustomerID, i.InvoiceDate, i.IDInvoice;
```

Expected result: 11 rows, 7 for customer `1` and 4 for customer `2`. `DaysSinceFirst` starts at `0` again for customer `2`, because `PARTITION BY` restarts the window. Customer `1`'s last invoice is `638` days after the first one.

`FIRST_VALUE` is safe with the default frame, because the first row is always inside it. `LAST_VALUE` is not (Lab 11, Section 9.4).

</details>

---

## Exercise 21 — Compared with two years ago [ADVANCED]

Management compares each year's revenue (`SUM(InvoiceItem.TotalPrice)`) with the year **two years before it**, not the year just before. Show each year's revenue, the revenue from two years earlier, and the difference.

<details>
<summary>Hint 1</summary>

`LAG` has a second argument: how many rows back to look. `LAG(x, 2)` looks two rows back.

</details>

<details>
<summary>Hint 2</summary>

As in Exercise 13, the window function can use an aggregate: `LAG(SUM(ii.TotalPrice), 2) OVER (ORDER BY YEAR(i.InvoiceDate))`.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    YEAR(i.InvoiceDate) AS InvoiceYear,
    SUM(ii.TotalPrice) AS Revenue,
    LAG(SUM(ii.TotalPrice), 2) OVER (ORDER BY YEAR(i.InvoiceDate)) AS RevenueTwoYearsEarlier,
    SUM(ii.TotalPrice)
      - LAG(SUM(ii.TotalPrice), 2) OVER (ORDER BY YEAR(i.InvoiceDate)) AS Change
FROM Invoice i
JOIN InvoiceItem ii ON ii.InvoiceID = i.IDInvoice
GROUP BY YEAR(i.InvoiceDate)
ORDER BY InvoiceYear;
```

Expected result: 4 rows, 2001–2004. The first two years have `NULL` in the last two columns: there is no year two rows earlier. 2003 is about `30.7` million higher than 2001, and 2004 is about `4.8` million lower than 2002.

</details>

---

# Part E – Putting it together

## Exercise 22 — The leader in each category [ADVANCED]

Category managers want to see how their subcategories compare. For each category, list its subcategories with their revenue (`SUM(InvoiceItem.TotalPrice)`) and their position **within that category**, the highest revenue first. Each category's list starts again at position `1`.

<details>
<summary>Hint 1</summary>

This combines two exercises: the grouped total from Exercise 13 and the restart per group from Exercise 10.

</details>

<details>
<summary>Hint 2</summary>

`RANK() OVER (PARTITION BY c.Name ORDER BY SUM(ii.TotalPrice) DESC)` after `GROUP BY c.Name, s.Name`.

</details>

<details>
<summary>Solution</summary>

```sql
SELECT
    c.Name AS Category,
    s.Name AS Subcategory,
    SUM(ii.TotalPrice) AS Revenue,
    RANK() OVER (
        PARTITION BY c.Name
        ORDER BY SUM(ii.TotalPrice) DESC
    ) AS RankInCategory
FROM InvoiceItem ii
JOIN Product p ON p.IDProduct = ii.ProductID
JOIN Subcategory s ON s.IDSubcategory = p.SubcategoryID
JOIN Category c ON c.IDCategory = s.CategoryID
GROUP BY c.Name, s.Name
ORDER BY Category, RankInCategory;
```

Expected result: 35 rows. The leaders are `Kacige` (Accessories), `Road Bikes` (Bicycles), `Jerseys` (Clothes), and `Mountain Frames` (Parts). Without `PARTITION BY`, all 35 subcategories would be ranked together, and the three bicycle subcategories would take the first three places.

</details>

---

## References

- [Lab 11 – Advanced Grouping and Window Functions](../labs/lab11-grouping-and-window-functions.md)
