# Lab 10 – Concurrency Exercises

**Databases:** `AdventureWorksENG` (Part A), `TransactionsLab` (Part B)

These exercises build on [Lab 10 – Concurrency and Isolation](../labs/lab10-concurrency.md). **Part A** (Exercises 1–6) reproduces the three anomalies — dirty read, non-repeatable read, and phantom read — and their isolation-level fixes on real `AdventureWorksENG` tables, following the same two-session format Lab 10 uses. **Part B** (Exercises 7–11) continues in the lab's `TransactionsLab` database with blocking predictions, deadlocks, and `READ_COMMITTED_SNAPSHOT`.

Part A inserts its own, clearly tagged rows and deletes only those rows during cleanup; no existing `AdventureWorksENG` data is changed or removed. Part B changes only the fictional data in `TransactionsLab`.

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

# Part B – `TransactionsLab`

Exercises 7–11 use the `dbo.BankAccount` and `dbo.Branch` tables that [Lab 10](../labs/lab10-concurrency.md) prepares in the `TransactionsLab` database. Do them after Lab 10, in the same database. Exercises 8 and 10 need two SSMS windows; the others are questions you answer on paper and then check.

Use your two SSMS windows for every exercise below. Reset `AccountID = 1`'s values (`AccountName = 'Account A'`, `Balance = 1000.00`) and `dbo.Branch` to its three seed rows between exercises if a previous one changed them.

```sql
USE TransactionsLab;
GO
```

## Exercise 7 — Classify the anomaly [BEGINNER]

Read this transcript:

```
Session A: BEGIN TRAN; SELECT Balance FROM BankAccount WHERE AccountID = 1;  -- 1000.00
Session B: UPDATE BankAccount SET Balance = 1500.00 WHERE AccountID = 1; COMMIT;
Session A: SELECT Balance FROM BankAccount WHERE AccountID = 1;  -- 1500.00
Session A: COMMIT;
```

Which of the three concurrency problems does this show? Which isolation level would have prevented it?

### Hints

- Compare the two `SELECT` results in Session A. Did a value change, or did a new row appear?

<details>
<summary>Show solution</summary>

A non-repeatable read: Session A's `SELECT` returned two different values for the same row within one transaction. `REPEATABLE READ` (or stricter) would have blocked Session B's `UPDATE` until Session A finished.

</details>

---

## Exercise 8 — Predict the blocking [INTERMEDIATE]

Session A runs `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE; BEGIN TRAN; SELECT * FROM dbo.Branch WHERE BranchName LIKE N'West%';` and does not commit. Predict the outcome of each of these, run in Session B, **before** you test it:

1. `SELECT * FROM dbo.Branch WHERE BranchName = N'Central Osijek';`
2. `INSERT INTO dbo.Branch (BranchName) VALUES (N'West Pazin');`
3. `UPDATE dbo.Branch SET BranchName = N'Central Osijek 2' WHERE BranchName = N'Central Osijek';`

### Hints

- `SERIALIZABLE` locks the rows Session A read **and** the range its `WHERE` condition covers. Ask whether each Session B statement touches that range.

<details>
<summary>Show solution</summary>

1. Succeeds immediately — outside the locked range.
2. Blocks — falls inside the `West%` range Session A locked.
3. Succeeds immediately — `Central Osijek` was never read by Session A's query, so it holds no lock there.

Finish by rolling back Session A: `ROLLBACK TRANSACTION;`.

</details>

---

## Exercise 9 — Fix a given anomaly [INTERMEDIATE]

A reporting procedure must read the total balance across all accounts twice in one transaction (for a before/after comparison) and must not see a different total the second time, even if another session commits a transfer in between. Which isolation level is the minimum sufficient choice, and why not a stricter one?

### Hints

- First name the anomaly the procedure must avoid, then pick the weakest isolation level that prevents it.

<details>
<summary>Show solution</summary>

`REPEATABLE READ`. The procedure only re-reads existing rows — it needs protection against a non-repeatable read, not against new rows appearing (no phantom risk, since it is not filtering a growing range). `SERIALIZABLE` would also work but costs more blocking for no extra benefit here.

</details>

---

## Exercise 10 — Trigger and explain a deadlock [ADVANCED]

Reproduce the deadlock from [Section 8.1 of Lab 10](../labs/lab10-concurrency.md#81-two-sessions-opposite-order), but swap which account each session updates first (Session A starts with account 2, Session B starts with account 1). Confirm a deadlock still occurs, and explain in your own words why swapping the starting account did not fix it.

### Hints

- A deadlock needs two sessions that each hold one lock and wait for the other's. Look at the order in which each session takes its locks.

<details>
<summary>Show solution</summary>

A deadlock still occurs. What matters is that the two sessions acquire the two locks in **opposite order relative to each other** — it does not matter which specific account each one starts with, only that A then wants what B holds and B then wants what A holds. The fix from [Section 8.2](../labs/lab10-concurrency.md#82-avoiding-deadlocks) (always touch accounts in the same, e.g. ascending, ID order, in every transaction) is still required.

</details>

---

## Exercise 11 — READ_COMMITTED_SNAPSHOT, costs and benefits [INTERMEDIATE]

`READ_COMMITTED_SNAPSHOT` removes the blocking you saw in [Section 2.2 of Lab 10](../labs/lab10-concurrency.md#22-fix-read-committed-blocks-instead-of-lying). List one scenario where you would turn it on, and one reason a team might deliberately choose not to.

### Hints

- Row versions are kept in `tempdb`. Think about who gains from readers not waiting for writers, and who pays for the versions.

<details>
<summary>Show solution</summary>

Turn it on for a read-heavy application where long-running reports currently block, or get blocked by, ordinary transactional writes — the version-based reads stop that contention with no application code changes.

A team might avoid it if `tempdb` is already a bottleneck (it must hold every row version) or if write-heavy workloads cannot absorb the extra cost of maintaining versions on every write.

</details>

---

## Cleanup

In Part A, each exercise's solution already cleans up the rows it changed; this is a safety net in case an exercise was interrupted partway through.

```sql
DELETE FROM dbo.State WHERE Name LIKE N'ExerciseConc%';
```

Part B needs no cleanup beyond the resets described in its introduction. To start over completely, rerun the *Before you start* setup of Lab 10.

---

## References

- [Lab 10 – Concurrency and Isolation](../labs/lab10-concurrency.md) — dirty reads, non-repeatable reads, phantom reads, the four isolation levels, locking, and MVCC.
- **Microsoft Learn**: [SET TRANSACTION ISOLATION LEVEL](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql)
- **Microsoft Learn**: [Transaction Locking and Row Versioning Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide)
