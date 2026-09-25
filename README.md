# Database Design Labs — Sample Coursework

A selection of lab scripts from a university course on relational database
design and SQL Server / T-SQL programming. These are the student-facing
materials — the SQL each student writes and runs during a hands-on lab,
reformatted here as Markdown for easier reading on GitHub.

Shared for demonstration purposes; this is not a maintained course repository,
and the instructor-facing teaching materials (lesson plans, timing, delivery
notes) are not included here.

Target database: `AdventureWorksENG`, a Croatian-market variant of the classic
sample schema (`Customer`, `Product`, `Invoice`, `InvoiceItem`, `State`,
`City`, `Subcategory`).

---

## Labs

| # | Lab | Topic |
|---|---|---|
| 00 | [T-SQL Essentials](labs/lab00-tsql-essentials.md) | Batches, variables, IF/ELSE, SCOPE_IDENTITY, inline CAST |
| 01 | [Views (intro)](labs/lab01-views.md) | `CREATE VIEW`, hiding complexity |
| 02 | [Views (advanced)](labs/lab02-views.md) | Schema binding, updatable views |
| 03 | [Triggers](labs/lab03-triggers.md) | DML triggers, `inserted`/`deleted` |
| 04 | [Stored Procedures](labs/lab04-stored-procedures.md) | `CREATE PROC`, params, `OUTPUT`, `RETURN` |
| 05 | [Functions](labs/lab05-functions.md) | Scalar, inline TVF, multi-statement TVF |
| 06 | [Physical Storage](labs/lab06-physical-storage.md) | Pages, rows, extents; DBCC page inspection |
| 07 | [Indexes](labs/lab07-indexes.md) | Clustered, non-clustered, composite; a 300,000× speedup demo |
| 08 | [T-SQL Programming](labs/lab08-tsql-programming.md) | `CAST`/`CONVERT`/`FORMAT`, `CASE`, `WHILE`, `TRY/CATCH`, `THROW` |
| 09 | [Complex Parameters (Part 1)](labs/lab09-complex-parameters.md) | Client-side anti-example, delimited string, XML |
| 10 | [TVPs and JSON](labs/lab10-tvp-and-json.md) | Table-valued parameters, `OPENJSON`, `FOR JSON` |
| 11 | [Transactions & Concurrency](labs/lab11-transactions-and-concurrency.md) | ACID, `@@TRANCOUNT`, isolation levels, deadlocks, MVCC |
| 12 | [Advanced Grouping](labs/lab12-advanced-grouping.md) | `ROLLUP`, `CUBE`, `GROUPING SETS`, `GROUPING()` |
| 13 | [Window Functions](labs/lab13-window-functions.md) | `OVER`, `PARTITION BY`, ranking, running totals, `LAG`/`LEAD`, frames |

Two-part arc: Labs 1–11 build the database as a service; Labs 12–13 pivot to
analytical SQL for reporting.

