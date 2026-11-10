# Lab 11 – Advanced Grouping Exercises

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

</details>

---

## References

- [Lab 11 – Advanced Grouping](../labs/lab11-advanced-grouping.md)
- [SELECT – GROUP BY (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-group-by-transact-sql)
- [GROUPING (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/functions/grouping-transact-sql)
