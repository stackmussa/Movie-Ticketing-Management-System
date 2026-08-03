import streamlit as st
import requests 
import app.config as config
import app.logger as logger 
import app.queries as queries
from Frontend import components 

api_url = config.API_URL

if not st.session_state.get('logged_in'):
    logger.warning("Please log-in to Book Seats!")
    st.warning("Please log-in to Book Seats!")
    st.stop()

if 'Booking_target_movie' not in st.session_state:
    logger.error("Please Select a Movie, return to Dashboard!")
    st.warning("Please Select a Movie, return to Dashboard")
    st.stop()

# --- Load Target Data ---
movie_title = st.session_state['Booking_target_movie']
city = st.session_state['Booking_target_city']
user_email = st.session_state['user_email']
movie_details = st.session_state.get('Booking_target_details', {})

st.title(f"Booking: {movie_title}")
st.write(f"**Location:** {movie_details.get('CinemaName', 'Unknown')} ({city})")
st.write(f"**Date:** {movie_details.get('ShowDate', 'TBD')}")
st.write(f"**Time:** {movie_details.get('ShowTime', 'TBD')}")
st.divider()

# --- Fetch Availability ---
availability = {"Platinum": 0, "Gold": 0, "Standard": 0, "Recliner": 0}
try:
    avail_resp = requests.get(f"{api_url}/availability", params={"title": movie_title, "city": city})
    if avail_resp.status_code == 200:
        availability = avail_resp.json()
except Exception as e:
    logger.error(f"Failed to fetch availability: {e}")

st.subheader("Select Category & Tickets")

# Display Tickets Left
st.info(f"**Tickets Remaining:** Platinum: {availability.get('Platinum', 0)} | Gold: {availability.get('Gold', 0)} | Standard: {availability.get('Standard', 0)}")

col1, col2 = st.columns(2)

with col1:
    selected_category = st.selectbox("Seat Category",  ["Platinum", "Gold", "Standard", "Recliners"])

with col2:
    max_available = availability.get(selected_category, 0)
    if max_available == 0:
        st.error(f"Oops no seats left for the {selected_category}")
        logger.error(f"Oops no seats left for the {selected_category}")
        tickets_needed = 0
    else:
        max_limit = min(10, max_available)
        tickets_needed = st.number_input("Number of Tickets", min_value=1, max_value=10)

st.subheader("Hall Layout!")
st.write("Seats are automatically assigned best-available within your chosen category.")

# Creating a visual 5x10 grid using HTML/CSS
seat_map = components.get_seat_map_html(selected_category)
st.markdown(seat_map, unsafe_allow_html=True)

legend = components.get_legend_html()
st.markdown(legend, unsafe_allow_html=True)

st.divider()

# --- 3. Checkout ---
st.subheader("Checkout!")

if tickets_needed >0:
    if st.button("Check Out", type="primary", use_container_width=True):
        with st.spinner("Processing your booking..."):
            # Match the Form() data expected by api.py
            payload = {
                "email": user_email,
                "title": movie_title,
                "City": city,
                "TicketsNeeded": tickets_needed,
                "seatCategory": selected_category
            }
            
            response = requests.post(f"{api_url}/booking", data=payload)
            
            if response.status_code == 200:
                booking_info = response.json().get("booking_details", {})
                st.success("Booking confirmed! Seats have been successfully allocated.")
                
                # Display the auto-assigned seats returned from the API
                assigned_seats_str = ", ".join(booking_info.get("assigned_seats", []))
                
                st.info(f"""
                **Booking ID:** {booking_info.get("booking_id")}  
                **Assigned Seats:** {assigned_seats_str}  
                **Total Amount:** {booking_info.get("currency")} {booking_info.get("total_amount")}
                """)
                
                # Future Navigation to Payment
                # st.switch_page("frontend/payment.py")
                
            else:
                error_detail = response.json().get("detail", "Booking failed.")
                st.error(error_detail)
else:
    st.button("Check Out", type="primary", use_container_width=True, disabled=True)    