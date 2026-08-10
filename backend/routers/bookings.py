from fastapi import APIRouter, HTTPException, Form, Depends, BackgroundTasks
from typing import Annotated
import asyncio
import re
import uuid
import pyodbc
from app.logger import logger
import app.config as config
import app.queries as queries
import app.jwt_Security as jwt_Security

router = APIRouter(tags=["Bookings & Payments"])

async def auto_cancel_booking(booking_id: int):
    #starts the 5 minuts counter 
    await asyncio.sleep(config.booking_hold_timer)
    try:
        conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(queries.get_booking_status, (booking_id,))
        record = cursor.fetchone()
        
        if record and record[0] == 'Pending':
            cursor.execute("UPDATE Booking SET BookingStatus = 'Cancelled' WHERE BookingID = ?", (booking_id,))
            logger.info(f"Timeout: Booking {booking_id} automatically cancelled after 5 minutes.")
        conn.close()
    except pyodbc.Error as e:
        logger.error(f"Background task DB error for Booking {booking_id}")

# Fetch seats that are currently unavailable 
@router.get("/booked_seats")
def Get_Booked_Seats(title: str, city: str, conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        cursor.execute(queries.Select_City_Title_Query, (title, city))
        show_record = cursor.fetchone()
        
        if not show_record:
            raise HTTPException(status_code=400, detail="Show not found")
        
        show_id = show_record[0]
        
        # Pull seats those that are Pending or Confirmed bookings
        cursor.execute(queries.get_confirmed_pending_seats , (show_id,))
        
        # Format rows into "A1", "C4", etc.
        booked_seats = [f"{str(row[0]).strip()}{str(row[1]).strip()}" for row in cursor.fetchall()]        

        return {"booked_seats": booked_seats}
    except pyodbc.Error as e:
        logger.error(f"DB Error fetching booked seats")
        raise HTTPException(status_code=500, detail="Database Error")

@router.post("/booking")
def Book_Show(
    title: Annotated[str, Form()], City: Annotated[config.CityEnum, Form()],
    selectedSeats: Annotated[str, Form()], seatCategory: Annotated[config.SeatCategoryEnum, Form()],
    background_tasks: BackgroundTasks, 
    current_user: dict = Depends(jwt_Security.get_current_user), 
    conn: pyodbc.Connection = Depends(config.get_DB)
):
        # Parse the string into a list and calculate quantity automatically
        requested_seats = [seat.strip() for seat in selectedSeats.split(',') if seat.strip()]
        TicketsNeeded = len(requested_seats)

        if TicketsNeeded<=0:
            logger.error(f"Invalid User Input, Tickets Quantity can never be -ve or 0")
            raise HTTPException(status_code=400, detail="Negative Tickets Quantity or 0 Entered")
        
        max_tickets = config.SYSTEM_CONFIG.get("max_tickets_per_order", 10)
    
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

            # fetches available seats
            cursor.execute(queries.seat_query, (hall_id, selected_category, show_id))
            all_available_seats = cursor.fetchall()

            # Map them as "A1" -> SeatID
            available_seat_map = {f"{str(s[1]).strip()}{str(s[2]).strip()}": s[0] for s in all_available_seats}

            # Validate that every requested seat is actually in the available pool
            validated_seat_ids = []
            for req_seat in requested_seats:
                if req_seat not in available_seat_map:
                    raise HTTPException(status_code=400, detail=f"Seat {req_seat} is currently unavailable.")
                validated_seat_ids.append(available_seat_map[req_seat])

            final_ticket_price = float(base_price) * (config.get_Category_Multiplier(selected_category))
            total_ammount = final_ticket_price * TicketsNeeded

            cursor.execute(queries.insert_booking_query, (user_id, show_id, total_ammount, TicketsNeeded))
            booking_id = cursor.fetchone()[0]
            
            # Map the specific seats to this booking & check for preventing the race condition
            try:
                for seat_id in validated_seat_ids:
                    # Assuming insert_seat_query is updated to take show_id
                    cursor.execute(queries.insert_seat_query, (booking_id, show_id, seat_id))
                conn.commit()
                
                logger.info(f"Booking {booking_id} created successfully for {user_email}.")
                background_tasks.add_task(auto_cancel_booking, booking_id)
                
                return {
                                "message": "Booking successful! Proceed to payment.",
                                "booking_details": {
                                    "booking_id": booking_id,
                                    "cinema": cinema_name,
                                    "city": selected_city,
                                    "category": selected_category,
                                    "tickets_booked": TicketsNeeded,
                                    "assigned_seats": requested_seats,
                                    "total_amount": round(total_ammount, 2),
                                    "currency": "PKR"
                                }
                            }
                
            except pyodbc.IntegrityError:
                # The constraint caught someone else taking the seat!
                # Manually wipe the orphaned Booking record just in case autocommit is on
                cursor.execute("DELETE FROM Booking WHERE BookingID = ?", (booking_id,))
                conn.commit()
                
                logger.warning(f"Race condition caught. Orphaned booking {booking_id} wiped.")
                raise HTTPException(
                    status_code=400, 
                    detail="We're sorry, but one or more of your selected seats were just booked by someone else! Refreshing map..."
                )
    
        except HTTPException as e:
            conn.rollback()
            raise
        except pyodbc.Error as e:
            conn.rollback()
            logger.error(f"DB Error Occurred during booking.")
            raise HTTPException(status_code=500, detail=f"DB Error Occured ")


@router.get("/booking/{booking_id}")
def Get_User_Booking_Details(
    booking_id: int, current_user: dict = Depends(jwt_Security.get_current_user),
    conn: pyodbc.Connection = Depends(config.get_DB)
):
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
                "cinema": record.CinemaName,
                "booking_date": str(record.BookingDate),
                "assigned_seats": record.AssignedSeats
            }
    except pyodbc.Error as e:
        logger.error(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

@router.get("/pendingorders")
def get_Pending_bookings(
    current_user: dict = Depends(jwt_Security.get_current_user),
    conn: pyodbc.Connection = Depends(config.get_DB)
):
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

@router.post("/checkout")
def process_payment(
    BookingID: Annotated[int, Form()], method: Annotated[config.PaymentMethodEnum, Form()], 
    mobile_number: Annotated[str | None, Form()] = None, card_number: Annotated[str | None, Form()] = None,
    expiry_date: Annotated[str | None, Form()] = None, cvv: Annotated[str | None, Form()] = None,
    current_user: dict = Depends(jwt_Security.get_current_user), conn: pyodbc.Connection = Depends(config.get_DB)
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

@router.put("/cancelBooking/{booking_ID}")
def cancel_Booking(
    booking_ID: int, 
    cancellation_reason: Annotated[str | None, Form()] = None,
    current_user: dict = Depends(jwt_Security.get_current_user),
    conn: pyodbc.Connection = Depends(config.get_DB)
):
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

        # 1. Free the seats and store the cancellation reason
        cursor.execute(
            "UPDATE Booking SET BookingStatus = 'Cancelled', CancellationReason = ? WHERE BookingID = ?", 
            (cancellation_reason, booking_ID)
        )

        # 2. Process Refund & Penalty Logic
        message = "Booking has been successfully cancelled."
        
        if status == 'Confirmed':
            cursor.execute("UPDATE Payment SET PaymentStatus = 'Refunded' WHERE BookingID = ?", (booking_ID,))
            
            # Calculate the 10% deduction
            deduction = float(total_amount) * 0.10
            refund_amount = float(total_amount) - deduction
            message = f"Booking cancelled. Rs. {refund_amount:.2f} refunded (10% cancellation fee applied)."
        
        conn.commit()
        logger.info(f"Booking {booking_ID} cancelled by User {current_user['user_id']}. Reason: {cancellation_reason or 'N/A'}")
    
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

@router.get("/reviews/{movie_title}")
def get_reviews(movie_title: str, conn: pyodbc.Connection = Depends(config.get_DB)):
    """Fetch all reviews + average rating for a movie by its title."""
    cursor = conn.cursor()
    try:
        # Resolve movie title to MovieID
        cursor.execute(queries.get_movie_id_by_title, (movie_title,))
        movie_record = cursor.fetchone()
        if not movie_record:
            raise HTTPException(status_code=404, detail="Movie not found.")
        movie_id = movie_record[0]

        # Get average rating
        cursor.execute(queries.get_movie_avg_rating, (movie_id,))
        avg_record = cursor.fetchone()
        avg_rating = round(float(avg_record[0]), 1) if avg_record and avg_record[0] else 0.0
        total_reviews = int(avg_record[1]) if avg_record and avg_record[1] else 0

        # Get all reviews + replies
        cursor.execute(queries.get_movie_reviews, (movie_id,))
        results = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]
        reviews = [dict(zip(column_names, row)) for row in results]

        # Convert datetime objects to strings for JSON serialization
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


@router.post("/reviews")
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


@router.post("/reviews/reply")
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