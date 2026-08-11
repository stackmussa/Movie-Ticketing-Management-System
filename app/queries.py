verify_email = '''
        SELECT UserID
        FROM [User]
        WHERE Email = ?
'''
verify_password = '''
        SELECT PasswordHash 
        FROM [User] 
        WHERE Email = ?
'''
authorize_owner = '''
        SELECT UserID, BookingStatus
        FROM Booking 
        WHERE BookingID = ?
'''
get_shows_query = """
SELECT 
    M.Title, 
    M.Genre,
    M.DurationMinutes,
    M.PosterURL,
    M.TrailerURL,
    S.ShowDate, 
    S.ShowTime, 
    C.CinemaName, 
    C.Address, 
    S.TicketPrice,
    CT.CityName AS City
FROM Show S
INNER JOIN Movie M ON S.MovieID = M.MovieID
INNER JOIN Hall H ON S.HallID = H.HallID
INNER JOIN Cinema C ON H.CinemaID = C.CinemaID
INNER JOIN City CT ON C.CityID = CT.CityID
WHERE S.ShowDate > CAST(GETDATE() AS DATE) 
   OR (S.ShowDate = CAST(GETDATE() AS DATE) AND S.ShowTime > CAST(GETDATE() AS TIME))
ORDER BY S.ShowDate, S.ShowTime
"""

get_specific_show = """
SELECT 
    M.Title,
    M.Genre,
    M.DurationMinutes,
    M.PosterURL,
    M.TrailerURL,
    S.ShowDate, 
    S.ShowTime, 
    C.CinemaName, 
    C.Address, 
    S.TicketPrice,
    CT.CityName AS City
FROM Show S
INNER JOIN Movie M ON S.MovieID = M.MovieID
INNER JOIN Hall H ON S.HallID = H.HallID
INNER JOIN Cinema C ON H.CinemaID = C.CinemaID
INNER JOIN City CT ON C.CityID = CT.CityID
WHERE M.Title LIKE '%' + ? + '%'
  AND (S.ShowDate > CAST(GETDATE() AS DATE) 
       OR (S.ShowDate = CAST(GETDATE() AS DATE) AND S.ShowTime > CAST(GETDATE() AS TIME)))
ORDER BY 
    CASE 
        WHEN M.Title = ? THEN 1          -- Rank 1: Exact match
        WHEN M.Title LIKE ? + '%' THEN 2 -- Rank 2: Starts with the typed string
        ELSE 3                           -- Rank 3: Contains the string anywhere
    END,
    S.ShowDate, S.ShowTime
"""

# Fetch distinct genres from the Movie table for filter dropdown
get_distinct_genres = '''
    SELECT DISTINCT Genre FROM Movie ORDER BY Genre ASC
'''

# Fetch the date range of upcoming shows (min today, max last show)
get_show_date_range = '''
    SELECT 
        MIN(S.ShowDate) AS MinDate,
        MAX(S.ShowDate) AS MaxDate
    FROM Show S
    WHERE S.ShowDate >= CAST(GETDATE() AS DATE)
'''


Cities_query = '''SELECT DISTINCT CityName
                        FROM City
                        ORDER BY CityName ASC'''

Categories_query = '''SELECT DISTINCT SeatCategory
                        FROM Seat
                        ORDER BY SeatCategory ASC'''

# Based upon Selected Movie Title & City, query gives the results 
Select_City_Title_Query='''SELECT S.ShowID, S.TicketPrice, S.HallID, C.CinemaName
            FROM Show AS S
            INNER JOIN Movie AS M ON S.MovieID = M.MovieID
            INNER JOIN Hall AS H ON S.HallID = H.HallID
            INNER JOIN Cinema AS C ON H.CinemaID = C.CinemaID
            INNER JOIN City AS Ct ON C.CityID = Ct.CityID
            WHERE M.Title = ? AND Ct.CityName = ? AND S.ShowDate >= CAST(GETDATE() AS DATE)
            ORDER BY S.ShowDate ASC, S.ShowTime ASC
        '''
# Check Seat Availability for requested Category in this Hallexp
        # Find unbooked seats for this specific ShowID
seat_query = '''
            SELECT St.SeatID, St.SeatRow, St.SeatNumber
            FROM Seat St
            WHERE St.HallID = ? AND St.SeatCategory = ?
            AND NOT EXISTS (
                SELECT 1
                FROM BookingSeat BS
                INNER JOIN Booking B ON BS.BookingID = B.BookingID
                WHERE B.ShowID = ? AND B.BookingStatus != 'Cancelled'
                AND BS.SeatID = St.SeatID
            )
            ORDER BY St.SeatRow ASC, St.SeatNumber ASC
        '''
insert_booking_query = '''
            INSERT INTO Booking (UserID, ShowID, TotalAmount, TicketsNeeded, BookingStatus)
            OUTPUT INSERTED.BookingID
            VALUES (?, ?, ?, ?, 'Pending')
        '''

insert_seat_query = "INSERT INTO BookingSeat (BookingID, ShowID, SeatID) VALUES (?, ?, ?)"

get_user_order = '''
    SELECT 
        B.BookingID, 
        B.TotalAmount, 
        B.BookingStatus, 
        M.Title, 
        M.DurationMinutes,
        C.CinemaName, 
        C.Address, 
        P.PaymentMethod,
        S.ShowDate,
        S.ShowTime,
        B.BookingDate,
        STRING_AGG(CONCAT(St.SeatRow, St.SeatNumber), ', ') AS AssignedSeats
    FROM Booking B
    INNER JOIN Show S ON B.ShowID = S.ShowID
    INNER JOIN Movie M ON S.MovieID = M.MovieID
    INNER JOIN Hall H ON S.HallID = H.HallID
    INNER JOIN Cinema C ON H.CinemaID = C.CinemaID
    LEFT JOIN Payment P ON B.BookingID = P.BookingID
    LEFT JOIN BookingSeat BS ON B.BookingID = BS.BookingID
    LEFT JOIN Seat St ON BS.SeatID = St.SeatID
    WHERE B.UserID = ?
    GROUP BY 
        B.BookingID, B.TotalAmount, B.BookingStatus, M.Title, M.DurationMinutes, C.CinemaName, 
        C.Address, P.PaymentMethod, S.ShowDate, S.ShowTime, B.BookingDate
    ORDER BY B.BookingDate DESC
'''

# Fetch all seats and their booking status for a specific Show and Hall
get_interactive_seats_query = '''
    SELECT 
        St.SeatID, St.SeatRow, St.SeatNumber, St.SeatCategory,
        CASE 
            WHEN B.BookingID IS NOT NULL THEN 1 
            ELSE 0 
        END AS IsBooked
    FROM Seat St
    LEFT JOIN BookingSeat BS ON St.SeatID = BS.SeatID
    LEFT JOIN Booking B ON BS.BookingID = B.BookingID 
        AND B.ShowID = ? 
        AND B.BookingStatus != 'Cancelled'
    WHERE St.HallID = ?
    ORDER BY St.SeatRow ASC, St.SeatNumber ASC
'''
# Fetch detailed booking info for the payment checkout page
get_booking_details_query = '''
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
    WHERE B.BookingID = ?
    GROUP BY 
        B.TotalAmount, B.BookingStatus, M.Title, M.DurationMinutes, S.ShowDate, S.ShowTime, C.CinemaName, B.BookingDate
'''

# get the total amount for user's booking
get_booking_amount='''
    SELECT TotalAmount, BookingStatus
    FROM Booking
    WHERE BookingID = ?
'''
# Insert the successful payment record (Generates a new PaymentID)
insert_payment_query = '''
    INSERT INTO Payment (BookingID, Amount, PaymentMethod, PaymentStatus, TransactionReference)
    OUTPUT INSERTED.PaymentID
    VALUES (?, ?, ?, 'Success', ?)
'''

# Update the booking status to Confirmed once paid
update_booking_status_query = '''
    UPDATE Booking 
    SET BookingStatus = 'Confirmed' 
    WHERE BookingID = ?
'''

#cancellation of booking
cancel_booking = '''
    UPDATE Booking
    SET BookingStatus = 'Cancelled'
    WHERE BookingID = ?
'''
# Cancel the Booked Seat
delete_booking_seat = '''
    DELETE FROM BookingSeat
    WHERE BookingID = ?
'''

get_booking_status = '''
    SELECT BookingStatus 
    FROM Booking 
    WHERE BookingID = ?
'''

get_confirmed_pending_seats = """
    SELECT s.SeatRow, s.SeatNumber
    FROM Seat s
    INNER JOIN BookingSeat bs ON s.SeatID = bs.SeatID
    INNER JOIN Booking b ON bs.BookingID = b.BookingID
    WHERE b.ShowID = ? AND b.BookingStatus IN ('Pending', 'Confirmed')
"""

# ============================================================
# REVIEW QUERIES
# ============================================================

# Fetch all reviews (top-level + replies) for a specific movie
get_movie_reviews = '''
    SELECT 
        R.ReviewID,
        R.MovieID,
        R.UserID,
        U.firstName + ' ' + U.lastName AS UserName,
        R.Rating,
        R.ReviewText,
        R.ParentReviewID,
        R.CreatedAt
    FROM Review R
    INNER JOIN [User] U ON R.UserID = U.UserID
    WHERE R.MovieID = ?
    ORDER BY 
        COALESCE(R.ParentReviewID, R.ReviewID) ASC,
        R.ParentReviewID ASC,
        R.CreatedAt ASC
'''

# Get the MovieID from a title (helper)
get_movie_id_by_title = '''
    SELECT MovieID FROM Movie WHERE Title = ?
'''

# Insert a new top-level review (with rating)
insert_review = '''
    INSERT INTO Review (MovieID, UserID, Rating, ReviewText)
    OUTPUT INSERTED.ReviewID
    VALUES (?, ?, ?, ?)
'''

# Insert a reply to an existing review (no rating)
insert_reply = '''
    INSERT INTO Review (MovieID, UserID, Rating, ReviewText, ParentReviewID)
    OUTPUT INSERTED.ReviewID
    VALUES (?, ?, NULL, ?, ?)
'''

# Get the average rating for a movie
get_movie_avg_rating = '''
    SELECT 
        AVG(CAST(Rating AS FLOAT)) AS AvgRating,
        COUNT(*) AS TotalReviews
    FROM Review
    WHERE MovieID = ? AND ParentReviewID IS NULL
'''

# Fetch the owner (UserID) of a specific review
get_review_owner = '''
    SELECT UserID FROM Review WHERE ReviewID = ?
'''

# Delete all child replies of a review (must run before deleting the parent)
delete_review_replies = '''
    DELETE FROM Review WHERE ParentReviewID = ?
'''

# Delete a specific review by its ID
delete_review = '''
    DELETE FROM Review WHERE ReviewID = ?
'''
