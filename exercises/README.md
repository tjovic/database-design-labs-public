# SQL Exercise Collection

## Purpose

This collection provides focused SQL Server exercises that build on the course labs. Each exercise should give students a clear goal, a chance to reason through the problem before writing SQL, and a way to check their work.

The collection currently covers **triggers**, **stored procedures**, **functions**, and **indexes**. Exercises use `AdventureWorksENG` unless an exercise says otherwise.

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

### Indexes

The index collection is in [Index Exercises](indexes.md) and follows the learning goals in [Lab 06 – Indexes](../labs/lab06-indexes.md):

1. **What `INCLUDE` actually buys you** — staged exercise measuring `STATISTICS IO` before and after: a filter-only index, why returning the clustering key is always free, proof that one more returned column reintroduces a `Key Lookup`, the `INCLUDE` fix, and why an included column also covers an extra filter predicate.
2. **Composite index column order** — reason about which queries a multi-column index can and cannot seek on.
3. **Covering indexes** — design an index so a query needs no `Key Lookup`.
4. **Selectivity** — judge when a low-cardinality column is still a good index candidate, including covering a `GROUP BY` column.
5. **Evaluating suggestions** — decide whether a "Missing Index" recommendation is worth creating, given indexes that already exist.

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
- [Lab 06 – Indexes](../labs/lab06-indexes.md)
- [Index Exercises](indexes.md)
- [Repository overview](../README.md)
