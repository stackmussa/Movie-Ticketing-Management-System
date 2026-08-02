CREATE DATABASE TicketSystem
USE TicketSystem

CREATE TABLE [User] (
	UserID int IDENTITY(1,1) PRIMARY KEY,
    firstName VARCHAR(30) NOT NULL,
    lastName VARCHAR(30) NOT NULL,
    Email VARCHAR(100) NOT NULL,
    PasswordHash varchar(255) NOT NULL, 
    IsActive bit NOT NULL DEFAULT 1
);

-- ============================================================
-- 1. CITY
-- ============================================================
CREATE TABLE City (
    CityID INT IDENTITY(1,1) PRIMARY KEY,
    CityName VARCHAR(50) NOT NULL,
    Province VARCHAR(50) NOT NULL
);



-- ============================================================
-- 2. CINEMA (the chain's branch/location)
-- ============================================================
CREATE TABLE Cinema (
    CinemaID INT IDENTITY(1,1) PRIMARY KEY,
    CinemaName VARCHAR(100) NOT NULL,      -- e.g. Cinepax, Nueplex
    BranchName VARCHAR(100) NOT NULL,      -- e.g. Ocean Mall, Packages Mall
    CityID INT NOT NULL,
    Address VARCHAR(200) NOT NULL,
    ContactNumber VARCHAR(20),
    CONSTRAINT FK_Cinema_City FOREIGN KEY (CityID) REFERENCES City(CityID)
);


-- ============================================================
-- 3. HALL (screen inside a cinema)
-- ============================================================
CREATE TABLE Hall (
    HallID INT IDENTITY(1,1) PRIMARY KEY,
    CinemaID INT NOT NULL,
    HallName VARCHAR(50) NOT NULL,          -- e.g. Screen 1, Gold Screen
    ScreenType VARCHAR(20) NOT NULL,        -- 2D, 3D, IMAX, 4DX
    TotalSeats INT NOT NULL,
    CONSTRAINT FK_Hall_Cinema FOREIGN KEY (CinemaID) REFERENCES Cinema(CinemaID)
);



-- ============================================================
-- 4. SEAT (individual seats within a hall)
--    Sample seating generated per hall: rows A-E, seats 1-10
-- ============================================================
CREATE TABLE Seat (
    SeatID INT IDENTITY(1,1) PRIMARY KEY,
    HallID INT NOT NULL,
    SeatRow CHAR(1) NOT NULL,
    SeatNumber INT NOT NULL,
    SeatCategory VARCHAR(20) NOT NULL DEFAULT 'Standard',   -- Standard, Gold, Platinum, Recliner
    CONSTRAINT FK_Seat_Hall FOREIGN KEY (HallID) REFERENCES Hall(HallID),
    CONSTRAINT UQ_Seat UNIQUE (HallID, SeatRow, SeatNumber)
);

-- Generate a compact 5x10 seat map (rows A-E, seats 1-10) for every hall
DECLARE @HallID INT;
DECLARE @RowLetter CHAR(1);
DECLARE @SeatNum INT;
DECLARE hall_cursor CURSOR FOR SELECT HallID FROM Hall;

OPEN hall_cursor;
FETCH NEXT FROM hall_cursor INTO @HallID;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @RowLetter = 'A';
    WHILE @RowLetter <= 'E'
    BEGIN
        SET @SeatNum = 1;
        WHILE @SeatNum <= 10
        BEGIN
            INSERT INTO Seat (HallID, SeatRow, SeatNumber, SeatCategory)
            VALUES (
                @HallID,
                @RowLetter,
                @SeatNum,
                CASE WHEN @RowLetter IN ('A','B') THEN 'Platinum'
                     WHEN @RowLetter IN ('C','D') THEN 'Gold'
                     ELSE 'Standard' END
            );
            SET @SeatNum = @SeatNum + 1;
        END
        SET @RowLetter = CHAR(ASCII(@RowLetter) + 1);
    END
    FETCH NEXT FROM hall_cursor INTO @HallID;
END

CLOSE hall_cursor;
DEALLOCATE hall_cursor;

-- ============================================================
-- 5. MOVIE
-- ============================================================
CREATE TABLE Movie (
    MovieID INT IDENTITY(1,1) PRIMARY KEY,
    Title VARCHAR(150) NOT NULL,
    Genre VARCHAR(50) NOT NULL,
    [Language] VARCHAR(30) NOT NULL,
    DurationMinutes INT NOT NULL,
    ReleaseDate DATE NOT NULL,
    [DESCRIPTION] VARCHAR(500),
    CensorRating VARCHAR(10) NOT NULL DEFAULT 'U',   -- U, U/A, A
);


-- ============================================================
-- 6. SHOW (a screening of a movie in a hall)
-- ============================================================
CREATE TABLE Show (
    ShowID INT IDENTITY(1,1) PRIMARY KEY,
    MovieID INT NOT NULL,
    HallID INT NOT NULL,
    ShowDate DATE NOT NULL,
    ShowTime TIME NOT NULL,
    TicketPrice DECIMAL(8,2) NOT NULL,
    CONSTRAINT FK_Show_Movie FOREIGN KEY (MovieID) REFERENCES Movie(MovieID),
    CONSTRAINT FK_Show_Hall FOREIGN KEY (HallID) REFERENCES Hall(HallID)
);



-- ============================================================
-- 7. BOOKING (a user's ticket booking for a show)
--    Left empty here - populated by the FastAPI backend once
--    real users exist, since it depends on [User].UserID.
-- ============================================================
CREATE TABLE Booking (
    BookingID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL,
    ShowID INT NOT NULL,
    BookingDate DATETIME NOT NULL DEFAULT GETDATE(),
    TotalAmount DECIMAL(8,2) NOT NULL,
    BookingStatus VARCHAR(20) NOT NULL DEFAULT 'Pending',  -- Pending, Confirmed, Cancelled
    TicketsNeeded INT NOT NULL DEFAULT 1,
    CONSTRAINT FK_Booking_User FOREIGN KEY (UserID) REFERENCES [User](UserID),
    CONSTRAINT FK_Booking_Show FOREIGN KEY (ShowID) REFERENCES Show(ShowID)
);

-- ============================================================
-- 8. BOOKING_SEAT (junction table: which seats belong to a booking)
-- ============================================================
CREATE TABLE BookingSeat (
    BookingSeatID INT IDENTITY(1,1) PRIMARY KEY,
    BookingID INT NOT NULL,
    SeatID INT NOT NULL,
    CONSTRAINT FK_BookingSeat_Booking FOREIGN KEY (BookingID) REFERENCES Booking(BookingID),
    CONSTRAINT FK_BookingSeat_Seat FOREIGN KEY (SeatID) REFERENCES Seat(SeatID),
    CONSTRAINT UQ_BookingSeat UNIQUE (BookingID, SeatID)
);

-- ============================================================
-- 9. PAYMENT
-- ============================================================
CREATE TABLE Payment (
    PaymentID INT IDENTITY(1,1) PRIMARY KEY,
    BookingID INT NOT NULL,
    Amount DECIMAL(8,2) NOT NULL,
    PaymentMethod VARCHAR(30) NOT NULL,      -- JazzCash, EasyPaisa, Debit/Credit Card, Cash
    PaymentStatus VARCHAR(20) NOT NULL DEFAULT 'Pending',  -- Pending, Success, Failed, Refunded
    TransactionReference VARCHAR(100),
    PaymentDate DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Payment_Booking FOREIGN KEY (BookingID) REFERENCES Booking(BookingID)
);

INSERT INTO City (CityName, Province) VALUES
('Karachi', 'Sindh'),
('Lahore', 'Punjab'),
('Islamabad', 'Islamabad Capital Territory'),
('Rawalpindi', 'Punjab'),
('Faisalabad', 'Punjab'),
('Hyderabad', 'Sindh');

INSERT INTO Cinema (CinemaName, BranchName, CityID, Address, ContactNumber) VALUES
('Cinepax', 'Ocean Mall', 1, 'Ocean Mall, Clifton, Karachi', '021-111626384'),
('Cineplex Atrium', 'Atrium Mall', 1, 'Atrium Mall, Saddar, Zaibunnisa Street, Karachi', '021-111626384'),
('Nueplex Cinemas', 'The Place DHA', 1, 'The Place, Khayaban-e-Shaheen, Phase-VIII, DHA, Karachi', '021-111683759'),
('Universe Cineplex', 'Seaview', 1, 'Seaview, Clifton Beach, Karachi', '021-35862001'),
('Cinepax', 'Packages Mall', 2, 'Packages Mall, Walton Road, Lahore', '042-111246362'),
('Universal Cinemas', 'Emporium Mall', 2, 'Emporium Mall, Canal Road, Lahore', '042-111246362'),
('Cinestar', 'IMAX Lahore', 2, 'Fortress Stadium, Lahore Cantt, Lahore', '042-111529292'),
('Cinepax', 'Centaurus Mall', 3, 'The Centaurus Mall, F-8, Islamabad', '051-111246329'),
('Cinestar', 'Islamabad', 3, 'Safa Gold Mall, F-8 Markaz, Islamabad', '051-111529292'),
('Nueplex Cinemas', 'DHA Islamabad', 3, 'DHA Phase II, Islamabad', '051-111683759'),
('Cinepax', 'Faisalabad', 5, 'D Ground, Faisalabad', '041-111246329');

INSERT INTO Hall (CinemaID, HallName, ScreenType, TotalSeats) VALUES
(1, 'Gold Screen', '2D', 120),
(1, 'Platinum Screen', '3D', 90),
(2, 'Cinema A', '2D', 150),
(2, 'Cinema D', '3D', 100),
(3, 'Screen 1', 'IMAX', 300),
(3, 'Screen 2', '3D', 200),
(4, 'Family Hall', '2D', 180),
(5, 'CMAX', '4DX', 80),
(5, 'Minipax', '2D', 60),
(6, 'Screen 1', '2D', 140),
(7, 'IMAX Screen', 'IMAX', 320),
(8, 'Gold Screen', '2D', 130),
(9, 'Screen 1', '3D', 110),
(10, 'Screen 1', '2D', 100),
(11, 'Screen 1', '2D', 100);

INSERT INTO Movie (Title, Genre, [Language], DurationMinutes, ReleaseDate, [Description], CensorRating) VALUES
('Aag Lagay Basti Mein', 'Crime/Drama', 'Urdu', 148, '2026-03-21', 'A crime-drama reuniting Fahad Mustafa and Mahira Khan, presented by ARY Films and Big Bang Entertainment.', 'U/A'),
('Bullah', 'Drama', 'Punjabi', 135, '2026-03-21', 'A drama starring Shaan Shahid and Sara Loren, produced by Shake Films.', 'U/A'),
('Delhi Gate', 'Historical/Drama', 'Urdu', 140, '2026-03-21', 'A historical drama directed by Nadeem Cheema featuring Jawed Sheikh and Shafqat Cheema.', 'U/A'),
('Mera Lyari', 'Drama', 'Urdu', 125, '2026-05-08', 'A drama set in Karachi''s Lyari neighbourhood starring Ayesha Omar and Dananeer Mobeen.', 'U/A'),
('Luv Di Saun', 'Romance/Comedy', 'Punjabi', 130, '2026-05-27', 'A romantic comedy from ARY Films starring Farhan Saeed and Babar Ali.', 'U'),
('Zombeid', 'Horror/Comedy', 'Urdu', 128, '2026-05-27', 'A horror-comedy from Filmwala Pictures starring Fahad Mustafa and Mehwish Hayat.', 'U/A'),
('Psycho', 'Thriller', 'Urdu', 122, '2026-05-27', 'A psychological thriller written, directed by and starring Shaan Shahid, with Meera and Sonya Hussyn.', 'A'),
('The Super Mario Galaxy Movie', 'Animation/Adventure', 'English', 104, '2026-04-01', 'Animated adventure distributed in Pakistan by Universal Pictures International.', 'U'),
('Wicked: For Good', 'Musical/Fantasy', 'English', 137, '2025-11-21', 'The second part of the Wicked musical fantasy, distributed by Universal Pictures International.', 'U'),
('The Housemaid', 'Thriller', 'English', 119, '2025-12-25', 'Psychological thriller that had an extended theatrical run in Pakistani cinemas in early 2026.', 'A');

INSERT INTO Show (MovieID, HallID, ShowDate, ShowTime, TicketPrice) VALUES
(1, 1, '2026-07-30', '18:00', 900.00),
(1, 5, '2026-07-30', '21:00', 1500.00),
(2, 8, '2026-07-30', '17:30', 800.00),
(3, 3, '2026-07-30', '19:15', 1000.00),
(4, 12, '2026-07-30', '16:00', 700.00),
(5, 10, '2026-07-31', '20:00', 900.00),
(6, 6, '2026-07-31', '22:00', 1000.00),
(7, 9, '2026-07-31', '19:00', 850.00),
(8, 11, '2026-07-30', '15:00', 1200.00),
(9, 7, '2026-07-30', '20:30', 1800.00),
(10, 4, '2026-07-31', '18:45', 900.00),
(1, 8, '2026-07-31', '21:30', 950.00),
(1,3, '2026-05-12', '18:00', 500);

SELECT *
FROM [User]

SELECT 
    M.Title AS MovieTitle,
    C.CinemaName,
    C.BranchName,
    H.HallName,
    H.TotalSeats AS SeatingCapacity
FROM Movie M
INNER JOIN Show S ON M.MovieID = S.MovieID
INNER JOIN Hall H ON S.HallID = H.HallID
INNER JOIN Cinema C ON H.CinemaID = C.CinemaID
WHERE M.Title = 'Aag Lagay Basti Mein'; 
-- You can replace 'Aag Lagay Basti Mein' with whichever specific movie you are looking for.

SELECT COUNT(*) FROM Seat WHERE HallID = 6;



SELECT *
FROM [User]

SELECT *
FROM Booking

DROP TABLE City
TRUNCATE TABLE City
SELECT * 
FROM City

SELECT *
FROM Seat

SELECT * 
FROM SHOW