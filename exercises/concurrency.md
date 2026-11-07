# Concurrency Exercises

**Database:** `AdventureWorksENG`

These exercises extend the material from [Lab 10 – Concurrency and Isolation](../labs/lab10-concurrency.md), which uses its own dedicated `TransactionsLab` database. Here, the same three anomalies — dirty read, non-repeatable read, and phantom read — and their isolation-level fixes are reproduced against real `AdventureWorksENG` tables, following the same two-session format Lab 10 uses.

All exercises insert their own, clearly tagged rows and delete only those rows during cleanup. No existing `AdventureWorksENG` data is changed or removed.

> [!NOTE]
> Every exercise below needs **two SSMS query windows**, both connected to `AdventureWorksENG` — exactly as in Lab 10. Label them **Session A** and **Session B** before starting.

---

## Setup — Shared by All Exercises

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

### Hints

- Session B's `SELECT` should return immediately with `ExerciseConc Base [DIRTY]`, even though Session A never confirmed that change.
- After Session A rolls back, re-run Session B's query (still at `READ UNCOMMITTED`) and compare.

<details>
<summary>Show solution</summary>

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

### Hints

- Session B's query should **hang** this time — do not cancel it.
- It is waiting for the exclusive lock Session A is holding on that row.

<details>
<summary>Show solution</summary>

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

### Hints

- Session B's `UPDATE` should complete immediately — `READ COMMITTED` does not hold a lock past the instant of a `SELECT`.
- Re-run Session A's query a second time, in the same transaction, before committing.

<details>
<summary>Show solution</summary>

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

### Hints

- Session B's `UPDATE` should **hang** this time.
- `REPEATABLE READ` holds its shared lock on a read row until the transaction ends, instead of releasing it immediately.

<details>
<summary>Show solution</summary>

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

### Hints

- Session B's `INSERT` should complete immediately — `REPEATABLE READ` only locks rows it has already read, not rows that don't exist yet.
- Re-run Session A's range query a second time before committing.

<details>
<summary>Show solution</summary>

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

### Hints

- Session B's `INSERT` should **hang** this time.
- `SERIALIZABLE` locks the whole range implied by the predicate, including the gap a new matching row would fall into.

<details>
<summary>Show solution</summary>

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

## Cleanup

Each exercise's solution already cleans up the rows it changed; this is a safety net in case an exercise was interrupted partway through.

```sql
DELETE FROM dbo.State WHERE Name LIKE N'ExerciseConc%';
```

---

## References

- [Lab 10 – Concurrency and Isolation](../labs/lab10-concurrency.md) — dirty reads, non-repeatable reads, phantom reads, the four isolation levels, locking, and MVCC.
- **Microsoft Learn**: [SET TRANSACTION ISOLATION LEVEL](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql)
- **Microsoft Learn**: [Transaction Locking and Row Versioning Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide)
