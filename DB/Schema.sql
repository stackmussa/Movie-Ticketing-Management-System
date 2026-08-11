
CREATE DATABASE TicketSystem
GO
USE TicketSystem
GO

-- ============================================================
-- 0. USER
-- ============================================================
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
    SeatCategory VARCHAR(20) NOT NULL DEFAULT 'Standard',   -- Standard, Gold, Platinum
    CONSTRAINT FK_Seat_Hall FOREIGN KEY (HallID) REFERENCES Hall(HallID),
    CONSTRAINT UQ_Seat UNIQUE (HallID, SeatRow, SeatNumber)
);

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
    [Description] VARCHAR(500),
    CensorRating VARCHAR(10) NOT NULL DEFAULT 'U'   -- U, U/A, A
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
--    real users register, since it depends on [User].UserID.
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

DROP TABLE IF EXISTS BookingSeat 
-- ============================================================
-- 8. BOOKING_SEAT (junction table: which seats belong to a booking)
-- ============================================================
CREATE TABLE BookingSeat (
    BookingSeatID INT IDENTITY(1,1) PRIMARY KEY,
    BookingID INT NOT NULL,
    ShowID INT NOT NULL, -- NEW COLUMN
    SeatID INT NOT NULL,
    CONSTRAINT FK_BookingSeat_Booking FOREIGN KEY (BookingID) REFERENCES Booking(BookingID),
    CONSTRAINT FK_BookingSeat_Show FOREIGN KEY (ShowID) REFERENCES Show(ShowID),
    CONSTRAINT FK_BookingSeat_Seat FOREIGN KEY (SeatID) REFERENCES Seat(SeatID),
    CONSTRAINT UQ_ShowSeat UNIQUE (ShowID, SeatID) -- THE MAGIC FIX
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

-- ============================================================
-- 10. REVIEW (user reviews & ratings for movies, with reply threading)
-- ============================================================
CREATE TABLE Review (
    ReviewID INT IDENTITY(1,1) PRIMARY KEY,
    MovieID INT NOT NULL,
    UserID INT NOT NULL,
    Rating INT NULL CHECK (Rating BETWEEN 1 AND 5),      -- NULL for replies (only top-level reviews have ratings)
    ReviewText VARCHAR(1000) NOT NULL,
    ParentReviewID INT NULL,                              -- NULL = top-level review, set = reply to another review
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Review_Movie FOREIGN KEY (MovieID) REFERENCES Movie(MovieID),
    CONSTRAINT FK_Review_User FOREIGN KEY (UserID) REFERENCES [User](UserID),
    CONSTRAINT FK_Review_Parent FOREIGN KEY (ParentReviewID) REFERENCES Review(ReviewID)
);

/* ============================================================
   DATA - CITY
   ============================================================ */
INSERT INTO City (CityName, Province) VALUES
('Karachi', 'Sindh'),                          -- CityID 1
('Lahore', 'Punjab'),                          -- CityID 2
('Islamabad', 'Islamabad Capital Territory'),  -- CityID 3
('Rawalpindi', 'Punjab'),                      -- CityID 4
('Faisalabad', 'Punjab'),                      -- CityID 5
('Hyderabad', 'Sindh'),                        -- CityID 6
('Multan', 'Punjab'),                          -- CityID 7
('Peshawar', 'Khyber Pakhtunkhwa'),            -- CityID 8
('Sialkot', 'Punjab'),                         -- CityID 9
('Gujranwala', 'Punjab'),                      -- CityID 10
('Quetta', 'Balochistan');                     -- CityID 11

/* ============================================================
   DATA - CINEMA
   ============================================================ */
INSERT INTO Cinema (CinemaName, BranchName, CityID, Address, ContactNumber) VALUES
('Cinepax', 'Ocean Mall', 1, 'Ocean Mall, Clifton, Karachi', '021-111626384'),                              -- CinemaID 1
('Cineplex Atrium', 'Atrium Mall', 1, 'Atrium Mall, Saddar, Zaibunnisa Street, Karachi', '021-111626384'),  -- CinemaID 2
('Nueplex Cinemas', 'The Place DHA', 1, 'The Place, Khayaban-e-Shaheen, Phase-VIII, DHA, Karachi', '021-111683759'), -- CinemaID 3
('Universe Cineplex', 'Seaview', 1, 'Seaview, Clifton Beach, Karachi', '021-35862001'),                     -- CinemaID 4
('Cinepax', 'Packages Mall', 2, 'Packages Mall, Walton Road, Lahore', '042-111246362'),                     -- CinemaID 5
('Universal Cinemas', 'Emporium Mall', 2, 'Emporium Mall, Canal Road, Lahore', '042-111246362'),            -- CinemaID 6
('Cinestar', 'IMAX Lahore', 2, 'Fortress Stadium, Lahore Cantt, Lahore', '042-111529292'),                  -- CinemaID 7
('Cinepax', 'Centaurus Mall', 3, 'The Centaurus Mall, F-8, Islamabad', '051-111246329'),                    -- CinemaID 8
('Cinestar', 'Islamabad', 3, 'Safa Gold Mall, F-8 Markaz, Islamabad', '051-111529292'),                     -- CinemaID 9
('Nueplex Cinemas', 'DHA Islamabad', 3, 'DHA Phase II, Islamabad', '051-111683759'),                        -- CinemaID 10
('Cinepax', 'Faisalabad', 5, 'D Ground, Faisalabad', '041-111246329'),                                      -- CinemaID 11
('Cinepax', 'Jinnah Park', 4, 'Jinnah Park, Committee Chowk, Rawalpindi', '051-111246329'),                 -- CinemaID 12
('Cinepax', 'Giga Mall WTC', 4, 'Giga Mall, World Trade Centre, GT Road, DHA Phase II, Rawalpindi', '051-111246372'), -- CinemaID 13
('Cinepax', 'Hyderabad', 6, 'Latifabad, Hyderabad', '022-111246329'),                                       -- CinemaID 14
('Cine Star', 'Multan', 7, 'Abdali Road, Multan', '061-111529292'),                                         -- CinemaID 15
('Cinepax', 'Multan', 7, 'Officers Colony, Multan', '061-111246329'),                                       -- CinemaID 16
('Cinepax', 'Peshawar', 8, 'University Road, Peshawar', '091-111246329'),                                   -- CinemaID 17
('Cinepax', 'Sialkot', 9, 'Paris Road, Sialkot', '052-111246329'),                                          -- CinemaID 18
('Cinepax', 'Gujranwala', 10, 'GT Road, Gujranwala', '055-111246329'),                                      -- CinemaID 19
('Cinepax', 'Quetta', 11, 'Jinnah Road, Quetta', '081-111246329');                                          -- CinemaID 20

/* ============================================================
   DATA - HALL
   ============================================================ */
INSERT INTO Hall (CinemaID, HallName, ScreenType, TotalSeats) VALUES
(1, 'Gold Screen', '2D', 120),        -- HallID 1  Cinepax Ocean Mall, Karachi
(1, 'Platinum Screen', '3D', 90),     -- HallID 2  Cinepax Ocean Mall, Karachi
(2, 'Cinema A', '2D', 150),           -- HallID 3  Cineplex Atrium, Karachi
(2, 'Cinema D', '3D', 100),           -- HallID 4  Cineplex Atrium, Karachi
(3, 'Screen 1', 'IMAX', 300),         -- HallID 5  Nueplex, The Place DHA, Karachi
(3, 'Screen 2', '3D', 200),           -- HallID 6  Nueplex, The Place DHA, Karachi
(4, 'Family Hall', '2D', 180),        -- HallID 7  Universe Cineplex, Seaview, Karachi
(5, 'CMAX', '4DX', 80),               -- HallID 8  Cinepax, Packages Mall, Lahore
(5, 'Minipax', '2D', 60),             -- HallID 9  Cinepax, Packages Mall, Lahore
(6, 'Screen 1', '2D', 140),           -- HallID 10 Universal Cinemas, Emporium Mall, Lahore
(7, 'IMAX Screen', 'IMAX', 320),      -- HallID 11 Cinestar, IMAX Lahore
(8, 'Gold Screen', '2D', 130),        -- HallID 12 Cinepax, Centaurus Mall, Islamabad
(9, 'Screen 1', '3D', 110),           -- HallID 13 Cinestar, Islamabad
(10, 'Screen 1', '2D', 100),          -- HallID 14 Nueplex, DHA Islamabad
(11, 'Screen 1', '2D', 100),          -- HallID 15 Cinepax, Faisalabad
(12, 'Screen 1', '2D', 100),          -- HallID 16 Cinepax, Jinnah Park, Rawalpindi
(12, 'Screen 2', '3D', 80),           -- HallID 17 Cinepax, Jinnah Park, Rawalpindi
(13, 'Gold Screen', '2D', 120),       -- HallID 18 Cinepax, Giga Mall WTC, Rawalpindi
(13, 'Platinum Screen', '3D', 90),    -- HallID 19 Cinepax, Giga Mall WTC, Rawalpindi
(14, 'Screen 1', '2D', 100),          -- HallID 20 Cinepax, Hyderabad
(14, 'Screen 2', '2D', 90),           -- HallID 21 Cinepax, Hyderabad
(15, 'Screen 1', '2D', 110),          -- HallID 22 Cine Star, Multan
(15, 'Screen 2', '3D', 90),           -- HallID 23 Cine Star, Multan
(16, 'Gold Screen', '2D', 100),       -- HallID 24 Cinepax, Multan
(16, 'Platinum Screen', '3D', 80),    -- HallID 25 Cinepax, Multan
(17, 'Screen 1', '2D', 100),          -- HallID 26 Cinepax, Peshawar
(18, 'Screen 1', '2D', 90),           -- HallID 27 Cinepax, Sialkot
(19, 'Screen 1', '2D', 90),           -- HallID 28 Cinepax, Gujranwala
(20, 'Screen 1', '2D', 80);           -- HallID 29 Cinepax, Quetta

/* ============================================================
   DATA - SEAT
   Generates a compact 5x10 seat map (rows A-E, seats 1-10) for
   every hall: A/B = Platinum, C/D = Gold, E = Standard.
   ============================================================ */
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

/* ============================================================
   DATA - MOVIE
   Pakistani cinema releases + current/upcoming Hollywood titles,
   as actually playing/booking in Pakistan as of Aug 2026.
   ============================================================ */
INSERT INTO Movie (Title, Genre, [Language], DurationMinutes, ReleaseDate, [Description], CensorRating) VALUES
('Aag Lagay Basti Mein', 'Crime/Drama', 'Urdu', 148, '2026-03-21', 'A crime-drama reuniting Fahad Mustafa and Mahira Khan, presented by ARY Films and Big Bang Entertainment.', 'U/A'),                          -- MovieID 1
('Bullah', 'Drama', 'Punjabi', 135, '2026-03-21', 'A drama starring Shaan Shahid and Sara Loren, produced by Shake Films.', 'U/A'),                                                                                            -- MovieID 2
('Delhi Gate', 'Historical/Drama', 'Urdu', 140, '2026-03-21', 'A historical drama directed by Nadeem Cheema featuring Jawed Sheikh and Shafqat Cheema.', 'U/A'),                                                              -- MovieID 3
('Mera Lyari', 'Drama', 'Urdu', 125, '2026-05-08', 'A drama set in Karachi''s Lyari neighbourhood starring Ayesha Omar and Dananeer Mobeen.', 'U/A'),                                                                         -- MovieID 4
('Luv Di Saun', 'Romance/Comedy', 'Punjabi', 130, '2026-05-27', 'A romantic comedy from ARY Films starring Farhan Saeed and Babar Ali.', 'U'),                                                                                 -- MovieID 5
('Zombeid', 'Horror/Comedy', 'Urdu', 128, '2026-05-27', 'A horror-comedy from Filmwala Pictures starring Fahad Mustafa and Mehwish Hayat.', 'U/A'),                                                                           -- MovieID 6
('Psycho', 'Thriller', 'Urdu', 122, '2026-05-27', 'A psychological thriller written, directed by and starring Shaan Shahid, with Meera and Sonya Hussyn.', 'A'),                                                              -- MovieID 7
('The Super Mario Galaxy Movie', 'Animation/Adventure', 'English', 104, '2026-04-01', 'Animated adventure distributed in Pakistan by Universal Pictures International.', 'U'),                                                -- MovieID 8
('Wicked: For Good', 'Musical/Fantasy', 'English', 137, '2025-11-21', 'The second part of the Wicked musical fantasy, distributed by Universal Pictures International.', 'U'),                                                -- MovieID 9
('The Housemaid', 'Thriller', 'English', 119, '2025-12-25', 'Psychological thriller that had an extended theatrical run in Pakistani cinemas in early 2026.', 'A'),                                                           -- MovieID 10
('Spider-Man: Brand New Day', 'Action/Adventure', 'English', 145, '2026-07-31', 'Peter Parker fights crime full-time in a world that no longer remembers him, starring Tom Holland, Zendaya and Sadie Sink. Distributed in Pakistan by Sony Pictures/Marvel Studios.', 'U/A'), -- MovieID 11
('Avengers: Doomsday', 'Action/Sci-Fi', 'English', 150, '2026-12-18', 'The Avengers face Doctor Doom (Robert Downey Jr.) alongside the X-Men and Fantastic Four, directed by the Russo brothers. Advance bookings only - releases worldwide December 18, 2026.', 'U/A'),        -- MovieID 12
('Toy Story 5', 'Animation/Family', 'English', 102, '2026-06-19', 'Woody, Buzz and the gang face a new tech-savvy rival, Lilypad, for Bonnie''s attention. A Pixar production distributed by Walt Disney Studios.', 'U'),      -- MovieID 13
('The Odyssey', 'Adventure/Drama', 'English', 150, '2026-07-17', 'Christopher Nolan''s epic retelling of Homer''s Odyssey, distributed by Universal Pictures International.', 'U/A'),                                         -- MovieID 14
('Minions 3', 'Animation/Comedy', 'English', 95, '2026-07-01', 'The Minions return in a new adventure from Illumination, distributed by Universal Pictures International.', 'U'),                                             -- MovieID 15
('Supergirl', 'Action/Adventure', 'English', 130, '2026-06-26', 'Milly Alcock stars as Kara Zor-El in this DC Studios adventure, distributed by Warner Bros.', 'U/A');                                                        -- MovieID 16

/* ============================================================
   DATA - SHOW
   Schedule runs today, 2026-08-03, through next week,
   2026-08-10 - except Avengers: Doomsday, a genuine Dec 18,
   2026 release shown here as an advance-booking listing.
   MovieID is looked up by title so this doesn't break if your
   Movie insert order or IDs ever drift.
   ============================================================ */
INSERT INTO Show (MovieID, HallID, ShowDate, ShowTime, TicketPrice)
SELECT (SELECT MovieID FROM Movie WHERE Title = S.MovieTitle), S.HallID, S.ShowDate, S.ShowTime, S.TicketPrice
FROM (VALUES
    -- Aag Lagay Basti Mein
    ('Aag Lagay Basti Mein', 1,  '2026-08-03', '18:00', 900.00),
    ('Aag Lagay Basti Mein', 12, '2026-08-05', '19:00', 950.00),
    ('Aag Lagay Basti Mein', 8,  '2026-08-08', '21:00', 1000.00),
    ('Aag Lagay Basti Mein', 16, '2026-08-06', '19:30', 850.00),   -- Cinepax Jinnah Park, Rawalpindi

    -- Bullah
    ('Bullah', 9,  '2026-08-04', '17:30', 800.00),
    ('Bullah', 3,  '2026-08-07', '20:00', 850.00),
    ('Bullah', 24, '2026-08-05', '18:00', 750.00),                -- Cinepax, Multan

    -- Delhi Gate
    ('Delhi Gate', 3,  '2026-08-03', '19:15', 1000.00),
    ('Delhi Gate', 13, '2026-08-06', '18:30', 1000.00),
    ('Delhi Gate', 18, '2026-08-08', '19:00', 900.00),             -- Cinepax, Giga Mall WTC, Rawalpindi

    -- Mera Lyari
    ('Mera Lyari', 12, '2026-08-04', '16:00', 700.00),
    ('Mera Lyari', 10, '2026-08-09', '17:00', 750.00),
    ('Mera Lyari', 20, '2026-08-07', '16:30', 650.00),             -- Cinepax, Hyderabad

    -- Luv Di Saun
    ('Luv Di Saun', 10, '2026-08-05', '20:00', 900.00),
    ('Luv Di Saun', 1,  '2026-08-08', '19:30', 900.00),
    ('Luv Di Saun', 28, '2026-08-06', '20:00', 800.00),            -- Cinepax, Gujranwala

    -- Zombeid
    ('Zombeid', 6,  '2026-08-04', '22:00', 1000.00),
    ('Zombeid', 8,  '2026-08-07', '21:30', 1050.00),
    ('Zombeid', 22, '2026-08-09', '21:00', 900.00),                -- Cine Star, Multan

    -- Psycho
    ('Psycho', 13, '2026-08-05', '19:00', 850.00),
    ('Psycho', 3,  '2026-08-09', '21:00', 900.00),
    ('Psycho', 27, '2026-08-08', '20:30', 800.00),                 -- Cinepax, Sialkot

    -- The Super Mario Galaxy Movie
    ('The Super Mario Galaxy Movie', 14, '2026-08-03', '15:00', 1200.00),
    ('The Super Mario Galaxy Movie', 7,  '2026-08-06', '13:30', 1100.00),
    ('The Super Mario Galaxy Movie', 21, '2026-08-05', '14:00', 950.00),   -- Cinepax, Hyderabad

    -- Wicked: For Good
    ('Wicked: For Good', 11, '2026-08-04', '20:30', 1800.00),
    ('Wicked: For Good', 4,  '2026-08-08', '18:45', 1600.00),
    ('Wicked: For Good', 23, '2026-08-07', '19:15', 1300.00),      -- Cine Star, Multan

    -- The Housemaid
    ('The Housemaid', 4,  '2026-08-05', '18:45', 900.00),
    ('The Housemaid', 6,  '2026-08-09', '22:15', 950.00),
    ('The Housemaid', 17, '2026-08-04', '21:45', 850.00),          -- Cinepax, Jinnah Park, Rawalpindi

    -- Spider-Man: Brand New Day (wide release - extra shows across the country)
    ('Spider-Man: Brand New Day', 11, '2026-08-03', '15:00', 2000.00),
    ('Spider-Man: Brand New Day', 5,  '2026-08-04', '19:00', 2200.00),
    ('Spider-Man: Brand New Day', 12, '2026-08-06', '17:30', 1500.00),
    ('Spider-Man: Brand New Day', 1,  '2026-08-07', '20:00', 1300.00),
    ('Spider-Man: Brand New Day', 3,  '2026-08-08', '18:00', 1200.00),
    ('Spider-Man: Brand New Day', 8,  '2026-08-09', '21:00', 2500.00),
    ('Spider-Man: Brand New Day', 7,  '2026-08-10', '16:30', 1100.00),
    ('Spider-Man: Brand New Day', 11, '2026-08-10', '20:30', 2100.00),
    ('Spider-Man: Brand New Day', 18, '2026-08-04', '20:00', 1300.00),   -- Cinepax, Giga Mall WTC, Rawalpindi
    ('Spider-Man: Brand New Day', 25, '2026-08-06', '21:00', 1200.00),   -- Cinepax, Multan
    ('Spider-Man: Brand New Day', 26, '2026-08-08', '19:30', 1100.00),   -- Cinepax, Peshawar
    ('Spider-Man: Brand New Day', 29, '2026-08-09', '20:00', 1100.00),   -- Cinepax, Quetta

    -- Avengers: Doomsday (advance booking - real Dec 18, 2026 release)
    ('Avengers: Doomsday', 11, '2026-12-18', '20:00', 2500.00),
    ('Avengers: Doomsday', 13, '2026-12-18', '21:00', 1800.00),
    ('Avengers: Doomsday', 24, '2026-12-18', '20:30', 1500.00),   -- Cinepax, Multan

    -- Toy Story 5
    ('Toy Story 5', 7,  '2026-08-03', '13:00', 900.00),
    ('Toy Story 5', 9,  '2026-08-06', '12:30', 700.00),
    ('Toy Story 5', 14, '2026-08-10', '14:00', 750.00),
    ('Toy Story 5', 19, '2026-08-05', '13:30', 700.00),            -- Cinepax, Giga Mall WTC, Rawalpindi

    -- The Odyssey
    ('The Odyssey', 6,  '2026-08-04', '19:30', 1400.00),
    ('The Odyssey', 4,  '2026-08-08', '20:15', 1300.00),
    ('The Odyssey', 27, '2026-08-09', '19:00', 1000.00),           -- Cinepax, Sialkot

    -- Minions 3
    ('Minions 3', 9,  '2026-08-04', '15:30', 700.00),
    ('Minions 3', 14, '2026-08-07', '14:00', 750.00),
    ('Minions 3', 7,  '2026-08-10', '13:00', 720.00),
    ('Minions 3', 20, '2026-08-06', '14:30', 650.00),              -- Cinepax, Hyderabad

    -- Supergirl
    ('Supergirl', 2,  '2026-08-04', '18:30', 1000.00),
    ('Supergirl', 13, '2026-08-09', '19:45', 1100.00),
    ('Supergirl', 28, '2026-08-08', '18:00', 850.00)               -- Cinepax, Gujranwala
) AS S(MovieTitle, HallID, ShowDate, ShowTime, TicketPrice);


ALTER TABLE Movie
ADD PosterURL VARCHAR(300) NULL,
    TrailerURL VARCHAR(300) NULL;
GO
 
-- ============================================================
-- Populate poster & trailer links per movie (matched by Title,
-- so this is safe regardless of MovieID insert order/drift)
-- ============================================================
 


UPDATE Movie SET
    PosterURL  = 'https://tse4.mm.bing.net/th/id/OIP.DCucwD9EtlHcKmYJCnPgMgHaK9?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=Y5Q8z66aV9U'
WHERE Title = 'Aag Lagay Basti Mein';
 
UPDATE Movie SET
    PosterURL  = 'https://tse3.mm.bing.net/th/id/OIP.Ve1Wkh7asBHn8p1ohyuFhAAAAA?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=Z0SpyQ588NQ'
WHERE Title = 'Bullah';
 
UPDATE Movie SET
    PosterURL  = 'https://th.bing.com/th/id/OIP.PTn1aq-vGwcKFfnsUewVxgHaJQ?w=128&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=_8Pn6d-a-fw'
WHERE Title = 'Delhi Gate';
 
UPDATE Movie SET
    PosterURL  = 'https://th.bing.com/th/id/OIP.67yDrurhXT7IBvsnFPZrCAHaLb?w=115&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=ouzEuRvdVC0'
WHERE Title = 'Mera Lyari';
 
UPDATE Movie SET
    PosterURL  = 'https://th.bing.com/th/id/OIP.AmW8XUycoYUrNE3tP-jFpgHaKX?w=123&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=pNPFlT--b94'
WHERE Title = 'Luv Di Saun';
 
UPDATE Movie SET
    PosterURL  = 'https://th.bing.com/th/id/OIP.jsIsK8rH54UB4pduUj5MpQHaLC?w=204&h=305&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=Q6G4WhB4OZY'
WHERE Title = 'Zombeid';
 
UPDATE Movie SET
    PosterURL  = 'https://tse1.mm.bing.net/th/id/OIP.abj47tAAkDgzSE_ekJrbGAHaLH?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=b0zvfQhlDKw'
WHERE Title = 'Psycho';
 
UPDATE Movie SET
    PosterURL  = 'https://tse2.mm.bing.net/th/id/OIP.zUQAeCdRKwIjX3XjQ9KWWAHaLQ?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=GuCejewteF8'
WHERE Title = 'The Super Mario Galaxy Movie';
 
UPDATE Movie SET
    PosterURL  = 'https://th.bing.com/th/id/OIP.bYmudvvp6KlPJiGAIGbfxwHaLu?w=198&h=314&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=vt98AlBDI9Y'
WHERE Title = 'Wicked: For Good';
 
UPDATE Movie SET
    PosterURL  = 'https://th.bing.com/th/id/OIP.U9h8DDEp4LJnGmoDbyzEkgHaME?w=195&h=319&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=48CtX6OgU3s'
WHERE Title = 'The Housemaid';
 
UPDATE Movie SET
    PosterURL  = 'https://th.bing.com/th/id/R.6b53f069498c04f0a3927a4738685ae3?rik=jIjBqABcB0ewVw&riu=http%3a%2f%2fwww.impawards.com%2f2026%2fposters%2fspiderman_brand_new_day_ver2.jpg&ehk=ALi9WrWkpUiMYYwVCKryihyPSvDArhBwWg3ctStf%2b0s%3d&risl=&pid=ImgRaw&r=0',
    TrailerURL = 'https://www.youtube.com/watch?v=8TZMtslA3UY'
WHERE Title = 'Spider-Man: Brand New Day';
 
UPDATE Movie SET
    PosterURL  = 'https://tse1.mm.bing.net/th/id/OIP.7duC_G5d2iZJsCYigLsArQHaK-?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=S5ehYTyjvrs'
WHERE Title = 'Avengers: Doomsday';
 
UPDATE Movie SET
    PosterURL  = 'https://tse1.mm.bing.net/th/id/OIP.oTGBd_7ph3k2V_81jzDwuAHaLH?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=c51ND9Hdbw0'
WHERE Title = 'Toy Story 5';
 
UPDATE Movie SET
    PosterURL  = 'https://tse1.mm.bing.net/th/id/OIP.s8I37Mq0QhIHOFO5TJCP-QHaLu?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=Mzw2ttJD2qQ'
WHERE Title = 'The Odyssey';
 
UPDATE Movie SET
    PosterURL  = 'https://tse4.mm.bing.net/th/id/OIP.45TMirLOFVKNL0uKgHdKiwHaLC?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=UoZqKMZyf3U'
WHERE Title = 'Minions 3';
 
UPDATE Movie SET
    PosterURL  = 'https://tse1.mm.bing.net/th/id/OIP.ivFcO9cpsox5bMaNj9yakQHaLH?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
    TrailerURL = 'https://www.youtube.com/watch?v=s1-pfiVMKAs'
WHERE Title = 'Supergirl';

ALTER TABLE Booking ADD CancellationReason VARCHAR(255) NULL;

UPDATE Show
SET ShowDate = DATEADD(DAY, 7, ShowDate)
WHERE ShowDate < CAST(GETDATE() AS DATE);

SELECT ShowID, MovieID, HallID, ShowDate, ShowTime
FROM Show
WHERE ShowDate < CAST(GETDATE() AS DATE);

SELECT *
FROM [User]

SELECT *
FROM Booking
WHERE BookingID = 158

SELECT *
FROM Booking
WHERE BookingStatus = 'Confirmed'

SELECT
    B.BookingID,
    B.UserID,
    U.firstName,
    U.lastName,
    U.Email,
    B.ShowID,
    M.Title AS MovieTitle,
    S.ShowDate,
    S.ShowTime,
    B.BookingDate,
    B.TotalAmount,
    B.TicketsNeeded,
    B.BookingStatus
FROM Booking B
INNER JOIN [User] U ON U.UserID = B.UserID
INNER JOIN Show S ON S.ShowID = B.ShowID
INNER JOIN Movie M ON M.MovieID = S.MovieID
WHERE (U.UserID = 2 or U.UserID = 1) and (B.BookingStatus = 'Pending' or B.BookingStatus = 'Confirmed');

SELECT *
FROM Review

SELECT *
FROM Booking

SELECT * FROM Show Where ShowID = 54


SELECT 
        B.TotalAmount, B.BookingStatus, M.Title, M.DurationMinutes, S.ShowDate, S.ShowTime, C.CinemaName, B.BookingDate,
        STRING_AGG(CONCAT(St.SeatRow, St.SeatNumber), ', ') AS AssignedSeats
    FROM Booking B
    INNER JOIN Show S ON B.ShowID = S.ShowID
    INNER JOIN Movie M ON S.MovieID = M.MovieID
    INNER JOIN Hall H ON S.HallID = H.HallID
    INNER JOIN Cinema C ON H.CinemaID = C.CinemaID
    LEFT JOIN BookingSeat BS ON B.BookingID = BS.BookingID
    LEFT JOIN Seat St ON BS.SeatID = St.SeatID
    WHERE B.BookingID = 5
    GROUP BY 
        B.TotalAmount, B.BookingStatus, M.Title, S.ShowDate, S.ShowTime, C.CinemaName, B.BookingDate

-- Physically free up any seats trapped by old Cancelled test bookings
DELETE FROM BookingSeat
WHERE BookingID IN (
    SELECT BookingID 
    FROM Booking 
    WHERE BookingStatus = 'Cancelled'
);