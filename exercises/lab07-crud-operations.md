# Lab 07 – CRUD Operation Exercises

These exercises build on [Lab 07 – CRUD Operations](../labs/lab07-crud-operations.md). They progress from one procedure per operation to combined procedures, error handling, and operations that must also handle rows in related tables. They use only what Labs 03, 04 and 07 cover; transactions follow in Lab 9.

The exercises do not touch existing `AdventureWorksENG` data. They use three small tables created in the setup below: `Exercise_Student`, `Exercise_Course`, and `Exercise_Enrollment`. Every object created here starts with `Exercise_`, `usp_Exercises_`, or `fn_Exercises_` and is removed in the cleanup section.

## Setup

Run the setup once before the first exercise. It recreates the three exercise tables, so you can also run it again to start over with the original data.

```sql
USE AdventureWorksENG;
GO

DROP TABLE IF EXISTS dbo.Exercise_Enrollment;
DROP TABLE IF EXISTS dbo.Exercise_Student;
DROP TABLE IF EXISTS dbo.Exercise_Course;
GO

CREATE TABLE dbo.Exercise_Student
(
    IDStudent     int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Exercise_Student PRIMARY KEY,
    FirstName     nvarchar(50) NOT NULL,
    LastName      nvarchar(50) NOT NULL,
    StudentNumber char(10)     NOT NULL
        CONSTRAINT UQ_Exercise_Student_StudentNumber UNIQUE
);

CREATE TABLE dbo.Exercise_Course
(
    IDCourse int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Exercise_Course PRIMARY KEY,
    Code     nvarchar(10)  NOT NULL
        CONSTRAINT UQ_Exercise_Course_Code UNIQUE,
    Name     nvarchar(100) NOT NULL
);

CREATE TABLE dbo.Exercise_Enrollment
(
    IDEnrollment int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Exercise_Enrollment PRIMARY KEY,
    StudentID    int NOT NULL
        CONSTRAINT FK_Exercise_Enrollment_Student REFERENCES dbo.Exercise_Student (IDStudent),
    CourseID     int NOT NULL
        CONSTRAINT FK_Exercise_Enrollment_Course REFERENCES dbo.Exercise_Course (IDCourse),
    CONSTRAINT UQ_Exercise_Enrollment_StudentCourse UNIQUE (StudentID, CourseID)
);
GO

INSERT INTO dbo.Exercise_Student (FirstName, LastName, StudentNumber)
VALUES
    (N'Ana',   N'Anić',   '0036511111'),
    (N'Ivan',  N'Horvat', '0036522222'),
    (N'Marko', N'Kovač',  '0036533333'),
    (N'Petra', N'Babić',  '0036544444');

INSERT INTO dbo.Exercise_Course (Code, Name)
VALUES
    (N'DBD', N'Database Design'),
    (N'PRG', N'Programming'),
    (N'NET', N'Computer Networks');

INSERT INTO dbo.Exercise_Enrollment (StudentID, CourseID)
VALUES
    (1, 1),   -- Ana   – Database Design
    (1, 2),   -- Ana   – Programming
    (2, 1),   -- Ivan  – Database Design
    (4, 3);   -- Petra – Computer Networks
GO
```

After the setup, the data looks like this:

| IDStudent | Student | Enrollments |
| --- | --- | --- |
| 1 | Ana Anić | DBD, PRG |
| 2 | Ivan Horvat | DBD |
| 3 | Marko Kovač | – |
| 4 | Petra Babić | NET |

Exercises 1–6 work only on students they insert themselves, so the four students above stay unchanged until Exercise 7.

---

## Exercise 1 — One procedure per operation [BEGINNER]

Create four procedures for `Exercise_Student`, one for each CRUD operation:

| Procedure | Parameters | Behavior |
| --- | --- | --- |
| `dbo.usp_Exercises_InsertStudent` | `@FirstName`, `@LastName`, `@StudentNumber`, `@IDStudent OUTPUT` | Inserts a student and returns the new ID through `@IDStudent` |
| `dbo.usp_Exercises_GetStudent` | `@IDStudent` | Returns the student's row |
| `dbo.usp_Exercises_UpdateStudent` | `@IDStudent`, `@FirstName`, `@LastName`, `@StudentNumber` | Updates all columns; `RETURN 0` if the student was updated, `RETURN 1` if it does not exist |
| `dbo.usp_Exercises_DeleteStudent` | `@IDStudent` | Deletes the student; `RETURN 0` if it was deleted, `RETURN 1` if it does not exist |

Use the procedures to insert the student `Luka Perić` (`0036555555`), read it, change the last name to `Perić Horvat`, read it again, delete it, and read it once more. Finally, try to update a student with ID `999`.

<details>
<summary>Hint 1</summary>

Use `SCOPE_IDENTITY()` right after the `INSERT` to read the new identity value.

</details>

<details>
<summary>Hint 2</summary>

`@@ROWCOUNT` right after an `UPDATE` or `DELETE` tells you how many rows were affected. Zero rows means the student does not exist.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_InsertStudent
    @FirstName     nvarchar(50),
    @LastName      nvarchar(50),
    @StudentNumber char(10),
    @IDStudent     int OUTPUT
AS
BEGIN
    INSERT INTO dbo.Exercise_Student (FirstName, LastName, StudentNumber)
    VALUES (@FirstName, @LastName, @StudentNumber);

    SET @IDStudent = SCOPE_IDENTITY();
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Exercises_GetStudent
    @IDStudent int
AS
BEGIN
    SELECT IDStudent, FirstName, LastName, StudentNumber
    FROM dbo.Exercise_Student
    WHERE IDStudent = @IDStudent;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Exercises_UpdateStudent
    @IDStudent     int,
    @FirstName     nvarchar(50),
    @LastName      nvarchar(50),
    @StudentNumber char(10)
AS
BEGIN
    UPDATE dbo.Exercise_Student
    SET FirstName     = @FirstName,
        LastName      = @LastName,
        StudentNumber = @StudentNumber
    WHERE IDStudent = @IDStudent;

    IF @@ROWCOUNT = 0
        RETURN 1;   -- student does not exist

    RETURN 0;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Exercises_DeleteStudent
    @IDStudent int
AS
BEGIN
    DELETE FROM dbo.Exercise_Student
    WHERE IDStudent = @IDStudent;

    IF @@ROWCOUNT = 0
        RETURN 1;   -- student does not exist

    RETURN 0;
END;
GO
```

Test all four operations in one batch, so every call can use the ID returned by the insert:

```sql
DECLARE @ID int, @Result int;

EXEC dbo.usp_Exercises_InsertStudent
    @FirstName = N'Luka',
    @LastName = N'Perić',
    @StudentNumber = '0036555555',
    @IDStudent = @ID OUTPUT;

SELECT @ID AS NewStudentID;                       -- 5

EXEC dbo.usp_Exercises_GetStudent @IDStudent = @ID;

EXEC @Result = dbo.usp_Exercises_UpdateStudent
    @IDStudent = @ID,
    @FirstName = N'Luka',
    @LastName = N'Perić Horvat',
    @StudentNumber = '0036555555';
SELECT @Result AS UpdateResult;                   -- 0

EXEC dbo.usp_Exercises_GetStudent @IDStudent = @ID;

EXEC @Result = dbo.usp_Exercises_DeleteStudent @IDStudent = @ID;
SELECT @Result AS DeleteResult;                   -- 0

EXEC dbo.usp_Exercises_GetStudent @IDStudent = @ID;   -- empty result

EXEC @Result = dbo.usp_Exercises_UpdateStudent
    @IDStudent = 999,
    @FirstName = N'Nobody',
    @LastName = N'Nobody',
    @StudentNumber = '0000000000';
SELECT @Result AS UpdateMissingResult;            -- 1
GO
```

The `UPDATE` of student `999` is not an error: it simply affects zero rows. Without the `@@ROWCOUNT` check, the caller could not tell a successful update from an update of a missing student.

</details>

---

## Exercise 2 — Read through an inline table-valued function [BEGINNER]

Create an inline table-valued function `dbo.fn_Exercises_GetStudent` that takes `@IDStudent` and returns that student's `IDStudent`, `FirstName`, `LastName`, and `StudentNumber`.

Use the function to:

1. read student `1`;
2. list the courses of student `1` together with the student's name, by joining the function's result with `Exercise_Enrollment` and `Exercise_Course`.

<details>
<summary>Hint</summary>

An inline table-valued function has a `RETURNS TABLE` header and a single `RETURN (SELECT ...)`. It is used in the `FROM` clause like a table, so it can be joined.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER FUNCTION dbo.fn_Exercises_GetStudent (@IDStudent int)
RETURNS TABLE
AS
RETURN
(
    SELECT IDStudent, FirstName, LastName, StudentNumber
    FROM dbo.Exercise_Student
    WHERE IDStudent = @IDStudent
);
GO

-- 1. Read one student
SELECT *
FROM dbo.fn_Exercises_GetStudent(1);

-- 2. Use the function in a larger query
SELECT
    s.FirstName,
    s.LastName,
    c.Code,
    c.Name AS Course
FROM dbo.fn_Exercises_GetStudent(1) AS s
INNER JOIN dbo.Exercise_Enrollment AS e ON e.StudentID = s.IDStudent
INNER JOIN dbo.Exercise_Course AS c ON c.IDCourse = e.CourseID
ORDER BY c.Code;
GO
```

The second query returns two rows: Ana Anić with `DBD` and `PRG`.

A procedure such as `usp_Exercises_GetStudent` returns the same row, but its result cannot be joined or filtered further. That is the main reason to choose a function for the Read operation.

</details>

---

## Exercise 3 — Insert and update in one procedure [INTERMEDIATE]

Create `dbo.usp_Exercises_SaveStudent` that inserts **or** updates a student, depending on `@IDStudent`:

| `@IDStudent` | Behavior | Return value |
| --- | --- | --- |
| `NULL` | Insert a new student and return its ID through `@IDStudent` | `0` |
| Existing ID | Update that student | `0` |
| Nonexistent ID | Change nothing | `1` |

Test all three cases. Use the student `Mia Jurić` (`0036566666`) for the insert, then change her last name to `Jurić Kovač`.

<details>
<summary>Hint</summary>

`@IDStudent` is both an input and an `OUTPUT` parameter. Check `@IDStudent IS NULL` first; otherwise use `IF NOT EXISTS` to detect a nonexistent student before updating.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_SaveStudent
    @IDStudent     int OUTPUT,
    @FirstName     nvarchar(50),
    @LastName      nvarchar(50),
    @StudentNumber char(10)
AS
BEGIN
    IF @IDStudent IS NULL
    BEGIN
        INSERT INTO dbo.Exercise_Student (FirstName, LastName, StudentNumber)
        VALUES (@FirstName, @LastName, @StudentNumber);

        SET @IDStudent = SCOPE_IDENTITY();
        RETURN 0;
    END;

    IF NOT EXISTS (SELECT 1 FROM dbo.Exercise_Student WHERE IDStudent = @IDStudent)
        RETURN 1;   -- student does not exist

    UPDATE dbo.Exercise_Student
    SET FirstName     = @FirstName,
        LastName      = @LastName,
        StudentNumber = @StudentNumber
    WHERE IDStudent = @IDStudent;

    RETURN 0;
END;
GO

DECLARE @ID int = NULL, @Result int;

-- Insert
EXEC @Result = dbo.usp_Exercises_SaveStudent
    @IDStudent = @ID OUTPUT,
    @FirstName = N'Mia',
    @LastName = N'Jurić',
    @StudentNumber = '0036566666';
SELECT @Result AS Result, @ID AS IDStudent;       -- 0, new ID

-- Update the same student
EXEC @Result = dbo.usp_Exercises_SaveStudent
    @IDStudent = @ID OUTPUT,
    @FirstName = N'Mia',
    @LastName = N'Jurić Kovač',
    @StudentNumber = '0036566666';
SELECT @Result AS Result, @ID AS IDStudent;       -- 0, same ID

SELECT * FROM dbo.fn_Exercises_GetStudent(@ID);

-- Nonexistent student
DECLARE @Missing int = 999;
EXEC @Result = dbo.usp_Exercises_SaveStudent
    @IDStudent = @Missing OUTPUT,
    @FirstName = N'Nobody',
    @LastName = N'Nobody',
    @StudentNumber = '0000000000';
SELECT @Result AS Result;                         -- 1
GO
```

Note that the nonexistent ID does **not** become an insert. Treating an unknown ID as "insert a new row" would silently create a student with a different ID than the caller asked for.

</details>

---

## Exercise 4 — Find the bug [INTERMEDIATE]

A colleague wrote this procedure. It should update an existing student or insert a new one, and always return the student's ID through `@IDStudent`.

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_MergeStudent
    @IDStudent     int OUTPUT,
    @FirstName     nvarchar(50),
    @LastName      nvarchar(50),
    @StudentNumber char(10)
AS
IF EXISTS (SELECT * FROM dbo.Exercise_Student WHERE IDStudent = @IDStudent)
    UPDATE dbo.Exercise_Student
    SET FirstName = @FirstName, LastName = @LastName, StudentNumber = @StudentNumber
    WHERE IDStudent = @IDStudent
ELSE
    INSERT INTO dbo.Exercise_Student (FirstName, LastName, StudentNumber)
    VALUES (@FirstName, @LastName, @StudentNumber)
    SET @IDStudent = SCOPE_IDENTITY()
GO
```

Create the procedure and run this test:

```sql
DECLARE @ID int = NULL;

EXEC dbo.usp_Exercises_MergeStudent @ID OUTPUT, N'Nina', N'Lovrić', '0036577777';
SELECT @ID AS AfterInsert;

EXEC dbo.usp_Exercises_MergeStudent @ID OUTPUT, N'Nina', N'Lovrić Babić', '0036577777';
SELECT @ID AS AfterUpdate;
GO
```

1. Before running it, predict both values. Then run it and compare.
2. Explain what is wrong.
3. Fix the procedure.

<details>
<summary>Hint</summary>

Indentation means nothing to SQL Server. Without `BEGIN ... END`, how many statements does `ELSE` control?

</details>

<details>
<summary>Solution</summary>

`AfterInsert` is the new ID, as expected, but `AfterUpdate` is `NULL`.

`ELSE` controls only the next single statement, the `INSERT`. The `SET @IDStudent = SCOPE_IDENTITY()` line is **not** part of the `ELSE` branch, even though it is indented as if it were. It runs after every call, including the update.

During the update call, no row was inserted in the procedure's scope, so `SCOPE_IDENTITY()` returns `NULL`. The update itself succeeds, but the caller loses the student's ID.

The fix is to group the `INSERT` and the `SET` with `BEGIN ... END`:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_MergeStudent
    @IDStudent     int OUTPUT,
    @FirstName     nvarchar(50),
    @LastName      nvarchar(50),
    @StudentNumber char(10)
AS
BEGIN
    IF EXISTS (SELECT 1 FROM dbo.Exercise_Student WHERE IDStudent = @IDStudent)
    BEGIN
        UPDATE dbo.Exercise_Student
        SET FirstName = @FirstName, LastName = @LastName, StudentNumber = @StudentNumber
        WHERE IDStudent = @IDStudent;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.Exercise_Student (FirstName, LastName, StudentNumber)
        VALUES (@FirstName, @LastName, @StudentNumber);

        SET @IDStudent = SCOPE_IDENTITY();
    END;
END;
GO
```

Before running the test again, delete the student it created so the student number is free:

```sql
DELETE FROM dbo.Exercise_Student WHERE StudentNumber = '0036577777';
GO
```

Now both `AfterInsert` and `AfterUpdate` return the same ID.

Unlike `usp_Exercises_SaveStudent` in Exercise 3, this procedure turns an unknown ID into an insert. Compare the two designs: which one would you choose, and why?

</details>

---

## Exercise 5 — One procedure for several operations [INTERMEDIATE]

Create `dbo.usp_Exercises_ChangeStudent` that performs insert, update, or delete on `Exercise_Student`, chosen by an action parameter. Reading stays in `fn_Exercises_GetStudent` from Exercise 2.

| `@Action` | Operation |
| --- | --- |
| `'I'` | Insert; return the new ID through `@IDStudent` |
| `'U'` | Update the student with `@IDStudent` |
| `'D'` | Delete the student with `@IDStudent` |

Return values: `0` = success, `1` = student does not exist, `-1` = unknown action.

Only the parameters the action needs should be required: `@FirstName`, `@LastName`, and `@StudentNumber` should default to `NULL`.

Use the procedure and the function to insert `Tea Marić` (`0036588888`), read her, rename her to `Tea Marić Horvat`, read her again, delete her, and read her once more. Also call the procedure with action `'X'`.

<details>
<summary>Hint 1</summary>

Use `IF @Action = 'I' ... ELSE IF @Action = 'U' ... ELSE IF @Action = 'D' ...`, with a `BEGIN ... END` block for every branch that has more than one statement.

</details>

<details>
<summary>Hint 2</summary>

For update and delete, check `@@ROWCOUNT` right after the statement to detect a missing student.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_ChangeStudent
    @Action        char(1),
    @IDStudent     int OUTPUT,
    @FirstName     nvarchar(50) = NULL,
    @LastName      nvarchar(50) = NULL,
    @StudentNumber char(10)     = NULL
AS
BEGIN
    IF @Action = 'I'
    BEGIN
        INSERT INTO dbo.Exercise_Student (FirstName, LastName, StudentNumber)
        VALUES (@FirstName, @LastName, @StudentNumber);

        SET @IDStudent = SCOPE_IDENTITY();
        RETURN 0;
    END
    ELSE IF @Action = 'U'
    BEGIN
        UPDATE dbo.Exercise_Student
        SET FirstName     = @FirstName,
            LastName      = @LastName,
            StudentNumber = @StudentNumber
        WHERE IDStudent = @IDStudent;

        IF @@ROWCOUNT = 0 RETURN 1;
        RETURN 0;
    END
    ELSE IF @Action = 'D'
    BEGIN
        DELETE FROM dbo.Exercise_Student
        WHERE IDStudent = @IDStudent;

        IF @@ROWCOUNT = 0 RETURN 1;
        RETURN 0;
    END;

    RETURN -1;   -- unknown action
END;
GO

DECLARE @ID int, @Result int;

EXEC @Result = dbo.usp_Exercises_ChangeStudent 'I', @ID OUTPUT, N'Tea', N'Marić', '0036588888';
SELECT @Result AS InsertResult, @ID AS IDStudent;     -- 0, new ID
SELECT * FROM dbo.fn_Exercises_GetStudent(@ID);

EXEC @Result = dbo.usp_Exercises_ChangeStudent 'U', @ID OUTPUT, N'Tea', N'Marić Horvat', '0036588888';
SELECT @Result AS UpdateResult;                       -- 0
SELECT * FROM dbo.fn_Exercises_GetStudent(@ID);

EXEC @Result = dbo.usp_Exercises_ChangeStudent 'D', @ID OUTPUT;
SELECT @Result AS DeleteResult;                       -- 0
SELECT * FROM dbo.fn_Exercises_GetStudent(@ID);       -- empty

EXEC @Result = dbo.usp_Exercises_ChangeStudent 'X', @ID OUTPUT;
SELECT @Result AS UnknownActionResult;                -- -1
GO
```

The delete call passes only the action and the ID, because the other parameters have defaults. An update must still pass every column: this procedure has no way to tell "set this column to `NULL`" from "leave this column unchanged".

</details>

---

## Exercise 6 — Where to catch the error [INTERMEDIATE]

`StudentNumber` has a `UNIQUE` constraint, so inserting a second student with the same number fails.

**Part A.** Call `usp_Exercises_InsertStudent` from Exercise 1 with the existing student number `0036511111`. Catch the error **outside** the procedure and print the error number and message.

**Part B.** Create `dbo.usp_Exercises_InsertStudentSafe`, which has the same parameters but catches the error **inside**. It should return:

| Return value | Meaning |
| --- | --- |
| `0` | Student inserted |
| `2` | Student number already exists |
| `-1` | Any other error |

Call it with an existing and with a new student number (`0036599999`).

**Part C.** Compare the two approaches. Who decides what happens after the error in each case?

<details>
<summary>Hint</summary>

Inside `BEGIN CATCH`, `ERROR_NUMBER()` returns `2627` for a violated `PRIMARY KEY` or `UNIQUE` constraint (and `2601` for a duplicate in a unique index).

</details>

<details>
<summary>Solution</summary>

**Part A** – `TRY/CATCH` outside the procedure:

```sql
DECLARE @ID int;

BEGIN TRY
    EXEC dbo.usp_Exercises_InsertStudent
        @FirstName = N'Ana',
        @LastName = N'Duplicate',
        @StudentNumber = '0036511111',
        @IDStudent = @ID OUTPUT;

    PRINT 'Student inserted.';
END TRY
BEGIN CATCH
    PRINT 'Error number: ' + CAST(ERROR_NUMBER() AS nvarchar(10));
    PRINT 'Error message: ' + ERROR_MESSAGE();
END CATCH;
GO
```

The output shows error `2627` and a message about the violated `UQ_Exercise_Student_StudentNumber` constraint. `Student inserted.` is never printed: execution jumps to `CATCH` as soon as the error occurs.

**Part B** – `TRY/CATCH` inside the procedure:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_InsertStudentSafe
    @FirstName     nvarchar(50),
    @LastName      nvarchar(50),
    @StudentNumber char(10),
    @IDStudent     int OUTPUT
AS
BEGIN
    BEGIN TRY
        INSERT INTO dbo.Exercise_Student (FirstName, LastName, StudentNumber)
        VALUES (@FirstName, @LastName, @StudentNumber);

        SET @IDStudent = SCOPE_IDENTITY();
        RETURN 0;
    END TRY
    BEGIN CATCH
        SET @IDStudent = NULL;

        IF ERROR_NUMBER() IN (2627, 2601)
            RETURN 2;   -- student number already exists

        RETURN -1;      -- any other error
    END CATCH;
END;
GO

DECLARE @ID int, @Result int;

EXEC @Result = dbo.usp_Exercises_InsertStudentSafe
    N'Ana', N'Duplicate', '0036511111', @ID OUTPUT;
SELECT @Result AS Result, @ID AS IDStudent;       -- 2, NULL

EXEC @Result = dbo.usp_Exercises_InsertStudentSafe
    N'Lana', N'Novak', '0036599999', @ID OUTPUT;
SELECT @Result AS Result, @ID AS IDStudent;       -- 0, new ID
GO
```

The new student's ID is higher than you might expect: each failed `INSERT` still used up an identity value. Identity values are not guaranteed to be consecutive.

**Part C** – In Part A, the **caller** handles the error. Every caller has to write its own `TRY/CATCH` and understand SQL Server error numbers.

In Part B, the **procedure** handles the error and translates it into a simple, documented return value. Callers only check `0`, `2`, or `-1`. The cost is that the original error message is hidden from the caller, so the procedure should only translate errors it understands and report the rest as a general failure.

</details>

---

## Exercise 7 — Delete with related rows [ADVANCED]

A student who is enrolled in courses cannot be deleted directly: the foreign key from `Exercise_Enrollment` rejects the `DELETE`.

Create `dbo.usp_Exercises_DeleteStudentWithEnrollments` with these parameters:

- `@IDStudent int`
- `@DeleteEnrollments bit = 0`
- `@DeletedEnrollments int OUTPUT` – how many enrollments were deleted

Behavior:

| Situation | Behavior | Return value |
| --- | --- | --- |
| The student does not exist | Change nothing | `1` |
| The student has enrollments and `@DeleteEnrollments = 0` | Change nothing | `2` |
| Otherwise | Delete the student's enrollments (if any) and then the student | `0` |
| An error occurs | Catch it | `-1` |

Test the procedure in this order:

1. student `999`;
2. student `1` (Ana) without `@DeleteEnrollments`;
3. student `3` (Marko, no enrollments);
4. student `1` (Ana) with `@DeleteEnrollments = 1`.

<details>
<summary>Hint 1</summary>

Check both "does not exist" and "has enrollments" with `IF NOT EXISTS` / `IF EXISTS` before changing anything.

</details>

<details>
<summary>Hint 2</summary>

The order of the two `DELETE` statements matters. Which rows does the foreign key protect?

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_DeleteStudentWithEnrollments
    @IDStudent          int,
    @DeleteEnrollments  bit = 0,
    @DeletedEnrollments int OUTPUT
AS
BEGIN
    SET @DeletedEnrollments = 0;

    IF NOT EXISTS (SELECT 1 FROM dbo.Exercise_Student WHERE IDStudent = @IDStudent)
        RETURN 1;   -- student does not exist

    IF @DeleteEnrollments = 0
       AND EXISTS (SELECT 1 FROM dbo.Exercise_Enrollment WHERE StudentID = @IDStudent)
        RETURN 2;   -- student has enrollments

    BEGIN TRY
        DELETE FROM dbo.Exercise_Enrollment
        WHERE StudentID = @IDStudent;

        SET @DeletedEnrollments = @@ROWCOUNT;

        DELETE FROM dbo.Exercise_Student
        WHERE IDStudent = @IDStudent;

        RETURN 0;
    END TRY
    BEGIN CATCH
        RETURN -1;
    END CATCH;
END;
GO

DECLARE @Result int, @Deleted int;

EXEC @Result = dbo.usp_Exercises_DeleteStudentWithEnrollments
    @IDStudent = 999, @DeletedEnrollments = @Deleted OUTPUT;
SELECT 'Student 999' AS Test, @Result AS Result, @Deleted AS DeletedEnrollments;   -- 1, 0

EXEC @Result = dbo.usp_Exercises_DeleteStudentWithEnrollments
    @IDStudent = 1, @DeletedEnrollments = @Deleted OUTPUT;
SELECT 'Ana, keep enrollments' AS Test, @Result AS Result, @Deleted AS DeletedEnrollments;   -- 2, 0

EXEC @Result = dbo.usp_Exercises_DeleteStudentWithEnrollments
    @IDStudent = 3, @DeletedEnrollments = @Deleted OUTPUT;
SELECT 'Marko' AS Test, @Result AS Result, @Deleted AS DeletedEnrollments;   -- 0, 0

EXEC @Result = dbo.usp_Exercises_DeleteStudentWithEnrollments
    @IDStudent = 1, @DeleteEnrollments = 1, @DeletedEnrollments = @Deleted OUTPUT;
SELECT 'Ana, delete enrollments' AS Test, @Result AS Result, @Deleted AS DeletedEnrollments;   -- 0, 2

SELECT * FROM dbo.Exercise_Student WHERE IDStudent IN (1, 3);   -- empty
SELECT * FROM dbo.Exercise_Enrollment WHERE StudentID = 1;      -- empty
GO
```

The checks run before any `DELETE`, so the "does not exist" and "has enrollments" cases return without changing anything.

The deletion order matters: enrollments first, then the student. Deleting the student first would violate `FK_Exercise_Enrollment_Student`.

The `@DeleteEnrollments` flag makes deleting related rows an explicit decision of the caller. A procedure that always deleted them would make it too easy to remove a student's whole history by accident.

> [!NOTE]
> If the second `DELETE` failed, the first one would already have removed the enrollments: the student would remain, but without their enrollments. Making both deletions succeed or fail together requires a transaction, which [Lab 9 – Transactions](../labs/lab09-transactions.md) introduces.

</details>

---

## Exercise 8 — Insert with related rows [ADVANCED]

Create `dbo.usp_Exercises_EnrollStudent`, which enrolls a student in a course. The caller identifies both by their business keys, not by IDs:

- `@StudentNumber`, `@FirstName`, `@LastName`
- `@CourseCode`, `@CourseName`
- `@IDEnrollment int OUTPUT`

Behavior:

1. If the student and the course both exist and the student is already enrolled in the course, change nothing and `RETURN 2`.
2. If no student has `@StudentNumber`, insert a new student with `@FirstName` and `@LastName`. Otherwise use the existing student.
3. If no course has `@CourseCode`, insert a new course with `@CourseName`. Otherwise use the existing course.
4. Insert the enrollment, return its ID through `@IDEnrollment`, and `RETURN 0`.

If an error occurs, catch it and `RETURN -1`.

Test the procedure:

1. enroll the existing student Ivan Horvat (`0036522222`) in the existing course `PRG`;
2. enroll a new student, `Sara Vuković` (`0036500001`), in a new course, `SEC` – `Information Security`;
3. repeat test 2.

After the tests, list all enrollments with the student and course names.

<details>
<summary>Hint 1</summary>

First look up both IDs into variables. If both are found, check for an existing enrollment before inserting anything.

</details>

<details>
<summary>Hint 2</summary>

If a variable is still `NULL` after the lookup, insert the missing row and set the variable with `SCOPE_IDENTITY()`.

</details>

<details>
<summary>Solution</summary>

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Exercises_EnrollStudent
    @StudentNumber char(10),
    @FirstName     nvarchar(50),
    @LastName      nvarchar(50),
    @CourseCode    nvarchar(10),
    @CourseName    nvarchar(100),
    @IDEnrollment  int OUTPUT
AS
BEGIN
    DECLARE @IDStudent int, @IDCourse int;
    SET @IDEnrollment = NULL;

    -- 1. Look up the parents by their business keys
    SELECT @IDStudent = IDStudent
    FROM dbo.Exercise_Student
    WHERE StudentNumber = @StudentNumber;

    SELECT @IDCourse = IDCourse
    FROM dbo.Exercise_Course
    WHERE Code = @CourseCode;

    -- 2. Already enrolled? Check before inserting anything.
    IF EXISTS (SELECT 1 FROM dbo.Exercise_Enrollment
               WHERE StudentID = @IDStudent AND CourseID = @IDCourse)
        RETURN 2;

    BEGIN TRY
        -- 3. Create the missing parents
        IF @IDStudent IS NULL
        BEGIN
            INSERT INTO dbo.Exercise_Student (FirstName, LastName, StudentNumber)
            VALUES (@FirstName, @LastName, @StudentNumber);

            SET @IDStudent = SCOPE_IDENTITY();
        END;

        IF @IDCourse IS NULL
        BEGIN
            INSERT INTO dbo.Exercise_Course (Code, Name)
            VALUES (@CourseCode, @CourseName);

            SET @IDCourse = SCOPE_IDENTITY();
        END;

        -- 4. Enrollment
        INSERT INTO dbo.Exercise_Enrollment (StudentID, CourseID)
        VALUES (@IDStudent, @IDCourse);

        SET @IDEnrollment = SCOPE_IDENTITY();
        RETURN 0;
    END TRY
    BEGIN CATCH
        SET @IDEnrollment = NULL;
        RETURN -1;
    END CATCH;
END;
GO

DECLARE @Result int, @ID int;

-- 1. Existing student, existing course
EXEC @Result = dbo.usp_Exercises_EnrollStudent
    '0036522222', N'Ivan', N'Horvat', N'PRG', N'Programming', @ID OUTPUT;
SELECT 'Ivan - PRG' AS Test, @Result AS Result, @ID AS IDEnrollment;   -- 0, new ID

-- 2. New student, new course
EXEC @Result = dbo.usp_Exercises_EnrollStudent
    '0036500001', N'Sara', N'Vuković', N'SEC', N'Information Security', @ID OUTPUT;
SELECT 'Sara - SEC' AS Test, @Result AS Result, @ID AS IDEnrollment;   -- 0, new ID

-- 3. The same enrollment again
EXEC @Result = dbo.usp_Exercises_EnrollStudent
    '0036500001', N'Sara', N'Vuković', N'SEC', N'Information Security', @ID OUTPUT;
SELECT 'Sara - SEC again' AS Test, @Result AS Result, @ID AS IDEnrollment;   -- 2, NULL

SELECT s.FirstName, s.LastName, c.Code, c.Name AS Course
FROM dbo.Exercise_Enrollment AS e
INNER JOIN dbo.Exercise_Student AS s ON s.IDStudent = e.StudentID
INNER JOIN dbo.Exercise_Course AS c ON c.IDCourse = e.CourseID
ORDER BY s.LastName, c.Code;
GO
```

Test 2 inserts three rows: a student, a course, and an enrollment. The parents are inserted first, because the enrollment's foreign keys need their IDs.

The duplicate check runs before any `INSERT`. If either parent is missing, the student cannot already be enrolled: in that case one of the IDs is `NULL`, the `EXISTS` check finds nothing, and the procedure continues. Checking first means test 3 returns `2` without creating anything.

The parent rows are looked up by their business keys (`StudentNumber`, `Code`). These are the values a user actually knows. The `UNIQUE` constraints on those columns guarantee that each lookup finds at most one row.

> [!NOTE]
> If the enrollment `INSERT` failed after a new student or course had been inserted, those parent rows would stay in the database. Undoing all three inserts together requires a transaction, which [Lab 9 – Transactions](../labs/lab09-transactions.md) introduces.

</details>

---

## Cleanup

Remove all objects created by this collection:

```sql
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_InsertStudent;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_GetStudent;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_UpdateStudent;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_DeleteStudent;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_SaveStudent;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_MergeStudent;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_ChangeStudent;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_InsertStudentSafe;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_DeleteStudentWithEnrollments;
DROP PROCEDURE IF EXISTS dbo.usp_Exercises_EnrollStudent;
DROP FUNCTION IF EXISTS dbo.fn_Exercises_GetStudent;

DROP TABLE IF EXISTS dbo.Exercise_Enrollment;
DROP TABLE IF EXISTS dbo.Exercise_Student;
DROP TABLE IF EXISTS dbo.Exercise_Course;
GO
```

## References

- [Lab 07 – CRUD Operations](../labs/lab07-crud-operations.md)
- [Lab 03 – Stored Procedures](../labs/lab03-stored-procedures.md)
- [Lab 04 – Functions](../labs/lab04-functions.md)
- [TRY...CATCH (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/try-catch-transact-sql)
- [SCOPE_IDENTITY (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/functions/scope-identity-transact-sql)
- [@@ROWCOUNT (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/functions/rowcount-transact-sql)
