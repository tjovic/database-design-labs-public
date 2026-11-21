# Lab 12 – Window Function Exercises

**Database:** `AdventureWorksENG`

These exercises build on [Lab 12 – Window Functions](../labs/lab12-window-functions.md) and use `AdventureWorksENG`. They are grouped like the lab: ranking functions, aggregate window functions with running totals and frames, and the analytical functions `LAG`, `LEAD`, and `FIRST_VALUE`. The last exercise combines several of them.

All exercises are plain `SELECT` statements, except Exercise 11, which creates a small table.

```sql
USE AdventureWorksENG;
GO
```

---

# Part A – Ranking functions

## Exercise 1 — Row number by (LastName, FirstName) [BEGINNER]

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

## Exercise 2 — Per-city row number [BEGINNER]

Same as Exercise 1, but the row number restarts for each city.

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

`PARTITION BY` is the entire trick — everything else is identical to Exercise 1.

Expected result: the same `19,972` customers, but the numbering starts again at `1` in each city. Berlin comes first alphabetically, starting with Syed Abbas.

</details>

---

## Exercise 3 — Rank invoice items by quantity [BEGINNER]

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

## Exercise 4 — Salesman 284's invoices, bucketed into groups of 3 [INTERMEDIATE]

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

## Exercise 5 — Best-selling colors [INTERMEDIATE]

Marketing wants to know which product colors sell best. Show each color with the total quantity sold (`SUM(InvoiceItem.Quantity)`) and its position, best-selling first. Show products without a color as `(no color)`. If two colors sold the same quantity, they share a position, and the next position is not skipped.

<details>
<summary>Hint 1</summary>

First write the `GROUP BY p.Color` query with the total. Then add the ranking column.

</details>

<details>
<summary>Hint 2</summary>

A window function can order by an aggregate: `DENSE_RANK() OVER (ORDER BY SUM(ii.Quantity) DESC)`. Window functions run after `GROUP BY` (Lab 12, Section 1.3).

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

# Part B – Aggregate window functions

## Exercise 6 — Running total of revenue per year [INTERMEDIATE]

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

## Exercise 7 — Products with a count of same-color products [BEGINNER]

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

No `ORDER BY` inside `OVER`, so `COUNT(*)` is computed across the whole partition — every product of a given color gets the same count. This is the "constant per partition" case from [Section 3.1 of Lab 12](../labs/lab12-window-functions.md#31-two-shapes).

Expected result: one row per product (504). Products without a color show `248` in `ProductsInColor`; black (`Crna`) products show `93`.

</details>

---

## Exercise 8 — Distance from the most expensive product [INTERMEDIATE]

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

## Exercise 9 — Smooth out the price jumps [INTERMEDIATE]

A chart of touring bike prices (`SubcategoryID = 3`, cheapest first) jumps sharply between models. To draw a smoother line, show each bike's price next to the average price of that bike, the 2 bikes before it, and the 2 bikes after it.

<details>
<summary>Hint 1</summary>

The third part of `OVER` is the frame (Lab 12, Section 5): `ROWS BETWEEN ... PRECEDING AND ... FOLLOWING`.

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

# Part C – Analytical functions

## Exercise 10 — Delta from the previous product [INTERMEDIATE]

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

## Exercise 11 — A train schedule with LEAD [INTERMEDIATE]

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

## Exercise 12 — How long has the customer been with us? [INTERMEDIATE]

For customers `1` and `2`, show every invoice with its date, the date of that customer's **first** invoice, and how many days have passed since then.

<details>
<summary>Hint 1</summary>

`FIRST_VALUE(column) OVER (PARTITION BY ... ORDER BY ...)` returns the value from the first row of each partition (Lab 12, Section 4.4).

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

`FIRST_VALUE` is safe with the default frame, because the first row is always inside it. `LAST_VALUE` is not (Lab 12, Section 4.4).

</details>

---

## Exercise 13 — Compared with two years ago [ADVANCED]

Management compares each year's revenue (`SUM(InvoiceItem.TotalPrice)`) with the year **two years before it**, not the year just before. Show each year's revenue, the revenue from two years earlier, and the difference.

<details>
<summary>Hint 1</summary>

`LAG` has a second argument: how many rows back to look. `LAG(x, 2)` looks two rows back.

</details>

<details>
<summary>Hint 2</summary>

As in Exercise 5, the window function can use an aggregate: `LAG(SUM(ii.TotalPrice), 2) OVER (ORDER BY YEAR(i.InvoiceDate))`.

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

# Part D – Putting it together

## Exercise 14 — The leader in each category [ADVANCED]

Category managers want to see how their subcategories compare. For each category, list its subcategories with their revenue (`SUM(InvoiceItem.TotalPrice)`) and their position **within that category**, the highest revenue first. Each category's list starts again at position `1`.

<details>
<summary>Hint 1</summary>

This combines two exercises: the grouped total from Exercise 5 and the restart per group from Exercise 2.

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

- [Lab 12 – Window Functions](../labs/lab12-window-functions.md)
