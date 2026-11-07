# Transaction Exercises

**Database:** `AdventureWorksENG`

These exercises extend the material from [Lab 9 – Transactions](../labs/lab09-transactions.md), which uses its own dedicated `TransactionsLab` database. Here, the same concepts — explicit transactions, savepoints, and transaction ownership between a caller and a procedure — are applied to real `AdventureWorksENG` tables.

All exercises insert their own, clearly tagged rows and delete only those rows during cleanup. No existing `AdventureWorksENG` data is changed or removed.

---

## Exercise 1 — Commit or Cancel a Multi-Row Insert [BEGINNER]

Using `dbo.Customer`, insert three temporary customers tagged with a distinctive, exercise-only last name, once inside a transaction you cancel, and once inside a transaction you confirm.

1. Count existing rows with `LastName = 'ExerciseTxDemo'` (expect `0`).
2. Start a transaction and insert three customers with that last name.
3. Roll back. Confirm the count is `0` again.
4. Repeat the three inserts in a new transaction and commit.
5. Confirm the count is `3`, then clean up.

### Hints

- `FirstName` and `LastName` are the only required columns; leave `CityID` and the other nullable columns out of the `INSERT` list.
- Query the count **inside** the transaction too, so you can see the rows exist there even before `COMMIT` confirms them.

<details>
<summary>Show solution</summary>

```sql
SELECT COUNT(*) AS BeforeAnything
FROM dbo.Customer
WHERE LastName = N'ExerciseTxDemo';

BEGIN TRANSACTION;

INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Mia', N'ExerciseTxDemo');
INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Noah', N'ExerciseTxDemo');
INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Olivia', N'ExerciseTxDemo');

SELECT COUNT(*) AS InsideTransaction
FROM dbo.Customer
WHERE LastName = N'ExerciseTxDemo';

ROLLBACK TRANSACTION;

SELECT COUNT(*) AS AfterRollback
FROM dbo.Customer
WHERE LastName = N'ExerciseTxDemo';

BEGIN TRANSACTION;

INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Mia', N'ExerciseTxDemo');
INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Noah', N'ExerciseTxDemo');
INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Olivia', N'ExerciseTxDemo');

COMMIT TRANSACTION;

SELECT COUNT(*) AS AfterCommit
FROM dbo.Customer
WHERE LastName = N'ExerciseTxDemo';

-- Cleanup
DELETE FROM dbo.Customer WHERE LastName = N'ExerciseTxDemo';
```

Expected results: `BeforeAnything = 0`, `InsideTransaction = 3`, `AfterRollback = 0`, `AfterCommit = 3`.

</details>

---

## Exercise 2 — Savepoints in Practice [INTERMEDIATE]

This is a staged exercise: run each part in order against `dbo.Customer`, tagging every row with `LastName = 'ExerciseTxSavepoint'`, and clean up between parts.

**(a) Rollback to a savepoint, then commit.** Insert `Keep1`, create a savepoint, insert `Cancel1`, roll back to the savepoint, then commit. Which row remains?

**(b) A full rollback instead.** Insert `Keep2`, create a savepoint, insert `Cancel2`, then issue a full `ROLLBACK TRANSACTION` (no savepoint name). How many rows remain, and why does this differ from (a)?

**(c) An unused savepoint.** Insert `Keep3`, create a savepoint, insert `Keep4`, then commit **without** rolling back to the savepoint at all. How many rows remain?

**(d) [ADVANCED] Two savepoints, then a cascade.** Insert `Keep5`, create savepoint `SP1`, insert `Cancel5a`, create savepoint `SP2`, insert `Cancel5b`. Roll back to `SP1`, then issue a full `ROLLBACK TRANSACTION`. At each stage, check the row count and `@@TRANCOUNT`. What happens if you try to roll back to `SP2` *after* already rolling back to `SP1`?

### Hints

- `SAVE TRANSACTION <name>` and `ROLLBACK TRANSACTION <name>` do not change `@@TRANCOUNT`. A full `ROLLBACK TRANSACTION` (no name) always resets it to `0`.
- A savepoint only protects earlier work from a **partial** rollback. It does not protect that work from a **full** rollback — see (b).
- Rolling back to an earlier savepoint discards any savepoint defined after it — see (d).

<details>
<summary>Show solution</summary>

**(a)**

```sql
BEGIN TRANSACTION;

INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Keep1', N'ExerciseTxSavepoint');
SAVE TRANSACTION AfterFirstBatch;
INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Cancel1', N'ExerciseTxSavepoint');

ROLLBACK TRANSACTION AfterFirstBatch;
COMMIT TRANSACTION;

SELECT FirstName
FROM dbo.Customer
WHERE LastName = N'ExerciseTxSavepoint'
ORDER BY FirstName;
-- Only 'Keep1' remains.

DELETE FROM dbo.Customer WHERE LastName = N'ExerciseTxSavepoint';
```

**(b)**

```sql
BEGIN TRANSACTION;

INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Keep2', N'ExerciseTxSavepoint');
SAVE TRANSACTION AfterFirstBatch;
INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Cancel2', N'ExerciseTxSavepoint');

ROLLBACK TRANSACTION;

SELECT COUNT(*) AS AfterFullRollback
FROM dbo.Customer
WHERE LastName = N'ExerciseTxSavepoint';
-- 0. The full rollback undid both inserts, including the one made before the savepoint.

DELETE FROM dbo.Customer WHERE LastName = N'ExerciseTxSavepoint';
```

**(c)**

```sql
BEGIN TRANSACTION;

INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Keep3', N'ExerciseTxSavepoint');
SAVE TRANSACTION Marker;
INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Keep4', N'ExerciseTxSavepoint');

COMMIT TRANSACTION;

SELECT COUNT(*) AS AfterUnusedSavepointCommit
FROM dbo.Customer
WHERE LastName = N'ExerciseTxSavepoint';
-- 2. A savepoint that is never used in a ROLLBACK has no effect at all.

DELETE FROM dbo.Customer WHERE LastName = N'ExerciseTxSavepoint';
```

**(d)**

```sql
BEGIN TRANSACTION;

INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Keep5', N'ExerciseTxSavepoint');
SAVE TRANSACTION SP1;
INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Cancel5a', N'ExerciseTxSavepoint');
SAVE TRANSACTION SP2;
INSERT INTO dbo.Customer (FirstName, LastName) VALUES (N'Cancel5b', N'ExerciseTxSavepoint');

SELECT COUNT(*) AS BeforeAnyRollback
FROM dbo.Customer WHERE LastName = N'ExerciseTxSavepoint'; -- 3

ROLLBACK TRANSACTION SP1;

SELECT COUNT(*) AS AfterSavepointRollback
FROM dbo.Customer WHERE LastName = N'ExerciseTxSavepoint'; -- 1 ('Keep5' only)

SELECT @@TRANCOUNT AS StillOpen; -- 1

ROLLBACK TRANSACTION;

SELECT COUNT(*) AS AfterFinalFullRollback
FROM dbo.Customer WHERE LastName = N'ExerciseTxSavepoint'; -- 0

SELECT @@TRANCOUNT AS FinalCount; -- 0

DELETE FROM dbo.Customer WHERE LastName = N'ExerciseTxSavepoint';
```

After `ROLLBACK TRANSACTION SP1`, the savepoint `SP2` no longer exists — running `ROLLBACK TRANSACTION SP2` at that point fails with an error, because it was defined after the point already rolled back to.

</details>

---

## Exercise 3 — A Procedure Without Its Own Transaction [INTERMEDIATE]

`dbo.State` is referenced by `dbo.City` through `FK_City_State`. Deleting a state that still has cities fails; deleting one that has none succeeds.

Write a procedure `dbo.usp_DeleteState` that takes one parameter, `@StateID`, and deletes that state. **The procedure must not manage its own transaction** — transaction ownership belongs to the caller.

1. Insert three new, unreferenced states (e.g. `'ExerciseTx State A'`, `'B'`, `'C'`) and capture their generated IDs.
2. In the caller, wrap three calls to `dbo.usp_DeleteState` in one transaction with `TRY/CATCH`, and commit on success.
3. Insert two more new states (`'D'`, `'E'`). Repeat the caller pattern, but this time delete `D`, then `E`, then state `1` (`Croatia` — referenced by existing cities).
4. What happened to `D` and `E` after the third call failed?

### Hints

- `SCOPE_IDENTITY()` immediately after each `INSERT` gives you the new `IDState`.
- The procedure body is a single `DELETE` statement — no `BEGIN TRY`, no transaction commands.
- The caller's `CATCH` block needs `IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;` because the procedure itself never started or ended a transaction — the caller's is the only one open.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_DeleteState
    @StateID int
AS
BEGIN
    DELETE FROM dbo.State WHERE IDState = @StateID;
END;
GO

-- Three deletes that all succeed
DECLARE @ID1 int, @ID2 int, @ID3 int;

INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State A'); SET @ID1 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State B'); SET @ID2 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State C'); SET @ID3 = SCOPE_IDENTITY();

BEGIN TRY
    BEGIN TRANSACTION;
    EXEC dbo.usp_DeleteState @StateID = @ID1;
    EXEC dbo.usp_DeleteState @StateID = @ID2;
    EXEC dbo.usp_DeleteState @StateID = @ID3;
    COMMIT TRANSACTION;
    PRINT 'Deletion succeeded';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    PRINT 'Deletion failed: ' + ERROR_MESSAGE();
END CATCH;

SELECT COUNT(*) AS RemainingAfterSuccess
FROM dbo.State WHERE Name LIKE N'ExerciseTx State%'; -- 0
GO

-- The third delete hits a referenced state and fails
DECLARE @ID1 int, @ID2 int;

INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State D'); SET @ID1 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State E'); SET @ID2 = SCOPE_IDENTITY();

BEGIN TRY
    BEGIN TRANSACTION;
    EXEC dbo.usp_DeleteState @StateID = @ID1;
    EXEC dbo.usp_DeleteState @StateID = @ID2;
    EXEC dbo.usp_DeleteState @StateID = 1; -- Croatia: referenced by City, delete fails
    COMMIT TRANSACTION;
    PRINT 'Deletion succeeded';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    PRINT 'Deletion failed: ' + ERROR_MESSAGE();
END CATCH;

SELECT COUNT(*) AS RemainingAfterFailure
FROM dbo.State WHERE Name LIKE N'ExerciseTx State%'; -- 2: D and E both survive

SELECT Name FROM dbo.State WHERE IDState = 1; -- Croatia, untouched

-- Cleanup
DROP PROCEDURE dbo.usp_DeleteState;
DELETE FROM dbo.State WHERE Name LIKE N'ExerciseTx%';
```

`D` and `E` were deleted first but the caller's rollback restored them, because `usp_DeleteState` never committed anything itself — the caller's transaction was the only one in control.

</details>

---

## Exercise 4 — A Procedure That Manages Its Own Transaction [INTERMEDIATE]

Write a procedure `dbo.usp_DeleteThreeStates` that takes three parameters (`@StateID1`, `@StateID2`, `@StateID3`), deletes all three states, and **owns its transaction**: it starts it, commits on success, and rolls back and reports failure on error.

1. Insert three new, unreferenced states and call the procedure with their IDs. Confirm all three are gone.
2. Insert two more new states. Call the procedure with their IDs plus state `1` (`Croatia`) as the third argument. Confirm the two new states survive.

### Hints

- This is the same `BEGIN TRY / BEGIN TRANSACTION ... COMMIT / CATCH / ROLLBACK` pattern as Lab 9's `usp_TransferFunds`, just with three `DELETE` statements instead of two `UPDATE` statements.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_DeleteThreeStates
    @StateID1 int,
    @StateID2 int,
    @StateID3 int
AS
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;
        DELETE FROM dbo.State WHERE IDState = @StateID1;
        DELETE FROM dbo.State WHERE IDState = @StateID2;
        DELETE FROM dbo.State WHERE IDState = @StateID3;
        COMMIT TRANSACTION;
        PRINT 'Deletion succeeded';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        PRINT 'Deletion failed: ' + ERROR_MESSAGE();
    END CATCH;
END;
GO

-- Success
DECLARE @ID1 int, @ID2 int, @ID3 int;
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State F'); SET @ID1 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State G'); SET @ID2 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State H'); SET @ID3 = SCOPE_IDENTITY();

EXEC dbo.usp_DeleteThreeStates @StateID1 = @ID1, @StateID2 = @ID2, @StateID3 = @ID3;

SELECT COUNT(*) AS RemainingAfterSuccess
FROM dbo.State WHERE Name LIKE N'ExerciseTx State%'; -- 0
GO

-- Failure: third ID is a referenced state
DECLARE @ID1 int, @ID2 int;
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State I'); SET @ID1 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State J'); SET @ID2 = SCOPE_IDENTITY();

EXEC dbo.usp_DeleteThreeStates @StateID1 = @ID1, @StateID2 = @ID2, @StateID3 = 1;

SELECT COUNT(*) AS RemainingAfterFailure
FROM dbo.State WHERE Name LIKE N'ExerciseTx State%'; -- 2

-- Cleanup
DROP PROCEDURE dbo.usp_DeleteThreeStates;
DELETE FROM dbo.State WHERE Name LIKE N'ExerciseTx%';
```

</details>

---

## Exercise 5 — An Outer Transaction Overrides an Inner Commit [ADVANCED]

Using `dbo.usp_DeleteThreeStates` from Exercise 4, wrap a call to it in an **outer** transaction that the caller then deliberately rolls back — even though the procedure itself reports success and runs its own `COMMIT`.

1. If you already ran Exercise 4's cleanup, recreate `dbo.usp_DeleteThreeStates` first.
2. Insert three new, unreferenced states.
3. Start an outer transaction, call `dbo.usp_DeleteThreeStates` with all three IDs, then issue a full `ROLLBACK TRANSACTION` in the caller — not because of an error, just because the caller decided to cancel.
4. Check `@@TRANCOUNT` right after the procedure call returns, and check the row count after the outer rollback.

Predict the outcome before running it: does the procedure's own `COMMIT` protect the deletions from the caller's rollback?

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_DeleteThreeStates
    @StateID1 int,
    @StateID2 int,
    @StateID3 int
AS
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;
        DELETE FROM dbo.State WHERE IDState = @StateID1;
        DELETE FROM dbo.State WHERE IDState = @StateID2;
        DELETE FROM dbo.State WHERE IDState = @StateID3;
        COMMIT TRANSACTION;
        PRINT 'Deletion succeeded';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        PRINT 'Deletion failed: ' + ERROR_MESSAGE();
    END CATCH;
END;
GO

DECLARE @ID1 int, @ID2 int, @ID3 int;
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State K'); SET @ID1 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State L'); SET @ID2 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State M'); SET @ID3 = SCOPE_IDENTITY();

BEGIN TRY
    BEGIN TRANSACTION;

    EXEC dbo.usp_DeleteThreeStates @StateID1 = @ID1, @StateID2 = @ID2, @StateID3 = @ID3;

    SELECT @@TRANCOUNT AS AfterProcedureReturns; -- 1: the procedure's COMMIT only reduced 2 -> 1

    ROLLBACK TRANSACTION;
    PRINT 'Outer transaction rolled back on purpose';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    PRINT 'Unexpected error: ' + ERROR_MESSAGE();
END CATCH;

SELECT COUNT(*) AS RemainingAfterOuterRollback
FROM dbo.State WHERE Name LIKE N'ExerciseTx State%'; -- 3: all three are back

SELECT @@TRANCOUNT AS FinalTranCount; -- 0

-- Cleanup
DROP PROCEDURE dbo.usp_DeleteThreeStates;
DELETE FROM dbo.State WHERE Name LIKE N'ExerciseTx%';
```

The procedure printed `'Deletion succeeded'` and ran `COMMIT TRANSACTION`, but that commit only brought `@@TRANCOUNT` from `2` down to `1` — the caller's outer transaction was still open. The caller's own `ROLLBACK TRANSACTION` then undid all three deletes anyway. No individual `COMMIT` is final until the outermost one runs.

</details>

---

# Cleanup

Each exercise's solution already cleans up its own rows and procedures; this is a safety net in case an exercise was interrupted partway through.

```sql
DROP PROCEDURE IF EXISTS dbo.usp_DeleteThreeStates;
DROP PROCEDURE IF EXISTS dbo.usp_DeleteState;
GO

DELETE FROM dbo.Customer WHERE LastName IN (N'ExerciseTxDemo', N'ExerciseTxSavepoint');
DELETE FROM dbo.State WHERE Name LIKE N'ExerciseTx%';
GO
```

---

# References

- [Lab 9 – Transactions](../labs/lab09-transactions.md) — `BEGIN/COMMIT/ROLLBACK`, savepoints, `@@TRANCOUNT`, and transaction ownership between a caller and a procedure.
- **Microsoft Learn**: [Transactions (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/transactions-transact-sql)
- **Microsoft Learn**: [SAVE TRANSACTION](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/save-transaction-transact-sql)
- **Microsoft Learn**: [@@TRANCOUNT](https://learn.microsoft.com/en-us/sql/t-sql/functions/trancount-transact-sql)
- **Microsoft Learn**: [TRY...CATCH](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/try-catch-transact-sql)
