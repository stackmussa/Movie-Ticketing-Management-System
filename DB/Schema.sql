CREATE DATABASE MovieSystem
USE MovieSystem

CREATE TABLE [User] (
	UserID int IDENTITY(1,1) PRIMARY KEY,
    firstName VARCHAR(30) NOT NULL,
    lastName VARCHAR(30) NOT NULL,
    Email VARCHAR(100) NOT NULL,
    PasswordHash varchar(255) NOT NULL, 
    IsActive bit NOT NULL DEFAULT 1
);

SELECT *
FROM [User]

