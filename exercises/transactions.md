# Transaction Exercises

**Databases:** `AdventureWorksENG` (Part A), `TransactionsLab` (Part B)

These exercises build on [Lab 9 – Transactions](../labs/lab09-transactions.md). **Part A** (Exercises 1–5) applies explicit transactions, savepoints, and transaction ownership between a caller and a procedure to real `AdventureWorksENG` tables. **Part B** (Exercises 6–11) continues in the lab's own `TransactionsLab` database.

Part A inserts its own, clearly tagged rows and deletes only those rows during cleanup; no existing `AdventureWorksENG` data is changed or removed. Part B changes the fictional account balances and notes in `TransactionsLab`.

---

# Part A – `AdventureWorksENG`

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

# Part B – `TransactionsLab`

Exercises 6–11 continue in the fictional `TransactionsLab` database from [Lab 9](../labs/lab09-transactions.md). They use the objects the lab creates: the `dbo.BankAccount` table (Section 1.1), the `dbo.Note` table (Section 2.5), and the `dbo.usp_TransferFunds` procedure (Section 7). Do them after Lab 9, in the same database.

> [!IMPORTANT]
> Start each exercise with `@@TRANCOUNT = 0`. Every transaction you start must end with `COMMIT` or a full `ROLLBACK`.

```sql
USE TransactionsLab;
GO
```

## Exercise 6 — Predict COMMIT and ROLLBACK [BEGINNER]

Reset the two balances to `1000.00` and `500.00`.

1. Start a transaction.
2. Transfer `150.00` from account 1 to account 2.
3. Display the balances inside the transaction.
4. Roll back and display the balances again.
5. Repeat the operation, this time committing it.

Predict the final balances before running the code.

### Hints

- Run the two `UPDATE` statements between `BEGIN TRANSACTION` and `ROLLBACK TRANSACTION`, then repeat them with `COMMIT TRANSACTION`. Query the balances inside and after each transaction.

<details>
<summary>Show solution</summary>

```sql
UPDATE dbo.BankAccount
SET Balance = CASE AccountID
                  WHEN 1 THEN 1000.00
                  WHEN 2 THEN  500.00
              END;

BEGIN TRANSACTION;

UPDATE dbo.BankAccount
SET Balance = Balance - 150.00
WHERE AccountID = 1;

UPDATE dbo.BankAccount
SET Balance = Balance + 150.00
WHERE AccountID = 2;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

ROLLBACK TRANSACTION;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

BEGIN TRANSACTION;

UPDATE dbo.BankAccount
SET Balance = Balance - 150.00
WHERE AccountID = 1;

UPDATE dbo.BankAccount
SET Balance = Balance + 150.00
WHERE AccountID = 2;

COMMIT TRANSACTION;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

SELECT @@TRANCOUNT AS OpenTransactionCount;
```

After rollback: `1000.00` and `500.00`. After the committed transfer: `850.00` and `650.00`. The transaction count is `0`.

</details>

---

## Exercise 7 — Keep one change, cancel another [INTERMEDIATE]

Using `dbo.Note` from [Section 2.5 of Lab 9](../labs/lab09-transactions.md#25-rollback-and-identity-values):

1. Start a transaction.
2. Insert the note `Exercise 7: keep this note`.
3. Create a savepoint.
4. Insert the note `Exercise 7: cancel this note`.
5. Roll back to the savepoint.
6. Commit the transaction.
7. Verify which note was kept and inspect `@@TRANCOUNT`.

### Hints

- `SAVE TRANSACTION <name>` records a point inside the transaction; `ROLLBACK TRANSACTION <name>` undoes only the work after it. The transaction stays open until `COMMIT`.

<details>
<summary>Show solution</summary>

```sql
BEGIN TRANSACTION;

INSERT INTO dbo.Note (NoteText)
VALUES (N'Exercise 7: keep this note');

SAVE TRANSACTION KeepFirstNote;

INSERT INTO dbo.Note (NoteText)
VALUES (N'Exercise 7: cancel this note');

ROLLBACK TRANSACTION KeepFirstNote;

SELECT @@TRANCOUNT AS BeforeCommit; -- 1

COMMIT TRANSACTION;

SELECT NoteID, NoteText
FROM dbo.Note
WHERE NoteText LIKE N'Exercise 7:%'
ORDER BY NoteID;

SELECT @@TRANCOUNT AS AfterCommit; -- 0
```

Only the first exercise note is stored. Repeating the exercise adds another copy of that note. Identity values may contain gaps.

</details>

---

## Exercise 8 — An unused savepoint [BEGINNER]

Using `dbo.Note`:

1. Start a transaction.
2. Insert the note `Exercise 8: first note`.
3. Create a savepoint.
4. Insert the note `Exercise 8: second note`.
5. Commit the transaction **without** rolling back to the savepoint.
6. Verify which notes were kept.

Predict the result before running the code: does creating a savepoint that is never rolled back to change anything?

### Hints

- Ask what `COMMIT` confirms: everything done inside the transaction that was not rolled back.

<details>
<summary>Show solution</summary>

```sql
BEGIN TRANSACTION;

INSERT INTO dbo.Note (NoteText)
VALUES (N'Exercise 8: first note');

SAVE TRANSACTION FirstNoteDone;

INSERT INTO dbo.Note (NoteText)
VALUES (N'Exercise 8: second note');

COMMIT TRANSACTION;

SELECT NoteID, NoteText
FROM dbo.Note
WHERE NoteText LIKE N'Exercise 8:%'
ORDER BY NoteID;

SELECT @@TRANCOUNT AS AfterCommit; -- 0
```

Both notes are stored. A savepoint that is never used in a `ROLLBACK TRANSACTION <savepoint>` has no effect at all — `SAVE TRANSACTION` only records a possible point to return to; it does not change what `COMMIT` confirms.

</details>

---

## Exercise 9 — Test the transfer procedure [INTERMEDIATE]

Reset balances to `1000.00` and `500.00`. Test `dbo.usp_TransferFunds` with:

1. a valid transfer of `250.00` from account 1 to account 2;
2. a transfer of `100.00` to account `999`;
3. a transfer of `5000.00` from account 1;
4. a transfer amount of `0.00`;
5. the same source and destination account.

Cases 1–3 repeat scenarios from [Sections 7.3–7.5 of Lab 9](../labs/lab09-transactions.md#73-test-a-successful-transfer) — write them **from memory**, without looking back, as a quick retrieval check. Cases 4 and 5 are new: Lab 9 never actually triggered errors `50011` or `50012`, so this is the first time you confirm they fire.

Verify the balances and transaction count after the successful call, then after each expected-error call. Use a separate `TRY/CATCH` for each expected error so verification still runs.

### Hints

- Give each expected-error call its own `BEGIN TRY ... END TRY BEGIN CATCH ... END CATCH`, and check the balances and `@@TRANCOUNT` after every call.

<details>
<summary>Show solution</summary>

Reset and run the successful test:

```sql
UPDATE dbo.BankAccount
SET Balance = CASE AccountID
                  WHEN 1 THEN 1000.00
                  WHEN 2 THEN  500.00
              END;

EXEC dbo.usp_TransferFunds
    @SourceAccountID = 1,
    @DestinationAccountID = 2,
    @Amount = 250.00;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

SELECT @@TRANCOUNT AS OpenTransactionCount;
```

Use this block for the missing destination:

```sql
BEGIN TRY
    EXEC dbo.usp_TransferFunds
        @SourceAccountID = 1,
        @DestinationAccountID = 999,
        @Amount = 100.00;
END TRY
BEGIN CATCH
    SELECT ERROR_NUMBER() AS ErrorNumber,
           ERROR_MESSAGE() AS ErrorMessage;
END CATCH;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

SELECT @@TRANCOUNT AS OpenTransactionCount;
```

Repeat the same `TRY/CATCH` pattern, one call per test. Each call needs its **own** `TRY/CATCH` — an uncaught `THROW` ends the whole batch, so stacking bare `EXEC` calls without one each would skip the tests after the first failure. Run the balance and transaction-count `SELECT` statements after each call, as shown for the missing-destination case:

```sql
-- Insufficient funds.
BEGIN TRY
    EXEC dbo.usp_TransferFunds
        @SourceAccountID = 1,
        @DestinationAccountID = 2,
        @Amount = 5000.00;
END TRY
BEGIN CATCH
    SELECT ERROR_NUMBER() AS ErrorNumber,
           ERROR_MESSAGE() AS ErrorMessage;
END CATCH;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

SELECT @@TRANCOUNT AS OpenTransactionCount;

-- Invalid amount.
BEGIN TRY
    EXEC dbo.usp_TransferFunds
        @SourceAccountID = 1,
        @DestinationAccountID = 2,
        @Amount = 0.00;
END TRY
BEGIN CATCH
    SELECT ERROR_NUMBER() AS ErrorNumber,
           ERROR_MESSAGE() AS ErrorMessage;
END CATCH;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

SELECT @@TRANCOUNT AS OpenTransactionCount;

-- Same account.
BEGIN TRY
    EXEC dbo.usp_TransferFunds
        @SourceAccountID = 1,
        @DestinationAccountID = 1,
        @Amount = 100.00;
END TRY
BEGIN CATCH
    SELECT ERROR_NUMBER() AS ErrorNumber,
           ERROR_MESSAGE() AS ErrorMessage;
END CATCH;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

SELECT @@TRANCOUNT AS OpenTransactionCount;
```

Expected balances remain `750.00` and `750.00`, and `@@TRANCOUNT` remains `0` after each test.

| Test | Account 1 | Account 2 | Expected error | Final count |
|---|---:|---:|---|---:|
| Valid transfer | 750.00 | 750.00 | None | 0 |
| Missing destination | 750.00 | 750.00 | 50014 | 0 |
| Insufficient funds | 750.00 | 750.00 | 50013 | 0 |
| Zero amount | 750.00 | 750.00 | 50011 | 0 |
| Same account | 750.00 | 750.00 | 50012 | 0 |

</details>

---

## Exercise 10 — Add a transfer record [ADVANCED]

Extend the transfer operation so that it also stores a record of the successful transfer.

Create this table:

```sql
CREATE TABLE dbo.TransferHistory
(
    TransferID int IDENTITY(1, 1) NOT NULL
        CONSTRAINT PK_TransferHistory PRIMARY KEY,
    SourceAccountID int NOT NULL,
    DestinationAccountID int NOT NULL,
    Amount decimal(12, 2) NOT NULL,
    CreatedAt datetime2(0) NOT NULL
        CONSTRAINT DF_TransferHistory_CreatedAt
        DEFAULT SYSDATETIME(),
    CONSTRAINT FK_TransferHistory_Source
        FOREIGN KEY (SourceAccountID)
        REFERENCES dbo.BankAccount (AccountID),
    CONSTRAINT FK_TransferHistory_Destination
        FOREIGN KEY (DestinationAccountID)
        REFERENCES dbo.BankAccount (AccountID),
    CONSTRAINT CK_TransferHistory_Amount CHECK (Amount > 0),
    CONSTRAINT CK_TransferHistory_Accounts
        CHECK (SourceAccountID <> DestinationAccountID)
);
GO
```

Create `dbo.usp_TransferFundsWithHistory` by adapting `dbo.usp_TransferFunds` from [Section 7 of Lab 9](../labs/lab09-transactions.md#section-7--a-complete-transfer-procedure).

Requirements:

- Keep the parameter validation and balance checks.
- Insert one history row after both account updates and before `COMMIT`.
- Make all three changes part of the same transaction.
- Test a successful transfer and a missing destination.
- Verify that a failed transfer creates no history row.

### Hints

- Start from `dbo.usp_TransferFunds` and insert the history row after both `UPDATE` statements, inside the same `TRY` block and before `COMMIT`.

<details>
<summary>Show solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_TransferFundsWithHistory
    @SourceAccountID int,
    @DestinationAccountID int,
    @Amount decimal(12, 2)
AS
BEGIN
    SET XACT_ABORT ON;

    IF @SourceAccountID IS NULL
       OR @DestinationAccountID IS NULL
       OR @Amount IS NULL
        THROW 50010, 'Account IDs and amount are required.', 1;

    IF @Amount <= 0
        THROW 50011, 'Transfer amount must be greater than zero.', 1;

    IF @SourceAccountID = @DestinationAccountID
        THROW 50012, 'Source and destination accounts must be different.', 1;

    BEGIN TRY
        BEGIN TRANSACTION;

        UPDATE dbo.BankAccount
        SET Balance = Balance - @Amount
        WHERE AccountID = @SourceAccountID
          AND Balance >= @Amount;

        IF @@ROWCOUNT <> 1
            THROW 50013,
                'Source account does not exist or has insufficient funds.', 1;

        UPDATE dbo.BankAccount
        SET Balance = Balance + @Amount
        WHERE AccountID = @DestinationAccountID;

        IF @@ROWCOUNT <> 1
            THROW 50014, 'Destination account does not exist.', 1;

        INSERT INTO dbo.TransferHistory
            (SourceAccountID, DestinationAccountID, Amount)
        VALUES
            (@SourceAccountID, @DestinationAccountID, @Amount);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO
```

Test success:

```sql
UPDATE dbo.BankAccount
SET Balance = CASE AccountID
                  WHEN 1 THEN 1000.00
                  WHEN 2 THEN  500.00
              END;

SELECT COUNT(*) AS HistoryRowsBefore
FROM dbo.TransferHistory;

EXEC dbo.usp_TransferFundsWithHistory
    @SourceAccountID = 1,
    @DestinationAccountID = 2,
    @Amount = 100.00;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

SELECT TransferID, SourceAccountID, DestinationAccountID, Amount, CreatedAt
FROM dbo.TransferHistory
ORDER BY TransferID;

SELECT COUNT(*) AS HistoryRowsAfterSuccess
FROM dbo.TransferHistory;
```

Balances become `900.00` and `600.00`. The number of history rows increases by one.

Test failure:

```sql
DECLARE @HistoryRowsBefore int;

SELECT @HistoryRowsBefore = COUNT(*)
FROM dbo.TransferHistory;

BEGIN TRY
    EXEC dbo.usp_TransferFundsWithHistory
        @SourceAccountID = 1,
        @DestinationAccountID = 999,
        @Amount = 100.00;
END TRY
BEGIN CATCH
    SELECT ERROR_MESSAGE() AS ErrorMessage;
END CATCH;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

SELECT @HistoryRowsBefore AS HistoryRowsBeforeFailure,
       COUNT(*) AS HistoryRowsAfterFailure,
       @@TRANCOUNT AS OpenTransactionCount
FROM dbo.TransferHistory;
```

Balances remain `900.00` and `600.00`. The history count is unchanged, and the transaction count is `0`.

This demonstration intentionally resets balances between tests, so the history table is a record of procedure calls, not a complete ledger of all lab changes.

</details>

---

## Exercise 11 — Connect transactions to Lab 8 [INTERMEDIATE]

In Lab 8, one procedure inserted a parent row and related child rows from structured input.

Without changing its original code yet, explain:

1. Why does passing all input in one call not guarantee atomicity?
2. Where should `BEGIN TRANSACTION` and `COMMIT` go?
3. What should happen if inserting a child row fails after the parent was inserted?
4. Should JSON/XML parsing and basic input validation always happen inside the transaction?
5. If a generated parent identity is rolled back, must the next insert reuse it?

### Hints

- Think about which statements must succeed or fail together, and which work does not depend on the database at all.

<details>
<summary>Show solution</summary>

1. One call can contain several independently committed statements unless a transaction groups them.
2. The transaction must cover all related writes: the parent insert and all child inserts. Commit only after every required write and check succeeds.
3. The complete operation should be rolled back, including the parent insert.
4. Independent parsing and basic input validation can often be done before opening the transaction. Checks that depend on database state must be designed together with the writes and concurrency requirements.
5. No. Rolled-back inserts can consume identity values.

The following is a **structural outline**, not an executable replacement for a tested Lab 8 procedure:

```sql
-- Validate and parse the input where appropriate.

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Insert the parent.
    -- Capture its ID with SCOPE_IDENTITY() or OUTPUT INSERTED.
    -- Insert all children using that parent ID.
    -- Check any required business conditions.

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
```

Preserve the tested table names, column names, and insert logic from Lab 8 when applying this structure to that database.

</details>

---

# Cleanup

In Part A, each exercise's solution already cleans up its own rows and procedures; the first block is a safety net in case an exercise was interrupted partway through.

```sql
DROP PROCEDURE IF EXISTS dbo.usp_DeleteThreeStates;
DROP PROCEDURE IF EXISTS dbo.usp_DeleteState;
GO

DELETE FROM dbo.Customer WHERE LastName IN (N'ExerciseTxDemo', N'ExerciseTxSavepoint');
DELETE FROM dbo.State WHERE Name LIKE N'ExerciseTx%';
GO
```

For Part B, remove the objects created in Exercise 10. To reset the balances and notes as well, rerun the *Before you start* setup of Lab 9, which recreates `TransactionsLab`.

```sql
USE TransactionsLab;
GO
DROP PROCEDURE IF EXISTS dbo.usp_TransferFundsWithHistory;
DROP TABLE IF EXISTS dbo.TransferHistory;
GO
```

---

# References

- [Lab 9 – Transactions](../labs/lab09-transactions.md) — `BEGIN/COMMIT/ROLLBACK`, savepoints, `@@TRANCOUNT`, and transaction ownership between a caller and a procedure.
- **Microsoft Learn**: [Transactions (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/transactions-transact-sql)
- **Microsoft Learn**: [SAVE TRANSACTION](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/save-transaction-transact-sql)
- **Microsoft Learn**: [@@TRANCOUNT](https://learn.microsoft.com/en-us/sql/t-sql/functions/trancount-transact-sql)
- **Microsoft Learn**: [TRY...CATCH](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/try-catch-transact-sql)
