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
get_shows_query = '''SELECT DISTINCT M.Title, M.Genre, M.Language, M.DurationMinutes, M.Description,
                M.CensorRating, S.ShowTime, S.ShowDate, S.TicketPrice, H.HallName, H.ScreenType, H.TotalSeats,
                C.CinemaName, C.BranchName, C.Address, C.ContactNumber, Ct.CityName AS City
            FROM Show AS S
            INNER JOIN Movie AS M ON S.MovieID = M.MovieID
            INNER JOIN HALL AS H ON S.HallID = H.HallID
            INNER JOIN Cinema AS C ON H.CinemaID = C.CinemaID
            INNER JOIN City AS Ct ON C.CityID = Ct.CityID
            WHERE S.ShowDate >= CAST(GETDATE() AS DATE)
            ORDER BY S.ShowDate ASC, S.ShowTime ASC'''

get_specific_show = '''SELECT DISTINCT M.Title, M.Genre, M.Language, M.DurationMinutes, M.Description, 
                M.CensorRating, S.ShowTime, S.ShowDate, S.TicketPrice, H.HallName, H.ScreenType, H.TotalSeats, 
                C.CinemaName, C.BranchName, C.Address, C.ContactNumber, Ct.CityName AS City
            FROM Show AS S
            INNER JOIN Movie AS M ON S.MovieID = M.MovieID
            INNER JOIN HALL AS H ON S.HallID = H.HallID
            INNER JOIN Cinema AS C ON H.CinemaID = C.CinemaID
            INNER JOIN City AS Ct ON C.CityID = Ct.CityID
            WHERE M.Title = ? AND S.ShowDate >= CAST(GETDATE() AS DATE)
            ORDER BY S.ShowDate ASC, S.ShowTime ASC'''

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
# Check Seat Availability for requested Category in this Hall
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

insert_seat_query = "INSERT INTO BookingSeat (BookingID, SeatID) VALUES (?, ?)"

get_user_order = '''
    SELECT 
        B.BookingID, 
        B.TotalAmount, 
        B.BookingStatus, 
        M.Title, 
        C.CinemaName, 
        C.Address, 
        P.PaymentMethod
    FROM Booking B
    INNER JOIN Show S ON B.ShowID = S.ShowID
    INNER JOIN Movie M ON S.MovieID = M.MovieID
    INNER JOIN Hall H ON S.HallID = H.HallID
    INNER JOIN Cinema C ON H.CinemaID = C.CinemaID
    LEFT JOIN Payment P ON B.BookingID = P.BookingID
    WHERE B.UserID = ?
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
    SELECT B.TotalAmount, B.BookingStatus, M.Title, S.ShowDate, S.ShowTime, C.CinemaName
    FROM Booking B
    INNER JOIN Show S ON B.ShowID = S.ShowID
    INNER JOIN Movie M ON S.MovieID = M.MovieID
    INNER JOIN Hall H ON S.HallID = H.HallID
    INNER JOIN Cinema C ON H.CinemaID = C.CinemaID
    WHERE B.BookingID = ?
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