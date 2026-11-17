IF DB_ID('CyberLab') IS NULL
BEGIN
    CREATE DATABASE CyberLab;
END
GO

USE CyberLab;
GO

IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL
    DROP TABLE dbo.Users;
GO

CREATE TABLE dbo.Users
(
    Id         INT IDENTITY(1,1) PRIMARY KEY,
    Username   NVARCHAR(50)  NOT NULL UNIQUE,
    FullName   NVARCHAR(100) NOT NULL,
    Department NVARCHAR(50)  NULL,
    Password   NVARCHAR(100) NULL
);
GO

IF OBJECT_ID('dbo.CreditCards', 'U') IS NOT NULL
    DROP TABLE dbo.CreditCards;
GO

CREATE TABLE dbo.CreditCards
(
    Id         INT IDENTITY(1,1) PRIMARY KEY,
    CardNumber NVARCHAR(25)  NOT NULL,
    CVV        NVARCHAR(5)   NOT NULL,
    Owner      NVARCHAR(100) NOT NULL,
    ExpiryDate NVARCHAR(10)  NOT NULL
);
GO

IF OBJECT_ID('dbo.Products', 'U') IS NOT NULL
    DROP TABLE dbo.Products;
GO

-- Products are what the search page is meant to show.
-- Users and CreditCards are what an attacker wants instead.
CREATE TABLE dbo.Products
(
    Id       INT IDENTITY(1,1) PRIMARY KEY,
    Name     NVARCHAR(100)  NOT NULL,
    Category NVARCHAR(50)   NOT NULL,
    Price    DECIMAL(10, 2) NOT NULL
);
GO
