USE CyberLab;
GO

DELETE FROM dbo.Users;
DBCC CHECKIDENT ('dbo.Users', RESEED, 0);
GO

INSERT INTO dbo.Users (Username, FullName, Department, Password) VALUES
    ('admin',    'Administrator',  'IT',          '12345'),
    ('tomislav', 'Tomislav Jovic', 'Development', 'tajna123'),
    ('ana',      'Ana Horvat',     'HR',          'ana2025');
GO

DELETE FROM dbo.CreditCards;
DBCC CHECKIDENT ('dbo.CreditCards', RESEED, 0);
GO

INSERT INTO dbo.CreditCards (CardNumber, CVV, Owner, ExpiryDate) VALUES
    ('4539-1488-0343-6467', '123',  'Administrator',  '12/27'),
    ('5555-3412-4444-1115', '456',  'Tomislav Jovic', '08/26'),
    ('3782-822463-10005',   '7890', 'Ana Horvat',     '03/29');
GO
