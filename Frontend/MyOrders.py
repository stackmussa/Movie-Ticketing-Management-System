import streamlit as st
import requests
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
            # Safely handle the specific 400 exception raised by your backend when empty
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
if not all_orders:
    st.info("You don't have any orders yet! Head to the dashboard to book a movie.")
else:
    # Filter the arrays based on the BookingStatus column returned from your database
    pending_orders = [o for o in all_orders if o.get('BookingStatus', o.get('status')) == 'Pending']
    history_orders = [o for o in all_orders if o.get('BookingStatus', o.get('status')) in ['Confirmed', 'Cancelled']]

    # Create the visual tabs
    tab_pending, tab_history = st.tabs(["Pending Orders", "Order History"])

    # --- TAB 1: PENDING ORDERS ---
    with tab_pending:
        if not pending_orders:
            st.success("You have no pending orders! All caught up.")
        else:
            for order in pending_orders:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2.5, 1, 1])
                    
                    # Account for potential variations in SQL column casing
                    booking_id = order.get('BookingID', order.get('booking_id'))
                    
                    with col1:
                        st.subheader(f"{order.get('Title', 'Unknown Movie')}")
                        st.write(f"**Booking ID:** {booking_id}")
                        st.write(f"**Cinema:** {order.get('CinemaName', 'N/A')}")
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
                        # The Cancel Button
                        if st.button("Cancel", key=f"cancel_{booking_id}", use_container_width=True):
                            with st.spinner("Canceling..."):
                                cancel_resp = requests.put(
                                    f"{api_url.rstrip('/')}/cancelBooking/{booking_id}", 
                                    headers=headers
                                )
                                if cancel_resp.status_code == 200:
                                    st.toast(f"Booking {booking_id} cancelled successfully.")
                                    # Refresh the UI immediately to move it to history
                                    st.rerun()
                                else:
                                    try:
                                        st.error(cancel_resp.json().get("detail", "Failed to cancel."))
                                    except ValueError:
                                        st.error("Server error during cancellation.")

    # --- TAB 2: ORDER HISTORY ---
    with tab_history:
        if not history_orders:
            st.info("Your order history is empty.")
        else:
            for order in history_orders:
                with st.container(border=True):
                    
                    status = order.get('BookingStatus', order.get('status'))
                    
                    # Dynamically set the text color based on the transaction status
                    status_color = "#4CAF50" if status == "Confirmed" else "#FF5252"
                    
                    st.subheader(f"{order.get('Title', 'Unknown Movie')}")
                    st.write(f"**Booking ID:** {order.get('BookingID', order.get('booking_id'))}")
                    st.write(f"**Cinema:** {order.get('CinemaName', 'N/A')}")
                    st.write(f"**Address:** {order.get('Address', 'N/A')}")
                    st.write(f"**Total Amount:** Rs. {order.get('TotalAmount', 0.0)}")
                    st.write(f"**Payment Method:** {order.get('PaymentMethod')}")
                    st.markdown(f"**Status:** <span style='color: {status_color}; font-weight: bold;'>{status}</span>", unsafe_allow_html=True)