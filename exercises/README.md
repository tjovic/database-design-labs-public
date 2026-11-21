# SQL Exercise Collection

## Purpose

This collection provides focused SQL Server exercises that build on the course labs. Each exercise should give students a clear goal, a chance to reason through the problem before writing SQL, and a way to check their work.

The collection currently covers **T-SQL essentials**, **views**, **triggers**, **stored procedures**, **functions**, **CRUD operations**, **complex parameters**, **transactions**, **concurrency**, **physical storage**, **indexes**, **advanced grouping**, and **window functions**. Exercises use `AdventureWorksENG` unless an exercise says otherwise.

## Organization

Exercises are grouped by topic and arranged from introductory concepts to more involved applications. The current topics are:

### T-SQL essentials

The T-SQL collection is in [T-SQL Essentials Exercises](lab00-tsql-essentials.md) and follows the learning goals in [Lab 00 – T-SQL Essentials](../labs/lab00-tsql-essentials.md):

1. **Variables** — load values from a table, keep them within one batch, and recognize the no-row and multi-row traps.
2. **Table variables and control flow** — fill a table variable and use `IF / ELSE`, `WHILE`, and `CASE`, including `CASE` inside aggregate functions.
3. **Identity values** — capture `SCOPE_IDENTITY()` and use it for a related insert.
4. **Row counts and errors** — use `@@ROWCOUNT` and a basic `TRY/CATCH` block.

### Views

The View collection is in [View Exercises](lab01-views.md) and follows the learning goals in [Lab 01 – Views](../labs/lab01-views.md):

1. **View fundamentals** — create, change, and query Views, hide a `JOIN` inside a View, and use an aggregate View in a query.
2. **System Views** — read table and column metadata from `sys.tables` and `sys.columns`.
3. **Modifying data through Views** — insert, update, and delete through a simple View, and recognize the restrictions of a `JOIN` View.
4. **View options** — use `WITH CHECK OPTION`, `WITH SCHEMABINDING`, and `WITH ENCRYPTION`.

### Triggers

The trigger collection is in [Trigger Exercises](lab02-triggers.md) and follows the learning goals in [Lab 02 – Triggers](../labs/lab02-triggers.md):

1. **Trigger fundamentals** — recognize DML events, create an `AFTER` trigger, and detect in one trigger whether an `INSERT`, `UPDATE`, or `DELETE` fired it.
2. **Auditing changes** — use `inserted` and `deleted` to record inserts, updates, or deletes, classify changes with `CASE`, and check new rows against existing ones.
3. **Multi-row operations** — write set-based trigger logic that handles every affected row.
4. **Business rules** — validate related values and decide when a trigger is an appropriate tool.
5. **Review and debugging** — inspect trigger behavior, identify common mistakes, and explain side effects.

Part A logs changes to `City` in a simple log table; Part B audits `Product` changes. Each exercise names the relevant tables or objects, describes the expected behavior, and explains how to test it.

### Stored procedures

The procedure collection is in [Stored Procedure Exercises](lab03-stored-procedures.md) and follows the learning goals in [Lab 03 – Stored Procedures](../labs/lab03-stored-procedures.md):

1. **Procedure fundamentals** — create, alter, execute, and remove a procedure.
2. **Input parameters** — filter results using values supplied by the caller.
3. **Returning information** — return result sets and use `OUTPUT` parameters, including finding a missing `OUTPUT` keyword.
4. **Changing data** — insert a row and its missing parent row, using `SCOPE_IDENTITY()`.
5. **Status values** — use `RETURN` to report which of several cases occurred, together with a value in an `OUTPUT` parameter.
6. **Reusing a procedure** — call a validation procedure for every row in a `WHILE` loop.

The exercises need no test data setup. Exercise 6 inserts a state and two cities, and Exercise 7 inserts one test city. All other procedures only read data.

### Functions

The function collection is in [Function Exercises](lab04-functions.md) and follows the learning goals in [Lab 04 – Functions](../labs/lab04-functions.md):

1. **Scalar calculations** — accept input and return one value.
2. **Choosing a function type** — decide between a scalar function, an inline TVF, and a multi-statement TVF.
3. **Data-reading functions** — calculate or look up a value from existing rows, use it in a query, and change the function's behavior for missing values.
4. **Inline table-valued functions** — return a table from one query and join it with other tables.
5. **Multi-statement table-valued functions** — populate a returned table using variables and conditional logic, and compare them with inline TVFs.
6. **Real-world calculations** — a payroll calculation split into two functions, and an OIB checksum.

The functions read existing tables and do not change their data. The multi-statement functions insert only into their local return tables.

### CRUD operations

The CRUD collection is in [CRUD Operation Exercises](lab07-crud-operations.md) and follows the learning goals in [Lab 07 – CRUD Operations](../labs/lab07-crud-operations.md):

1. **One procedure per operation** — separate insert, read, update, and delete procedures, with `@@ROWCOUNT` to detect a missing row.
2. **Reading through a function** — an inline table-valued function that can be joined in a larger query.
3. **Combined procedures** — a save procedure for insert and update, a debugging exercise on a missing `BEGIN ... END`, and one procedure with an action parameter.
4. **Error handling** — catching a constraint violation outside and inside a procedure, and translating it into a return value.
5. **Related tables** — deleting a parent together with its child rows, and inserting a child row while finding or creating its parents. These exercises do not use transactions yet; they point out where Lab 9 will make the operations safer.

Unlike Lab 07, which works on the real `AdventureWorksENG` catalog, these exercises use three small tables of their own (`Student`, `Course`, `Enrollment`). The setup recreates them with the original data, so the exercises can be repeated.

### Complex Parameters

The complex parameters collection is in [Complex Parameters Exercises](lab08-complex-parameters.md) and follows the learning goals in [Lab 08 – Complex Parameters](../labs/lab08-complex-parameters.md):

1. **Delimited strings** — accept a comma-separated list, split it with `STRING_SPLIT`, and use it in an `IN` clause or `JOIN`.
2. **XML shredding** — use `.nodes()` and `.value()` to turn XML attributes and element text into rows, including a parent with its children.
3. **Building XML** — use `FOR XML PATH` with slash-separated aliases to create nested XML structures from queries.
4. **JSON** — use `JSON_VALUE` and `OPENJSON` to insert a parent with its children and to delete by a list of IDs, and build JSON with `FOR JSON PATH`.
5. **Table-Valued Parameters** — define a table type and pass typed rows to a procedure.
6. **Choosing the right method** — reason about when to use delimited strings, XML, JSON, or TVPs.

These exercises range from direct SQL rewrites of Lab 08's core patterns to design scenarios where students must justify their method choice. They include building manual string splitters to understand why built-in functions matter, nested XML processing, finding or creating related records, and trade-off analysis across all five methods.

### Transactions

The transaction collection is in [Transaction Exercises](lab09-transactions.md) and follows the learning goals in [Lab 9 – Transactions](../labs/lab09-transactions.md):

1. **Commit or cancel** — confirm or undo a multi-row insert with an explicit transaction.
2. **Savepoints in practice** — a staged exercise covering rollback-to-savepoint, a full rollback that reaches past the savepoint, an unused savepoint, and a cascading two-savepoint rollback.
3. **Caller-managed transactions** — a procedure with no transaction of its own, wrapped by a caller that commits on success and rolls back on a real constraint-violation error.
4. **Close down a country** — a procedure deletes a state with its cities and their customers, and the caller decides whether the whole operation is kept.
5. **Procedure-managed transactions** — a procedure that owns its transaction across three related deletes.
6. **Extend a card, or say why not** — a procedure checks `@@ROWCOUNT`, because an `UPDATE` of a missing row is not an error.
7. **Merge two cities** — two dependent changes, all or nothing, with checks before and after the changes.
8. **Outer transaction vs. inner commit** — an outer transaction rolls back after a called procedure already ran its own `COMMIT`, showing that no nested commit is final until the outermost one runs.
9. **`TransactionsLab` practice (Exercises 9–14)** — predict `COMMIT` and `ROLLBACK`, use savepoints, test the lab's transfer procedure, extend it with a history record, and plan a transaction for a Lab 8 procedure.

Part A (Exercises 1–8) applies the concepts to real `AdventureWorksENG` data — deleting `State` rows referenced by `City` through a real foreign key, and tagging inserted test rows so they can be counted and removed precisely. Part B (Exercises 9–14) continues in Lab 9's `TransactionsLab` database with its fictional bank accounts and relies on the objects the lab creates.

### Concurrency

The concurrency collection is in [Concurrency Exercises](lab10-concurrency.md) and follows the learning goals in [Lab 10 – Concurrency and Isolation](../labs/lab10-concurrency.md):

1. **Dirty read** — reproduce it under `READ UNCOMMITTED`, then prevent it with `READ COMMITTED`.
2. **Non-repeatable read** — reproduce it under `READ COMMITTED`, then prevent it with `REPEATABLE READ`.
3. **Phantom read** — reproduce it under `REPEATABLE READ`, then prevent it with `SERIALIZABLE`.
4. **From a symptom to a fix (Exercises 7–9)** — start from a description of what went wrong, recognize the anomaly, choose the lowest isolation level that prevents it, and demonstrate both.
5. **`TransactionsLab` practice (Exercises 10–14)** — classify an anomaly, predict blocking under `SERIALIZABLE`, choose the minimum isolation level, explain a deadlock, and weigh `READ_COMMITTED_SNAPSHOT`.

Part A (Exercises 1–9) needs two SSMS query windows (Session A / Session B), like Lab 10. Exercises 1–6 use tagged, temporary rows in `AdventureWorksENG`'s `State` table; Exercises 7–9 change real rows only inside transactions they roll back, or test rows they delete. Part B (Exercises 10–14) continues in Lab 10's `TransactionsLab` database with its fictional bank accounts and branches.

### Physical storage

The physical storage collection is in [Physical Storage Exercises](lab05-physical-storage.md) and follows the learning goals in [Lab 05 – Physical Storage](../labs/lab05-physical-storage.md):

1. **A small clustered table** — use `DBCC IND`/`DBCC PAGE` to see how a `PRIMARY KEY CLUSTERED` determines physical row order, on a table of only 3 rows.
2. **Page boundaries on a medium table** — identify data vs. root pages, and confirm that a clustered key's value stays consecutive across a page boundary.
3. **A larger table, two ways** — compare listing every page with `DBCC IND` against summarizing page counts with `sys.dm_db_partition_stats`, motivating why the latter scales to very large tables.
4. **Pages and logical reads** — connect the page counts from the first three exercises to `STATISTICS IO`'s `logical reads`, showing it counts every page type touched, not just leaf data pages.
5. **Finding one row** — count data and index pages, then use the root page to find which data page holds a given row and how long its record is.
6. **Page math and `IndexLab`** — estimate page counts by calculation, compare logical and physical reads, and summarize a very large table.

Part A intentionally uses `AdventureWorksENG`, so results are small enough to read in full while still showing real, non-trivial numbers. Part B uses the large `IndexLab` database from the lab.

### Indexes

The index collection is in [Index Exercises](lab06-indexes.md) and follows the learning goals in [Lab 06 – Indexes](../labs/lab06-indexes.md):

1. **What `INCLUDE` actually buys you** — staged exercise measuring `STATISTICS IO` before and after: a filter-only index, why returning the clustering key is always free, proof that one more returned column reintroduces a `Key Lookup`, the `INCLUDE` fix, and why an included column also covers an extra filter predicate.
2. **Composite index column order** — reason about which queries a multi-column index can and cannot seek on.
3. **Covering indexes** — design an index so a query needs no `Key Lookup`.
4. **Selectivity** — judge when a low-cardinality column is still a good index candidate, including covering a `GROUP BY` column.
5. **Evaluating suggestions** — decide whether a "Missing Index" recommendation is worth creating, given indexes that already exist.
6. **The same pattern, a different table** — repeat Exercise 1's staged `INCLUDE` walkthrough on `Invoice` instead of `Product`, then connect the result back to Exercise 5's missing-index suggestion.
7. **Optimizing a query from start to finish** — drop existing nonclustered indexes, rewrite a non-SARGable condition, create a filtered covering index, and prove the improvement with `STATISTICS IO`.
8. **Large-table practice (Exercises 8–11)** — design an index for a filtered, sorted query, and revisit column order, covering, and Missing Index suggestions on `IndexLab`.

Part A (Exercises 1–7) intentionally uses `AdventureWorksENG` — the database the midterm is written against — so students can practice designing and reading indexes in that exact environment. Part B (Exercises 8–11) continues in Lab 06's large `IndexLab` database, where performance differences are obvious, and relies on the indexes the lab creates. Each exercise creates at most one real index on an existing table (see the database safety note below) rather than an isolated new object.

### Advanced grouping

The grouping collection is in [Advanced Grouping Exercises](lab11-advanced-grouping.md) and follows the learning goals in [Lab 11 – Advanced Grouping](../labs/lab11-advanced-grouping.md):

1. **ROLLUP** — subtotals up a hierarchy, and why the column order matters.
2. **CUBE** — subtotals for every combination of columns.
3. **GROUPING SETS** — exactly the grouping levels you need, and rewriting `ROLLUP` as `GROUPING SETS`.
4. **GROUPING()** — readable labels for subtotal and grand-total rows, also when the grouped column is an expression such as a year.
5. **Choosing the grouping** — start from a report request and decide which of the three tools fits.

All exercises are plain `SELECT` statements on `AdventureWorksENG`.

### Window functions

The window function collection is in [Window Function Exercises](lab12-window-functions.md) and follows the learning goals in [Lab 12 – Window Functions](../labs/lab12-window-functions.md):

1. **Ranking functions** — `ROW_NUMBER`, `RANK`, `DENSE_RANK`, fixed-size buckets, and ranking the result of a `GROUP BY`.
2. **Aggregate window functions** — running totals, values that are constant per partition, and moving averages with a `ROWS` frame.
3. **Analytical functions** — `LAG` and `LEAD` (also more than one row away) and `FIRST_VALUE` per partition.
4. **Putting it together** — rank grouped totals within each group.

All exercises are plain `SELECT` statements on `AdventureWorksENG`, except one that creates a small test table.

## Difficulty labels

Every exercise uses one of these labels:

- **[BEGINNER]** — focuses on one core concept with direct instructions and a clear expected result.
- **[INTERMEDIATE]** — combines multiple concepts, handles multiple affected rows, or returns more than one kind of result.
- **[ADVANCED]** — combines several rules or concepts, requires careful reasoning about set-based behavior or module flow, or asks students to assess the design choice.

Difficulty describes the reasoning and SQL work expected. It does not indicate that an exercise is safe to run against a shared database.

## Hints, solutions, and references

- Try the exercise before opening its hints or solution.
- Hints should be optional and progressive: start with the relevant concept, then point to a useful table or logical step, and only then suggest a SQL structure.
- Put hints and complete solutions in collapsible Markdown `<details>` sections so students can attempt the task first.
- A solution should explain why it works, including how it handles zero, one, or many affected rows where relevant. Include a test statement and expected behavior when practical.
- Link to the relevant course lab section, not to external pages.
- Give test objects plain, descriptive names without an `Exercise` prefix, but check that they do not collide with objects the lab creates. State clearly which test data is inserted or changed.
- Do not add cleanup sections. Exercises are run in order on a freshly restored database, and later exercises may use objects from earlier ones. Keep a `DROP` or `DELETE` only when it is part of the task or when the next step needs a known starting state (for example, a row count).

## Database safety note

Start each exercise collection with a freshly restored `AdventureWorksENG` (see [About the database](../README.md#about-the-database)), so objects left over from a lab (for example, triggers on `dbo.City`) do not interfere. To start over, restore the database again. An exercise must not drop, replace, disable, or clear existing objects or data as part of its setup. Prefer isolated test objects or a dedicated database; if an exercise must use an existing object, document a safe, reversible procedure that preserves its original state.

The index exercises are a deliberate, narrow exception to "prefer isolated test objects": by nature, an index exercise creates a real physical index on an existing table. Because such an index can change the execution plan observed by a later, unrelated exercise or lab, restore the database after finishing the index exercises.

## References

- [Lab 00 – T-SQL Essentials](../labs/lab00-tsql-essentials.md)
- [T-SQL Essentials Exercises](lab00-tsql-essentials.md)
- [Lab 01 – Views](../labs/lab01-views.md)
- [View Exercises](lab01-views.md)
- [Lab 02 – Triggers](../labs/lab02-triggers.md)
- [Trigger Exercises](lab02-triggers.md)
- [Lab 03 – Stored Procedures](../labs/lab03-stored-procedures.md)
- [Stored Procedure Exercises](lab03-stored-procedures.md)
- [Lab 04 – Functions](../labs/lab04-functions.md)
- [Function Exercises](lab04-functions.md)
- [Lab 07 – CRUD Operations](../labs/lab07-crud-operations.md)
- [CRUD Operation Exercises](lab07-crud-operations.md)
- [Lab 08 – Complex Parameters](../labs/lab08-complex-parameters.md)
- [Complex Parameters Exercises](lab08-complex-parameters.md)
- [Lab 9 – Transactions](../labs/lab09-transactions.md)
- [Transaction Exercises](lab09-transactions.md)
- [Lab 10 – Concurrency and Isolation](../labs/lab10-concurrency.md)
- [Concurrency Exercises](lab10-concurrency.md)
- [Lab 05 – Physical Storage](../labs/lab05-physical-storage.md)
- [Physical Storage Exercises](lab05-physical-storage.md)
- [Lab 06 – Indexes](../labs/lab06-indexes.md)
- [Index Exercises](lab06-indexes.md)
- [Lab 11 – Advanced Grouping](../labs/lab11-advanced-grouping.md)
- [Advanced Grouping Exercises](lab11-advanced-grouping.md)
- [Lab 12 – Window Functions](../labs/lab12-window-functions.md)
- [Window Function Exercises](lab12-window-functions.md)
- [Repository overview](../README.md)
