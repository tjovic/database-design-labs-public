# SQL Exercise Collection

## Purpose

This collection provides focused SQL Server exercises that build on the course labs. Each exercise should give students a clear goal, a chance to reason through the problem before writing SQL, and a way to check their work.

The collection currently covers **triggers**, **stored procedures**, **functions**, **complex parameters**, **transactions**, **concurrency**, **physical storage**, and **indexes**. Exercises use `AdventureWorksENG` unless an exercise says otherwise.

## Organization

Exercises are grouped by topic and arranged from introductory concepts to more involved applications. The current topics are:

### Triggers

The trigger collection is in [Trigger Exercises](triggers.md) and follows the learning goals in [Lab 02 – Triggers](../labs/lab02-triggers.md):

1. **Trigger fundamentals** — recognize DML events and create an `AFTER` trigger.
2. **Auditing changes** — use `inserted` and `deleted` to record inserts, updates, or deletes.
3. **Multi-row operations** — write set-based trigger logic that handles every affected row.
4. **Business rules** — validate related values and decide when a trigger is an appropriate tool.
5. **Review and debugging** — inspect trigger behavior, identify common mistakes, and explain side effects.

Each exercise names the relevant tables or objects, describes the expected behavior, and explains how to test and clean up safely.

### Stored procedures

The procedure collection is in [Stored Procedure Exercises](procedures.md) and follows the learning goals in [Lab 03 – Stored Procedures](../labs/lab03-stored-procedures.md):

1. **Procedure fundamentals** — create, alter, execute, and remove a procedure.
2. **Input parameters** — filter results using values supplied by the caller.
3. **Returning information** — return result sets and use `OUTPUT` parameters.
4. **Status values** — use `RETURN` to report a simple outcome to the caller.

These exercises use read-only procedures and require no test data setup. They include direct result queries, input parameters, output values, and return status codes.

### Functions

The function collection is in [Function Exercises](functions.md) and follows the learning goals in [Lab 04 – Functions](../labs/lab04-functions.md):

1. **Scalar calculations** — accept input and return one value.
2. **Data-reading functions** — calculate a value from existing rows.
3. **Inline table-valued functions** — return a table from one query.
4. **Multi-statement table-valued functions** — populate a returned table using variables and conditional logic.

The functions read existing tables and do not change their data. The multi-statement function inserts only into its local return table. Scalar function examples include both data-based calculations and simple text transformation.

### Complex Parameters

The complex parameters collection is in [Complex Parameters Exercises](complex-parameters.md) and follows the learning goals in [Lab 08 – Complex Parameters](../labs/lab08-complex-parameters.md):

1. **Delimited strings** — accept a comma-separated list, split it with `STRING_SPLIT`, and use it in an `IN` clause or `JOIN`.
2. **XML shredding** — use `.nodes()` and `.value()` to turn XML into rows.
3. **Building XML** — use `FOR XML PATH` with dotted aliases to create nested XML structures from queries.
4. **Choosing the right method** — reason about when to use delimited strings versus XML versus later methods (TVPs, JSON).

These exercises range from direct SQL rewrites of Lab 08's core patterns to design scenarios where students must justify their method choice. They include building manual string splitters to understand why built-in functions matter, nested XML processing, and trade-off analysis across all five methods.

### Transactions

The transaction collection is in [Transaction Exercises](transactions.md) and follows the learning goals in [Lab 9 – Transactions](../labs/lab09-transactions.md):

1. **Commit or cancel** — confirm or undo a multi-row insert with an explicit transaction.
2. **Savepoints in practice** — a staged exercise covering rollback-to-savepoint, a full rollback that reaches past the savepoint, an unused savepoint, and a cascading two-savepoint rollback.
3. **Caller-managed transactions** — a procedure with no transaction of its own, wrapped by a caller that commits on success and rolls back on a real constraint-violation error.
4. **Procedure-managed transactions** — a procedure that owns its transaction across three related deletes.
5. **Outer transaction vs. inner commit** — an outer transaction rolls back after a called procedure already ran its own `COMMIT`, showing that no nested commit is final until the outermost one runs.

Unlike Lab 9, which uses its own dedicated `TransactionsLab` database with fictional bank accounts, these exercises apply the same concepts to real `AdventureWorksENG` data — deleting `State` rows referenced by `City` through a real foreign key, and tagging inserted `Customer` rows for safe, precise cleanup.

### Concurrency

The concurrency collection is in [Concurrency Exercises](concurrency.md) and follows the learning goals in [Lab 10 – Concurrency and Isolation](../labs/lab10-concurrency.md):

1. **Dirty read** — reproduce it under `READ UNCOMMITTED`, then prevent it with `READ COMMITTED`.
2. **Non-repeatable read** — reproduce it under `READ COMMITTED`, then prevent it with `REPEATABLE READ`.
3. **Phantom read** — reproduce it under `REPEATABLE READ`, then prevent it with `SERIALIZABLE`.

Like Lab 10, every exercise needs two SSMS query windows (Session A / Session B). Unlike Lab 10, which uses `TransactionsLab`'s fictional bank accounts, these exercises apply the same three anomalies to tagged, temporary rows in `AdventureWorksENG`'s `State` table — cleaned up at the end, with the real `Croatia`/`Germany`/`Italy` rows never touched.

### Physical storage

The physical storage collection is in [Physical Storage Exercises](physical-storage.md) and follows the learning goals in [Lab 05 – Physical Storage](../labs/lab05-physical-storage.md):

1. **A small clustered table** — use `DBCC IND`/`DBCC PAGE` to see how a `PRIMARY KEY CLUSTERED` determines physical row order, on a table of only 3 rows.
2. **Page boundaries on a medium table** — identify data vs. root pages, and confirm that a clustered key's value stays consecutive across a page boundary.
3. **A larger table, two ways** — compare listing every page with `DBCC IND` against summarizing page counts with `sys.dm_db_partition_stats`, motivating why the latter scales to very large tables.
4. **Pages and logical reads** — connect the page counts from the first three exercises to `STATISTICS IO`'s `logical reads`, showing it counts every page type touched, not just leaf data pages.

Like the index exercises, these intentionally use `AdventureWorksENG` instead of the large generated `IndexLab` database, so results are small enough to read in full while still showing real, non-trivial numbers.

### Indexes

The index collection is in [Index Exercises](indexes.md) and follows the learning goals in [Lab 06 – Indexes](../labs/lab06-indexes.md):

1. **What `INCLUDE` actually buys you** — staged exercise measuring `STATISTICS IO` before and after: a filter-only index, why returning the clustering key is always free, proof that one more returned column reintroduces a `Key Lookup`, the `INCLUDE` fix, and why an included column also covers an extra filter predicate.
2. **Composite index column order** — reason about which queries a multi-column index can and cannot seek on.
3. **Covering indexes** — design an index so a query needs no `Key Lookup`.
4. **Selectivity** — judge when a low-cardinality column is still a good index candidate, including covering a `GROUP BY` column.
5. **Evaluating suggestions** — decide whether a "Missing Index" recommendation is worth creating, given indexes that already exist.
6. **The same pattern, a different table** — repeat Exercise 1's staged `INCLUDE` walkthrough on `Invoice` instead of `Product`, then connect the result back to Exercise 5's missing-index suggestion.

Unlike Lab 06, which uses the large generated `IndexLab` database to make performance differences obvious, these exercises intentionally use `AdventureWorksENG` — the database the midterm is written against — so students can practice designing and reading indexes in that exact environment. Each exercise creates one real index on an existing table (see the database safety note below) rather than an isolated new object.

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
- Add references beside the exercise or in a short reference list. Prefer links to the relevant course lab section and official SQL Server documentation. References support learning; they should not replace the exercise requirements.
- Keep object names and cleanup scoped to the exercise. State clearly which test data is inserted or changed and how it is restored.

## Database safety note

The inspected `AdventureWorksENG` database already contains four enabled triggers on `dbo.City` and a populated `dbo.ActivityLog` table. Do not assume these are temporary exercise objects. An exercise must not drop, replace, disable, or clear existing objects or data as part of setup or cleanup. Prefer isolated test objects or a dedicated database; if an exercise must use an existing object, document a safe, reversible procedure that preserves its original state.

The index exercises are a deliberate, narrow exception to "prefer isolated test objects": by nature, an index exercise creates a real physical index on an existing table. Each one uses the `IX_Exercises_` naming prefix and is listed in that file's cleanup section — never leave one of these indexes in place after finishing, since it can change the execution plan observed by a later, unrelated exercise or lab.

## References

- [Lab 02 – Triggers](../labs/lab02-triggers.md)
- [Trigger Exercises](triggers.md)
- [Lab 03 – Stored Procedures](../labs/lab03-stored-procedures.md)
- [Stored Procedure Exercises](procedures.md)
- [Lab 04 – Functions](../labs/lab04-functions.md)
- [Function Exercises](functions.md)
- [Lab 08 – Complex Parameters](../labs/lab08-complex-parameters.md)
- [Complex Parameters Exercises](complex-parameters.md)
- [Lab 9 – Transactions](../labs/lab09-transactions.md)
- [Transaction Exercises](transactions.md)
- [Lab 10 – Concurrency and Isolation](../labs/lab10-concurrency.md)
- [Concurrency Exercises](concurrency.md)
- [Lab 05 – Physical Storage](../labs/lab05-physical-storage.md)
- [Physical Storage Exercises](physical-storage.md)
- [Lab 06 – Indexes](../labs/lab06-indexes.md)
- [Index Exercises](indexes.md)
- [Repository overview](../README.md)
