USE CyberLab;
GO

-- TRUNCATE TABLE removes all rows and restarts the IDENTITY values at 1,
-- both on a new table and on a table that already had rows.
TRUNCATE TABLE dbo.Users;
TRUNCATE TABLE dbo.CreditCards;
TRUNCATE TABLE dbo.Products;
GO

INSERT INTO dbo.Users (Username, FullName, Department, Password) VALUES
    ('admin',    'Administrator',  'IT',          '12345'),
    ('tomislav', 'Tomislav Jovic', 'Development', 'tajna123'),
    ('ana',      'Ana Horvat',     'HR',          'ana2025');
GO

INSERT INTO dbo.CreditCards (CardNumber, CVV, Owner, ExpiryDate) VALUES
    ('4539-1488-0343-6467', '123',  'Administrator',  '12/27'),
    ('5555-3412-4444-1115', '456',  'Tomislav Jovic', '08/26'),
    ('3782-822463-10005',   '7890', 'Ana Horvat',     '03/29');
GO

INSERT INTO dbo.Products (Name, Category, Price) VALUES
    ('Dell Latitude 5540',    'Laptops',     1450.00),
    ('Lenovo ThinkPad T14',   'Laptops',     1390.00),
    ('Dell 27" Monitor',      'Monitors',     299.00),
    ('LG 32" 4K Monitor',     'Monitors',     449.00),
    ('Logitech MX Master 3S', 'Accessories',  109.00),
    ('Logitech MX Keys',      'Accessories',  129.00),
    ('HP USB-C Dock',         'Accessories',  189.00),
    ('Kingston SSD 1TB',      'Storage',       99.00);
GO
