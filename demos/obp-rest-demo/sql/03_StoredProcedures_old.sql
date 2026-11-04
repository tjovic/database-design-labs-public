USE [OBPRestDemo]
GO

CREATE   PROCEDURE [dbo].[sp_UpdateInvoice]
(
    @InvoiceID int,

    @Json nvarchar(MAX)
)
AS
BEGIN

    SET NOCOUNT ON;

    UPDATE Invoice

    SET

        Date =
            JSON_VALUE(@Json,'$.date'),

        CustomerID =
            JSON_VALUE(@Json,'$.customerId')

    WHERE InvoiceID=@InvoiceID;

END;
GO


/******************************************************************************
    PROCEDURE: sp_AddInvoice

    Description:
        Inserts an invoice and all of its items.

    Input:
        JSON document.

******************************************************************************/

CREATE   PROCEDURE [dbo].[sp_AddInvoice]
(
    @Json nvarchar(MAX)
)
AS
BEGIN

    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY

        BEGIN TRANSACTION;

        -------------------------------------------------------
        -- Invoice header
        -------------------------------------------------------

        DECLARE @CustomerID int =
            JSON_VALUE(@Json,'$.customerId');

        DECLARE @Date date =
            JSON_VALUE(@Json,'$.date');

        DECLARE @NewInvoice TABLE
        (
            InvoiceID int
        );

        INSERT INTO Invoice
        (
            Date,
            CustomerID
        )

        OUTPUT INSERTED.InvoiceID
        INTO @NewInvoice

        VALUES
        (
            @Date,
            @CustomerID
        );

        -------------------------------------------------------
        -- Invoice items
        -------------------------------------------------------

        INSERT INTO InvoiceItem
        (
            InvoiceID,
            ProductID,
            Quantity,
            UnitPrice
        )

        SELECT

            r.InvoiceID,

            j.ProductID,

            j.Quantity,

            j.UnitPrice

        FROM @NewInvoice r

        CROSS APPLY OPENJSON(@Json,'$.items')

        WITH
        (
            ProductID int '$.productId',

            Quantity int '$.quantity',

            UnitPrice decimal(10,2)
                '$.unitPrice'
        ) j;

        COMMIT;

    END TRY

    BEGIN CATCH

        IF @@TRANCOUNT > 0
            ROLLBACK;

        THROW;

    END CATCH

END;
GO


/******************************************************************************
    PROCEDURE: sp_GetCustomers
******************************************************************************/

CREATE   PROCEDURE [dbo].[sp_GetCustomers]
AS
BEGIN

    SET NOCOUNT ON;

    SELECT

        CustomerID,

        FirstName,

        LastName,

        Email

    FROM Customer

    ORDER BY

        LastName,

        FirstName;

END;
GO


CREATE   PROCEDURE [dbo].[sp_GetInvoice]
(
    @InvoiceID INT
)
AS
BEGIN

    SET NOCOUNT ON;

    SELECT

        r.InvoiceID,
        r.Date,

        c.CustomerID,
        c.FirstName,
        c.LastName,
        c.Email,

        p.ProductID,
        p.Name,

        ii.Quantity,
        ii.UnitPrice

    FROM Invoice r

    INNER JOIN Customer c
        ON r.CustomerID = c.CustomerID

    INNER JOIN InvoiceItem ii
        ON r.InvoiceID = ii.InvoiceID

    INNER JOIN Product p
        ON ii.ProductID = p.ProductID

    WHERE r.InvoiceID = @InvoiceID;

END;
GO


CREATE   PROCEDURE [dbo].[sp_GetInvoices]
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        r.InvoiceID,
        r.Date,
        c.CustomerID,
        c.FirstName,
        c.LastName,
        SUM(ii.Quantity * ii.UnitPrice) AS Total
    FROM Invoice r
    INNER JOIN Customer c
        ON r.CustomerID = c.CustomerID
    INNER JOIN InvoiceItem ii
        ON r.InvoiceID = ii.InvoiceID
    GROUP BY
        r.InvoiceID,
        r.Date,
        c.CustomerID,
        c.FirstName,
        c.LastName
    ORDER BY
        r.InvoiceID DESC;
END;
GO



CREATE   PROCEDURE [dbo].[sp_DeleteInvoice]
(
    @InvoiceID int
)
AS
BEGIN

    SET NOCOUNT ON;

    DELETE
    FROM Invoice
    WHERE InvoiceID=@InvoiceID;

END;
GO
