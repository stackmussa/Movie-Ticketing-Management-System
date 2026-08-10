import streamlit as st
import requests 
import app.config as config
import app.queries as queries
import time
from app.logger import logger 
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

# Track which specific seats the user clicks
if 'selected_seats' not in st.session_state:
    st.session_state['selected_seats'] = []

# --- Load Target Data ---
movie_title = st.session_state['Booking_target_movie']
city = st.session_state['Booking_target_city']
user_email = st.session_state['user_email']
movie_details = st.session_state.get('Booking_target_details', {})

st.title(f"{movie_title}")
st.write(f"**Location:** {movie_details.get('CinemaName', 'Unknown')} ({city})")
st.write(f"**Date:** {movie_details.get('ShowDate', 'TBD')}")
st.write(f"**Time:** {movie_details.get('ShowTime', 'TBD')}")
st.divider()

# --- Fetch Availability ---
availability = {"Platinum": 0, "Gold": 0, "Standard": 0, "Recliner": 0}
booked_seats_list = []
try:
    # fetch total count of seats availaible category vise
    avail_resp = requests.get(f"{api_url}/availability", params={"title": movie_title, "city": city})
    if avail_resp.status_code == 200:
        availability = avail_resp.json()

    # fetch the exact seats that are taken
    booked_resp = requests.get(f"{api_url}/booked_seats", params={"title": movie_title, "city": city})
    if booked_resp.status_code == 200:
        booked_seats_list = booked_resp.json().get("booked_seats", [])

except Exception as e:
    logger.error(f"Failed to fetch availability: {e}")

st.subheader("Select Category & Tickets")

# Display general category capacities
st.info(f"**Total Available in Hall:** Platinum: {availability.get('Platinum', 0)} | Gold: {availability.get('Gold', 0)} | Standard: {availability.get('Standard', 0)}")

selected_category = st.selectbox("Seat Category", ["Platinum", "Gold", "Standard", "Recliners"])

# If the user switches categories, wipe their previously selected seats so they dont book the wrong tier
if 'prev_category' not in st.session_state:
    st.session_state['prev_category'] = selected_category
elif st.session_state['prev_category'] != selected_category:
    st.session_state['selected_seats'] = []
    st.session_state['prev_category'] = selected_category
    st.rerun()

st.divider()
st.subheader("Hall Layout!")
st.write("Click on the available seats to select them. Hover over grayed-out seats to see why they are unavailable.")

max_available = availability.get(selected_category, 0)
max_limit = min(10, max_available)

# Render the interactive map based on real-time data
if max_available > 0:
    components.render_interactive_seat_map(selected_category, booked_seats_list, max_limit)
else:
    st.error(f"No seats left for {selected_category}.")

st.markdown(components.get_legend_html(), unsafe_allow_html=True)
st.divider()


# --- 3. Checkout ---
st.subheader("Checkout!")

col_clear, col_checkout = st.columns([1, 2])
with col_clear:
    if st.button("Clear Selection", use_container_width=True):
        # Explicitly uncheck the Streamlit visual boxes
        for seat in st.session_state.get('selected_seats', []):
            chk_key = f"chk_{seat}"
            if chk_key in st.session_state:
                del st.session_state[chk_key]
                
        st.session_state['selected_seats'] = []
        st.rerun()

# Infer quantity directly from the clicks
tickets_needed = len(st.session_state['selected_seats'])
st.write(f"**Selected Seats:** {', '.join(st.session_state['selected_seats']) if tickets_needed > 0 else 'None'}")
st.write(f"**Total Tickets:** {tickets_needed}")

if tickets_needed > 0 and tickets_needed <= 10:
    if st.button("Check Out", type="primary", use_container_width=True):
        with st.spinner("Processing your booking..."):

            headers = {
                "Authorization": f"Bearer {st.session_state.get('token')}"
            }

            # Send the comma-separated string to the backend
            payload = {
                "title": movie_title,
                "City": city,
                "selectedSeats": ",".join(st.session_state['selected_seats']),
                "seatCategory": selected_category
            }
            
            response = requests.post(f"{api_url}/booking", data=payload, headers=headers)
            
            if response.status_code == 200:
                booking_info = response.json().get("booking_details", {})
                st.success("Booking confirmed! Seats have been successfully allocated.")
                
                assigned_seats_str = ", ".join(booking_info.get("assigned_seats", []))
                
                st.info(f"""
                **Booking ID:** {booking_info.get("booking_id")}  
                **Assigned Seats:** {assigned_seats_str}  
                **Total Amount:** {booking_info.get("currency", "PKR")} {booking_info.get("total_amount")}
                """)

                time.sleep(3)
                
                # Push booking ID for payment page and wipe selected seats memory
                st.session_state['current_booking_id'] = booking_info.get("booking_id")
                st.session_state['selected_seats'] = []
                st.session_state.pop('current_order', None)
                
                st.switch_page(config.payment_page)
                
            else:
                error_detail = response.json().get("detail", "Booking failed.")
                st.error(error_detail)
                # Allow them to read the error for 2.5 seconds
                time.sleep(2.5) 
                
                # Wipe all checkbox states and reload the page
                for seat in st.session_state.get('selected_seats', []):
                    if f"chk_{seat}" in st.session_state:
                        del st.session_state[f"chk_{seat}"]
                st.session_state['selected_seats'] = []
                st.rerun()
else:
    st.button("Check Out", type="primary", use_container_width=True, disabled=True)