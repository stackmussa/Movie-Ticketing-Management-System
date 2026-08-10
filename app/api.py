from enum import Enum
from fastapi import FastAPI, HTTPException, status, Form, Depends, Response, BackgroundTasks
from pydantic import BaseModel, field_validator
from contextlib import asynccontextmanager
from typing import Annotated, List
from fastapi.security import OAuth2PasswordRequestForm
from app.logger import logger
import asyncio
import re
import os
import uuid
import asyncio
import pyodbc
import app.config as config
import app.passHash as passHash
import app.queries as queries
import app.jwt_Security as jwt_Security

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        with open("DB/Schema.sql", "r") as file:
            sql_script = file.read()
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Initialization Failed")
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
def check_health(response: Response, conn : pyodbc.Connection = Depends(config.get_DB)):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return {"status": "healthy", "database": "connected"}
    except pyodbc.Error: 
        response.status_code = 503
        return {"status": "unhealthy", "database": "disconnected", "error": "Database connection failed."}
    
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
        cursor.execute(queries.verify_email, (email,))
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
def Login_User(form_data : Annotated[OAuth2PasswordRequestForm, Depends()],
               conn: pyodbc.Connection = Depends(config.get_DB)):

    cursor = conn.cursor()

    # Extract email from the standard OAuth2 'username' field
    email = form_data.username.lower()
    password = form_data.password

    email_regex = r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$"

    if not re.match(email_regex, email):
        logger.error(f"Invalid Email Format. Must be in the Format user@domain.com")
        raise HTTPException(status_code=400, detail="Invalid Email Format. Must be in the Format user@domain.com")
    email =  email.lower()

    try:
        cursor.execute(queries.verify_password, (email,))
        result = cursor.fetchone()
        if not result:
            logger.error(f"Invalid Email / Password")
            raise HTTPException(status_code=400, detail="Invalid Email / Password")
        hashed_pass = result[0]
        is_valid = passHash.verify_Password(hashed_pass, password)

        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid Email / Password")

        #access tokens for Security
        access_token = jwt_Security.create_access_tokens(data={"sub": email})
        logger.info(f"User {email} has logged in & recieved a token!")
        return {"access_token": access_token, "token_type": "bearer"}
    
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
        print(f"Failed to load categories for dropdown.")
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
        print(f"Failed to load categories for dropdown.")
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
        print(f"Database error calculating booked seats")
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
        logger.error(f"DB Error")
        raise HTTPException(status_code=500, detail="Database Error")

#5 minutes timer helper function
async def auto_cancel_booking(booking_id: int):
    # Start the 5-minute countdown (300 seconds)
    await asyncio.sleep(config.booking_hold_timer)
    
    try:
        # Open a new connection specifically for this background task
        conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        
        # Check if the booking is still 'Pending'
        cursor.execute(queries.get_booking_status, (booking_id,))
        record = cursor.fetchone()
        
        if record and record[0] == 'Pending':
            # Expire the booking, which instantly releases the seats for other users
            cursor.execute("UPDATE Booking SET BookingStatus = 'Cancelled' WHERE BookingID = ?", (booking_id,))
            logger.info(f"Timeout: Booking {booking_id} automatically cancelled after 5 minutes.")
            
        conn.close()
    except pyodbc.Error as e:
        logger.error(f"Background task DB error for Booking {booking_id}")

# for booking tickets of selected Show
@app.post("/booking")
def Book_Show(
    title: Annotated[str, Form()], 
    City: Annotated[config.CityEnum, Form()],
    TicketsNeeded: Annotated[int, Form()], 
    seatCategory: Annotated[config.SeatCategoryEnum, Form()],
    background_tasks: BackgroundTasks, 
    current_user: dict = Depends(jwt_Security.get_current_user), 
    conn: pyodbc.Connection = Depends(config.get_DB)
):
    
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
    user_id = current_user['user_id']
    user_email = current_user['email']

    try:
        #selection based on Movie's Title & in the respective city
        cursor.execute(queries.Select_City_Title_Query, (title, selected_city,) )
        show_record = cursor.fetchone()

        if not show_record:
            logger.error(f"The Movie with Title: {title} is not available in {selected_city}")
            raise HTTPException(status_code=400, detail=f"The Movie with Title: {title} is not available in {selected_city}")
        
        show_id, base_price, hall_id, cinema_name = show_record
        cursor.execute(queries.seat_query, (hall_id, selected_category, show_id))
        all_available_seats = cursor.fetchall()

        #validation for Total Seats
        if len(all_available_seats) < TicketsNeeded:
            logger.error(f"Not enough {selected_category} seats available for Show {show_id}.")
            raise HTTPException(status_code=400, detail=f"Only {len(all_available_seats)} {selected_category} seats left.")

        available_seats = all_available_seats[:TicketsNeeded]
        
        final_ticket_price = float(base_price) * (config.get_Category_Multiplier(selected_category))
        total_ammount = final_ticket_price * TicketsNeeded

        cursor.execute(queries.insert_booking_query, (user_id, show_id, total_ammount, TicketsNeeded))
        booking_id = cursor.fetchone()[0]

        #seat validations & equipment
        for seat in available_seats:
            seat_id = seat[0]
            cursor.execute(queries.insert_seat_query, (booking_id, seat_id))

        conn.commit()
        assigned_seats = [f"Row {s[1]} Seat {s[2]}" for s in available_seats]
        logger.info(f"Booking {booking_id} created successfully for {user_email}.")

        #Starting timer of 5 Minutes for the seat to be booked 
        background_tasks.add_task(auto_cancel_booking, booking_id)

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
        logger.error(f"DB Error Occurred during booking.")
        raise HTTPException(status_code=500, detail=f"DB Error Occured ")

#get the booking history of the User
@app.get("/booking/{booking_id}")
def Get_User_Booking_Details(booking_id: int, current_user : dict = Depends(jwt_Security.get_current_user),
                                conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        # Authorization verification 
        cursor.execute(queries.authorize_owner, (booking_id,))
        booking_owner = cursor.fetchone()
        
        if not booking_owner:
            logger.error(f"Booking ID {booking_id} not found")
            raise HTTPException(status_code=404, detail="Booking ID not found.")
        if booking_owner[0] != current_user["user_id"]:
            logger.warning(f"Unauthorized access attempt on Booking {booking_id}")
            raise HTTPException(status_code=403, detail="You are not authorized to view this booking.")

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
def get_Pending_bookings(current_user : dict = Depends(jwt_Security.get_current_user),
                         conn : pyodbc.Connection = Depends(config.get_DB)):
    
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_user_order, (current_user["user_id"],))
        results = cursor.fetchall()
        
        if not results:
            logger.error(f"No Pending Orders!")
            return []
        column_names = [column[0] for column in cursor.description]
        formatted_results = [dict(zip(column_names, row)) for row in results]
        return formatted_results
    except:
        logger.error(f"Database error in fetching Pending Orders")
        raise HTTPException(status_code=500, detail="Error validating seat availability.")


#processing payment for the User's Booking
@app.post("/checkout")
def process_payment(
    BookingID: Annotated[int, Form()], 
    method: Annotated[config.PaymentMethodEnum, Form()], 
    mobile_number: Annotated[str | None, Form()] = None,
    card_number: Annotated[str | None, Form()] = None,
    expiry_date: Annotated[str | None, Form()] = None,
    cvv: Annotated[str | None, Form()] = None,
    current_user: dict = Depends(jwt_Security.get_current_user), 
    conn: pyodbc.Connection = Depends(config.get_DB)
):
    # --- 1. Dynamic Payment Validation ---
    if method.value in ["JazzCash", "EasyPaisa"]:
        if not mobile_number or not re.match(r"^03\d{9}$", mobile_number):
            logger.error("Checkout Failed: Invalid Mobile Number.")
            raise HTTPException(status_code=400, detail="Mobile number must be exactly 11 digits and start with '03'.")
            
    elif method.value == "Debit/Credit Card":
        # Remove spaces from card number for validation
        clean_card = card_number.replace(" ", "") if card_number else ""
        if not clean_card or not re.match(r"^\d{16}$", clean_card):
            logger.error("Invalid Card Number. Must be 16 digits.")
            raise HTTPException(status_code=400, detail="Invalid Card Number. Must be 16 digits.")
        if not expiry_date or not re.match(r"^(0[1-9]|1[0-2])\/?([0-9]{2})$", expiry_date):
            logger.error("Invalid Expiry Date. Use MM/YY format.")
            raise HTTPException(status_code=400, detail="Invalid Expiry Date. Use MM/YY format.")
        if not cvv or not re.match(r"^\d{3,4}$", cvv):
            logger.error("Invalid CVV")
            raise HTTPException(status_code=400, detail="Invalid CVV.")

    # --- 2. Database Processing ---
    cursor = conn.cursor()
    try:
        # Verify ownership to block illicit payments (IDOR Protection)
        cursor.execute("SELECT UserID FROM Booking WHERE BookingID = ?", (BookingID,))
        owner = cursor.fetchone()
        if not owner or owner[0] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Unauthorized payment attempt.")

        cursor.execute(queries.get_booking_amount, (BookingID,))
        booking_record = cursor.fetchone()
        
        if not booking_record:
            raise HTTPException(status_code=400, detail="No Active Pending Orders Found!")
            
        expected_amount, current_status = booking_record

        if current_status == 'Confirmed':
            raise HTTPException(status_code=400, detail="User Already Checked out!")
        if current_status == 'Cancelled':
            raise HTTPException(status_code=400, detail="User Cancelled the Order, No Such Order Exists now")

        transaction_ref = f"TXN-{str(uuid.uuid4())[:8].upper()}"

        cursor.execute(queries.insert_payment_query, (
            BookingID, 
            expected_amount, 
            method.value, 
            transaction_ref
        ))
        payment_id = cursor.fetchone()[0]

        cursor.execute(queries.update_booking_status_query, (BookingID,))
        conn.commit()

        logger.info(f"Payment {payment_id} processed successfully for Booking {BookingID}.")
        return {
            "message": "Payment successful! Your tickets are confirmed.",
            "transaction_reference": transaction_ref,
            "payment_id": payment_id
        }

    except HTTPException:
        conn.rollback()
        raise
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"Database error during payment processing: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the payment.")

@app.put("/cancelBooking/{booking_ID}")
def cancel_Booking(booking_ID: int, current_user: dict = Depends(jwt_Security.get_current_user),
    conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        # Fetch the TotalAmount along with the status
        cursor.execute("SELECT UserID, BookingStatus, TotalAmount FROM Booking WHERE BookingID = ?", (booking_ID,))
        record = cursor.fetchone()

        if not record:
            logger.info(f"Booking {booking_ID} not found.")
            raise HTTPException(status_code=404, detail="Booking not found.")
            
        user_id, status, total_amount = record
        
        if user_id != current_user['user_id']:
            logger.warning(f"Unauthorized cancellation attempt on Booking No. {booking_ID}")
            raise HTTPException(status_code=403, detail="Unauthorized cancellation attempt!")

        if status == 'Cancelled':
            raise HTTPException(status_code=400, detail="This booking is already cancelled.")

        # 1. Free the seats by updating the status
        cursor.execute("UPDATE Booking SET BookingStatus = 'Cancelled' WHERE BookingID = ?", (booking_ID,))

        # 2. Process Refund & Penalty Logic
        message = "Booking has been successfully cancelled."
        
        if status == 'Confirmed':
            cursor.execute("UPDATE Payment SET PaymentStatus = 'Refunded' WHERE BookingID = ?", (booking_ID,))
            
            # Calculate the 10% deduction
            deduction = float(total_amount) * 0.10
            refund_amount = float(total_amount) - deduction
            message = f"Booking cancelled. Rs. {refund_amount:.2f} refunded (10% cancellation fee applied)."
        
        conn.commit()
        logger.info(f"Booking {booking_ID} cancelled by User {current_user['user_id']}.")
    
        return {"message": message}

    except HTTPException:
        conn.rollback()
        raise
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"Database error during cancellation")
        raise HTTPException(status_code=500, detail="An internal database error occurred.")

# ============================================================
# REVIEW ENDPOINTS
# ============================================================

@app.get("/reviews/{movie_title}")
def get_reviews(movie_title: str, conn: pyodbc.Connection = Depends(config.get_DB)):
    """Fetch all reviews + average rating for a movie by its title."""
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_movie_id_by_title, (movie_title,))
        movie_record = cursor.fetchone()
        if not movie_record:
            raise HTTPException(status_code=404, detail="Movie not found.")
        movie_id = movie_record[0]

        cursor.execute(queries.get_movie_avg_rating, (movie_id,))
        avg_record = cursor.fetchone()
        avg_rating = round(float(avg_record[0]), 1) if avg_record and avg_record[0] else 0.0
        total_reviews = int(avg_record[1]) if avg_record and avg_record[1] else 0

        cursor.execute(queries.get_movie_reviews, (movie_id,))
        results = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]
        reviews = [dict(zip(column_names, row)) for row in results]

        for review in reviews:
            if review.get("CreatedAt"):
                review["CreatedAt"] = str(review["CreatedAt"])

        return {
            "movie_title": movie_title,
            "average_rating": avg_rating,
            "total_reviews": total_reviews,
            "reviews": reviews
        }
    except HTTPException:
        raise
    except pyodbc.Error as e:
        logger.error(f"DB Error fetching reviews: {e}")
        raise HTTPException(status_code=500, detail="Database Error fetching reviews.")


@app.post("/reviews")
def post_review(
    movie_title: Annotated[str, Form()],
    rating: Annotated[int, Form()],
    review_text: Annotated[str, Form()],
    current_user: dict = Depends(jwt_Security.get_current_user),
    conn: pyodbc.Connection = Depends(config.get_DB)
):
    """Submit a new top-level review with a star rating (1-5)."""
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
    if not review_text.strip():
        raise HTTPException(status_code=400, detail="Review text cannot be empty.")

    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_movie_id_by_title, (movie_title,))
        movie_record = cursor.fetchone()
        if not movie_record:
            raise HTTPException(status_code=404, detail="Movie not found.")
        movie_id = movie_record[0]

        cursor.execute(queries.insert_review, (movie_id, current_user["user_id"], rating, review_text.strip()))
        review_id = cursor.fetchone()[0]
        conn.commit()

        logger.info(f"Review {review_id} posted by User {current_user['user_id']} for Movie '{movie_title}'.")
        return {"message": "Review posted successfully!", "review_id": review_id}

    except HTTPException:
        conn.rollback()
        raise
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"DB Error posting review: {e}")
        raise HTTPException(status_code=500, detail="Database Error posting review.")


@app.post("/reviews/reply")
def post_reply(
    movie_title: Annotated[str, Form()],
    parent_review_id: Annotated[int, Form()],
    review_text: Annotated[str, Form()],
    current_user: dict = Depends(jwt_Security.get_current_user),
    conn: pyodbc.Connection = Depends(config.get_DB)
):
    """Post a reply to an existing review."""
    if not review_text.strip():
        raise HTTPException(status_code=400, detail="Reply text cannot be empty.")

    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_movie_id_by_title, (movie_title,))
        movie_record = cursor.fetchone()
        if not movie_record:
            raise HTTPException(status_code=404, detail="Movie not found.")
        movie_id = movie_record[0]

        cursor.execute(queries.insert_reply, (movie_id, current_user["user_id"], review_text.strip(), parent_review_id))
        reply_id = cursor.fetchone()[0]
        conn.commit()

        logger.info(f"Reply {reply_id} posted by User {current_user['user_id']} on Review {parent_review_id}.")
        return {"message": "Reply posted successfully!", "review_id": reply_id}

    except HTTPException:
        conn.rollback()
        raise
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"DB Error posting reply: {e}")
        raise HTTPException(status_code=500, detail="Database Error posting reply.")