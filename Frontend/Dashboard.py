from datetime import datetime, timedelta, date
import time
import streamlit as st
import requests 
import app.config as config
from app.logger import logger 
from Frontend import components

api_url = config.API_URL


if 'flash_message' in st.session_state:
    st.toast(st.session_state['flash_message'])
    del st.session_state['flash_message']


def check_booking_conflict(target_show: dict, api_url: str, auth_token: str) -> bool:
    """
    Checks if a target show overlaps with any of the CURRENT user's 
    Pending or Confirmed bookings. Returns True if a conflict is found.
    """
    if not auth_token:
        return False  # No token = no user = no conflict possible
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = requests.get(f"{api_url.rstrip('/')}/pendingorders", headers=headers)
        
        if resp.status_code != 200:
            return False  # API error - fail open, let the user proceed
        
        user_orders = resp.json()
        
        if not isinstance(user_orders, list) or len(user_orders) == 0:
            return False  # No existing bookings - no possible conflict
        
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
                continue  # Skip orders with unparseable dates - don't block the user
        
        return False
        
    except Exception:
        return False  # Network error - fail open, let the user proceed


def fetch_omdb_data(title: str) -> dict:
    """Fetch OMDb ratings for a movie title via the backend proxy. Returns empty dict on failure."""
    try:
        resp = requests.get(f"{api_url}/omdb/{title}", timeout=6)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


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

    # Inject custom CSS once
    st.markdown(components.get_movie_card_css(), unsafe_allow_html=True)

    # Pre-fetch OMDb ratings for unique titles to avoid duplicate calls
    unique_titles_in_view = list(set(s.get("Title", "") for s in shows_to_display))
    omdb_cache = {}
    for t in unique_titles_in_view:
        if t and t not in omdb_cache:
            omdb_cache[t] = fetch_omdb_data(t)

    cols = st.columns(3)
    for index, show in enumerate(shows_to_display):
        col = cols[index % 3]
        with col: 
            with st.container(border=False):

                # Fetching Movie Tiles Content
                date_val = show.get("ShowDate", "TBD")
                title = show.get("Title", "Unknown Title")
                show_time = show.get("ShowTime", "TBD")
                cinema = show.get("CinemaName", "Unknown Show")
                address = show.get("Address", "Unknown Show")
                price = show.get("TicketPrice", "TBD")
                genre = show.get("Genre", "")
                
                # Use a reliable placeholder image if the database link is missing or invalid
                pURL = show.get("PosterURL")
                if not pURL or pURL == "No Preview" or "imdb.com" in pURL:
                    pURL = "https://placehold.co/400x600/1e1e2f/FFD700.png?text=Hover+to+View+Details"
                
                tURL = show.get("TrailerURL", "")

                # Get cached OMDb data for this title
                omdb_data = omdb_cache.get(title, {})

                # Render the custom HTML Card from components.py
                card_html = components.render_movie_card_html(
                    title=title, 
                    date=date_val, 
                    show_time=show_time, 
                    cinema=cinema, 
                    address=address, 
                    price=price, 
                    poster_url=pURL,
                    genre=genre,
                    omdb_data=omdb_data
                )
                st.markdown(card_html, unsafe_allow_html=True)

                # Action Buttons: Book Now + Trailer side-by-side
                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    # Booking Button
                    if st.button("Book Now", key=f"{key_prefix}_book_{index}", use_container_width=True, type="primary"):

                        # storing Movie's Meta Data to keep track of the Movie 
                        st.session_state['Booking_target_movie'] = title
                        st.session_state['Booking_target_city'] = filter_city
                        st.session_state['Booking_target_details'] = show

                        # Overlap check: pass the CURRENT user's token explicitly
                        current_token = st.session_state.get('token', '')
                        conflict_found = check_booking_conflict(show, api_url, current_token)

                        if conflict_found:
                            st.toast("Heads up! This movie overlaps with another Pending or Confirmed booking in your account.")
                            time.sleep(3.5)
                        else:
                            st.toast(f"Navigating to Booking Page for {title}")

                        # Navigate to the booking page
                        st.switch_page(config.booking_page)

                with btn_col2:
                    # Trailer Link Button
                    if tURL and tURL != "No Trailer Found":
                        st.link_button("Trailer", url=tURL, use_container_width=True)
                    else:
                        st.button("Trailer", key=f"{key_prefix}_notrail_{index}", disabled=True, use_container_width=True)

                # Reviews Button full width underneath
                if st.button("See Reviews", key=f"{key_prefix}_review_{index}", use_container_width=True):
                    st.session_state['Review_target_movie'] = title
                    st.session_state['Review_target_details'] = show
                    st.switch_page(config.reviews_page)


# ==========================================
# Dashboard Layout
# ==========================================
st.title("Movie Ticket Purchase System")
st.write(f"Welcome to your dashboard, **{st.session_state['user_email'].lower()}**!")

if st.button("Logout", type="primary"):
    # wipes the entire browser tab's memory
    st.session_state.clear()
    st.session_state['logged_in'] = False
    st.session_state['user_email'] = ''
    st.rerun() # Triggers main.py to boot the user back to the login page

st.divider()

# ==========================================
# Filters Section: City, Genre, Date
# ==========================================
st.subheader("Filters")

filter_col1, filter_col2, filter_col3 = st.columns(3)

# City Selection
with filter_col1:
    selected_city = st.selectbox("City", config.cities_list)

# Genre Filter (fetched from DB)
available_genres = []
try:
    genre_resp = requests.get(f"{api_url}/genres")
    if genre_resp.status_code == 200:
        available_genres = genre_resp.json()
except Exception:
    pass

with filter_col2:
    selected_genre = st.selectbox("Genre", options=["All"] + available_genres)

# Date Range Filter (calendar-based)
min_date = date.today()
max_date = date.today() + timedelta(days=365)
try:
    dr_resp = requests.get(f"{api_url}/show-date-range")
    if dr_resp.status_code == 200:
        dr_data = dr_resp.json()
        if dr_data.get("min_date"):
            min_date = date.fromisoformat(str(dr_data["min_date"]))
        if dr_data.get("max_date"):
            max_date = date.fromisoformat(str(dr_data["max_date"]))
except Exception:
    pass

with filter_col3:
    selected_date = st.date_input(
        "Show Date (Clear to see all)",
        value=None,
        min_value=min_date,
        max_value=max_date,
    )

# Normalize selected_date to single dates
if isinstance(selected_date, tuple):
    if len(selected_date) == 2:
        date_start, date_end = selected_date
    elif len(selected_date) == 1:
        date_start = selected_date[0]
        date_end = selected_date[0]
    else:
        date_start, date_end = None, None
else:
    date_start = selected_date
    date_end = selected_date

st.divider()


def apply_filters(shows_data: list, city: str, genre: str, d_start, d_end) -> list:
    """Applies city, genre, and date filters to a list of show dicts."""
    filtered = []
    for show in shows_data:
        # City filter
        if city and show.get("City") != city:
            continue

        # Genre filter
        if genre and genre != "All":
            show_genre = show.get("Genre", "")
            # Check if the selected genre appears in the show's compound genre string
            genre_parts = [g.strip() for g in show_genre.replace("/", ",").split(",")]
            if genre not in genre_parts:
                continue

        # Date filter
        try:
            if d_start and d_end:
                show_date_str = str(show.get("ShowDate", ""))
                show_date = date.fromisoformat(show_date_str)
                if show_date < d_start or show_date > d_end:
                    continue
        except (ValueError, TypeError):
            pass  # If date is unparseable, include the show

        filtered.append(show)
    return filtered


# ==========================================
# Predictive Search
# ==========================================
st.subheader("Search for Desired Movie")

# 1. Grab all shows to feed the auto-suggest.
all_shows = []
try:
    resp = requests.get(f"{api_url}/shows")
    if resp.status_code == 200:
        all_shows = resp.json()
except:
    pass

# Extract unique titles for the dropdown
unique_titles = list(set([show.get("Title") for show in all_shows if show.get("Title")]))

# 2. Use selectbox instead of text_input for instant type-ahead filtering
selected_title = st.selectbox(
    "Movie Title", 
    options=[""] + unique_titles,
    index=0,
    placeholder="Start typing a movie title...",
    label_visibility="collapsed"
)

# 3. Execute instantly upon selection
if selected_title:
    with st.spinner(f"Loading shows for {selected_title}..."):
        response = requests.get(f"{api_url}/show/{selected_title}")

        if response.status_code == 200:
            shows_data = response.json()
            
            # Apply all filters
            filtered_shows = apply_filters(shows_data, selected_city, selected_genre, date_start, date_end)
            
            if filtered_shows:
                st.session_state['search_results'] = filtered_shows
                st.session_state['search_title'] = selected_title
            else:
                st.warning(f"No matching shows found for the selected filters.")
                st.session_state.pop('search_results', None)
        else:
            error_details = response.json().get("detail", "No such record found!")
            st.error(error_details)
            st.session_state.pop('search_results', None)
else:
    # Clear results if they clear the box
    st.session_state.pop('search_results', None)
    st.session_state.pop('search_title', None)


# 4. Render the search results
if 'search_results' in st.session_state:
    st.success(f"Searched Results for {st.session_state.get('search_title', '')}")
    display_movie_tiles(st.session_state['search_results'], filter_city=selected_city, key_prefix="search")

st.divider()

# 5. Render standard upcoming shows feed (with filters applied)
st.subheader(f"All Upcoming Shows in {selected_city}")

try:
    response = requests.get(f"{api_url}/shows")
    if response.status_code == 200:
        shows_data = response.json()
        # Apply genre and date filters to the main feed
        filtered_main = apply_filters(shows_data, selected_city, selected_genre, date_start, date_end)
        display_movie_tiles(filtered_main, filter_city=selected_city, key_prefix="all")
    else:
        error_detail = response.json().get("detail", "Failed to fetch shows from database.")
        st.error(error_detail)
except requests.exceptions.ConnectionError:
    st.error("Cannot connect to the backend server. Please ensure FastAPI is running.")

st.divider()