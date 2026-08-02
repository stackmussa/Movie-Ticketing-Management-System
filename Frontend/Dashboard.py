import streamlit as st
import requests 
import app.config as config
import app.logger as logger 
import app.queries as queries

api_url = config.API_URL

CITIES = ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Hyderabad"]

if 'flash_message' in st.session_state:
    st.toast(st.session_state['flash_message'], icon="🎉")
    del st.session_state['flash_message']

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
                title = show.get("Title", "Unknown Title")
                time = show.get("ShowTime", "TBD")
                cinema = show.get("CinemaName", "Unknown Show")
                address = show.get("Address", "Unknown Show")
                price = show.get("TicketPrice", "TBD")

                #Movie Tiles Content
                st.subheader(f"{title}")
                st.write(f"**Time:  {time}**")
                st.write(f"**Cinema Name:  {cinema}**")
                st.write(f"**Cinema Address:  {address}**")
                st.write(f"**Standard Ticket Price:  Rs.{price}**")

                st.markdown("<br>", unsafe_allow_html=True)

                #Booking Button
                if st.button("Book Now", key=f"{key_prefix}_book_{index}", use_container_width=True, type="primary"):

                    #storing Movie's Meta Data to keep track of the Movie 
                    st.session_state['Booking_target_movie']= title
                    st.session_state['Booking_target_city']= filter_city
                    st.session_state['Booking_target_details']= show

                    st.toast(f"Navigating to Booking Page for {title}")

                    #st.switch_page("E:\BetaCode Work\Ticketing Management System\Frontend\Booking.py")

#Dashboard
st.title("Movie Ticket Purchase System")
st.write(f"Welcome to your dashboard, **{st.session_state['user_email']}**!")
st.divider()

#City Selection
st.subheader("Where are you watching?")
selected_city = st.selectbox("Select your city to view available movies:", CITIES, label_visibility="collapsed")
st.divider()


st.subheader("Search for Desired Movie")

# Using columns to place the text input and button side-by-side
col1, col2 = st.columns([3, 1])
with col1:
    search_title = st.text_input("Movie Title", placeholder="Enter movie title...", label_visibility="collapsed")
with col2:
    search_button = st.button("Search", use_container_width=True)

if search_button:
    if search_title.strip():
        with st.spinner(f"Searching for {search_title}!!"):
            response = requests.get(f"{api_url}/show/{search_title}")

            if response.status_code == 200:
                shows_data = response.json()
                
                # Filter by city before showing any success message
                city_shows = [show for show in shows_data if show.get("City") == selected_city]
                
                if city_shows:
                    st.success(f"Searched Results for {search_title}")
                    display_movie_tiles(city_shows, filter_city=None, key_prefix="search")
                else:
                    st.warning(f"No movies currently scheduled in {selected_city}.")
            else:
                error_details = response.json().get("detail", "No such record found!")
                st.error(error_details)
    else:
        st.warning("Please enter a movie title to search from!")
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

if st.button("Logout", type="primary"):
    st.session_state['logged_in'] = False
    st.session_state['user_email'] = ''
    st.rerun() # Triggers main.py to boot the user back to the login page