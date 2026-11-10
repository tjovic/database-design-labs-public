# Lab 12 – Window Function Exercises

These exercises build on [Lab 12 – Window Functions](../labs/lab12-window-functions.md) and use `AdventureWorksENG`. They are grouped like the lab: ranking functions, aggregate window functions and running totals, and the analytical functions `LAG` and `LEAD`.

All exercises are plain `SELECT` statements, except Exercise 9, which creates a small table and drops it at the end of its solution.

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

</details>

---

# Part B – Aggregate window functions

## Exercise 5 — Running total of revenue per year [INTERMEDIATE]

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

</details>

---

## Exercise 6 — Products with a count of same-color products [BEGINNER]

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

</details>

---

## Exercise 7 — Distance from the most expensive product [INTERMEDIATE]

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

</details>

---

# Part C – Analytical functions

## Exercise 8 — Delta from the previous product [INTERMEDIATE]

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

</details>

---

## Exercise 9 — A train schedule with LEAD [INTERMEDIATE]

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

Clean up the table once you're done with this exercise:

```sql
DROP TABLE dbo.Lab12TrainSchedule;
```

</details>

---

## References

- [Lab 12 – Window Functions](../labs/lab12-window-functions.md)
- [OVER Clause (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-over-clause-transact-sql)
- [Ranking Functions (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/functions/ranking-functions-transact-sql)
- [Analytic Functions (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/functions/analytic-functions-transact-sql)
