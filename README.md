# Database Design Labs

Practical SQL Server lab materials for the **Database Design** course.

The repository is expanded during the course as new topics are introduced.

Most exercises use the `AdventureWorksENG` training database; Labs 05–06 and Labs 09–10 use their own separate, dedicated databases (see [About the database](#about-the-database)).

> Each lab contains explanations, SQL examples, short knowledge checks, exercises, and hidden solutions.

---

## Requirements

You will need:

- Microsoft SQL Server
- SQL Server Management Studio (SSMS)
- the `AdventureWorksENG` database

Before starting the labs, make sure you can connect to SQL Server and access the training database.

---

## Labs

| # | Lab | Main topics |
|---|---|---|
| 00 | [T-SQL Essentials](labs/lab00-tsql-essentials.md) | batches and `GO`, variables, table variables, `IF / ELSE`, `SCOPE_IDENTITY()`, `CAST` |
| 01 | [Views](labs/lab01-views.md) | creating and querying Views, hiding query complexity, stable interfaces, system Views, modifying data through Views, `WITH CHECK OPTION`, `SCHEMABINDING`, `ENCRYPTION` |
| 02 | [Triggers](labs/lab02-triggers.md) | DML triggers, `inserted` / `deleted`, multi-row safety, auditing and business rules |
| 03 | [Stored Procedures](labs/lab03-stored-procedures.md) | creating and executing procedures, input and output parameters, `RETURN`, encapsulating database operations |
| 04 | [Functions](labs/lab04-functions.md) | scalar functions, inline and multi-statement table-valued functions, parameters and return values, functions vs. procedures, performance considerations |
| 05 | [Physical Storage](labs/lab05-physical-storage.md) | pages, extents, buffer pool, logical vs. physical reads, `DBCC IND` / `DBCC PAGE` |
| 06 | [Indexes](labs/lab06-indexes.md) | B+-tree structure, heap vs. clustered vs. nonclustered indexes, reading execution plans, composite indexes, selectivity, covering indexes |
| 07 | [CRUD Operations](labs/lab07-crud-operations.md) | organizing Create/Read/Update/Delete with stored procedures, choosing between separate and combined procedures, read access through an inline table-valued function, `TRY/CATCH` with a CRUD example, referential integrity |
| 08 | [Complex Parameters](labs/lab08-complex-parameters.md) | passing collections into a procedure: why client-side query building enables SQL injection, delimited strings, XML (`.nodes()` / `.value()` / `FOR XML PATH`), Table-Valued Parameters (`CREATE TYPE ... AS TABLE`), JSON (`OPENJSON` / `FOR JSON PATH`), choosing the right method |
| 09 | [Transactions](labs/lab09-transactions.md) | `BEGIN/COMMIT/ROLLBACK TRANSACTION`, ACID properties, write-ahead logging, checkpoints, savepoints, `@@TRANCOUNT`, combining transactions with `TRY/CATCH` and `THROW`, transaction ownership between a procedure and its caller |
| 10 | [Concurrency and Isolation](labs/lab10-concurrency.md) | dirty reads, non-repeatable reads, phantom reads, the four isolation levels, two-session demos, shared/exclusive locks, two-phase locking, lock granularity and escalation, deadlocks, MVCC and `READ_COMMITTED_SNAPSHOT` |
| 11 | [Advanced Grouping](labs/lab11-advanced-grouping.md) | `GROUP BY ()` as the grand-total idiom, `ROLLUP`, `CUBE`, `GROUPING SETS`, rewriting `ROLLUP`/`CUBE` as `GROUPING SETS`, disambiguating grouping `NULL`s from data `NULL`s with `GROUPING()` |
| 12 | [Window Functions](labs/lab12-window-functions.md) | the `OVER` clause, ranking functions (`ROW_NUMBER`/`RANK`/`DENSE_RANK`/`NTILE`), aggregate windows and running totals, analytical functions (`LAG`/`LEAD`/`FIRST_VALUE`/`LAST_VALUE`), the `LAST_VALUE` default-frame trap, `ROWS`/`RANGE` frames |

> Additional labs will be added as the course progresses.

For extra practice beyond each lab's built-in exercises, see the [Exercise Collection](exercises/README.md) (triggers, stored procedures, functions, CRUD operations, complex parameters, transactions, physical storage, indexes).

Lab 8 also has two optional, self-contained live demos — a SQL-injection attack against a running login form, and a REST API that posts JSON into a stored procedure — see [demos/README.md](demos/README.md).

---

## Exams

What to expect on each midterm, with points per task type and where to practice:

- Midterm Exam 1 – [English](exams/midterm-1.md) · [Hrvatski](exams/midterm-1.hr.md)

---

## Lab order

The lab number identifies a thematic unit, but the labs are not necessarily taught strictly in numerical order.

For example, **Lab 00 – T-SQL Essentials** is used as preparation before **Lab 02 – Triggers**, because triggers rely on several T-SQL concepts introduced there.

A typical progression for the current materials is:

```text
Lab 01 – Views
        ↓
Lab 00 – T-SQL Essentials
        ↓
Lab 02 – Triggers
        ↓
Lab 03 – Stored Procedures
        ↓
Lab 04 – Functions
        ↓
Lab 05 – Physical Storage
        ↓
Lab 06 – Indexes
        ↓
Lab 07 – CRUD Operations
        ↓
Lab 08 – Complex Parameters
        ↓
Lab 09 – Transactions
        ↓
Lab 10 – Concurrency and Isolation
        ↓
Lab 11 – Advanced Grouping
        ↓
Lab 12 – Window Functions
```

A single lab may span more than one class session when the topic requires additional time.

The exact order may change as new labs are added.

---

## How to use the materials

For each lab:

1. start with a fresh copy of the lab's database (see [About the database](#about-the-database));
2. read the explanation;
3. run the SQL examples in SSMS;
4. answer the **Check your understanding** questions;
5. complete the exercises before opening the solutions.

Some examples intentionally produce SQL Server errors. These are part of the learning process and demonstrate database rules and behavior.

---

## About the database

Labs 00–04, 07, 08, 11, and 12 use `AdventureWorksENG`, a training database prepared for the course.

The examples create Views, tables, triggers, stored procedures, functions, and test rows, and the labs do not remove them at the end. Before each lab, drop `AdventureWorksENG` and recreate it from the backup, so every lab starts from the same, known state. Some labs contain short cleanup steps in the middle of the lab; run those, because later parts of the same lab depend on them.

Labs 05–06 use a separate generated database, `IndexLab`, built specifically to demonstrate physical storage and indexing at a scale `AdventureWorksENG` cannot provide (10+ million rows in its largest tables). Run the [setup script](labs/setup/index-lab-data-setup.md) once before starting Lab 05; both labs then share that same database. Lab 07 returns to `AdventureWorksENG`.

Lab 09 creates and uses its own small dedicated database, `TransactionsLab`, with a handful of fictional bank accounts. This keeps the transaction and rollback demonstrations fully isolated from `AdventureWorksENG` — nothing in Lab 09 reads or modifies the shared training database. The setup script is included at the start of the lab itself; no separate setup document is needed.

Lab 10 continues to use `TransactionsLab` — its own *Before you start* section recreates the database fresh, so Lab 10 can be run on its own without requiring Lab 09 to have been run first. Lab 10 is also the first lab that needs **two** SSMS query windows connected at once, to demonstrate how two sessions interact.

The two optional live demos linked from Lab 8 (see [demos/README.md](demos/README.md)) each use their own separate, dedicated database — neither touches `AdventureWorksENG`.

---

## Repository structure

Each lab is stored as a separate Markdown file.

New labs are added progressively as new topics are covered in class.

The repository therefore serves as a growing reference for the practical part of the course.