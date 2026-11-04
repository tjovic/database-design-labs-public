USE OBPRestDemo;
GO

-------------------------------------------------------------
-- Delete data
-------------------------------------------------------------

DELETE FROM InvoiceItem;
DELETE FROM Invoice;
DELETE FROM Product;
DELETE FROM Customer;
GO

-------------------------------------------------------------
-- Reset IDENTITY
-------------------------------------------------------------

DBCC CHECKIDENT ('InvoiceItem', RESEED, 0);
DBCC CHECKIDENT ('Invoice', RESEED, 0);
DBCC CHECKIDENT ('Product', RESEED, 0);
DBCC CHECKIDENT ('Customer', RESEED, 0);
GO

-------------------------------------------------------------
-- Customers
-------------------------------------------------------------

INSERT INTO Customer
(
    FirstName,
    LastName,
    Email
)
VALUES
('John','Smith','john.smith@gmail.com'),
('Emma','Johnson','emma.johnson@gmail.com'),
('Michael','Brown','michael.brown@gmail.com'),
('Sarah','Davis','sarah.davis@gmail.com'),
('Robert','Wilson','robert.wilson@gmail.com');
GO

-------------------------------------------------------------
-- Products
-------------------------------------------------------------

INSERT INTO Product
(
    Name,
    UnitPrice
)
VALUES
('Dell Latitude 5540',1450),
('Logitech MX Master 3S',109),
('Dell 27" Monitor',299),
('HP USB-C Dock',189),
('Logitech MX Keys',129),
('Kingston SSD 1TB',99),
('USB-C cable',12),
('HDMI cable',15);
GO

-------------------------------------------------------------
-- Invoices
-------------------------------------------------------------

INSERT INTO Invoice
(
    Date,
    CustomerID
)
VALUES
('2025-06-01',1),
('2025-06-10',2);
GO

-------------------------------------------------------------
-- Items
-------------------------------------------------------------

INSERT INTO InvoiceItem
(
    InvoiceID,
    ProductID,
    Quantity,
    UnitPrice
)
VALUES

(1,1,1,1450),
(1,2,1,109),
(1,7,2,12),

(2,3,2,299),
(2,5,1,129),
(2,8,1,15);

GO
