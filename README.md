# Database Design Labs

Practical SQL Server lab materials for the **Database Design** course.

The repository is expanded during the course as new topics are introduced.

The exercises use the `AdventureWorksENG` training database.

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
| 00 | [T-SQL Essentials](lab/lab00-tsql-essentials.md) | batches and `GO`, variables, `IF / ELSE`, `SCOPE_IDENTITY()`, `CAST` |
| 01 | [Views](lab/lab01-views.md) | creating Views, hiding query complexity, stable interfaces, system Views |
| 02 | [Views – continued](lab/lab02-views.md) | modifying data through Views, `WITH CHECK OPTION`, `SCHEMABINDING`, `ENCRYPTION` |
| 03 | [Triggers](lab/lab03-triggers.md) | DML triggers, `inserted` / `deleted`, multi-row safety, auditing and business rules |

> Additional labs will be added as the course progresses.

---

## Lab order

The lab number identifies the material, but the labs are not necessarily taught strictly in numerical order.

For example, **Lab 00 – T-SQL Essentials** is used as preparation before **Lab 03 – Triggers**, because triggers rely on several T-SQL concepts introduced there.

A typical progression for the current materials is:

```text
Lab 01 – Views
        ↓
Lab 02 – Views continued
        ↓
Lab 00 – T-SQL Essentials
        ↓
Lab 03 – Triggers
```

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

The labs use `AdventureWorksENG`, a training database prepared for the course.

The examples may create temporary Views, tables, triggers, or test rows. Cleanup scripts are included so the database can be returned to its expected state after each lab.

---

## Repository structure

Each lab is stored as a separate Markdown file.

New labs are added progressively as new topics are covered in class.

The repository therefore serves as a growing reference for the practical part of the course.