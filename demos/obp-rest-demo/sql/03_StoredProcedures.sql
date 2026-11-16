USE [OBPRestDemo]
GO

/******************************************************************************
    PROCEDURE: usp_UpdateInvoice

    Description:
        Updates the invoice header: date and customer.
        Note: the "items" array in the JSON is ignored - invoice items
        are not changed.

    Called by:
        PUT /invoices/{id}
        api/routes.py -> update_invoice()

    Input:
        @InvoiceID  ID of the invoice to update
        @Json       invoice as JSON (same shape as usp_AddInvoice)

    Output:
        none
******************************************************************************/

CREATE PROCEDURE [dbo].[usp_UpdateInvoice]
    @InvoiceID INT,
    @Json NVARCHAR (MAX)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Invoice
    SET    Date       = JSON_VALUE(@Json, '$.date'),
           CustomerID = JSON_VALUE(@Json, '$.customerId')
    WHERE  InvoiceID = @InvoiceID;
END
GO


/******************************************************************************
    PROCEDURE: usp_AddInvoice

    Description:
        Inserts an invoice header and all of its items in one transaction.
        The JSON is shredded with JSON_VALUE (header) and OPENJSON (items).
        If any insert fails, nothing is saved (ROLLBACK).

    Called by:
        POST /invoices
        api/routes.py -> add_invoice()

    Input:
        @Json  invoice as JSON, for example:
          {
            "customerId": 1,
            "date": "2025-06-15",
            "items": [
              { "productId": 2, "quantity": 1, "unitPrice": 109.00 }
            ]
          }

    Output:
        none
******************************************************************************/

CREATE OR ALTER PROCEDURE [dbo].[usp_AddInvoice]
    @Json NVARCHAR (MAX)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        -------------------------------------------------------
        -- Invoice header
        -------------------------------------------------------
        DECLARE @CustomerID AS INT = JSON_VALUE(@Json, '$.customerId');
        DECLARE @Date AS DATE = JSON_VALUE(@Json, '$.date');
        DECLARE @InvoiceID AS INT;
        INSERT  INTO Invoice (
            Date,
            CustomerID
        )
        VALUES               (@Date, @CustomerID);
        SET @InvoiceID = SCOPE_IDENTITY();
        -------------------------------------------------------
        -- Invoice items
        -------------------------------------------------------
        INSERT INTO InvoiceItem (
            InvoiceID,
            ProductID,
            Quantity,
            UnitPrice
        )
        SELECT @InvoiceID,
               j.ProductID,
               j.Quantity,
               j.UnitPrice
        FROM   OPENJSON (@Json, '$.items') 
		WITH 
			(ProductID INT '$.productId', Quantity INT '$.quantity', UnitPrice DECIMAL (10, 2) '$.unitPrice') AS j;
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK;
        THROW;
    END CATCH
END
GO


/******************************************************************************
    PROCEDURE: usp_GetCustomers

    Description:
        Returns all customers, sorted by last name and first name.

    Called by:
        GET /customers
        api/routes.py -> customers() -> api/database.py -> get_customers()

    Input:
        none

    Output:
        one row per customer: CustomerID, FirstName, LastName, Email
******************************************************************************/

CREATE PROCEDURE [dbo].[usp_GetCustomers]
AS
BEGIN
    SET NOCOUNT ON;
    SELECT   CustomerID,
             FirstName,
             LastName,
             Email
    FROM     Customer
    ORDER BY LastName,
             FirstName;
END
GO


/******************************************************************************
    PROCEDURE: usp_GetInvoice

    Description:
        Returns one invoice with its customer and items.
        The result has one row per invoice item; the invoice and customer
        columns repeat in every row. The API turns these rows into one
        nested JSON object { invoiceId, customer, items[] }.

    Called by:
        GET /invoices/{id}
        api/routes.py -> get_invoice_by_id() -> api/database.py -> get_invoice()

    Input:
        @InvoiceID  ID of the invoice

    Output:
        InvoiceID, Date, CustomerID, FirstName, LastName, Email,
        ProductID, Name, Quantity, UnitPrice
******************************************************************************/

CREATE PROCEDURE [dbo].[usp_GetInvoice]
    @InvoiceID INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT r.InvoiceID,
           r.Date,
           c.CustomerID,
           c.FirstName,
           c.LastName,
           c.Email,
           p.ProductID,
           p.Name,
           ii.Quantity,
           ii.UnitPrice
    FROM   Invoice AS r
           INNER JOIN
           Customer AS c
           ON r.CustomerID = c.CustomerID
           INNER JOIN
           InvoiceItem AS ii
           ON r.InvoiceID = ii.InvoiceID
           INNER JOIN
           Product AS p
           ON ii.ProductID = p.ProductID
    WHERE  r.InvoiceID = @InvoiceID;
END


GO


/******************************************************************************
    PROCEDURE: usp_GetInvoices

    Description:
        Returns the list of all invoices with the customer name and the
        invoice total (SUM of Quantity * UnitPrice), newest first.
        Note: an invoice without items is not listed (INNER JOIN).

    Called by:
        GET /invoices
        api/routes.py -> invoices() -> api/database.py -> get_invoices()

    Input:
        none

    Output:
        one row per invoice: InvoiceID, Date, CustomerID, FirstName,
        LastName, Total
******************************************************************************/

CREATE   PROCEDURE [dbo].[usp_GetInvoices]
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


/******************************************************************************
    PROCEDURE: usp_DeleteInvoice

    Description:
        Deletes an invoice. Its items are deleted automatically by the
        foreign key FK_InvoiceItem_Invoice (ON DELETE CASCADE).

    Called by:
        DELETE /invoices/{id}
        api/routes.py -> delete_invoice()

    Input:
        @InvoiceID  ID of the invoice to delete

    Output:
        none
******************************************************************************/

CREATE   PROCEDURE [dbo].[usp_DeleteInvoice]
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
