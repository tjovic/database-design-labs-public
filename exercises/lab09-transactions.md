# Lab 09 – Transaction Exercises

**Databases:** `AdventureWorksENG` (Part A), `TransactionsLab` (Part B)

These exercises build on [Lab 9 – Transactions](../labs/lab09-transactions.md). **Part A** (Exercises 1–8) applies explicit transactions, savepoints, and transaction ownership between a caller and a procedure to real `AdventureWorksENG` tables. **Part B** (Exercises 9–13) continues in the lab's own `TransactionsLab` database, and Exercise 14 returns to `AdventureWorksENG` to add a transaction to the invoice procedure from Lab 8.

Part A inserts its own, clearly tagged rows; no existing `AdventureWorksENG` data is changed or removed. Unlike most other collections, each Part A solution ends with a short cleanup that deletes its test rows and procedure, because the exercises compare row counts and the next exercise expects to start from zero. Part B changes the fictional account balances and notes in `TransactionsLab`.

---

# Part A – `AdventureWorksENG`

## Exercise 1 — Commit or Cancel a Multi-Row Insert [BEGINNER]

Using `dbo.Customer`, insert three temporary customers tagged with a distinctive, exercise-only last name, once inside a transaction you cancel, and once inside a transaction you confirm.

1. Count existing rows with `LastName = 'ExerciseTxDemo'` (expect `0`).
2. Start a transaction and insert three customers with that last name.
3. Roll back. Confirm the count is `0` again.
4. Repeat the three inserts in a new transaction and commit.
5. Confirm the count is `3`, then clean up.

<details>
<summary>Hint</summary>

- `FirstName` and `LastName` are the only required columns; leave `CityID` and the other nullable columns out of the `INSERT` list.
- Query the count **inside** the transaction too, so you can see the rows exist there even before `COMMIT` confirms them.

</details>

<details>
<summary>Solution</summary>

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

<details>
<summary>Hint</summary>

- `SAVE TRANSACTION <name>` and `ROLLBACK TRANSACTION <name>` do not change `@@TRANCOUNT`. A full `ROLLBACK TRANSACTION` (no name) always resets it to `0`.
- A savepoint only protects earlier work from a **partial** rollback. It does not protect that work from a **full** rollback — see (b).
- Rolling back to an earlier savepoint discards any savepoint defined after it — see (d).

</details>

<details>
<summary>Solution</summary>

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

<details>
<summary>Hint</summary>

- `SCOPE_IDENTITY()` immediately after each `INSERT` gives you the new `IDState`.
- The procedure body is a single `DELETE` statement — no `BEGIN TRY`, no transaction commands.
- The caller uses the complete pattern from Lab 9, Section 3: `SET XACT_ABORT ON`, `ROLLBACK` in `CATCH`, then `THROW;`. The procedure never starts or ends a transaction — the caller's is the only one open.

</details>

<details>
<summary>Solution</summary>

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

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;
    EXEC dbo.usp_DeleteState @StateID = @ID1;
    EXEC dbo.usp_DeleteState @StateID = @ID2;
    EXEC dbo.usp_DeleteState @StateID = @ID3;
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;

SELECT COUNT(*) AS RemainingAfterSuccess
FROM dbo.State WHERE Name LIKE N'ExerciseTx State%'; -- 0
GO

-- The third delete hits a referenced state and fails
DECLARE @ID1 int, @ID2 int;

INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State D'); SET @ID1 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State E'); SET @ID2 = SCOPE_IDENTITY();

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;
    EXEC dbo.usp_DeleteState @StateID = @ID1;
    EXEC dbo.usp_DeleteState @StateID = @ID2;
    EXEC dbo.usp_DeleteState @StateID = 1; -- Croatia: referenced by City, delete fails
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW; -- the FK error is expected; THROW ends this batch
END CATCH;
GO

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

## Exercise 4 — Close down a country [INTERMEDIATE]

The company stops doing business in a country. Its row in `State` has to go, together with all its cities and all customers who live in those cities. Closing a country is one step of a larger operation, so the procedure must not confirm anything by itself: whoever calls it decides whether the whole operation is kept or cancelled.

Write `dbo.usp_DeleteStateWithCities` with one parameter, `@IDState`. If the state does not exist, it raises an error.

Then test it as the caller:

1. Create test data: two states, `'ExerciseTx Cascade A'` and `'ExerciseTx Cascade B'`, each with one city and one customer in that city.
2. Close both test states in one operation. Print `Success` if everything was saved, or `Failure:` and the error message if not.
3. Create a third test state, `'ExerciseTx Cascade C'`, with one city. Close state `C` and state `1` (`Croatia`) in one operation. What is printed, and does state `C` still exist?

<details>
<summary>Hint 1</summary>

Draw the chain of foreign keys first: `Customer → City → State`. The `DELETE` statements must run in the opposite direction.

</details>

<details>
<summary>Hint 2</summary>

Customers of a state are the customers whose `CityID` is in `(SELECT IDCity FROM City WHERE StateID = @IDState)`.

The caller uses the pattern from Exercise 3, but prints a message instead of rethrowing the error: `PRINT 'Success';` after `COMMIT`, and `PRINT 'Failure: ' + ERROR_MESSAGE();` after `ROLLBACK`.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_DeleteStateWithCities
    @IDState int
AS
BEGIN
    IF NOT EXISTS (SELECT 1 FROM dbo.State WHERE IDState = @IDState)
        THROW 50001, 'State does not exist.', 1;

    DELETE FROM dbo.Customer
    WHERE CityID IN
    (
        SELECT IDCity
        FROM dbo.City
        WHERE StateID = @IDState
    );

    DELETE FROM dbo.City
    WHERE StateID = @IDState;

    DELETE FROM dbo.State
    WHERE IDState = @IDState;
END;
GO

-- Test data: two states, each with one city and one customer
DECLARE @StateA int, @StateB int, @CityA int, @CityB int;

INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx Cascade A'); SET @StateA = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx Cascade B'); SET @StateB = SCOPE_IDENTITY();

INSERT INTO dbo.City (Name, StateID) VALUES (N'ExerciseTx City A', @StateA); SET @CityA = SCOPE_IDENTITY();
INSERT INTO dbo.City (Name, StateID) VALUES (N'ExerciseTx City B', @StateB); SET @CityB = SCOPE_IDENTITY();

INSERT INTO dbo.Customer (FirstName, LastName, CityID)
VALUES
    (N'Test', N'ExerciseTxCascade', @CityA),
    (N'Test', N'ExerciseTxCascade', @CityB);

-- 1. Both deletes succeed
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    EXEC dbo.usp_DeleteStateWithCities @IDState = @StateA;
    EXEC dbo.usp_DeleteStateWithCities @IDState = @StateB;

    COMMIT TRANSACTION;
    PRINT 'Success';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    PRINT 'Failure: ' + ERROR_MESSAGE();
END CATCH;
GO

-- 2. The second delete fails, so the first one is undone as well
DECLARE @StateC int;

INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx Cascade C'); SET @StateC = SCOPE_IDENTITY();
INSERT INTO dbo.City (Name, StateID) VALUES (N'ExerciseTx City C', @StateC);

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    EXEC dbo.usp_DeleteStateWithCities @IDState = @StateC;
    EXEC dbo.usp_DeleteStateWithCities @IDState = 1;   -- Croatia: its customers have invoices

    COMMIT TRANSACTION;
    PRINT 'Success';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    PRINT 'Failure: ' + ERROR_MESSAGE();
END CATCH;
GO

SELECT Name
FROM dbo.State
WHERE Name LIKE N'ExerciseTx Cascade%';   -- ExerciseTx Cascade C

-- Cleanup
DELETE FROM dbo.City WHERE Name LIKE N'ExerciseTx City%';
DELETE FROM dbo.State WHERE Name LIKE N'ExerciseTx%';
DROP PROCEDURE dbo.usp_DeleteStateWithCities;
```

Expected output: the first test prints `Success`. The second prints `Failure:` followed by the foreign key error on `FK_Invoice_Customer`: Croatia's customers have invoices, so they cannot be deleted. Because the caller rolls back the whole transaction, state `C` and its city are still there, even though the first call had already deleted them.

</details>

---

## Exercise 5 — A Procedure That Manages Its Own Transaction [INTERMEDIATE]

Write a procedure `dbo.usp_DeleteThreeStates` that takes three parameters (`@StateID1`, `@StateID2`, `@StateID3`), deletes all three states, and **owns its transaction**: it starts it, commits on success, and rolls back and reports failure on error.

1. Insert three new, unreferenced states and call the procedure with their IDs. Confirm all three are gone.
2. Insert two more new states. Call the procedure with their IDs plus state `1` (`Croatia`) as the third argument. Confirm the two new states survive.

<details>
<summary>Hint</summary>

- This is the same pattern as Lab 9's `usp_TransferFunds` (`SET XACT_ABORT ON`, `BEGIN TRY / BEGIN TRANSACTION ... COMMIT`, `CATCH` with `ROLLBACK` and `THROW;`), just with three `DELETE` statements instead of two `UPDATE` statements.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_DeleteThreeStates
    @StateID1 int,
    @StateID2 int,
    @StateID3 int
AS
BEGIN
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;
        DELETE FROM dbo.State WHERE IDState = @StateID1;
        DELETE FROM dbo.State WHERE IDState = @StateID2;
        DELETE FROM dbo.State WHERE IDState = @StateID3;
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
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
GO -- the FK error is expected; the procedure's THROW ends the batch above

SELECT COUNT(*) AS RemainingAfterFailure
FROM dbo.State WHERE Name LIKE N'ExerciseTx State%'; -- 2

-- Cleanup
DROP PROCEDURE dbo.usp_DeleteThreeStates;
DELETE FROM dbo.State WHERE Name LIKE N'ExerciseTx%';
```

</details>

---

## Exercise 6 — Extend a card, or say why not [INTERMEDIATE]

Support staff use a tool to extend a credit card's expiry by one year. Last week the tool reported success for a mistyped card ID, although nothing was changed. Write `dbo.usp_ExtendCardExpiry` with one parameter, `@IDCreditCard`, so that the tool reports success only if a card really was extended. The procedure is called on its own, so it must confirm or cancel its own work.

1. Insert one test credit card: type `Visa`, number `4111111111111111`, expiring `12/2030`.
2. Call the procedure with the test card's ID, then with ID `-1`. For each call, print `Success` or `Failure:` with the error message.
3. Check the test card's `ExpirationYear`.

<details>
<summary>Hint 1</summary>

Check `@@ROWCOUNT` right after the `UPDATE` (Lab 9, Section 4.2). Any statement in between resets it.

</details>

<details>
<summary>Hint 2</summary>

Inside the transaction: `UPDATE`, then `IF @@ROWCOUNT <> 1 THROW ...;`, then `COMMIT`. The `CATCH` block rolls back and rethrows, so the caller's own `CATCH` can print the message.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_ExtendCardExpiry
    @IDCreditCard int
AS
BEGIN
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        UPDATE dbo.CreditCard
        SET ExpirationYear = ExpirationYear + 1
        WHERE IDCreditCard = @IDCreditCard;

        IF @@ROWCOUNT <> 1
            THROW 50001, 'Credit card does not exist.', 1;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO

DECLARE @CardID int;

INSERT INTO dbo.CreditCard (Type, CardNumber, ExpirationMonth, ExpirationYear)
VALUES (N'Visa', N'4111111111111111', 12, 2030);

SET @CardID = SCOPE_IDENTITY();

-- Existing card
BEGIN TRY
    EXEC dbo.usp_ExtendCardExpiry @IDCreditCard = @CardID;
    PRINT 'Success';
END TRY
BEGIN CATCH
    PRINT 'Failure: ' + ERROR_MESSAGE();
END CATCH;

-- Card that does not exist
BEGIN TRY
    EXEC dbo.usp_ExtendCardExpiry @IDCreditCard = -1;
    PRINT 'Success';
END TRY
BEGIN CATCH
    PRINT 'Failure: ' + ERROR_MESSAGE();
END CATCH;

SELECT ExpirationMonth, ExpirationYear
FROM dbo.CreditCard
WHERE IDCreditCard = @CardID;   -- 12, 2031
GO

-- Cleanup
DELETE FROM dbo.CreditCard WHERE CardNumber = N'4111111111111111';
DROP PROCEDURE dbo.usp_ExtendCardExpiry;
```

Expected output: `Success`, then `Failure: Credit card does not exist.` The test card now expires in `2031`. Without the `@@ROWCOUNT` check, the second call would also print `Success`, even though it changed nothing.

</details>

---

## Exercise 7 — Merge two cities [ADVANCED]

The same city was entered twice, and customers are split between the two rows. Write `dbo.usp_MergeCities` with the parameters `@FromCityID`, `@ToCityID`, and `@MovedCustomers int OUTPUT`. It moves all customers from the first city to the second and then deletes the first city.

- Both steps happen, or neither does.
- The procedure fails and changes nothing if the two IDs are the same, if the target city does not exist, or if the city to delete does not exist.
- `@MovedCustomers` returns how many customers were moved.
- The procedure is called on its own, so it confirms or cancels its own work.

Test it:

1. Create a test state with two cities, `'ExerciseTx Town'` and `'ExerciseTx Town (duplicate)'`, and two customers in the duplicate.
2. Merge the duplicate into `'ExerciseTx Town'`.
3. Call the procedure again with the same IDs. The duplicate no longer exists.
4. For each call, print `Success` and the number of moved customers, or `Failure:` and the error message.

<details>
<summary>Hint 1</summary>

Which checks can you do before changing anything, and which result can you only see after a statement has run? A `DELETE` of a city that does not exist is not an error.

</details>

<details>
<summary>Hint 2</summary>

Check the two IDs and the target city with `IF` and `THROW` before the transaction starts. Inside the transaction, save `@@ROWCOUNT` right after the `UPDATE`, and check it again right after the `DELETE` (Lab 9, Section 4.2). Use the procedure pattern from Exercise 6.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_MergeCities
    @FromCityID     int,
    @ToCityID       int,
    @MovedCustomers int OUTPUT
AS
BEGIN
    SET XACT_ABORT ON;

    SET @MovedCustomers = 0;

    IF @FromCityID = @ToCityID
        THROW 50001, 'A city cannot be merged into itself.', 1;

    IF NOT EXISTS (SELECT 1 FROM dbo.City WHERE IDCity = @ToCityID)
        THROW 50002, 'Target city does not exist.', 1;

    BEGIN TRY
        BEGIN TRANSACTION;

        UPDATE dbo.Customer
        SET CityID = @ToCityID
        WHERE CityID = @FromCityID;

        SET @MovedCustomers = @@ROWCOUNT;

        DELETE FROM dbo.City
        WHERE IDCity = @FromCityID;

        IF @@ROWCOUNT <> 1
            THROW 50003, 'City to merge does not exist.', 1;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        SET @MovedCustomers = 0;
        THROW;
    END CATCH;
END;
GO

-- Test data
DECLARE @StateID int, @TownID int, @DuplicateID int, @Moved int;

INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx Merge State');
SET @StateID = SCOPE_IDENTITY();

INSERT INTO dbo.City (Name, StateID) VALUES (N'ExerciseTx Town', @StateID);
SET @TownID = SCOPE_IDENTITY();

INSERT INTO dbo.City (Name, StateID) VALUES (N'ExerciseTx Town (duplicate)', @StateID);
SET @DuplicateID = SCOPE_IDENTITY();

INSERT INTO dbo.Customer (FirstName, LastName, CityID)
VALUES
    (N'Test1', N'ExerciseTxMerge', @DuplicateID),
    (N'Test2', N'ExerciseTxMerge', @DuplicateID);

-- 1. Merge the duplicate
BEGIN TRY
    EXEC dbo.usp_MergeCities
        @FromCityID = @DuplicateID,
        @ToCityID = @TownID,
        @MovedCustomers = @Moved OUTPUT;

    PRINT 'Success: ' + CAST(@Moved AS nvarchar(10)) + ' customer(s) moved';
END TRY
BEGIN CATCH
    PRINT 'Failure: ' + ERROR_MESSAGE();
END CATCH;

-- 2. The duplicate is already gone
BEGIN TRY
    EXEC dbo.usp_MergeCities
        @FromCityID = @DuplicateID,
        @ToCityID = @TownID,
        @MovedCustomers = @Moved OUTPUT;

    PRINT 'Success: ' + CAST(@Moved AS nvarchar(10)) + ' customer(s) moved';
END TRY
BEGIN CATCH
    PRINT 'Failure: ' + ERROR_MESSAGE();
END CATCH;

SELECT c.FirstName, ci.Name AS City
FROM dbo.Customer AS c
JOIN dbo.City AS ci ON ci.IDCity = c.CityID
WHERE c.LastName = N'ExerciseTxMerge';
GO

-- Cleanup
DELETE FROM dbo.Customer WHERE LastName = N'ExerciseTxMerge';
DELETE FROM dbo.City WHERE Name LIKE N'ExerciseTx Town%';
DELETE FROM dbo.State WHERE Name = N'ExerciseTx Merge State';
DROP PROCEDURE dbo.usp_MergeCities;
```

Expected output: `Success: 2 customer(s) moved`, then `Failure: City to merge does not exist.` Both test customers now live in `ExerciseTx Town`.

The second call is the interesting one. Its `UPDATE` moves `0` customers and its `DELETE` deletes `0` cities, and neither is an SQL error. Only the `@@ROWCOUNT` check turns "nothing happened" into a failure the caller can see.

</details>

---

## Exercise 8 — An Outer Transaction Overrides an Inner Commit [ADVANCED]

Using `dbo.usp_DeleteThreeStates` from Exercise 5, wrap a call to it in an **outer** transaction that the caller then deliberately rolls back — even though the procedure itself reports success and runs its own `COMMIT`.

1. Recreate `dbo.usp_DeleteThreeStates` from Exercise 5; the solution of Exercise 5 drops it at the end.
2. Insert three new, unreferenced states.
3. Start an outer transaction, call `dbo.usp_DeleteThreeStates` with all three IDs, then issue a full `ROLLBACK TRANSACTION` in the caller — not because of an error, just because the caller decided to cancel.
4. Check `@@TRANCOUNT` right after the procedure call returns, and check the row count after the outer rollback.

Predict the outcome before running it: does the procedure's own `COMMIT` protect the deletions from the caller's rollback?

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_DeleteThreeStates
    @StateID1 int,
    @StateID2 int,
    @StateID3 int
AS
BEGIN
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;
        DELETE FROM dbo.State WHERE IDState = @StateID1;
        DELETE FROM dbo.State WHERE IDState = @StateID2;
        DELETE FROM dbo.State WHERE IDState = @StateID3;
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

DECLARE @ID1 int, @ID2 int, @ID3 int;
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State K'); SET @ID1 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State L'); SET @ID2 = SCOPE_IDENTITY();
INSERT INTO dbo.State (Name) VALUES (N'ExerciseTx State M'); SET @ID3 = SCOPE_IDENTITY();

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    EXEC dbo.usp_DeleteThreeStates @StateID1 = @ID1, @StateID2 = @ID2, @StateID3 = @ID3;

    SELECT @@TRANCOUNT AS AfterProcedureReturns; -- 1: the procedure's COMMIT only reduced 2 -> 1

    ROLLBACK TRANSACTION; -- the caller cancels on purpose
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;

SELECT COUNT(*) AS RemainingAfterOuterRollback
FROM dbo.State WHERE Name LIKE N'ExerciseTx State%'; -- 3: all three are back

SELECT @@TRANCOUNT AS FinalTranCount; -- 0

-- Cleanup
DROP PROCEDURE dbo.usp_DeleteThreeStates;
DELETE FROM dbo.State WHERE Name LIKE N'ExerciseTx%';
```

The procedure returned without an error and ran `COMMIT TRANSACTION`, but that commit only brought `@@TRANCOUNT` from `2` down to `1` — the caller's outer transaction was still open. The caller's own `ROLLBACK TRANSACTION` then undid all three deletes anyway. No individual `COMMIT` is final until the outermost one runs.

</details>

---

# Part B – `TransactionsLab`

Exercises 9–13 continue in the fictional `TransactionsLab` database from [Lab 9](../labs/lab09-transactions.md). They use the objects the lab creates: the `dbo.BankAccount` table (Section 1.1), the `dbo.Note` table (Section 7.1), and the `dbo.usp_TransferFunds` procedure (Section 5). Do them after Lab 9, in the same database.

> [!IMPORTANT]
> Start each exercise with `@@TRANCOUNT = 0`. Every transaction you start must end with `COMMIT` or a full `ROLLBACK`.

```sql
USE TransactionsLab;
GO
```

## Exercise 9 — Predict COMMIT and ROLLBACK [BEGINNER]

Reset the two balances to `1000.00` and `500.00`.

1. Start a transaction.
2. Transfer `150.00` from account 1 to account 2.
3. Display the balances inside the transaction.
4. Roll back and display the balances again.
5. Repeat the operation, this time committing it.

Predict the final balances before running the code.

<details>
<summary>Hint</summary>

- Run the two `UPDATE` statements between `BEGIN TRANSACTION` and `ROLLBACK TRANSACTION`, then repeat them with `COMMIT TRANSACTION`. Query the balances inside and after each transaction.

</details>

<details>
<summary>Solution</summary>

```sql
UPDATE dbo.BankAccount
SET Balance = 1000.00
WHERE AccountID = 1;

UPDATE dbo.BankAccount
SET Balance = 500.00
WHERE AccountID = 2;

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

## Exercise 10 — Keep one change, cancel another [INTERMEDIATE]

Using `dbo.Note` from [Section 7.1 of Lab 9](../labs/lab09-transactions.md#71-identity-values):

1. Start a transaction.
2. Insert the note `Exercise 10: keep this note`.
3. Create a savepoint.
4. Insert the note `Exercise 10: cancel this note`.
5. Roll back to the savepoint.
6. Commit the transaction.
7. Verify which note was kept and inspect `@@TRANCOUNT`.

<details>
<summary>Hint</summary>

- `SAVE TRANSACTION <name>` records a point inside the transaction; `ROLLBACK TRANSACTION <name>` undoes only the work after it. The transaction stays open until `COMMIT`.

</details>

<details>
<summary>Solution</summary>

```sql
BEGIN TRANSACTION;

INSERT INTO dbo.Note (NoteText)
VALUES (N'Exercise 10: keep this note');

SAVE TRANSACTION KeepFirstNote;

INSERT INTO dbo.Note (NoteText)
VALUES (N'Exercise 10: cancel this note');

ROLLBACK TRANSACTION KeepFirstNote;

SELECT @@TRANCOUNT AS BeforeCommit; -- 1

COMMIT TRANSACTION;

SELECT NoteID, NoteText
FROM dbo.Note
WHERE NoteText LIKE N'Exercise 10:%'
ORDER BY NoteID;

SELECT @@TRANCOUNT AS AfterCommit; -- 0
```

Only the first exercise note is stored. Repeating the exercise adds another copy of that note. Identity values may contain gaps.

</details>

---

## Exercise 11 — An unused savepoint [BEGINNER]

Using `dbo.Note`:

1. Start a transaction.
2. Insert the note `Exercise 11: first note`.
3. Create a savepoint.
4. Insert the note `Exercise 11: second note`.
5. Commit the transaction **without** rolling back to the savepoint.
6. Verify which notes were kept.

Predict the result before running the code: does creating a savepoint that is never rolled back to change anything?

<details>
<summary>Hint</summary>

- Ask what `COMMIT` confirms: everything done inside the transaction that was not rolled back.

</details>

<details>
<summary>Solution</summary>

```sql
BEGIN TRANSACTION;

INSERT INTO dbo.Note (NoteText)
VALUES (N'Exercise 11: first note');

SAVE TRANSACTION FirstNoteDone;

INSERT INTO dbo.Note (NoteText)
VALUES (N'Exercise 11: second note');

COMMIT TRANSACTION;

SELECT NoteID, NoteText
FROM dbo.Note
WHERE NoteText LIKE N'Exercise 11:%'
ORDER BY NoteID;

SELECT @@TRANCOUNT AS AfterCommit; -- 0
```

Both notes are stored. A savepoint that is never used in a `ROLLBACK TRANSACTION <savepoint>` has no effect at all — `SAVE TRANSACTION` only records a possible point to return to; it does not change what `COMMIT` confirms.

</details>

---

## Exercise 12 — Test the transfer procedure [INTERMEDIATE]

Reset balances to `1000.00` and `500.00`. Test `dbo.usp_TransferFunds` with:

1. a valid transfer of `250.00` from account 1 to account 2;
2. a transfer of `100.00` to account `999`;
3. a transfer of `5000.00` from account 1;
4. a transfer amount of `0.00`;
5. the same source and destination account.

Cases 1–3 repeat scenarios from [Sections 5.3–5.5 of Lab 9](../labs/lab09-transactions.md#53-test-a-successful-transfer) — write them **from memory**, without looking back, as a quick retrieval check. Cases 4 and 5 are new: Lab 9 never actually triggered errors `50011` or `50012`, so this is the first time you confirm they fire.

Verify the balances after the successful call, then after each expected-error call.

<details>
<summary>Hint</summary>

- An expected error ends its batch, so statements after it in the same batch do not run. Put each expected-error call in its own batch (end it with `GO`), and check the balances in the next batch.

</details>

<details>
<summary>Solution</summary>

Reset and run the successful test:

```sql
UPDATE dbo.BankAccount
SET Balance = 1000.00
WHERE AccountID = 1;

UPDATE dbo.BankAccount
SET Balance = 500.00
WHERE AccountID = 2;

EXEC dbo.usp_TransferFunds
    @SourceAccountID = 1,
    @DestinationAccountID = 2,
    @Amount = 250.00;

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;
```

Expected balances: `750.00` and `750.00`.

Then run the four expected-error tests. Each call is its own batch, followed by a batch that checks the balances:

```sql
-- Missing destination: expected error 50014.
EXEC dbo.usp_TransferFunds
    @SourceAccountID = 1,
    @DestinationAccountID = 999,
    @Amount = 100.00;
GO

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;
GO

-- Insufficient funds: expected error 50013.
EXEC dbo.usp_TransferFunds
    @SourceAccountID = 1,
    @DestinationAccountID = 2,
    @Amount = 5000.00;
GO

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;
GO

-- Invalid amount: expected error 50011.
EXEC dbo.usp_TransferFunds
    @SourceAccountID = 1,
    @DestinationAccountID = 2,
    @Amount = 0.00;
GO

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;
GO

-- Same account: expected error 50012.
EXEC dbo.usp_TransferFunds
    @SourceAccountID = 1,
    @DestinationAccountID = 1,
    @Amount = 100.00;
GO

SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;
GO
```

Each test raises its expected error, and the balances remain `750.00` and `750.00` after every one.

| Test | Account 1 | Account 2 | Expected error |
|---|---:|---:|---|
| Valid transfer | 750.00 | 750.00 | None |
| Missing destination | 750.00 | 750.00 | 50014 |
| Insufficient funds | 750.00 | 750.00 | 50013 |
| Zero amount | 750.00 | 750.00 | 50011 |
| Same account | 750.00 | 750.00 | 50012 |

</details>

---

## Exercise 13 — Add a transfer record [ADVANCED]

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

Create `dbo.usp_TransferFundsWithHistory` by adapting `dbo.usp_TransferFunds` from [Section 5 of Lab 9](../labs/lab09-transactions.md#section-5--a-complete-transfer-procedure).

Requirements:

- Keep the parameter validation and balance checks.
- Insert one history row after both account updates and before `COMMIT`.
- Make all three changes part of the same transaction.
- Test a successful transfer and a missing destination.
- Verify that a failed transfer creates no history row.

<details>
<summary>Hint</summary>

- Start from `dbo.usp_TransferFunds` and insert the history row after both `UPDATE` statements, inside the same `TRY` block and before `COMMIT`.

</details>

<details>
<summary>Solution</summary>

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
SET Balance = 1000.00
WHERE AccountID = 1;

UPDATE dbo.BankAccount
SET Balance = 500.00
WHERE AccountID = 2;

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
```

Balances become `900.00` and `600.00`, and the history has a new row for the `100.00` transfer.

Test failure:

```sql
EXEC dbo.usp_TransferFundsWithHistory
    @SourceAccountID = 1,
    @DestinationAccountID = 999,
    @Amount = 100.00;
```

Error `50014` is expected. Check the balances and the history:

```sql
SELECT AccountID, Balance
FROM dbo.BankAccount
ORDER BY AccountID;

SELECT TransferID, SourceAccountID, DestinationAccountID, Amount, CreatedAt
FROM dbo.TransferHistory
ORDER BY TransferID;
```

Balances remain `900.00` and `600.00`, and the history has no new row: the history insert was never reached, and the withdrawal was rolled back.

This demonstration intentionally resets balances between tests, so the history table is a record of procedure calls, not a complete ledger of all lab changes.

</details>

---

## Exercise 14 — Finish what Lab 8 started [INTERMEDIATE]

**Database:** `AdventureWorksENG`, with `dbo.usp_InvoiceInsertFromXml` from [Lab 8, Section 4.4](../labs/lab08-complex-parameters.md#44-inserting-a-parent-and-its-children).

Lab 8 ended Section 4.4 with a warning: if inserting the items fails, the invoice header remains in the database. Now you can fix that.

**(a) See the problem.** Call the Lab 8 procedure with an invoice whose third item refers to product `9999`, which does not exist. Predict what remains in the database, then check:

```sql
EXEC dbo.usp_InvoiceInsertFromXml
    @Invoice = N'
<Invoice CustomerID="5" InvoiceDate="2026-11-04" InvoiceNumber="SO-TX-001">
    <Lines>
        <Line ProductID="1" Quantity="2" UnitPrice="199.00" />
        <Line ProductID="2" Quantity="1" UnitPrice="49.90" />
        <Line ProductID="9999" Quantity="5" UnitPrice="9.99" />
    </Lines>
</Invoice>';
```

```sql
SELECT i.InvoiceNumber, COUNT(ii.IDInvoiceItem) AS Items
FROM Invoice AS i
LEFT JOIN InvoiceItem AS ii ON ii.InvoiceID = i.IDInvoice
WHERE i.InvoiceNumber LIKE N'SO-TX-%'
GROUP BY i.InvoiceNumber
ORDER BY i.InvoiceNumber;
```

**(b) Fix it.** Change `dbo.usp_InvoiceInsertFromXml` so that the header and all items are kept or undone together, and the caller still receives the error.

**(c) Test the fix.** Call the changed procedure twice: once with the same bad item (invoice `SO-TX-002`), and once with three valid items (invoice `SO-TX-003`, third product `3`). Run the check query again.

**(d)** Should the XML be read before the transaction starts, or inside it? And when the insert of `SO-TX-002` is rolled back, will the next invoice reuse its `IDInvoice`?

<details>
<summary>Hint</summary>

- (a) Each `INSERT` in the Lab 8 procedure is its own autocommit transaction (Lab 9, 1.5).
- (b) Use the complete pattern from Lab 9, Section 3: `SET XACT_ABORT ON`, `TRY/CATCH`, one transaction, `ROLLBACK` and `THROW;` in `CATCH`.
- (d) Lab 9, Section 7 is about what `ROLLBACK` does not undo.

</details>

<details>
<summary>Solution</summary>

**(a)** The procedure fails with error 547 (`FK_InvoiceItem_Product`), but the header stays:

| InvoiceNumber | Items |
|---|---:|
| SO-TX-001 | 0 |

The header `INSERT` succeeded and was committed on its own. The items `INSERT` failed as a whole, so even the two valid items were not inserted: one statement is already atomic. The result is an invoice without items.

**(b)**

```sql
CREATE OR ALTER PROCEDURE dbo.usp_InvoiceInsertFromXml
    @Invoice xml
AS
BEGIN
    SET XACT_ABORT ON; -- NEW

    BEGIN TRY
        BEGIN TRANSACTION; -- NEW: header and items together

        DECLARE @NewInvoiceID int;

        -- Insert the invoice header
        INSERT INTO Invoice (CustomerID, InvoiceDate, InvoiceNumber)
        SELECT
            tbl.col.value('@CustomerID', 'int'),
            tbl.col.value('@InvoiceDate', 'date'),
            tbl.col.value('@InvoiceNumber', 'nvarchar(20)')
        FROM @Invoice.nodes('/Invoice') AS tbl(col);

        -- Get the generated invoice ID
        SET @NewInvoiceID = SCOPE_IDENTITY();

        -- Insert all invoice items
        INSERT INTO InvoiceItem
        (
            InvoiceID,
            ProductID,
            Quantity,
            InitialPrice,
            Discount,
            TotalPrice
        )
        SELECT
            @NewInvoiceID,
            ProductID,
            Quantity,
            UnitPrice,
            0,
            Quantity * UnitPrice
        FROM
        (
            SELECT
                tbl.col.value('@ProductID', 'int') AS ProductID,
                tbl.col.value('@Quantity', 'int') AS Quantity,
                tbl.col.value('@UnitPrice', 'money') AS UnitPrice
            FROM @Invoice.nodes('/Invoice/Lines/Line') AS tbl(col)
        ) AS lines;

        COMMIT TRANSACTION; -- NEW
    END TRY
    BEGIN CATCH -- NEW
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO
```

The two `INSERT` statements are the same as in Lab 8; only the transaction pattern around them is new.

**(c)**

```sql
EXEC dbo.usp_InvoiceInsertFromXml
    @Invoice = N'
<Invoice CustomerID="5" InvoiceDate="2026-11-04" InvoiceNumber="SO-TX-002">
    <Lines>
        <Line ProductID="1" Quantity="2" UnitPrice="199.00" />
        <Line ProductID="2" Quantity="1" UnitPrice="49.90" />
        <Line ProductID="9999" Quantity="5" UnitPrice="9.99" />
    </Lines>
</Invoice>';
```

```sql
EXEC dbo.usp_InvoiceInsertFromXml
    @Invoice = N'
<Invoice CustomerID="5" InvoiceDate="2026-11-04" InvoiceNumber="SO-TX-003">
    <Lines>
        <Line ProductID="1" Quantity="2" UnitPrice="199.00" />
        <Line ProductID="2" Quantity="1" UnitPrice="49.90" />
        <Line ProductID="3" Quantity="5" UnitPrice="9.99" />
    </Lines>
</Invoice>';
```

The first call fails with error 547 again; the second succeeds. The check query now returns:

| InvoiceNumber | Items |
|---|---:|
| SO-TX-001 | 0 |
| SO-TX-003 | 3 |

`SO-TX-002` is gone completely: the rollback undid its header together with the failed items. `SO-TX-001` is still the leftover from (a).

**(d)** Reading the XML does not change the database, so it could happen before the transaction. Here it is part of the `INSERT ... SELECT` statements, which is fine: the transaction is short either way. The `IDInvoice` of `SO-TX-002` is **not** reused: a rollback does not return identity values (Lab 9, Section 7), so the invoice IDs have a gap.

Clean up the test rows:

```sql
DELETE ii
FROM InvoiceItem AS ii
JOIN Invoice AS i ON i.IDInvoice = ii.InvoiceID
WHERE i.InvoiceNumber LIKE N'SO-TX-%';

DELETE FROM Invoice
WHERE InvoiceNumber LIKE N'SO-TX-%';
```

</details>

---

# References

- [Lab 9 – Transactions](../labs/lab09-transactions.md) — `BEGIN/COMMIT/ROLLBACK`, savepoints, `@@TRANCOUNT`, and transaction ownership between a caller and a procedure.
