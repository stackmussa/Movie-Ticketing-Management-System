from fastapi import FastAPI, HTTPException, status, Form, Depends
from pydantic import BaseModel, field_validator
from contextlib import asynccontextmanager
from typing import Annotated
from app.logger import logger
import re
import pyodbc
import app.config as config
import app.passHash as passHash


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        with open("E:\BetaCode Work\Ticketing Management System\DB\Schema.sql", "r") as file:
            sql_script = file.read()
        conn.commit()
        conn.close()
        yield
    except Exception as e:
        print(f"DB Initialization Failed: {e}")
        raise HTTPException(status_code=400, detail="Error Loading DB")
    finally:
        if 'conn' in locals():
            conn.commit()
    yield

app = FastAPI(lifespan=lifespan)

class UserRegistery(BaseModel):
    email:str
    password:str

def get_DB():
    conn = pyodbc.connect(config.CONNECTION_STRING)
    try:
        yield conn
    finally:
        conn.close()


@app.post("/register")
def Register_User(firstName: Annotated[str, Form()], lastName: Annotated[str, Form()],
                   email: Annotated[str, Form()], password: Annotated[str, Form()], 
                   conn: pyodbc.Connection = Depends(get_DB)):
    cursor = conn.cursor()
    email_regex = r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        logger.error(f"Invalid Email Format. Must be in the Format user@domain.com")
        raise ValueError("Invalid Email Format. Must be in the Format user@domain.com")
    email =  email.lower()
    try:
        cursor.execute("SELECT UserID FROM [User] WHERE Email = ?", (email,))
        if cursor.fetchone():
            logger.info(f"User with the same email {email} already exists!")
            raise HTTPException(status_code=400, detail=f"User with Email {email} already exists!")
        
        hashed_pass = passHash.hash_Password(password)
        query = "INSERT INTO [User] (firstName, lastName, Email, PasswordHash) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (firstName, lastName,email, hashed_pass))
        conn.commit()
        logger.info(f"User with {email} has been registered sucessfully")
        return {"message" : f"User with {email} has been registered sucessfully"}
    except HTTPException:
        raise


@app.post("/login")
def Login_User(email : Annotated[str, Form()], password : Annotated[str, Form()],
               conn: pyodbc.Connection = Depends(get_DB)):
    cursor = conn.cursor()
    email_regex = r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        logger.error(f"Invalid Email Format. Must be in the Format user@domain.com")
        raise ValueError("Invalid Email Format. Must be in the Format user@domain.com")
    email =  email.lower()
    try:
        cursor.execute("SELECT PasswordHash FROM [User] WHERE Email = ?", (email,))
        result = cursor.fetchone()
        if not result:
            logger.error(f"Invalid Email / Password")
            raise HTTPException(status_code=400, detail="Invalid Email / Password")
        hashed_pass = result[0]
        is_valid = passHash.verify_Password(hashed_pass, password)

        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid Email / Password")
        logger.info(f"User {email} has logged in!")
        return {"message" : "Welcome To Ticketing System"}
    except HTTPException :
        raise HTTPException(status_code=400, detail="Invalid Email / Password")
    

@app.get("/shows")
def Get_Shows(conn: pyodbc.Connection = Depends(get_DB)):
    User_query = '''SELECT DISTINCT M.Title, M.Genre, M.Language, M.DurationMinutes, M.Description,
                M.CensorRating, S.ShowTime, S.ShowDate, S.TicketPrice, H.HallName, H.ScreenType, H.TotalSeats,
                C.CinemaName, C.BranchName, C.Address, C.ContactNumber
            FROM Show AS S
            INNER JOIN Movie AS M ON S.MovieID = M.MovieID
            INNER JOIN HALL AS H ON S.HallID = H.HallID
            INNER JOIN Cinema AS C ON H.CinemaID = C.CinemaID
            WHERE S.ShowDate >= CAST(GETDATE() AS DATE)
            ORDER BY S.ShowDate ASC, S.ShowTime ASC'''
    cursor = conn.cursor()
    try:
        cursor.execute(User_query)
        results = cursor.fetchall()
        if not results:
            logger.error(f"No Upcoming Shows!")
            raise HTTPException(status_code=400, detail="No Upcoming Shows!")
        column_names = [column[0] for column in cursor.description]
        formatted_results = [dict(zip(column_names, row)) for row in results]
        return formatted_results
    except HTTPException as e:
        print(f"DB Failure! {e}")
        logger.error("DB Failure!")
        raise HTTPException(status_code=500, detail="Failed to fetch shows from database.") 
    

@app.get("/show/{title}")
def Get_Specific_Show(title :str, conn: pyodbc.Connection = Depends(get_DB)):
    User_query = '''SELECT DISTINCT M.Title, M.Genre, M.Language, M.DurationMinutes, M.Description, 
                M.CensorRating, S.ShowTime, S.ShowDate, S.TicketPrice, H.HallName, H.ScreenType, H.TotalSeats, 
                C.CinemaName, C.BranchName, C.Address, C.ContactNumber
            FROM Show AS S
            INNER JOIN Movie AS M ON S.MovieID = M.MovieID
            INNER JOIN HALL AS H ON S.HallID = H.HallID
            INNER JOIN Cinema AS C ON H.CinemaID = C.CinemaID
            WHERE M.Title = ? AND S.ShowDate >= CAST(GETDATE() AS DATE)
            ORDER BY S.ShowDate ASC, S.ShowTime ASC'''
    cursor = conn.cursor()
    try:
        cursor.execute(User_query, (title,))
        results = cursor.fetchall()
        if not results:
            logger.error(f"No Upcoming Shows!")
            raise HTTPException(status_code=400, detail="No Upcoming Shows!")
        column_names = [column[0] for column in cursor.description]
        formatted_results = [dict(zip(column_names, row)) for row in results]
        return formatted_results
    except HTTPException as e:
        print(f"No Such Record! {e}")
        logger.error(f"No such record!")
        raise HTTPException(status_code=400, detail="No Such Record Found!.") 

    
@app.get("/categories")
def get_seat_catergories(conn : pyodbc.Connection = Depends(get_DB)):
    User_query='''SELECT DISTINCT SeatCategory
                FROM Seat
                ORDER BY SeatCategory ASC'''
    cursor = conn.cursor()
    try:
        cursor.execute(User_query)
        results = cursor.fetchall()
        if not results:
            logger.error("No Results")
            raise HTTPException(status_code=400, detail="No Results")
        categories = [row[0] for row in results]
        return {"categories" : categories}
    except pyodbc.Error as e:
        logger.error(f"Error in Fetching the Seat Categories")
        raise HTTPException(status_code=500, detail="Failed to fetch seat categories.")


def get_booking_seats(SeatID : int, conn : pyodbc.Connection = Depends(get_DB)):
    User_Query = '''
            SELECT SUM(TicketsNeeded)
            FROM Seat
            WHERE SeatID = ? AND BookingStatus != 'Cancelled' 
    '''
    cursor = conn.cursor()
    try:    
        cursor.execute(User_Query, (SeatID,))
        results = cursor.fetchone()
        return int(results[0]) if results and results[0] is not None else 0
    except pyodbc.Error as e:
        print(f"Database error calculating booked seats: {e}")
        raise HTTPException(status_code=500, detail="Error validating seat availability.")


@app.post("/booking")
def Book_Show(title : Annotated[str,Form()], ticketsNeeded : Annotated[int, Form()],
              conn: pyodbc.Connection = Depends(get_DB)):
    
    if ticketsNeeded<=0:
        logger.error(f"Invalid User Input, Tickets Quantity can never be -ve")
        raise HTTPException(status_code=400, detail="Negative Tickets Quantity")
    cursor = conn.cursor()
    try:

        shows = Get_Specific_Show(title)

        if not shows:
            raise HTTPException(status_code=400, detail=f"The Movie with Title: {title} is not available")
        
    except HTTPException as e:
        raise
   