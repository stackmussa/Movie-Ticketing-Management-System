import streamlit as st
import time
import requests
import streamlit.components.v1 as st_components
import app.config as config
from app.logger import logger
from Frontend import components


api_url = config.API_URL

if not st.session_state.get('logged_in'):
    logger.error("Please Login First to Make Payment!")
    st.warning("Please Login First to Make Payment!")
    st.stop()

st.title("Payment Checkout")
st.write("Seamlessly Make Payments against your Order")
st.divider()

# --- Auto-Fetch Trigger ---
if 'current_booking_id' in st.session_state and 'current_order' not in st.session_state:
    auto_id = st.session_state['current_booking_id']
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    
    with st.spinner("Loading your order..."):
        resp = requests.get(f"{api_url.rstrip('/')}/booking/{auto_id}", headers=headers)
        if resp.status_code == 200:
            st.session_state['current_order'] = resp.json()

# fetching Order Details
col1, col2 = st.columns([3,1])
with col1:
    input_booking_id = st.text_input("Booking ID", placeholder="for example 123")
with col2:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    fetch_button = st.button("Fetch Order", use_container_width=True)

if fetch_button:
    if input_booking_id.isdigit():
        with st.spinner("Fetching Order Details...."):
            headers = {"Authorization" : f"Bearer {st.session_state.get('token')}"}
            resp = requests.get(f"{api_url}/booking/{input_booking_id}", headers=headers)

            if resp.status_code == 200:
                st.session_state['current_order'] = resp.json()
                st.session_state['current_booking_id'] = int(input_booking_id)
                logger.info(f"Fetched Order Details against Booking ID: {input_booking_id}")
            else:
                logger.error(f"Unable to Fetch Details against Booking ID: {input_booking_id}")
                st.error(f"Unable to Fetch Details againts Booking ID: {input_booking_id}")
    else:
        st.warning("Please enter a valid numeric Booking ID")

st.divider()

if 'current_order' in st.session_state:
    order = st.session_state['current_order']
    booking_id = st.session_state['current_booking_id']

    st.subheader("Order Summary")

    with st.container(border=True):
        st.write(f"**Movie:** {order.get('title')}")
        st.write(f"**Cinema:** {order.get('cinema')}")
        st.write(f"**Showtime:** {order.get('date')} at {order.get('time')}")
        st.write(f"**Status:** {order.get('status')}")
        st.markdown(f"<h3 style='color: #4CAF50;'>Total Due: Rs. {order.get('total_amount')}</h3>", unsafe_allow_html=True)

    if order.get('status') == 'Pending':

        # 5 minuts time counter 
        timer_key = f"timer_{booking_id}"
        if timer_key not in st.session_state:
            st.session_state[timer_key] = time.time()

        # Calculate exactly how many seconds are left (300 seconds = 5 minutes)
        elapsed_time = time.time() - st.session_state[timer_key]
        remaining_seconds = max(0, 300 - int(elapsed_time))

        timer_html = components.get_timer_html(remaining_seconds)
        st_components.html(timer_html, height=70)

        if remaining_seconds <=0:
            logger.error("The Booking time has passed, Please return to the dashboard to book again.")
            st.error("The Booking has expired. Please return to the dashboard to book again.")
            st.stop()

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

                            # Wipe the order from memory to prevent double-charging
                            del st.session_state['current_order']
                            st.session_state.pop(f"timer_{booking_id}", None)
                        except ValueError:
                            st.error(f"Server Error ({pay_resp.status_code}): {pay_resp.text}")
                    else:
                        try:
                            error_detail = pay_resp.json().get("detail", "Payment failed.")
                        except ValueError:
                            error_detail = f"Server Error ({pay_resp.status_code}): {pay_resp.text}"
                        st.error(error_detail)
            