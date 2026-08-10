import time
import streamlit as st
import requests
from datetime import datetime
import app.config as config
from app.logger import logger

api_url = config.API_URL

# --- 1. Authentication Check ---
if not st.session_state.get('logged_in'):
    logger.warning("Attempted to access My Orders without logging in.")
    st.warning("Please log in to view your orders!")
    st.stop()

st.title("My Orders")
st.write("Manage your pending bookings and view your order history.")
st.divider()

# --- 2. Fetch Orders from Backend ---
all_orders = []
with st.spinner("Fetching your orders..."):
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    
    # Targeting the endpoint defined in your api.py
    fetch_endpoint = f"{api_url.rstrip('/')}/pendingorders"
    
    try:
        resp = requests.get(fetch_endpoint, headers=headers)
        
        if resp.status_code == 200:
            all_orders = resp.json()
        elif resp.status_code == 400 and "No Pending Orders" in resp.text:
            all_orders = []
        else:
            try:
                error_detail = resp.json().get("detail", "Failed to fetch orders.")
            except ValueError:
                error_detail = f"Server Error ({resp.status_code})"
            st.error(error_detail)
            
    except requests.exceptions.ConnectionError:
        st.error("Failed to connect to the server. Please ensure the backend is running.")

# --- 3. Process and Divide Orders ---
pending_orders = []
history_orders = []

if not all_orders:
    st.info("You don't have any orders yet! Head to the dashboard to book a movie.")
else:
    current_time = datetime.now()

    # Filter the arrays based on the BookingStatus and Expiration Date
    for order in all_orders:
        status = order.get('BookingStatus', order.get('status'))
        
        is_expired = False
        try:
            show_date = str(order.get('ShowDate', ''))
            show_time = str(order.get('ShowTime', '')).split('.')[0]
            if show_date and show_time:
                show_datetime = datetime.strptime(f"{show_date} {show_time}", "%Y-%m-%d %H:%M:%S")
                is_expired = show_datetime < current_time
        except ValueError:
            pass 

        # Save the expiration status inside the order dictionary for later use
        order['is_expired'] = is_expired    

        if status == 'Pending': 
                pending_orders.append(order)
        elif status in ['Confirmed', 'Cancelled']:
            history_orders.append(order)

    # Create the visual tabs
    tab_pending, tab_history = st.tabs(["Pending Orders", "Order History"])

    # --- TAB 1: PENDING ORDERS ---
    with tab_pending:
        st.toast("Unpaid pending orders will automatically cancel 5 minutes after booking to free up seats.")

        if not pending_orders:
            st.success("You have no pending orders! All caught up.")
        else:
            for order in pending_orders:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2.5, 1, 1])
                    
                    booking_id = order.get('BookingID', order.get('booking_id'))
                    
                    with col1:
                        st.subheader(f"{order.get('Title', 'Unknown Movie')}")
                        st.write(f"**Date:** {order.get('ShowDate', 'N/A')} | **Time:** {order.get('ShowTime', 'N/A')}")
                        st.write(f"**Booking ID:** {booking_id}")
                        st.write(f"**Cinema:** {order.get('CinemaName', 'N/A')}")
                        st.write(f"**Seats:** {order.get('AssignedSeats', 'N/A')}")
                        st.write(f"**Address:** {order.get('Address', 'N/A')}")
                        st.markdown(f"**Amount Due:** <span style='color: #4CAF50;'>Rs. {order.get('TotalAmount', 0.0)}</span>", unsafe_allow_html=True)
                        
                    with col2:
                        st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
                        if st.button("Pay Now", key=f"pay_{booking_id}", type="primary", use_container_width=True):
                            st.session_state['current_booking_id'] = booking_id
                            st.session_state.pop('current_order', None)
                            st.switch_page(config.payment_page)
                    with col3:
                        st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
                        cancel_key = f"cancel_toggle_{booking_id}"
                        if cancel_key not in st.session_state:
                            st.session_state[cancel_key] = False
                        
                        if st.button("Cancel", key=f"cancel_{booking_id}", use_container_width=True):
                            st.session_state[cancel_key] = not st.session_state[cancel_key]
                    
                    # --- Cancellation Reason Form (toggles below the order card) ---
                    if st.session_state.get(f"cancel_toggle_{booking_id}", False):
                        with st.container(border=True):
                            st.markdown("**Why are you cancelling this booking?**")
                            
                            selected_reason = st.selectbox(
                                "Reason for cancellation",
                                options=config.CANCELLATION_REASONS,
                                key=f"cancel_reason_{booking_id}",
                                label_visibility="collapsed"
                            )
                            
                            # If "Other" is selected, show a custom text input
                            custom_reason = ""
                            if selected_reason == "Other":
                                custom_reason = st.text_input(
                                    "Please specify your reason:",
                                    key=f"cancel_custom_{booking_id}",
                                    placeholder="Enter your reason here..."
                                )
                            
                            col_confirm, col_back = st.columns(2)
                            with col_confirm:
                                if st.button("Confirm Cancellation", key=f"confirm_cancel_{booking_id}", type="primary", use_container_width=True):
                                    # Determine the final reason string
                                    final_reason = custom_reason.strip() if selected_reason == "Other" else selected_reason
                                    
                                    if selected_reason == "Other" and not final_reason:
                                        st.warning("Please specify your reason for cancellation.")
                                    else:
                                        with st.spinner("Canceling..."):
                                            logger.info("Cancelling Ticket!!")
                                            cancel_resp = requests.put(
                                                f"{api_url.rstrip('/')}/cancelBooking/{booking_id}", 
                                                headers=headers,
                                                data={"cancellation_reason": final_reason}
                                            )
                                            if cancel_resp.status_code == 200:
                                                st.toast(cancel_resp.json().get("message", f"Booking {booking_id} cancelled successfully."))
                                                # Clean up session state
                                                if st.session_state.get('current_booking_id') == booking_id:
                                                    st.session_state.pop('current_order', None)
                                                    st.session_state.pop('current_booking_id', None)
                                                    user_email = st.session_state.get('user_email', 'unknown')
                                                    st.session_state.pop(f"timer_{user_email}_{booking_id}", None)
                                                st.session_state[f"cancel_toggle_{booking_id}"] = False
                                                st.switch_page("Frontend/Dashboard.py")
                                                st.rerun()
                                            else:
                                                try:
                                                    st.error(cancel_resp.json().get("detail", "Failed to cancel."))
                                                except ValueError:
                                                    st.error("Server error during cancellation.")
                            with col_back:
                                if st.button("Go Back", key=f"back_cancel_{booking_id}", use_container_width=True):
                                    st.session_state[f"cancel_toggle_{booking_id}"] = False
                                    st.rerun()

    # --- TAB 2: ORDER HISTORY ---
    with tab_history:
        if not history_orders:
            st.info("Your order history is empty.")
        else:
            for order in history_orders:
                with st.container(border=True):
                    
                    status = order.get('BookingStatus', order.get('status'))
                    booking_id = order.get('BookingID', order.get('booking_id'))
                    
                    status_color = "#4CAF50" if status == "Confirmed" else "#FF5252"
                    payment_method = order.get('PaymentMethod') or 'None'
                    
                    # Split into columns to place the Refund button on the right
                    col_info, col_action = st.columns([3.5, 1])
                    
                    with col_info:
                        st.subheader(f"{order.get('Title', 'Unknown Movie')}")
                        st.write(f"**Date:** {order.get('ShowDate', 'N/A')} | **Time:** {order.get('ShowTime', 'N/A')}")
                        st.write(f"**Booking ID:** {booking_id}")
                        st.write(f"**Cinema:** {order.get('CinemaName', 'N/A')}")
                        st.write(f"**Seats:** {order.get('AssignedSeats', 'N/A')}")
                        st.write(f"**Address:** {order.get('Address', 'N/A')}")
                        st.write(f"**Total Amount:** Rs. {order.get('TotalAmount', 0.0)}")
                        st.write(f"**Payment Method:** {payment_method}")
                        st.markdown(f"**Status:** <span style='color: {status_color}; font-weight: bold;'>{status}</span>", unsafe_allow_html=True)

                    with col_action:
                        # Only show the refund button if the order is confirmed
                        if status == "Confirmed" and not order.get('is_expired', False):
                            st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
                            
                            refund_key = f"refund_toggle_{booking_id}"
                            if refund_key not in st.session_state:
                                st.session_state[refund_key] = False
                            
                            if st.button("Refund", key=f"refund_{booking_id}", use_container_width=True):
                                st.session_state[refund_key] = not st.session_state[refund_key]
                    
                    # --- Refund Reason Form (toggles below the order card) ---
                    if status == "Confirmed" and not order.get('is_expired', False) and st.session_state.get(f"refund_toggle_{booking_id}", False):
                        with st.container(border=True):
                            st.markdown("**Why are you requesting a refund?**")
                            st.caption("A 10% cancellation fee will be applied to your refund.")
                            
                            selected_reason = st.selectbox(
                                "Reason for refund",
                                options=config.CANCELLATION_REASONS,
                                key=f"refund_reason_{booking_id}",
                                label_visibility="collapsed"
                            )
                            
                            # If "Other" is selected, show a custom text input
                            custom_reason = ""
                            if selected_reason == "Other":
                                custom_reason = st.text_input(
                                    "Please specify your reason:",
                                    key=f"refund_custom_{booking_id}",
                                    placeholder="Enter your reason here..."
                                )
                            
                            col_confirm, col_back = st.columns(2)
                            with col_confirm:
                                if st.button("Confirm Refund", key=f"confirm_refund_{booking_id}", type="primary", use_container_width=True):
                                    final_reason = custom_reason.strip() if selected_reason == "Other" else selected_reason
                                    
                                    if selected_reason == "Other" and not final_reason:
                                        st.warning("Please specify your reason for refund.")
                                    else:
                                        with st.spinner("Processing refund... Please wait."):
                                            time.sleep(5)
                                            
                                            refund_resp = requests.put(
                                                f"{api_url.rstrip('/')}/cancelBooking/{booking_id}", 
                                                headers=headers,
                                                data={"cancellation_reason": final_reason}
                                            )
                                            
                                            if refund_resp.status_code == 200:
                                                st.toast(refund_resp.json().get("message", "Refund processed successfully."))
                                                st.session_state[f"refund_toggle_{booking_id}"] = False
                                                st.rerun()
                                            else:
                                                try:
                                                    st.error(refund_resp.json().get("detail", "Failed to process refund."))
                                                except ValueError:
                                                    st.error("Server error during refund processing.")
                            with col_back:
                                if st.button("Go Back", key=f"back_refund_{booking_id}", use_container_width=True):
                                    st.session_state[f"refund_toggle_{booking_id}"] = False
                                    st.rerun()