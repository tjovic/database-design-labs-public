/******************************************************************************
    OBP REST DEMO
    Create database
******************************************************************************/

USE master;
GO

IF DB_ID('OBPRestDemo') IS NOT NULL
BEGIN
    ALTER DATABASE OBPRestDemo SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE OBPRestDemo;
END
GO

CREATE DATABASE OBPRestDemo;
GO

USE OBPRestDemo;
GO

CREATE TABLE Customer
(
    CustomerID INT IDENTITY(1,1)
        CONSTRAINT PK_Customer PRIMARY KEY,

    FirstName NVARCHAR(50) NOT NULL,

    LastName NVARCHAR(50) NOT NULL,

    Email NVARCHAR(100) NULL
);
GO


CREATE TABLE Product
(
    ProductID INT IDENTITY(1,1)
        CONSTRAINT PK_Product PRIMARY KEY,

    Name NVARCHAR(100) NOT NULL,

    UnitPrice DECIMAL(10,2)
        CONSTRAINT CK_Product_Price
        CHECK(UnitPrice>=0)
);
GO

CREATE TABLE Invoice
(
    InvoiceID INT IDENTITY(1,1)
        CONSTRAINT PK_Invoice PRIMARY KEY,

    Date DATE NOT NULL
        CONSTRAINT DF_Invoice_Date
        DEFAULT(GETDATE()),

    CustomerID INT NOT NULL,

    CONSTRAINT FK_Invoice_Customer
        FOREIGN KEY(CustomerID)
        REFERENCES Customer(CustomerID)
);
GO

CREATE TABLE InvoiceItem
(
    InvoiceItemID INT IDENTITY(1,1)
        CONSTRAINT PK_InvoiceItem PRIMARY KEY,

    InvoiceID INT NOT NULL,

    ProductID INT NOT NULL,

    Quantity INT NOT NULL
        CONSTRAINT CK_InvoiceItem_Quantity
        CHECK(Quantity>0),

    UnitPrice DECIMAL(10,2) NOT NULL
        CONSTRAINT CK_InvoiceItem_Price
        CHECK(UnitPrice>=0),

    CONSTRAINT FK_InvoiceItem_Invoice
        FOREIGN KEY(InvoiceID)
        REFERENCES Invoice(InvoiceID)
        ON DELETE CASCADE,

    CONSTRAINT FK_InvoiceItem_Product
        FOREIGN KEY(ProductID)
        REFERENCES Product(ProductID)
);
GO


CREATE INDEX IX_Invoice_CustomerID
ON Invoice(CustomerID);
GO

CREATE INDEX IX_InvoiceItem_InvoiceID
ON InvoiceItem(InvoiceID);
GO

CREATE INDEX IX_InvoiceItem_ProductID
ON InvoiceItem(ProductID);
GO
