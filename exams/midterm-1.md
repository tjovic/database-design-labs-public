# Midterm Exam 1 – What to Expect

Midterm Exam 1 has 44 points in 88 minutes, spread over three learning outcomes. This page lists the types of tasks you can expect, how many points each type is worth, and where in this repository you can practice it.

---

## Format

- You solve every task by writing T-SQL in SQL Server Management Studio (SSMS).
- The exam uses the `AdventureWorksENG` database, the same one used in the labs.
- You hand in one `.sql` file named `DD-<Name-Surname>.sql`.
- Put a comment with the task label before each solution, e.g. `--LO2T1` (learning outcome 2, task 1).
- If the database gets damaged during the exam, you can restore `AdventureWorksENG` from a backup (in SSMS: **Databases → Restore Database…**). Make sure you know how to do this.
- No tools or services other than those listed in the exam instructions are allowed.

| Learning outcome | Topics | Tasks | Points | Time |
| --- | --- | --- | --- | --- |
| LO1 | Views and triggers | 6 | 24 | 48 min |
| LO2 | Procedures, functions, indexes, physical storage | 4 | 13 | 26 min |
| LO3 | CRUD operations | 2 | 7 | 14 min |
| **Total** | | **12** | **44** | **88 min** |

The suggested time is two minutes per point. Use it to decide when to move on from a task you are stuck on.

---

## Learning outcome 1 (LO1) – Views and triggers (24 points)

Expect four View tasks (14 points) and two trigger tasks (10 points).

| Task type | Points | You should be able to | Practice |
| --- | --- | --- | --- |
| Aggregate View | 3 | Create a View that returns an aggregated value from joined and filtered tables; drop it | Lab 01: [Section 1](../labs/lab01-views.md#section-1--why-views-exist), [Section 3](../labs/lab01-views.md#section-3--modifying-and-dropping-views)<br>[View exercises](../exercises/views.md): [Exercise 1](../exercises/views.md#exercise-1--create-your-first-view-beginner), [Exercise 2](../exercises/views.md#exercise-2--modify-the-view-beginner), [Exercise 3](../exercises/views.md#exercise-3--hide-a-join-inside-a-view-beginner) |
| Using a View in a query | 4 | Create a View and use it in a query with grouping, filtering or `TOP`; drop it | Lab 01: [Section 1](../labs/lab01-views.md#section-1--why-views-exist)<br>[View exercises](../exercises/views.md): [Exercise 3](../exercises/views.md#exercise-3--hide-a-join-inside-a-view-beginner) |
| View options | 3–4 | Recognize which option a requirement calls for – `WITH ENCRYPTION`, `WITH SCHEMABINDING` or `WITH CHECK OPTION` – and apply it with `ALTER VIEW` | Lab 01: [Section 7 (CHECK OPTION)](../labs/lab01-views.md#section-7--with-check-option), [Section 8 (SCHEMABINDING)](../labs/lab01-views.md#section-8--with-schemabinding), [Section 9 (ENCRYPTION)](../labs/lab01-views.md#section-9--with-encryption), [Section 10](../labs/lab01-views.md#section-10--combining-view-options)<br>[View exercises](../exercises/views.md): [Exercise 8](../exercises/views.md#exercise-8--with-check-option-advanced), [Exercise 9](../exercises/views.md#exercise-9--schemabinding-advanced) |
| Trigger that detects a situation | 5 | Create a log table and an `INSERT` or `UPDATE` trigger that detects which situation occurred and logs a matching message; demonstrate every case; drop the trigger | Lab 02: [Section 3](../labs/lab02-triggers.md#section-3--the-inserted-and-deleted-tables), [Section 4](../labs/lab02-triggers.md#section-4--triggers-fire-once-per-statement), [Section 8](../labs/lab02-triggers.md#section-8--one-trigger-for-multiple-events), [Section 10](../labs/lab02-triggers.md#section-10--real-world-example-checking-a-business-rule)<br>[Trigger exercises](../exercises/triggers.md): [Exercise 1](../exercises/triggers.md#exercise-1--first-logging-trigger-beginner), [Exercise 2](../exercises/triggers.md#exercise-2--log-inserted-rows-beginner), [Exercise 4](../exercises/triggers.md#exercise-4--log-renamed-cities-intermediate), [Exercise 5](../exercises/triggers.md#exercise-5--audit-inserted-products-beginner) |
| Trigger with old and new values | 5 | Create an `UPDATE` trigger that reacts to changes in specific columns and logs the old and new values; handle one and many changed rows; demonstrate every case | Lab 02: [Section 5](../labs/lab02-triggers.md#section-5--update-old-and-new-values), [Section 7](../labs/lab02-triggers.md#section-7--the-update-function)<br>[Trigger exercises](../exercises/triggers.md): [Exercise 3](../exercises/triggers.md#exercise-3--multi-row-safety-intermediate), [Exercise 4](../exercises/triggers.md#exercise-4--log-renamed-cities-intermediate), [Exercise 6](../exercises/triggers.md#exercise-6--audit-actual-price-changes-intermediate), [Exercise 9](../exercises/triggers.md#exercise-9--debug-a-flawed-price-audit-trigger-advanced) |

The View option tasks describe a problem, not the option. Practice reading a requirement ("nobody may read the definition", "the View broke when a table changed", "a row I inserted through the View disappeared") and naming the option that solves it.

---

## Learning outcome 2 (LO2) – Procedures, functions, indexes, physical storage (13 points)

Expect one task of each type.

| Task type | Points | You should be able to | Practice |
| --- | --- | --- | --- |
| Stored procedure with OUTPUT and RETURN | 5 | Write a procedure that returns different values through `OUTPUT` parameters and `RETURN`, depending on the data; call it to show every case | Lab 03: [Section 4](../labs/lab03-stored-procedures.md#section-4--returning-data), [Section 5](../labs/lab03-stored-procedures.md#section-5--putting-it-together-bank-transfer)<br>[Procedure exercises](../exercises/procedures.md): [Exercise 4](../exercises/procedures.md#exercise-4--find-the-bug-beginner), [Exercise 5](../exercises/procedures.md#exercise-5--return-invoices-and-a-match-count-intermediate), [Exercise 7](../exercises/procedures.md#exercise-7--return-a-product-price-and-status-advanced) |
| Scalar function | 3 | Write a scalar function that reads data; call it on its own and inside a query; change it with `ALTER`; drop it | Lab 04: [Section 3](../labs/lab04-functions.md#section-3--scalar-functions), [Section 4](../labs/lab04-functions.md#section-4--scalar-functions-that-read-data)<br>[Function exercises](../exercises/functions.md): [Exercise 4](../exercises/functions.md#exercise-4--total-quantity-sold-per-product-intermediate), [Exercise 5](../exercises/functions.md#exercise-5--latest-invoice-date-per-customer-intermediate) |
| Query optimization | 3 | Remove the nonclustered indexes from a table, then make a given query as fast as possible: rewrite its conditions where needed and create a suitable index; prove the improvement with `SET STATISTICS IO ON` | Lab 04: [Section 7](../labs/lab04-functions.md#section-7--two-performance-warnings)<br>Lab 06: [Section 8](../labs/lab06-indexes.md#8-create-indexes-and-observe-the-changing-plan), [Section 10](../labs/lab06-indexes.md#10-index-design-principles)<br>[Index exercises](../exercises/indexes.md) |
| Physical storage | 2 | Find how many data and index pages a table uses, which rows are on a given page, and how long a record is; write the commands and the answers in the script | Lab 05: [Section 11](../labs/lab05-physical-storage.md#11-dbcc-ind--which-pages-belong-to-a-table), [Section 12](../labs/lab05-physical-storage.md#12-dbcc-page--look-inside-a-data-page), [Section 13](../labs/lab05-physical-storage.md#13-practical-example--how-much-space-does-a-row-occupy)<br>[Physical storage exercises](../exercises/physical-storage.md) |

---

## Learning outcome 3 (LO3) – CRUD operations (7 points)

Expect two tasks. Read carefully which objects the task asks for and whether related tables must be handled.

| Task type | Points | You should be able to | Practice |
| --- | --- | --- | --- |
| CRUD on one table | 4 | Create exactly the objects requested – for example one procedure for all operations, or a procedure and a function – for insert, read, update and delete on a table; demonstrate all four operations | Lab 07: [Section 2](../labs/lab07-crud-operations.md#section-2--crud-with-separate-procedures), [Section 3](../labs/lab07-crud-operations.md#section-3--practice-crud-for-state-and-city), [Section 4](../labs/lab07-crud-operations.md#section-4--functions-and-data-access), [Section 5](../labs/lab07-crud-operations.md#section-5--one-procedure-for-multiple-operations)<br>[CRUD exercises](../exercises/crud-operations.md): [Exercise 1](../exercises/crud-operations.md#exercise-1--one-procedure-per-operation-beginner), [Exercise 2](../exercises/crud-operations.md#exercise-2--read-through-an-inline-table-valued-function-beginner), [Exercise 3](../exercises/crud-operations.md#exercise-3--insert-and-update-in-one-procedure-intermediate), [Exercise 4](../exercises/crud-operations.md#exercise-4--find-the-bug-intermediate), [Exercise 5](../exercises/crud-operations.md#exercise-5--one-procedure-for-several-operations-intermediate) |
| CRUD including related tables | 3 | Write a procedure for one CRUD operation (e.g. insert or delete) that also handles the rows of related tables; demonstrate it | Lab 07: [Section 6](../labs/lab07-crud-operations.md#section-6--error-handling-in-crud-operations), [Section 7](../labs/lab07-crud-operations.md#section-7--data-integrity-and-business-rules), [Section 8](../labs/lab07-crud-operations.md#section-8--final-exercise-get-and-delete-without-breaking-the-rules)<br>[CRUD exercises](../exercises/crud-operations.md): [Exercise 6](../exercises/crud-operations.md#exercise-6--where-to-catch-the-error-intermediate), [Exercise 7](../exercises/crud-operations.md#exercise-7--delete-with-related-rows-advanced), [Exercise 8](../exercises/crud-operations.md#exercise-8--insert-with-related-rows-advanced) |

---

## Tips

- **Demonstrate every case** a task asks for: each call of a procedure, function or trigger must be in your script.
- **Answer questions in comments** (e.g. page counts), next to the commands that produced the answers.
- **Include the `DROP` statement** when a task says to remove an object.
- **Run your whole script once before handing it in** and check that every task works without errors.
