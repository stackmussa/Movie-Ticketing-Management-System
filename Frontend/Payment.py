import streamlit as st
import time
import requests
import app.config as config
from app.logger import logger
from Frontend import components
from datetime import datetime


api_url = config.API_URL

if not st.session_state.get('logged_in'):
    logger.error("Please Login First to Make Payment!")
    st.warning("Please Login First to Make Payment!")
    st.stop()

st.title("Payment Checkout")
st.write("Seamlessly Make Payments against your Order")
st.divider()

if 'expired_booking' not in st.session_state:
    st.session_state ['expired_booking'] = []

# --- Auto-Fetch Trigger (If passed from another page) ---
if 'current_booking_id' in st.session_state and 'current_order' not in st.session_state:
    auto_id = st.session_state['current_booking_id']
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    
    with st.spinner("Loading your order..."):
        resp = requests.get(f"{api_url.rstrip('/')}/booking/{auto_id}", headers=headers)
        if resp.status_code == 200:
            st.session_state['current_order'] = resp.json()

# --- Fully Automatic Fresh Landing: Fetch Ongoing Pending Order ---
if 'current_order' not in st.session_state:
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    try:
        pending_resp = requests.get(f"{api_url.rstrip('/')}/pendingorders", headers=headers)
        if pending_resp.status_code == 200:
            pending_list = pending_resp.json()

            # Filter for Pending orders AND exclude any that just expired in this session
            active_pending = [
                o for o in pending_list 
                if (o.get('BookingStatus', o.get('status')) == 'Pending') and 
                   (o.get('BookingID', o.get('booking_id')) not in st.session_state['expired_bookings'])
            ]
            
            if active_pending:
                # Automatically grab the latest ongoing pending booking ID
                ongoing_id = active_pending[0].get('BookingID', active_pending[0].get('booking_id'))
                st.session_state['current_booking_id'] = ongoing_id
                
                # Fetch its details immediately without user interaction
                resp = requests.get(f"{api_url.rstrip('/')}/booking/{ongoing_id}", headers=headers)
                if resp.status_code == 200:
                    st.session_state['current_order'] = resp.json()
                    st.rerun()
            else:
                st.info("You have no ongoing payment checkouts right now.")
    except Exception as e:
        logger.error(f"Failed to auto-fetch pending orders: {e}")
        st.info("You have no ongoing payment checkouts right now.")

st.divider()

# --- 3. Order Summary & Payment Processing ---
if 'current_order' in st.session_state:
    order = st.session_state['current_order']
    booking_id = st.session_state['current_booking_id']

    user_email = st.session_state.get('user_email', 'unknown')
    timer_key = f"timer_{user_email}_{booking_id}"  
    
    st.subheader("Order Summary")

    with st.container(border=True):
        st.write(f"**Movie:** {order.get('title')}")
        st.write(f"**Cinema:** {order.get('cinema')}")
        st.write(f"**Showtime:** {order.get('date')} at {order.get('time')}")
        st.write(f"**Seats:** {order.get('assigned_seats', 'N/A')}")
        st.write(f"**Status:** {order.get('status')}")
        st.markdown(f"<h3 style='color: #4CAF50;'>Total Due: Rs. {order.get('total_amount')}</h3>", unsafe_allow_html=True)

    if order.get('status') == 'Pending':

        # 1. Parse the official creation time from the database
        booking_date_str = order.get('booking_date', '')
        
        # 2. Convert SQL string to Python datetime (stripping fractional seconds)
        db_creation_time = datetime.strptime(booking_date_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
        
        # 3. Calculate true elapsed time based on the database clock
        current_time = datetime.now()
        elapsed_time = (current_time - db_creation_time).total_seconds()
        
        # 4. Calculate remaining seconds
        remaining_seconds = max(0, config.booking_hold_timer - int(elapsed_time))

        timer_html = components.get_timer_html(remaining_seconds)
        st.html(timer_html, unsafe_allow_javascript=True)

        # 5. Interactive reset mechanism 
        if remaining_seconds <= 0:
            logger.error(f"Booking {booking_id} expired. Auto-clearing.")
            
            # 1. FORCE CANCELLATION: Instantly tell the backend to free the seats
            requests.put(
                f"{api_url.rstrip('/')}/cancelBooking/{booking_id}", 
                headers={"Authorization": f"Bearer {st.session_state.get('token')}"}
            )
            
            # 2. Silently wipe the Streamlit memory without a button
            st.session_state.pop('current_order', None)
            st.session_state.pop('current_booking_id', None)
            st.session_state.pop(timer_key, None)
            
            # 3. Show a brief warning, pause so they can read it, and reload the app
            st.error("Time is up! Your booking has expired and seats have been released.")
            time.sleep(2.5)
            st.switch_page(config.dashboard_page)
            st.rerun()

        #load payment Methods
        payment_methods = [method.value for method in config.PaymentMethodEnum]
        selected_method = st.selectbox("Select Payment Method", payment_methods)

        mobile_number = None
        card_number = None
        expiry_date = None
        cvv = None

        if selected_method in ['JazzCash', "Easypaisa"]:
            mobile_number = st.text_input("Mobile Number", placeholder="03XXXXXXXXX", max_chars=11)

        elif selected_method == 'Debit/Credit Card':
            col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
            with col_c1:
                card_number = st.text_input("Card Number", placeholder="1234 5678 9101 1121", max_chars=19)
            with col_c2:
                expiry_date = st.text_input("Expiry", placeholder="MM/YY", max_chars=5)
            with col_c3:
                cvv = st.text_input("CVV", type="password", max_chars=4)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Pay Now", type="primary", use_container_width=True):

            # Frontend Validation
            if selected_method in ["JazzCash", "EasyPaisa"] and (not mobile_number or not mobile_number.startswith("03") or len(mobile_number) != 11):
                st.error("Please enter a valid 11-digit mobile number starting with '03'.")
            elif selected_method == "Debit/Credit Card" and (not card_number or not expiry_date or not cvv):
                st.error("Please fill in all card details.")
            else:
                with st.spinner("Processing Transaction"):
                    headers = {"Authorization" : f"Bearer {st.session_state['token']}"}

                    # Build the dynamic payload
                    payload = {
                        "BookingID": booking_id,
                        "method": selected_method
                    }
                    
                    # Only append the fields that were actively populated
                    if mobile_number: payload["mobile_number"] = mobile_number
                    if card_number: payload["card_number"] = card_number
                    if expiry_date: payload["expiry_date"] = expiry_date
                    if cvv: payload["cvv"] = cvv
                    
                    checkout_endpoint = f"{api_url.rstrip('/')}/checkout"
                    pay_resp = requests.post(checkout_endpoint, data=payload, headers=headers)

                    logger.info("Tansaction Details Sent!")

                    if pay_resp.status_code == 200:
                        try:
                            data = pay_resp.json()
                            time.sleep(5)
                            st.success(data.get("message", "Payment successful!"))
                            st.info(f"**Transaction Reference:** {data.get('transaction_reference')}")

                            # Wipe the order from memory to prevent double-charging using the new timer key
                            st.session_state.pop('current_order', None)
                            st.session_state.pop('current_booking_id', None)
                            st.session_state.pop(timer_key, None)

                        except ValueError:
                            st.error(f"Server Error ({pay_resp.status_code}): {pay_resp.text}")
                    else:
                        try:
                            error_detail = pay_resp.json().get("detail", "Payment failed.")
                        except ValueError:
                            error_detail = f"Server Error ({pay_resp.status_code}): {pay_resp.text}"
                        st.error(error_detail)