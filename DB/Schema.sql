/* ============================================================
   MOVIE TICKETING MANAGEMENT SYSTEM - SUPABASE (PostgreSQL)
   Converted from SQL Server. Run this in the Supabase SQL
   Editor (Project -> SQL Editor -> New query) on a fresh
   project. It creates its own schema in the default "postgres"
   database Supabase already gives you - there is no CREATE
   DATABASE / USE step in Postgres, so those two lines are gone.

   WHAT CHANGED FROM YOUR SQL SERVER VERSION (read this first):
   1. IDENTITY(1,1)              -> GENERATED ALWAYS AS IDENTITY
   2. [User], [Language], etc.   -> "User", "Language" (double
      quotes are Postgres's quoted-identifier syntax; case is
      preserved exactly so your existing FastAPI queries that
      reference "UserID", "firstName" etc. keep working as long
      as you also double-quote them there)
   3. bit / DEFAULT 1            -> BOOLEAN / DEFAULT TRUE
   4. DATETIME / GETDATE()       -> TIMESTAMPTZ / NOW()
   5. The T-SQL cursor that generated seats doesn't exist in
      Postgres - replaced with a single set-based INSERT using
      generate_series (simpler and faster, not a workaround)
   6. DATEADD(DAY,7,x)           -> x + 7  (Postgres adds integer
      days to a DATE directly)
   7. Every ALTER TABLE you'd run later (PosterURL, TrailerURL,
      CancellationReason, BookingSeat.ShowID) is folded straight
      into the CREATE TABLE statements below, since this is a
      fresh build - no need to replay your migration history.

   IMPORTANT SUPABASE-SPECIFIC GOTCHA:
   Supabase auto-exposes every table in the "public" schema
   through its REST API (PostgREST) unless Row Level Security
   (RLS) is enabled. Your "User" table holds PasswordHash - if
   RLS is left off, anyone with your project's anon key could
   query it directly over HTTP, bypassing FastAPI entirely. Since
   your backend talks to Postgres directly (not through the REST
   API), enabling RLS with no policies blocks the public API
   while leaving your FastAPI connection untouched. Section 2
   below does this for every table. If you later need Supabase's
   REST API or client SDKs to read specific tables (e.g. public
   movie listings), add a scoped SELECT policy for that table.
   ============================================================ */

-- ============================================================
-- SECTION 1: TABLES
-- ============================================================

CREATE TABLE "User" (
    "UserID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "firstName" VARCHAR(30) NOT NULL,
    "lastName" VARCHAR(30) NOT NULL,
    "Email" VARCHAR(100) NOT NULL,
    "PasswordHash" VARCHAR(255) NOT NULL,
    "IsActive" BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE "City" (
    "CityID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "CityName" VARCHAR(50) NOT NULL,
    "Province" VARCHAR(50) NOT NULL
);

CREATE TABLE "Cinema" (
    "CinemaID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "CinemaName" VARCHAR(100) NOT NULL,
    "BranchName" VARCHAR(100) NOT NULL,
    "CityID" INT NOT NULL,
    "Address" VARCHAR(200) NOT NULL,
    "ContactNumber" VARCHAR(20),
    CONSTRAINT "FK_Cinema_City" FOREIGN KEY ("CityID") REFERENCES "City"("CityID")
);

CREATE TABLE "Hall" (
    "HallID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "CinemaID" INT NOT NULL,
    "HallName" VARCHAR(50) NOT NULL,
    "ScreenType" VARCHAR(20) NOT NULL,
    "TotalSeats" INT NOT NULL,
    CONSTRAINT "FK_Hall_Cinema" FOREIGN KEY ("CinemaID") REFERENCES "Cinema"("CinemaID")
);

CREATE TABLE "Seat" (
    "SeatID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "HallID" INT NOT NULL,
    "SeatRow" CHAR(1) NOT NULL,
    "SeatNumber" INT NOT NULL,
    "SeatCategory" VARCHAR(20) NOT NULL DEFAULT 'Standard',
    CONSTRAINT "FK_Seat_Hall" FOREIGN KEY ("HallID") REFERENCES "Hall"("HallID"),
    CONSTRAINT "UQ_Seat" UNIQUE ("HallID", "SeatRow", "SeatNumber")
);

CREATE TABLE "Movie" (
    "MovieID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "Title" VARCHAR(150) NOT NULL,
    "Genre" VARCHAR(50) NOT NULL,
    "Language" VARCHAR(30) NOT NULL,
    "DurationMinutes" INT NOT NULL,
    "ReleaseDate" DATE NOT NULL,
    "Description" VARCHAR(500),
    "CensorRating" VARCHAR(10) NOT NULL DEFAULT 'U',
    "PosterURL" VARCHAR(300),
    "TrailerURL" VARCHAR(300)
);

CREATE TABLE "Show" (
    "ShowID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "MovieID" INT NOT NULL,
    "HallID" INT NOT NULL,
    "ShowDate" DATE NOT NULL,
    "ShowTime" TIME NOT NULL,
    "TicketPrice" DECIMAL(8,2) NOT NULL,
    CONSTRAINT "FK_Show_Movie" FOREIGN KEY ("MovieID") REFERENCES "Movie"("MovieID"),
    CONSTRAINT "FK_Show_Hall" FOREIGN KEY ("HallID") REFERENCES "Hall"("HallID")
);

CREATE TABLE "Booking" (
    "BookingID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "UserID" INT NOT NULL,
    "ShowID" INT NOT NULL,
    "BookingDate" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "TotalAmount" DECIMAL(8,2) NOT NULL,
    "BookingStatus" VARCHAR(20) NOT NULL DEFAULT 'Pending',
    "TicketsNeeded" INT NOT NULL DEFAULT 1,
    "CancellationReason" VARCHAR(255),
    CONSTRAINT "FK_Booking_User" FOREIGN KEY ("UserID") REFERENCES "User"("UserID"),
    CONSTRAINT "FK_Booking_Show" FOREIGN KEY ("ShowID") REFERENCES "Show"("ShowID")
);

CREATE TABLE "BookingSeat" (
    "BookingSeatID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "BookingID" INT NOT NULL,
    "ShowID" INT NOT NULL,
    "SeatID" INT NOT NULL,
    CONSTRAINT "FK_BookingSeat_Booking" FOREIGN KEY ("BookingID") REFERENCES "Booking"("BookingID"),
    CONSTRAINT "FK_BookingSeat_Show" FOREIGN KEY ("ShowID") REFERENCES "Show"("ShowID"),
    CONSTRAINT "FK_BookingSeat_Seat" FOREIGN KEY ("SeatID") REFERENCES "Seat"("SeatID"),
    CONSTRAINT "UQ_ShowSeat" UNIQUE ("ShowID", "SeatID")
);

CREATE TABLE "Payment" (
    "PaymentID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "BookingID" INT NOT NULL,
    "Amount" DECIMAL(8,2) NOT NULL,
    "PaymentMethod" VARCHAR(30) NOT NULL,
    "PaymentStatus" VARCHAR(20) NOT NULL DEFAULT 'Pending',
    "TransactionReference" VARCHAR(100),
    "PaymentDate" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT "FK_Payment_Booking" FOREIGN KEY ("BookingID") REFERENCES "Booking"("BookingID")
);

CREATE TABLE "Review" (
    "ReviewID" INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "MovieID" INT NOT NULL,
    "UserID" INT NOT NULL,
    "Rating" INT NULL CHECK ("Rating" BETWEEN 1 AND 5),
    "ReviewText" VARCHAR(1000) NOT NULL,
    "ParentReviewID" INT NULL,
    "CreatedAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT "FK_Review_Movie" FOREIGN KEY ("MovieID") REFERENCES "Movie"("MovieID"),
    CONSTRAINT "FK_Review_User" FOREIGN KEY ("UserID") REFERENCES "User"("UserID"),
    CONSTRAINT "FK_Review_Parent" FOREIGN KEY ("ParentReviewID") REFERENCES "Review"("ReviewID")
);

-- ============================================================
-- SECTION 2: LOCK DOWN SUPABASE'S AUTO-GENERATED REST API
--   Enables RLS with zero policies on every table, so the
--   public API can't read/write anything. Your FastAPI backend,
--   connecting with the direct Postgres connection string, is
--   unaffected - RLS only governs PostgREST's anon/authenticated
--   roles, not a direct database connection.
-- ============================================================
ALTER TABLE "User" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "City" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Cinema" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Hall" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Seat" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Movie" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Show" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Booking" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "BookingSeat" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Payment" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Review" ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- SECTION 3: DATA - CITY
-- ============================================================
INSERT INTO "City" ("CityName", "Province") VALUES
('Karachi', 'Sindh'),
('Lahore', 'Punjab'),
('Islamabad', 'Islamabad Capital Territory'),
('Rawalpindi', 'Punjab'),
('Faisalabad', 'Punjab'),
('Hyderabad', 'Sindh'),
('Multan', 'Punjab'),
('Peshawar', 'Khyber Pakhtunkhwa'),
('Sialkot', 'Punjab'),
('Gujranwala', 'Punjab'),
('Quetta', 'Balochistan');

-- ============================================================
-- DATA - CINEMA
-- ============================================================
INSERT INTO "Cinema" ("CinemaName", "BranchName", "CityID", "Address", "ContactNumber") VALUES
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
('Cinepax', 'Faisalabad', 5, 'D Ground, Faisalabad', '041-111246329'),
('Cinepax', 'Jinnah Park', 4, 'Jinnah Park, Committee Chowk, Rawalpindi', '051-111246329'),
('Cinepax', 'Giga Mall WTC', 4, 'Giga Mall, World Trade Centre, GT Road, DHA Phase II, Rawalpindi', '051-111246372'),
('Cinepax', 'Hyderabad', 6, 'Latifabad, Hyderabad', '022-111246329'),
('Cine Star', 'Multan', 7, 'Abdali Road, Multan', '061-111529292'),
('Cinepax', 'Multan', 7, 'Officers Colony, Multan', '061-111246329'),
('Cinepax', 'Peshawar', 8, 'University Road, Peshawar', '091-111246329'),
('Cinepax', 'Sialkot', 9, 'Paris Road, Sialkot', '052-111246329'),
('Cinepax', 'Gujranwala', 10, 'GT Road, Gujranwala', '055-111246329'),
('Cinepax', 'Quetta', 11, 'Jinnah Road, Quetta', '081-111246329');

-- ============================================================
-- DATA - HALL
-- ============================================================
INSERT INTO "Hall" ("CinemaID", "HallName", "ScreenType", "TotalSeats") VALUES
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
(11, 'Screen 1', '2D', 100),
(12, 'Screen 1', '2D', 100),
(12, 'Screen 2', '3D', 80),
(13, 'Gold Screen', '2D', 120),
(13, 'Platinum Screen', '3D', 90),
(14, 'Screen 1', '2D', 100),
(14, 'Screen 2', '2D', 90),
(15, 'Screen 1', '2D', 110),
(15, 'Screen 2', '3D', 90),
(16, 'Gold Screen', '2D', 100),
(16, 'Platinum Screen', '3D', 80),
(17, 'Screen 1', '2D', 100),
(18, 'Screen 1', '2D', 90),
(19, 'Screen 1', '2D', 90),
(20, 'Screen 1', '2D', 80);

-- ============================================================
-- DATA - SEAT
--   Set-based replacement for the SQL Server cursor: generates
--   rows A-E x seats 1-10 for every hall in one INSERT, using
--   chr(64+n) to turn 1..5 into 'A'..'E'.
-- ============================================================
INSERT INTO "Seat" ("HallID", "SeatRow", "SeatNumber", "SeatCategory")
SELECT
    h."HallID",
    r.row_letter,
    n.seat_num,
    CASE WHEN r.row_letter IN ('A','B') THEN 'Platinum'
         WHEN r.row_letter IN ('C','D') THEN 'Gold'
         ELSE 'Standard' END
FROM "Hall" h
CROSS JOIN (SELECT chr(64 + g) AS row_letter FROM generate_series(1, 5) AS g) r
CROSS JOIN generate_series(1, 10) AS n(seat_num);

-- ============================================================
-- DATA - MOVIE
-- ============================================================
INSERT INTO "Movie" ("Title", "Genre", "Language", "DurationMinutes", "ReleaseDate", "Description", "CensorRating") VALUES
('Aag Lagay Basti Mein', 'Crime/Drama', 'Urdu', 148, '2026-03-21', 'A crime-drama reuniting Fahad Mustafa and Mahira Khan, presented by ARY Films and Big Bang Entertainment.', 'U/A'),
('Bullah', 'Drama', 'Punjabi', 135, '2026-03-21', 'A drama starring Shaan Shahid and Sara Loren, produced by Shake Films.', 'U/A'),
('Delhi Gate', 'Historical/Drama', 'Urdu', 140, '2026-03-21', 'A historical drama directed by Nadeem Cheema featuring Jawed Sheikh and Shafqat Cheema.', 'U/A'),
('Mera Lyari', 'Drama', 'Urdu', 125, '2026-05-08', 'A drama set in Karachi''s Lyari neighbourhood starring Ayesha Omar and Dananeer Mobeen.', 'U/A'),
('Luv Di Saun', 'Romance/Comedy', 'Punjabi', 130, '2026-05-27', 'A romantic comedy from ARY Films starring Farhan Saeed and Babar Ali.', 'U'),
('Zombeid', 'Horror/Comedy', 'Urdu', 128, '2026-05-27', 'A horror-comedy from Filmwala Pictures starring Fahad Mustafa and Mehwish Hayat.', 'U/A'),
('Psycho', 'Thriller', 'Urdu', 122, '2026-05-27', 'A psychological thriller written, directed by and starring Shaan Shahid, with Meera and Sonya Hussyn.', 'A'),
('The Super Mario Galaxy Movie', 'Animation/Adventure', 'English', 104, '2026-04-01', 'Animated adventure distributed in Pakistan by Universal Pictures International.', 'U'),
('Wicked: For Good', 'Musical/Fantasy', 'English', 137, '2025-11-21', 'The second part of the Wicked musical fantasy, distributed by Universal Pictures International.', 'U'),
('The Housemaid', 'Thriller', 'English', 119, '2025-12-25', 'Psychological thriller that had an extended theatrical run in Pakistani cinemas in early 2026.', 'A'),
('Spider-Man: Brand New Day', 'Action/Adventure', 'English', 145, '2026-07-31', 'Peter Parker fights crime full-time in a world that no longer remembers him, starring Tom Holland, Zendaya and Sadie Sink. Distributed in Pakistan by Sony Pictures/Marvel Studios.', 'U/A'),
('Avengers: Doomsday', 'Action/Sci-Fi', 'English', 150, '2026-12-18', 'The Avengers face Doctor Doom (Robert Downey Jr.) alongside the X-Men and Fantastic Four, directed by the Russo brothers. Advance bookings only - releases worldwide December 18, 2026.', 'U/A'),
('Toy Story 5', 'Animation/Family', 'English', 102, '2026-06-19', 'Woody, Buzz and the gang face a new tech-savvy rival, Lilypad, for Bonnie''s attention. A Pixar production distributed by Walt Disney Studios.', 'U'),
('The Odyssey', 'Adventure/Drama', 'English', 150, '2026-07-17', 'Christopher Nolan''s epic retelling of Homer''s Odyssey, distributed by Universal Pictures International.', 'U/A'),
('Minions 3', 'Animation/Comedy', 'English', 95, '2026-07-01', 'The Minions return in a new adventure from Illumination, distributed by Universal Pictures International.', 'U'),
('Supergirl', 'Action/Adventure', 'English', 130, '2026-06-26', 'Milly Alcock stars as Kara Zor-El in this DC Studios adventure, distributed by Warner Bros.', 'U/A');

-- Poster & trailer links (matched by Title so insert order doesn't matter)
UPDATE "Movie" SET "PosterURL" = 'https://tse4.mm.bing.net/th/id/OIP.DCucwD9EtlHcKmYJCnPgMgHaK9?r=0&rs=1&pid=ImgDetMain&o=7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=Y5Q8z66aV9U' WHERE "Title" = 'Aag Lagay Basti Mein';
UPDATE "Movie" SET "PosterURL" = 'https://tse3.mm.bing.net/th/id/OIP.Ve1Wkh7asBHn8p1ohyuFhAAAAA?r=0&rs=1&pid=ImgDetMain&o=7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=Z0SpyQ588NQ' WHERE "Title" = 'Bullah';
UPDATE "Movie" SET "PosterURL" = 'https://th.bing.com/th/id/OIP.PTn1aq-vGwcKFfnsUewVxgHaJQ?w=128&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=_8Pn6d-a-fw' WHERE "Title" = 'Delhi Gate';
UPDATE "Movie" SET "PosterURL" = 'https://th.bing.com/th/id/OIP.67yDrurhXT7IBvsnFPZrCAHaLb?w=115&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=ouzEuRvdVC0' WHERE "Title" = 'Mera Lyari';
UPDATE "Movie" SET "PosterURL" = 'https://th.bing.com/th/id/OIP.AmW8XUycoYUrNE3tP-jFpgHaKX?w=123&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=pNPFlT--b94' WHERE "Title" = 'Luv Di Saun';
UPDATE "Movie" SET "PosterURL" = 'https://th.bing.com/th/id/OIP.jsIsK8rH54UB4pduUj5MpQHaLC?w=204&h=305&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=Q6G4WhB4OZY' WHERE "Title" = 'Zombeid';
UPDATE "Movie" SET "PosterURL" = 'https://tse1.mm.bing.net/th/id/OIP.abj47tAAkDgzSE_ekJrbGAHaLH?r=0&rs=1&pid=ImgDetMain&o=7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=b0zvfQhlDKw' WHERE "Title" = 'Psycho';
UPDATE "Movie" SET "PosterURL" = 'https://tse2.mm.bing.net/th/id/OIP.zUQAeCdRKwIjX3XjQ9KWWAHaLQ?r=0&rs=1&pid=ImgDetMain&o=7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=GuCejewteF8' WHERE "Title" = 'The Super Mario Galaxy Movie';
UPDATE "Movie" SET "PosterURL" = 'https://th.bing.com/th/id/OIP.bYmudvvp6KlPJiGAIGbfxwHaLu?w=198&h=314&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=vt98AlBDI9Y' WHERE "Title" = 'Wicked: For Good';
UPDATE "Movie" SET "PosterURL" = 'https://th.bing.com/th/id/OIP.U9h8DDEp4LJnGmoDbyzEkgHaME?w=195&h=319&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=48CtX6OgU3s' WHERE "Title" = 'The Housemaid';
UPDATE "Movie" SET "PosterURL" = 'https://th.bing.com/th/id/R.6b53f069498c04f0a3927a4738685ae3?rik=jIjBqABcB0ewVw&riu=http%3a%2f%2fwww.impawards.com%2f2026%2fposters%2fspiderman_brand_new_day_ver2.jpg&ehk=ALi9WrWkpUiMYYwVCKryihyPSvDArhBwWg3ctStf%2b0s%3d&risl=&pid=ImgRaw&r=0', "TrailerURL" = 'https://www.youtube.com/watch?v=8TZMtslA3UY' WHERE "Title" = 'Spider-Man: Brand New Day';
UPDATE "Movie" SET "PosterURL" = 'https://tse1.mm.bing.net/th/id/OIP.7duC_G5d2iZJsCYigLsArQHaK-?r=0&rs=1&pid=ImgDetMain&o=7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=S5ehYTyjvrs' WHERE "Title" = 'Avengers: Doomsday';
UPDATE "Movie" SET "PosterURL" = 'https://tse1.mm.bing.net/th/id/OIP.oTGBd_7ph3k2V_81jzDwuAHaLH?r=0&rs=1&pid=ImgDetMain&o=7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=c51ND9Hdbw0' WHERE "Title" = 'Toy Story 5';
UPDATE "Movie" SET "PosterURL" = 'https://tse1.mm.bing.net/th/id/OIP.s8I37Mq0QhIHOFO5TJCP-QHaLu?r=0&rs=1&pid=ImgDetMain&o=7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=Mzw2ttJD2qQ' WHERE "Title" = 'The Odyssey';
UPDATE "Movie" SET "PosterURL" = 'https://tse4.mm.bing.net/th/id/OIP.45TMirLOFVKNL0uKgHdKiwHaLC?r=0&rs=1&pid=ImgDetMain&o=7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=UoZqKMZyf3U' WHERE "Title" = 'Minions 3';
UPDATE "Movie" SET "PosterURL" = 'https://tse1.mm.bing.net/th/id/OIP.ivFcO9cpsox5bMaNj9yakQHaLH?r=0&rs=1&pid=ImgDetMain&o=7&rm=3', "TrailerURL" = 'https://www.youtube.com/watch?v=s1-pfiVMKAs' WHERE "Title" = 'Supergirl';

-- ============================================================
-- DATA - SHOW
--   MovieID looked up by Title so this doesn't depend on
--   insert order. The VALUES-derived-table syntax is standard
--   SQL and needs no changes for Postgres.
-- ============================================================
INSERT INTO "Show" ("MovieID", "HallID", "ShowDate", "ShowTime", "TicketPrice")
SELECT (SELECT "MovieID" FROM "Movie" WHERE "Title" = s.movietitle), s.hallid, s.showdate::date, s.showtime::time, s.ticketprice::decimal(8,2)
FROM (VALUES
    ('Aag Lagay Basti Mein', 1,  '2026-08-03', '18:00', 900.00),
    ('Aag Lagay Basti Mein', 12, '2026-08-05', '19:00', 950.00),
    ('Aag Lagay Basti Mein', 8,  '2026-08-08', '21:00', 1000.00),
    ('Aag Lagay Basti Mein', 16, '2026-08-06', '19:30', 850.00),

    ('Bullah', 9,  '2026-08-04', '17:30', 800.00),
    ('Bullah', 3,  '2026-08-07', '20:00', 850.00),
    ('Bullah', 24, '2026-08-05', '18:00', 750.00),

    ('Delhi Gate', 3,  '2026-08-03', '19:15', 1000.00),
    ('Delhi Gate', 13, '2026-08-06', '18:30', 1000.00),
    ('Delhi Gate', 18, '2026-08-08', '19:00', 900.00),

    ('Mera Lyari', 12, '2026-08-04', '16:00', 700.00),
    ('Mera Lyari', 10, '2026-08-09', '17:00', 750.00),
    ('Mera Lyari', 20, '2026-08-07', '16:30', 650.00),

    ('Luv Di Saun', 10, '2026-08-05', '20:00', 900.00),
    ('Luv Di Saun', 1,  '2026-08-08', '19:30', 900.00),
    ('Luv Di Saun', 28, '2026-08-06', '20:00', 800.00),

    ('Zombeid', 6,  '2026-08-04', '22:00', 1000.00),
    ('Zombeid', 8,  '2026-08-07', '21:30', 1050.00),
    ('Zombeid', 22, '2026-08-09', '21:00', 900.00),

    ('Psycho', 13, '2026-08-05', '19:00', 850.00),
    ('Psycho', 3,  '2026-08-09', '21:00', 900.00),
    ('Psycho', 27, '2026-08-08', '20:30', 800.00),

    ('The Super Mario Galaxy Movie', 14, '2026-08-03', '15:00', 1200.00),
    ('The Super Mario Galaxy Movie', 7,  '2026-08-06', '13:30', 1100.00),
    ('The Super Mario Galaxy Movie', 21, '2026-08-05', '14:00', 950.00),

    ('Wicked: For Good', 11, '2026-08-04', '20:30', 1800.00),
    ('Wicked: For Good', 4,  '2026-08-08', '18:45', 1600.00),
    ('Wicked: For Good', 23, '2026-08-07', '19:15', 1300.00),

    ('The Housemaid', 4,  '2026-08-05', '18:45', 900.00),
    ('The Housemaid', 6,  '2026-08-09', '22:15', 950.00),
    ('The Housemaid', 17, '2026-08-04', '21:45', 850.00),

    ('Spider-Man: Brand New Day', 11, '2026-08-03', '15:00', 2000.00),
    ('Spider-Man: Brand New Day', 5,  '2026-08-04', '19:00', 2200.00),
    ('Spider-Man: Brand New Day', 12, '2026-08-06', '17:30', 1500.00),
    ('Spider-Man: Brand New Day', 1,  '2026-08-07', '20:00', 1300.00),
    ('Spider-Man: Brand New Day', 3,  '2026-08-08', '18:00', 1200.00),
    ('Spider-Man: Brand New Day', 8,  '2026-08-09', '21:00', 2500.00),
    ('Spider-Man: Brand New Day', 7,  '2026-08-10', '16:30', 1100.00),
    ('Spider-Man: Brand New Day', 11, '2026-08-10', '20:30', 2100.00),
    ('Spider-Man: Brand New Day', 18, '2026-08-04', '20:00', 1300.00),
    ('Spider-Man: Brand New Day', 25, '2026-08-06', '21:00', 1200.00),
    ('Spider-Man: Brand New Day', 26, '2026-08-08', '19:30', 1100.00),
    ('Spider-Man: Brand New Day', 29, '2026-08-09', '20:00', 1100.00),

    ('Avengers: Doomsday', 11, '2026-12-18', '20:00', 2500.00),
    ('Avengers: Doomsday', 13, '2026-12-18', '21:00', 1800.00),
    ('Avengers: Doomsday', 24, '2026-12-18', '20:30', 1500.00),

    ('Toy Story 5', 7,  '2026-08-03', '13:00', 900.00),
    ('Toy Story 5', 9,  '2026-08-06', '12:30', 700.00),
    ('Toy Story 5', 14, '2026-08-10', '14:00', 750.00),
    ('Toy Story 5', 19, '2026-08-05', '13:30', 700.00),

    ('The Odyssey', 6,  '2026-08-04', '19:30', 1400.00),
    ('The Odyssey', 4,  '2026-08-08', '20:15', 1300.00),
    ('The Odyssey', 27, '2026-08-09', '19:00', 1000.00),

    ('Minions 3', 9,  '2026-08-04', '15:30', 700.00),
    ('Minions 3', 14, '2026-08-07', '14:00', 750.00),
    ('Minions 3', 7,  '2026-08-10', '13:00', 720.00),
    ('Minions 3', 20, '2026-08-06', '14:30', 650.00),

    ('Supergirl', 2,  '2026-08-04', '18:30', 1000.00),
    ('Supergirl', 13, '2026-08-09', '19:45', 1100.00),
    ('Supergirl', 28, '2026-08-08', '18:00', 850.00)
) AS s(movietitle, hallid, showdate, showtime, ticketprice);

-- ============================================================
-- SECTION 4: MAINTENANCE - keep the schedule from going stale
--   Postgres adds an integer number of days to a DATE directly
--   (no DATEADD needed). Re-run whenever ShowDate falls behind.
-- ============================================================
UPDATE "Show"
SET "ShowDate" = "ShowDate" + 7
WHERE "ShowDate" < CURRENT_DATE;

-- ============================================================
-- SECTION 5: REFERENCE QUERIES (examples - not part of the
--   schema itself, safe to delete once you've ported the
--   equivalent logic into your FastAPI endpoints)
-- ============================================================

-- Who booked what, with the movie name
SELECT
    b."BookingID",
    b."UserID",
    u."firstName",
    u."lastName",
    u."Email",
    b."ShowID",
    m."Title" AS "MovieTitle",
    s."ShowDate",
    s."ShowTime",
    b."BookingDate",
    b."TotalAmount",
    b."TicketsNeeded",
    b."BookingStatus"
FROM "Booking" b
INNER JOIN "User" u ON u."UserID" = b."UserID"
INNER JOIN "Show" s ON s."ShowID" = b."ShowID"
INNER JOIN "Movie" m ON m."MovieID" = s."MovieID"
WHERE b."UserID" IN (1, 2)
  AND b."BookingStatus" IN ('Pending', 'Confirmed');

-- Full booking receipt: amount, movie, cinema, and every seat assigned
-- (CONCAT and STRING_AGG both work unchanged in Postgres)
SELECT
    b."TotalAmount", b."BookingStatus", m."Title", m."DurationMinutes",
    s."ShowDate", s."ShowTime", c."CinemaName", b."BookingDate",
    STRING_AGG(CONCAT(st."SeatRow", st."SeatNumber"), ', ') AS "AssignedSeats"
FROM "Booking" b
INNER JOIN "Show" s ON b."ShowID" = s."ShowID"
INNER JOIN "Movie" m ON s."MovieID" = m."MovieID"
INNER JOIN "Hall" h ON s."HallID" = h."HallID"
INNER JOIN "Cinema" c ON h."CinemaID" = c."CinemaID"
LEFT JOIN "BookingSeat" bs ON b."BookingID" = bs."BookingID"
LEFT JOIN "Seat" st ON bs."SeatID" = st."SeatID"
WHERE b."BookingID" = 5
GROUP BY b."TotalAmount", b."BookingStatus", m."Title", m."DurationMinutes",
         s."ShowDate", s."ShowTime", c."CinemaName", b."BookingDate";

-- Free up seats trapped by old cancelled test bookings
DELETE FROM "BookingSeat"
WHERE "BookingID" IN (
    SELECT "BookingID" FROM "Booking" WHERE "BookingStatus" = 'Cancelled'
);