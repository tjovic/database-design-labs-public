# Database Design Labs

Practical SQL Server lab materials for the **Database Design** course.

The repository is expanded during the course as new topics are introduced.

Most exercises use the `AdventureWorksENG` training database; Labs 05–06 use a separate generated database (see [About the database](#about-the-database)).

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

> Additional labs will be added as the course progresses.

For extra practice beyond each lab's built-in exercises, see the [Exercise Collection](exercises/README.md) (triggers, stored procedures, functions).

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
```

A single lab may span more than one class session when the topic requires additional time.

The exact order may change as new labs are added.

---

## How to use the materials

For each lab:

1. read the explanation;
2. run the SQL examples in SSMS;
3. answer the **Check your understanding** questions;
4. complete the exercises before opening the solutions;
5. run the cleanup section when provided.

Some examples intentionally produce SQL Server errors. These are part of the learning process and demonstrate database rules and behavior.

---

## About the database

Labs 00–04 and 07 use `AdventureWorksENG`, a training database prepared for the course.

The examples may create temporary Views, tables, triggers, stored procedures, functions, or test rows. Cleanup scripts are included so the database can be returned to its expected state after each lab.

Labs 05–06 use a separate generated database, `IndexLab`, built specifically to demonstrate physical storage and indexing at a scale `AdventureWorksENG` cannot provide (10+ million rows in its largest tables). Run the [setup script](labs/setup/index-lab-data-setup.md) once before starting Lab 05; both labs then share that same database. Lab 07 returns to `AdventureWorksENG`.

---

## Repository structure

Each lab is stored as a separate Markdown file.

New labs are added progressively as new topics are covered in class.

The repository therefore serves as a growing reference for the practical part of the course.