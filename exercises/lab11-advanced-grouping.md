# Lab 11 – Advanced Grouping Exercises

**Database:** `AdventureWorksENG`

These exercises build on [Lab 11 – Advanced Grouping](../labs/lab11-advanced-grouping.md) and use `AdventureWorksENG`. They practise `ROLLUP`, `CUBE`, `GROUPING SETS`, and `GROUPING()`. Every exercise is a plain `SELECT`: nothing is created or changed, so no setup or cleanup is needed.

```sql
USE AdventureWorksENG;
GO
```

---

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

---

## References

- [Lab 11 – Advanced Grouping](../labs/lab11-advanced-grouping.md)
