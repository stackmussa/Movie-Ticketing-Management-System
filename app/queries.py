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