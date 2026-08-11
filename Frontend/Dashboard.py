from datetime import datetime, timedelta
import time
import streamlit as st
import requests 
import app.config as config
import app.logger as logger 
import app.queries as queries

api_url = config.API_URL


if 'flash_message' in st.session_state:
    st.toast(st.session_state['flash_message'])
    del st.session_state['flash_message']


def check_booking_conflict(target_show: dict, api_url: str, auth_token: str) -> bool:
    """
    Checks if a target show overlaps with any of the CURRENT user's 
    Pending or Confirmed bookings. Returns True if a conflict is found.
    
    This function is stateless — it takes the auth token explicitly,
    ensuring it always validates against the correct user's orders.
    """
    if not auth_token:
        return False  # No token = no user = no conflict possible
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = requests.get(f"{api_url.rstrip('/')}/pendingorders", headers=headers)
        
        if resp.status_code != 200:
            return False  # API error (e.g. 401 expired token) — fail open, let the user proceed
        
        user_orders = resp.json()
        
        if not isinstance(user_orders, list) or len(user_orders) == 0:
            return False  # No existing bookings — no possible conflict
        
        # Parse the TARGET show's start/end window
        target_date = target_show.get("ShowDate", "")
        target_time = str(target_show.get("ShowTime", "")).split('.')[0]
        target_duration = target_show.get("DurationMinutes", 150)
        
        if len(target_time.split(':')) == 2:
            target_time += ":00"
        
        target_start = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M:%S")
        target_end = target_start + timedelta(minutes=target_duration)
        
        # Compare against ONLY this user's active (Pending/Confirmed) bookings
        for order in user_orders:
            status = order.get('BookingStatus', '')
            
            if status not in ['Pending', 'Confirmed']:
                continue  # Skip cancelled/expired orders
            
            try:
                o_date = order.get('ShowDate', '')
                o_time = str(order.get('ShowTime', '')).split('.')[0]
                o_duration = order.get("DurationMinutes", 150)
                
                if len(o_time.split(':')) == 2:
                    o_time += ":00"
                
                order_start = datetime.strptime(f"{o_date} {o_time}", "%Y-%m-%d %H:%M:%S")
                order_end = order_start + timedelta(minutes=o_duration)
                
                # Overlap Formula: (StartA < EndB) AND (EndA > StartB)
                if target_start < order_end and target_end > order_start:
                    return True
                    
            except (ValueError, TypeError):
                continue  # Skip orders with unparseable dates — don't block the user
        
        return False
        
    except Exception:
        return False  # Network error — fail open, let the user proceed


def display_movie_tiles(show_List, filter_city=None, key_prefix="main"):
    if not show_List:
        logger.info("No Available Shows")
        st.info("No Available Shows")
        return
    if filter_city:
        shows_to_display = [show for show in show_List if show.get("City") == filter_city]
    else:
        shows_to_display = show_List
    if not shows_to_display:
        st.warning(f"No movies currently scheduled in {filter_city}.")
        return 
    cols = st.columns(3)
    for index, show in enumerate(shows_to_display):
        col = cols[index %3]
        with col: 
            with st.container(border=True, height=420):

                # Fetching Movie Tiles Content
                date = show.get("ShowDate", "TBD")
                title = show.get("Title", "Unknown Title")
                show_time = show.get("ShowTime", "TBD")
                cinema = show.get("CinemaName", "Unknown Show")
                address = show.get("Address", "Unknown Show")
                price = show.get("TicketPrice", "TBD")

                #Movie Tiles Content
                st.subheader(f"{title}")
                st.write(f"**Date: {date}**")
                st.write(f"**Time:  {show_time}**")
                st.write(f"**Cinema Name:  {cinema}**")
                st.write(f"**Cinema Address:  {address}**")
                st.write(f"**Standard Ticket Price:  Rs.{price}**")

                st.markdown("<br>", unsafe_allow_html=True)

                #Booking Button
                if st.button("Book Now", key=f"{key_prefix}_book_{index}", use_container_width=True, type="primary"):

                    # storing Movie's Meta Data to keep track of the Movie 
                    st.session_state['Booking_target_movie'] = title
                    st.session_state['Booking_target_city'] = filter_city
                    st.session_state['Booking_target_details'] = show

                    # Overlap check: pass the CURRENT user's token explicitly
                    current_token = st.session_state.get('token', '')
                    conflict_found = check_booking_conflict(show, api_url, current_token)

                    if conflict_found:
                        st.toast("Heads up! This movie overlaps with another Pending or Confirmed booking in your account")
                        time.sleep(5)
                    else:
                        st.toast(f"Navigating to Booking Page for {title}")

                    # Navigate to the booking page
                    st.switch_page(config.booking_page)

#Dashboard
st.title("Movie Ticket Purchase System")
st.write(f"Welcome to your dashboard, **{st.session_state['user_email'].lower()}**!")

if st.button("Logout", type="primary"):
    # wipes the entire browser tab's memory
    st.session_state.clear()

    st.session_state['logged_in'] = False
    st.session_state['user_email'] = ''
    st.rerun() # Triggers main.py to boot the user back to the login page

st.divider()

#City Selection
st.subheader("Where are you watching?")
selected_city = st.selectbox("Select your city to view available movies:", config.cities_list, label_visibility="collapsed")
st.divider()


st.subheader("Search for Desired Movie")

# 1. We need the list of all available movies to feed the auto-suggest.
# We can grab this by doing a quick fetch of all shows first.
all_shows = []
try:
    resp = requests.get(f"{api_url}/shows")
    if resp.status_code == 200:
        all_shows = resp.json()
except:
    pass

# Extract unique titles for the dropdown
unique_titles = list(set([show.get("Title") for show in all_shows if show.get("Title")]))

# 2. Use selectbox instead of text_input. 
# As the user types in this box, Streamlit instantly filters the dropdown options!
selected_title = st.selectbox(
    "Movie Title", 
    options=[""] + unique_titles,
    index=0,
    placeholder="Start typing a movie title...",
    label_visibility="collapsed"
)

# 3. The moment the user clicks one of the suggested matches, this block executes instantly.
if selected_title:
    with st.spinner(f"Loading shows for {selected_title}..."):
        # Now we query the DB for the exact match
        response = requests.get(f"{api_url}/show/{selected_title}")

        if response.status_code == 200:
            shows_data = response.json()
            
            # Filter by city
            city_shows = [show for show in shows_data if show.get("City") == selected_city]
            
            if city_shows:
                st.session_state['search_results'] = city_shows
                st.session_state['search_title'] = selected_title
            else:
                st.warning(f"No movies currently scheduled in {selected_city}.")
                st.session_state.pop('search_results', None)
        else:
            error_details = response.json().get("detail", "No such record found!")
            st.error(error_details)
            st.session_state.pop('search_results', None)
else:
    # Clear results if they clear the box
    st.session_state.pop('search_results', None)
    st.session_state.pop('search_title', None)


# 4. Render the results
if 'search_results' in st.session_state:
    st.success(f"Searched Results for {st.session_state.get('search_title', '')}")
    display_movie_tiles(st.session_state['search_results'], filter_city=selected_city, key_prefix="search")

st.divider()

st.subheader(f"All Upcoming Shows in {selected_city}")

try:
    # Automatically fetch all shows when the dashboard loads
    response = requests.get(f"{api_url}/shows")
    if response.status_code == 200:
        shows_data = response.json()
        display_movie_tiles(shows_data, filter_city=selected_city, key_prefix="all")
    else:
        error_detail = response.json().get("detail", "Failed to fetch shows from database.")
        st.error(error_detail)
except requests.exceptions.ConnectionError:
    st.error("Cannot connect to the backend server. Please ensure FastAPI is running.")

st.divider()

