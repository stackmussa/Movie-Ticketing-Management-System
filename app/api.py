from enum import Enum
from fastapi import FastAPI, HTTPException, status, Form, Depends, Response, BackgroundTasks
from pydantic import BaseModel, field_validator
from contextlib import asynccontextmanager
from typing import Annotated, List
from app.logger import logger
import re
import os
import asyncio
import pyodbc
import app.config as config
import app.passHash as passHash
import app.queries as queries
import uuid

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



class PaymentRequest(BaseModel):
    booking_id: int
    amount: float
    payment_method: config.PaymentMethodEnum


@app.get("/")
def read_root():
    return {"Message" : "Welcome to Movie Ticket Purchase System."}

@app.get("/health")
def check_health(response : Response):
    try:
        conn = config.get_DB_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close
        return {"status": "healthy", "database": "connected"}
    except pyodbc.Error as e: 
        response.status_code=503
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
    except Exception as e:
        response.status_code = 500
        return {"status": "unhealthy", "error": "Internal Server Error"}

@app.get("/version")
def get_version():
    return {"api_version": "v1.4.2", "environment": os.getenv("ENV", "development")}

@app.get("/config")
def get_config():
    return {
        "max_tickets_per_order": 10,
        "convenience_fee": 15,
        "currency": "PKR",
        "supported_payments": ["debit-card", "credit-card", "easypaisa", "jazzcash"]
    }

# User Account Registry     
@app.post("/register")
def Register_User(firstName: Annotated[str, Form()], lastName: Annotated[str, Form()],
                   email: Annotated[str, Form()], password: Annotated[str, Form()], 
                   conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()

    if not cursor:
        logger.error("Server Down")
        raise HTTPException(status_code= 400, detail="Server Down")

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

# User Account Login
@app.post("/login")
def Login_User(email : Annotated[str, Form()], password : Annotated[str, Form()],
               conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    email_regex = r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        logger.error(f"Invalid Email Format. Must be in the Format user@domain.com")
        raise HTTPException(status_code=400, detail="Invalid Email Format. Must be in the Format user@domain.com")
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
    
# Get the all the Upcoming Shows
@app.get("/shows")
def Get_Shows(conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_shows_query)
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
    
# User to search a show 
@app.get("/show/{title}")
def Get_Specific_Show(title :str, conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_specific_show, (title,))
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

# Helper Function for Dropdown for Cities selection
def get_cities_for_dropdown():
    try:
        conn = pyodbc.connect(config.CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute(queries.Cities_query)
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {"Default": "Default"}

        return {row[0]: row[0] for row in results}
        
    except pyodbc.Error as e:
        print(f"Failed to load categories for dropdown: {e}")
        return {"Error": "Error"}
 
Cities = get_cities_for_dropdown()
DynamicCitiesDropdown = Enum("DynamicCitiesDropdown", Cities)

# Helper Function for Dropdown for Categories selection
def get_categories_for_dropdown():
    try:
        conn = pyodbc.connect(config.CONNECTION_STRING)
        cursor = conn.cursor()
                        
        cursor.execute(queries.Categories_query)
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {"Default": "Default"}
        
        return {row[0]: row[0] for row in results}
        
    except pyodbc.Error as e:
        print(f"Failed to load categories for dropdown: {e}")
        return {"Error": "Error"}
    
Seat_Categories = get_categories_for_dropdown()
DynamicSeatDropdown = Enum("DynamicSeatDropdown", Seat_Categories)

#get booking seats 
def get_booking_seats(SeatID : int, conn : pyodbc.Connection = Depends(config.get_DB)):
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

 
# check the availability of movie city wise    
@app.get("/availability")
def Check_Availability(title: str, city: str, conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        # Find the ShowID and HallID using your existing query
        cursor.execute(queries.Select_City_Title_Query, (title, city))
        show_record = cursor.fetchone()
        
        if not show_record:
            raise HTTPException(status_code=400, detail="Show not found")
        
        show_id, base_price, hall_id, cinema_name = show_record
        
        # Loop through categories and count unbooked seats using your existing seat_query
        availability = {}
        for cat in ["Platinum", "Gold", "Standard", "Recliner"]:
            cursor.execute(queries.seat_query, (hall_id, cat, show_id))
            availability[cat] = len(cursor.fetchall())
            
        return availability
    except pyodbc.Error as e:
        logger.error(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

# for booking tickets of selected Show
@app.post("/booking")
def Book_Show(email : Annotated[str , Form()],title : Annotated[str,Form()], City : Annotated[config.CityEnum , Form()], TicketsNeeded : Annotated[int, Form()],
              seatCategory : Annotated[config.SeatCategoryEnum, Form()],conn: pyodbc.Connection = Depends(config.get_DB)):
    
    if TicketsNeeded<=0:
        logger.error(f"Invalid User Input, Tickets Quantity can never be -ve or 0")
        raise HTTPException(status_code=400, detail="Negative Tickets Quantity or 0 Entered")
    config_data = get_config()
    max_tickets = config_data.get("max_tickets_per_order", 10)
    if TicketsNeeded > max_tickets:
        logger.error(f"User cannot request more than 10 Tickets at a time!")
        raise HTTPException(status_code=400, detail="User cannot request more than 10 Tickets at a time!")

    cursor = conn.cursor()
    selected_category = seatCategory.value
    selected_city = City.value
    user_email = email.lower()
    try:
        cursor.execute("SELECT UserID FROM [User] WHERE Email = ?", (user_email,))
        user_record = cursor.fetchone()

        if not user_record:
            logger.error(f"Booking failed: User with email {user_email} not found.")
            raise HTTPException(status_code=404, detail="User not found. Please register first.")
        user_id = user_record[0]

        cursor.execute(queries.Select_City_Title_Query, (title, selected_city,) )
        show_record = cursor.fetchone()

        if not show_record:
            logger.error(f"The Movie with Title: {title} is not available in {selected_city}")
            raise HTTPException(status_code=400, detail=f"The Movie with Title: {title} is not available in {selected_city}")
        
        show_id, base_price, hall_id, cinema_name = show_record
        cursor.execute(queries.seat_query, (hall_id, selected_category, show_id))
        all_available_seats = cursor.fetchall()

        if len(all_available_seats) < TicketsNeeded:
            logger.error(f"Not enough {selected_category} seats available for Show {show_id}.")
            raise HTTPException(status_code=400, detail=f"Only {len(all_available_seats)} {selected_category} seats left.")

        available_seats = all_available_seats[:TicketsNeeded]
        
        final_ticket_price = float(base_price) * (config.get_Category_Multiplier(selected_category))
        total_ammount = final_ticket_price * TicketsNeeded

        cursor.execute(queries.insert_booking_query, (user_id, show_id, total_ammount, TicketsNeeded))
        booking_id = cursor.fetchone()[0]

        for seat in available_seats:
            seat_id = seat[0]
            cursor.execute(queries.insert_seat_query, (booking_id, seat_id))

        conn.commit()
        assigned_seats = [f"Row {s[1]} Seat {s[2]}" for s in available_seats]
        logger.info(f"Booking {booking_id} created successfully for {user_email}.")
        return {
            "message": "Booking successful! Proceed to payment.",
            "booking_details": {
                "booking_id": booking_id,
                "cinema": cinema_name,
                "city": selected_city,
                "category": selected_category,
                "tickets_booked": TicketsNeeded,
                "assigned_seats": assigned_seats,
                "total_amount": round(total_ammount, 2),
                "currency": config_data.get("currency")
            }
        }
    
    except HTTPException as e:
        conn.rollback()
        raise
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"DB Error!!! {e}")
        raise HTTPException(status_code=500, detail=f"DB Error Occured {e}")

#get the booking history of the User
@app.get("/booking/{booking_id}")
def Get_User_Booking_Details(booking_id: int, conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_booking_details_query, (booking_id,))
        record = cursor.fetchone()
        
        if not record:
            raise HTTPException(status_code=404, detail="Booking ID not found.")
            
        return {
            "total_amount": float(record.TotalAmount),
            "status": record.BookingStatus,
            "title": record.Title,
            "date": record.ShowDate,
            "time": str(record.ShowTime),
            "cinema": record.CinemaName
        }
    except pyodbc.Error as e:
        logger.error(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

# get pending orders of the User 
@app.get("/pendingorders")
def get_Pending_bookings(conn : pyodbc.Connection = Depends(config.get_DB)):
    
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_user_order)
        results = cursor.fetchall()
        if not results:
            logger.error(f"No Pending Orders!")
            raise HTTPException(status_code=400, detail="No Pending Orders")
        column_names = [column[0] for column in cursor.description]
        formatted_results = [dict(zip(column_names, row)) for row in results]
        return formatted_results
    except:
        logger.error(f"Database error in fetching Pending Orders: {e}")
        raise HTTPException(status_code=500, detail="Error validating seat availability.")

#processing payment for the User's Booking
@app.post("/checkout")
def process_payment(BookingID : Annotated[int , Form()], method : Annotated[config.PaymentMethodEnum , Form()], conn : pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_booking_amount, (BookingID,))
        booking_record = cursor.fetchone()
        if not booking_record:
            logger.error("No Active Pending Orders Yet!!")
            raise HTTPException(status_code=400, detail="No Active Pending Orders Yet!!")
        expected_amount, current_status = booking_record

        if current_status == 'Confirmed':
            logger.info("User Already Checked out!")
            raise HTTPException(status_code=400, detail="User Already Checked out!")
        if current_status == 'Cancelled':
            logger.error("User Cancelled the Order, No Such Order Exists now")
            raise HTTPException(status_code=400, detail="User Cancelled the Order, No Such Order Exists now")

        transaction_ref = f"TXN-{str(uuid.uuid4())[:8].upper()}"

        #inserting into payment made into the Payment Table
        cursor.execute(queries.insert_payment_query, (
            BookingID, 
            expected_amount, 
            method.value, 
            transaction_ref
        ))
        payment_id = cursor.fetchone()[0]

        #updating booking status from pending to 
        cursor.execute(queries.update_booking_status_query, (BookingID,))

        conn.commit()

        logger.info(f"Payment {payment_id} processed successfully for Booking {BookingID}.")
        return {
            "message": "Payment successful! Your tickets are confirmed.",
            "transaction_reference": transaction_ref,
            "payment_id": payment_id
        }

    except HTTPException:
        logger.info(f"Transaction ID {transaction_ref}, has been rolled back!")
        conn.rollback()
        raise
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"Database error during payment processing: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the payment.")