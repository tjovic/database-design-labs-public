# Lab 10 – Concurrency Exercises

**Databases:** `AdventureWorksENG` (Part A), `TransactionsLab` (Part B)

These exercises build on [Lab 10 – Concurrency and Isolation](../labs/lab10-concurrency.md). **Part A** (Exercises 1–9) reproduces the three anomalies — dirty read, non-repeatable read, and phantom read — and their isolation-level fixes on real `AdventureWorksENG` tables, following the same two-session format Lab 10 uses. In Exercises 7–9 you start from a description of what went wrong: recognize the problem, choose the lowest isolation level that prevents it, and demonstrate both. **Part B** (Exercises 10–14) continues in the lab's `TransactionsLab` database with blocking predictions, deadlocks, and `READ_COMMITTED_SNAPSHOT`.

Part A inserts its own, clearly tagged rows; no existing `AdventureWorksENG` data is changed or removed. Exercises 5 and 6 delete the phantom row they insert, so the range again has two rows when the next exercise starts. Run the setup only once; on a freshly restored database the counts match the expected results. Part B changes only the fictional data in `TransactionsLab`.

> [!NOTE]
> Every Part A exercise needs **two SSMS query windows**, both connected to `AdventureWorksENG` — exactly as in Lab 10. Label them **Session A** and **Session B** before starting.

---

## Setup — Shared by All Part A Exercises

Run this once, in either window, before starting:

```sql
USE AdventureWorksENG;

INSERT INTO dbo.State (Name) VALUES (N'ExerciseConc Base');
INSERT INTO dbo.State (Name) VALUES (N'ExerciseConc Range A');
INSERT INTO dbo.State (Name) VALUES (N'ExerciseConc Range B');
```

`ExerciseConc Base` is the single row Exercises 1–4 read and update. `ExerciseConc Range A/B` form the two-row range Exercises 5–6 query with `LIKE N'ExerciseConc Range%'`.

In your second window, just switch to the database: `USE AdventureWorksENG;`.

---

# Part A – `AdventureWorksENG`

## Exercise 1 — Dirty Read [BEGINNER]

**Session A** starts a transaction, changes the tagged row, and does not commit. **Session B**, at `READ UNCOMMITTED`, reads the uncommitted value, then Session A rolls back — proving Session B saw a value that never existed.

**Session A:**

```sql
BEGIN TRANSACTION;

UPDATE dbo.State
SET Name = N'ExerciseConc Base [DIRTY]'
WHERE Name = N'ExerciseConc Base';

-- Do not COMMIT or ROLLBACK yet.
```

**Session B:**

```sql
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SELECT IDState, Name
FROM dbo.State
WHERE Name LIKE N'ExerciseConc Base%';
```

<details>
<summary>Hint</summary>

- Session B's `SELECT` should return immediately with `ExerciseConc Base [DIRTY]`, even though Session A never confirmed that change.
- After Session A rolls back, re-run Session B's query (still at `READ UNCOMMITTED`) and compare.

</details>

<details>
<summary>Solution</summary>

**Session A** (finish the transaction):

```sql
ROLLBACK TRANSACTION;
```

Re-running Session B's `SELECT` now returns `ExerciseConc Base` — the `[DIRTY]` value Session B saw a moment ago has never existed in the committed database and never will. That is the dirty read: Session B read a value with no corresponding committed state.

Reset Session B's isolation level before continuing:

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

</details>

---

## Exercise 2 — Fixing It with READ COMMITTED [BEGINNER]

Repeat Exercise 1's shape, but this time Session B is at the SQL Server default, `READ COMMITTED`.

**Session A:**

```sql
BEGIN TRANSACTION;

UPDATE dbo.State
SET Name = N'ExerciseConc Base [DIRTY]'
WHERE Name = N'ExerciseConc Base';

-- Leave this open again.
```

**Session B** (already reset to `READ COMMITTED`):

```sql
SELECT IDState, Name
FROM dbo.State
WHERE Name LIKE N'ExerciseConc Base%';
```

<details>
<summary>Hint</summary>

- Session B's query should **hang** this time — do not cancel it.
- It is waiting for the exclusive lock Session A is holding on that row.

</details>

<details>
<summary>Solution</summary>

**Session A:**

```sql
ROLLBACK TRANSACTION;
```

The instant Session A finishes, Session B's `SELECT` returns — with the true value, `ExerciseConc Base`. No lie this time, but Session B paid for it by waiting.

</details>

---

## Exercise 3 — Non-Repeatable Read [INTERMEDIATE]

**Session A** reads the tagged row twice inside one transaction. **Session B** updates it in between the two reads. Under `READ COMMITTED`, Session A's two reads disagree.

**Session A:**

```sql
BEGIN TRANSACTION;

SELECT IDState, Name
FROM dbo.State
WHERE Name LIKE N'ExerciseConc Base%';
-- Note the value. Keep this transaction open.
```

**Session B:**

```sql
UPDATE dbo.State
SET Name = N'ExerciseConc Base [CHANGED]'
WHERE Name = N'ExerciseConc Base';
```

<details>
<summary>Hint</summary>

- Session B's `UPDATE` should complete immediately — `READ COMMITTED` does not hold a lock past the instant of a `SELECT`.
- Re-run Session A's query a second time, in the same transaction, before committing.

</details>

<details>
<summary>Solution</summary>

**Session A:**

```sql
SELECT IDState, Name
FROM dbo.State
WHERE Name LIKE N'ExerciseConc Base%';
-- Now shows 'ExerciseConc Base [CHANGED]' — a different answer, same query, same transaction.

COMMIT TRANSACTION;
```

That is the non-repeatable read. Reset for the next exercise:

```sql
UPDATE dbo.State SET Name = N'ExerciseConc Base' WHERE Name = N'ExerciseConc Base [CHANGED]';
```

</details>

---

## Exercise 4 — Fixing It with REPEATABLE READ [INTERMEDIATE]

Repeat Exercise 3, but promote Session A to `REPEATABLE READ` first.

**Session A:**

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

BEGIN TRANSACTION;

SELECT IDState, Name
FROM dbo.State
WHERE Name LIKE N'ExerciseConc Base%';
-- Keep this transaction open.
```

**Session B:**

```sql
UPDATE dbo.State
SET Name = N'ExerciseConc Base [CHANGED]'
WHERE Name = N'ExerciseConc Base';
```

<details>
<summary>Hint</summary>

- Session B's `UPDATE` should **hang** this time.
- `REPEATABLE READ` holds its shared lock on a read row until the transaction ends, instead of releasing it immediately.

</details>

<details>
<summary>Solution</summary>

**Session A:**

```sql
SELECT IDState, Name
FROM dbo.State
WHERE Name LIKE N'ExerciseConc Base%';
-- Same value both times.

COMMIT TRANSACTION;
```

The moment Session A commits, Session B's `UPDATE` unblocks and completes. Reset both the data and the isolation level:

```sql
UPDATE dbo.State SET Name = N'ExerciseConc Base' WHERE Name = N'ExerciseConc Base [CHANGED]';
GO

SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

</details>

---

## Exercise 5 — Phantom Read [INTERMEDIATE]

**Session A** reads a range of rows twice inside one transaction. **Session B** inserts a new row that matches the range in between the two reads.

**Session A:**

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

BEGIN TRANSACTION;

SELECT IDState, Name
FROM dbo.State
WHERE Name LIKE N'ExerciseConc Range%';
-- 2 rows. Keep this transaction open.
```

**Session B:**

```sql
INSERT INTO dbo.State (Name) VALUES (N'ExerciseConc Range C');
```

<details>
<summary>Hint</summary>

- Session B's `INSERT` should complete immediately — `REPEATABLE READ` only locks rows it has already read, not rows that don't exist yet.
- Re-run Session A's range query a second time before committing.

</details>

<details>
<summary>Solution</summary>

**Session A:**

```sql
SELECT IDState, Name
FROM dbo.State
WHERE Name LIKE N'ExerciseConc Range%';
-- 3 rows now — ExerciseConc Range C is a phantom.

COMMIT TRANSACTION;
```

Clean up the phantom row:

```sql
DELETE FROM dbo.State WHERE Name = N'ExerciseConc Range C';
```

</details>

---

## Exercise 6 — Fixing It with SERIALIZABLE [ADVANCED]

Repeat Exercise 5, but promote Session A to `SERIALIZABLE` first.

**Session A:**

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

BEGIN TRANSACTION;

SELECT IDState, Name
FROM dbo.State
WHERE Name LIKE N'ExerciseConc Range%';
-- 2 rows. Keep this transaction open.
```

**Session B:**

```sql
INSERT INTO dbo.State (Name) VALUES (N'ExerciseConc Range C');
```

<details>
<summary>Hint</summary>

- Session B's `INSERT` should **hang** this time.
- `SERIALIZABLE` locks the whole range implied by the predicate, including the gap a new matching row would fall into.

</details>

<details>
<summary>Solution</summary>

**Session A:**

```sql
SELECT IDState, Name
FROM dbo.State
WHERE Name LIKE N'ExerciseConc Range%';
-- Still 2 rows.

COMMIT TRANSACTION;
```

Session B's `INSERT` unblocks and completes. Clean up and reset the isolation level:

```sql
DELETE FROM dbo.State WHERE Name = N'ExerciseConc Range C';
GO

SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

</details>

---

## Exercise 7 — A price nobody set [INTERMEDIATE]

The price-list report briefly showed product `707` (`Sport-100 Helmet, Red`, normally `34.99`) with a price of `0.01`. The product team says nobody ever saved that price: a colleague was testing an `UPDATE` inside a transaction and then rolled it back. The report runs at `READ UNCOMMITTED`, "so that it is never blocked".

1. Which concurrency problem is this?
2. Reproduce it with two sessions. Session A plays the colleague, Session B the report. The price must not change permanently.
3. Which is the **lowest** isolation level that prevents the problem, and which session has to use it? Show that it works.
4. What does the report pay for the fix?

<details>
<summary>Hint 1</summary>

Ask what the report saw: a value that was never committed, the same row with two different committed values, or a new row? Each answer points to one problem from Lab 10, Sections 2–4.

</details>

<details>
<summary>Hint 2</summary>

The problem is in what the report *reads*, so the fix belongs to the reading session. Lab 10, Section 5.1 lists which level prevents which problem.

</details>

<details>
<summary>Solution</summary>

1. A **dirty read**: the report read a change that was never committed.

2. and 3.

```sql
-- Problem

-- Session A (the colleague)
BEGIN TRANSACTION;

UPDATE dbo.Product
SET PriceWithoutVAT = 0.01
WHERE IDProduct = 707;
-- Keep the transaction open.

-- Session B (the report)
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SELECT IDProduct, Name, PriceWithoutVAT
FROM dbo.Product
WHERE IDProduct = 707;
-- 0.01: a price that was never committed

-- Session A
ROLLBACK TRANSACTION;
-- The price is 34.99 again.

-- Fix

-- Session A
BEGIN TRANSACTION;

UPDATE dbo.Product
SET PriceWithoutVAT = 0.01
WHERE IDProduct = 707;

-- Session B
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

SELECT IDProduct, Name, PriceWithoutVAT
FROM dbo.Product
WHERE IDProduct = 707;
-- Waits: Session A holds an exclusive lock on the row.

-- Session A
ROLLBACK TRANSACTION;
-- Session B now returns 34.99, the committed price.
```

The lowest level is `READ COMMITTED`, the SQL Server default, set in Session B. Session A does nothing wrong: it may change data and roll back.

4. The report can now wait while another session holds an uncommitted change. It no longer shows wrong prices, but it can be slower. [Lab 10, Additional Reading](../labs/lab10-concurrency.md#mvcc-an-alternative-to-locking) shows how row versioning removes that wait.

</details>

---

## Exercise 8 — The email changed in the middle of a job [INTERMEDIATE]

A mailing job works in one transaction: it reads a customer's email, sends the message, and then reads the email again to write it into the log. In the log, one customer has a different email from the one the message was sent to: the customer changed it on the website while the job was running. The job runs at `READ COMMITTED`.

1. Which concurrency problem is this?
2. Reproduce it with two sessions. So that no real customer is changed, use a test customer `ExerciseConc Customer` with the email `before@example.com`, and delete it at the end.
3. Which is the lowest isolation level that prevents the problem, and which session has to use it? Show that it works.
4. `SERIALIZABLE` would also prevent it. Why is it not the best choice here?

<details>
<summary>Hint 1</summary>

The job reads the **same row** twice, and both values it reads were committed. Which problem from Lab 10 is that?

</details>

<details>
<summary>Hint 2</summary>

The job needs the row to stay unchanged until its own transaction ends. Which level keeps the shared lock that long?

</details>

<details>
<summary>Solution</summary>

1. A **non-repeatable read**: the same row returns two different committed values within one transaction.

2. and 3.

```sql
-- Test data (either session)
INSERT INTO dbo.Customer (FirstName, LastName, Email)
VALUES (N'ExerciseConc', N'Customer', N'before@example.com');

-- Problem

-- Session A (the job)
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

BEGIN TRANSACTION;

SELECT Email
FROM dbo.Customer
WHERE FirstName = N'ExerciseConc';
-- before@example.com. Keep the transaction open.

-- Session B (the website)
UPDATE dbo.Customer
SET Email = N'after@example.com'
WHERE FirstName = N'ExerciseConc';
-- Runs immediately: READ COMMITTED releases the read lock after the SELECT.

-- Session A
SELECT Email
FROM dbo.Customer
WHERE FirstName = N'ExerciseConc';
-- after@example.com: the second read disagrees with the first

COMMIT TRANSACTION;

-- Fix

-- Session A
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

BEGIN TRANSACTION;

SELECT Email
FROM dbo.Customer
WHERE FirstName = N'ExerciseConc';
-- after@example.com

-- Session B
UPDATE dbo.Customer
SET Email = N'before@example.com'
WHERE FirstName = N'ExerciseConc';
-- Waits until Session A ends.

-- Session A
SELECT Email
FROM dbo.Customer
WHERE FirstName = N'ExerciseConc';
-- Still after@example.com: both reads agree.

COMMIT TRANSACTION;
-- Session B's UPDATE completes now.

SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- Clean up (either session)
DELETE FROM dbo.Customer
WHERE FirstName = N'ExerciseConc';
```

The lowest level is `REPEATABLE READ`, set in Session A, the session that reads twice.

4. `SERIALIZABLE` also locks ranges, so it would block inserts that have nothing to do with this customer as well. The job only needs the rows it has already read to stay unchanged; a higher level would only add waiting for other users (Lab 10, Section 5.2).

</details>

---

## Exercise 9 — The count does not match the list [ADVANCED]

A report for the `Accessories` category (`IDCategory = 4`) works in one transaction: it first prints how many subcategories the category has, then lists them. Once the count said `12`, but the list had `13` rows. Someone had already set the report to `REPEATABLE READ` "to be safe", and it still happened.

1. Which concurrency problem is this, and why did `REPEATABLE READ` not prevent it?
2. Reproduce it with two sessions. Delete the row you insert at the end.
3. Which isolation level prevents the problem, and in which session? Show that it works.

<details>
<summary>Hint 1</summary>

The 13th row in the list did not exist when the report counted. What does `REPEATABLE READ` lock, and what can it not lock?

</details>

<details>
<summary>Hint 2</summary>

The other session inserts a new subcategory into category `4` between the two reads (Lab 10, Section 4).

</details>

<details>
<summary>Solution</summary>

1. A **phantom read**: a new row appears in a range the transaction has already read. `REPEATABLE READ` locks only the rows it has read, so it cannot stop a new row from being inserted into the same range.

2. and 3.

```sql
-- Problem

-- Session A (the report)
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

BEGIN TRANSACTION;

SELECT COUNT(*) AS Subcategories
FROM dbo.Subcategory
WHERE CategoryID = 4;
-- 12. Keep the transaction open.

-- Session B
INSERT INTO dbo.Subcategory (CategoryID, Name)
VALUES (4, N'ExerciseConc Subcategory');
-- Runs immediately: no existing row it touches is locked.

-- Session A
SELECT IDSubcategory, Name
FROM dbo.Subcategory
WHERE CategoryID = 4;
-- 13 rows: the new subcategory is a phantom

COMMIT TRANSACTION;

-- Session B
DELETE FROM dbo.Subcategory
WHERE Name = N'ExerciseConc Subcategory';

-- Fix

-- Session A
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

BEGIN TRANSACTION;

SELECT COUNT(*) AS Subcategories
FROM dbo.Subcategory
WHERE CategoryID = 4;
-- 12

-- Session B
INSERT INTO dbo.Subcategory (CategoryID, Name)
VALUES (4, N'ExerciseConc Subcategory');
-- Waits until Session A ends.

-- Session A
SELECT IDSubcategory, Name
FROM dbo.Subcategory
WHERE CategoryID = 4;
-- Still 12 rows: the count and the list agree.

COMMIT TRANSACTION;
-- Session B's INSERT completes now.

SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- Session B: clean up
DELETE FROM dbo.Subcategory
WHERE Name = N'ExerciseConc Subcategory';
```

`SERIALIZABLE`, set in Session A, locks the whole range `CategoryID = 4`, including the place where a new row would go.

In all three exercises the fix goes to the session that **reads**: the reader decides how much it is protected from other sessions' changes.

</details>

---

# Part B – `TransactionsLab`

Exercises 10–14 use the `dbo.BankAccount` and `dbo.Branch` tables that [Lab 10](../labs/lab10-concurrency.md) prepares in the `TransactionsLab` database. Do them after Lab 10, in the same database. Exercises 11 and 13 need two SSMS windows; the others are questions you answer on paper and then check.

Use your two SSMS windows for every exercise below. Reset `AccountID = 1`'s values (`AccountName = 'Account A'`, `Balance = 1000.00`) and `dbo.Branch` to its three seed rows between exercises if a previous one changed them.

```sql
USE TransactionsLab;
GO
```

## Exercise 10 — Classify the anomaly [BEGINNER]

Read this transcript:

```
Session A: BEGIN TRAN; SELECT Balance FROM BankAccount WHERE AccountID = 1;  -- 1000.00
Session B: UPDATE BankAccount SET Balance = 1500.00 WHERE AccountID = 1; COMMIT;
Session A: SELECT Balance FROM BankAccount WHERE AccountID = 1;  -- 1500.00
Session A: COMMIT;
```

Which of the three concurrency problems does this show? Which isolation level would have prevented it?

<details>
<summary>Hint</summary>

- Compare the two `SELECT` results in Session A. Did a value change, or did a new row appear?

</details>

<details>
<summary>Solution</summary>

A non-repeatable read: Session A's `SELECT` returned two different values for the same row within one transaction. `REPEATABLE READ` (or stricter) would have blocked Session B's `UPDATE` until Session A finished.

</details>

---

## Exercise 11 — Predict the blocking [INTERMEDIATE]

Session A runs `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE; BEGIN TRAN; SELECT * FROM dbo.Branch WHERE BranchName LIKE N'West%';` and does not commit. Predict the outcome of each of these, run in Session B, **before** you test it:

1. `SELECT * FROM dbo.Branch WHERE BranchName = N'Central Osijek';`
2. `INSERT INTO dbo.Branch (BranchName) VALUES (N'West Pazin');`
3. `UPDATE dbo.Branch SET BranchName = N'Central Osijek 2' WHERE BranchName = N'Central Osijek';`

<details>
<summary>Hint</summary>

- `SERIALIZABLE` locks the rows Session A read **and** the ranges between them. Ask first how Session A's `SELECT` finds the `West%` rows: is there an index on `BranchName`, or does it read the whole table?

</details>

<details>
<summary>Solution</summary>

`dbo.Branch` has no index on `BranchName`, so Session A's `SELECT` scans the whole table. Under `SERIALIZABLE` it keeps a shared range lock on **every** row it scanned, not only on the two `West%` rows (Lab 10, Section 4.2).

1. Succeeds immediately — reading needs a shared lock, and shared locks are compatible.
2. Blocks — every range of the table is locked, so no new row can be inserted.
3. Blocks — the `UPDATE` needs an exclusive lock on the `Central Osijek` row, and Session A holds a shared lock on it, because its scan read that row too.

Finish by rolling back Session A: `ROLLBACK TRANSACTION;`.

</details>

---

## Exercise 12 — Fix a given anomaly [INTERMEDIATE]

A reporting procedure must read the total balance across all accounts twice in one transaction (for a before/after comparison) and must not see a different total the second time, even if another session commits a transfer in between. Which isolation level is the minimum sufficient choice, and why not a stricter one?

<details>
<summary>Hint</summary>

- First name the anomaly the procedure must avoid, then pick the weakest isolation level that prevents it.

</details>

<details>
<summary>Solution</summary>

`REPEATABLE READ`. The procedure only re-reads existing rows — it needs protection against a non-repeatable read, not against new rows appearing (no phantom risk, since it is not filtering a growing range). `SERIALIZABLE` would also work but costs more blocking for no extra benefit here.

</details>

---

## Exercise 13 — Trigger and explain a deadlock [ADVANCED]

Reproduce the deadlock from [Section 7.1 of Lab 10](../labs/lab10-concurrency.md#71-two-sessions-opposite-order), but swap the direction of the two transfers (Session A moves money from account 2 to account 1, Session B from account 1 to account 2). Confirm a deadlock still occurs, and explain in your own words why swapping the directions did not fix it.

<details>
<summary>Hint</summary>

- A deadlock needs two sessions that each hold one lock and wait for the other's. Look at the order in which each session takes its locks.

</details>

<details>
<summary>Solution</summary>

A deadlock still occurs. What matters is that the two sessions acquire the two locks in **opposite order relative to each other** — it does not matter which specific account each one starts with, only that A then wants what B holds and B then wants what A holds. The fix from [Section 7.2](../labs/lab10-concurrency.md#72-avoiding-deadlocks) (always touch accounts in the same, e.g. ascending, ID order, in every transaction) is still required.

</details>

---

## Exercise 14 — READ_COMMITTED_SNAPSHOT, costs and benefits [ADVANCED]

This exercise is based on [the Additional Reading of Lab 10](../labs/lab10-concurrency.md#mvcc-an-alternative-to-locking).

`READ_COMMITTED_SNAPSHOT` removes the blocking you saw in [Section 2.2 of Lab 10](../labs/lab10-concurrency.md#22-fix-read-committed-blocks-instead-of-lying). List one scenario where you would turn it on, and one reason a team might deliberately choose not to.

<details>
<summary>Hint</summary>

- Row versions are kept in `tempdb`. Think about who gains from readers not waiting for writers, and who pays for the versions.

</details>

<details>
<summary>Solution</summary>

Turn it on for a read-heavy application where long-running reports currently block, or get blocked by, ordinary transactional writes — the version-based reads stop that contention with no application code changes.

A team might avoid it if `tempdb` is already a bottleneck (it must hold every row version) or if write-heavy workloads cannot absorb the extra cost of maintaining versions on every write.

</details>

---

## References

- [Lab 10 – Concurrency and Isolation](../labs/lab10-concurrency.md) — dirty reads, non-repeatable reads, phantom reads, the four isolation levels, locking, deadlocks, and (in the additional reading) MVCC.
