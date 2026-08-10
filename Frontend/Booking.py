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

if st.session_state.get('clear_pending'):
    for seat in st.session_state.get('selected_seats', []):
        chk_key = f"chk_{seat}"
        st.session_state[chk_key] = False 
            
    st.session_state['selected_seats'] = []
    st.session_state['clear_pending'] = False   

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

# ============================================================
# USER REVIEWS SECTION
# ============================================================
st.subheader("User Reviews")

# --- Fetch existing reviews ---
review_data = {"average_rating": 0, "total_reviews": 0, "reviews": []}
try:
    rev_resp = requests.get(f"{api_url}/reviews/{movie_title}")
    if rev_resp.status_code == 200:
        review_data = rev_resp.json()
except Exception as e:
    logger.error(f"Failed to fetch reviews: {e}")

avg_rating = review_data.get("average_rating", 0)
total_reviews = review_data.get("total_reviews", 0)
all_reviews = review_data.get("reviews", [])

# --- Average Rating Display ---
def render_star_html(rating_val, size=22):
    """Generate HTML for gold stars from a float rating."""
    full = int(rating_val)
    half = 1 if (rating_val - full) >= 0.3 else 0
    empty = 5 - full - half
    stars_html = ""
    for _ in range(full):
        stars_html += f'<span style="color:#FFD700;font-size:{size}px;">★</span>'
    if half:
        stars_html += f'<span style="color:#FFD700;font-size:{size}px;">★</span>'
    for _ in range(empty):
        stars_html += f'<span style="color:#555;font-size:{size}px;">★</span>'
    return stars_html

rating_stars_html = render_star_html(avg_rating, size=28)

st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
    border: 1px solid #2a2a4a;
    display: flex;
    align-items: center;
    gap: 18px;
">
    <div style="text-align: center;">
        <div style="font-size: 42px; font-weight: 700; color: #FFD700;">{avg_rating}</div>
        <div>{rating_stars_html}</div>
    </div>
    <div style="border-left: 1px solid #444; padding-left: 18px;">
        <div style="font-size: 16px; color: #ccc;">Based on <strong style="color:#fff;">{total_reviews}</strong> review{'s' if total_reviews != 1 else ''}</div>
        <div style="font-size: 13px; color: #888; margin-top: 4px;">Share your experience below!</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Separate top-level reviews and replies ---
top_level_reviews = [r for r in all_reviews if r.get("ParentReviewID") is None]
replies_map = {}
for r in all_reviews:
    parent_id = r.get("ParentReviewID")
    if parent_id is not None:
        if parent_id not in replies_map:
            replies_map[parent_id] = []
        replies_map[parent_id].append(r)

# --- Render Reviews in Chat Style ---
if top_level_reviews:
    for review in top_level_reviews:
        review_id = review.get("ReviewID")
        user_name = review.get("UserName", "Anonymous")
        rating = review.get("Rating")
        text = review.get("ReviewText", "")
        created = review.get("CreatedAt", "")

        # Parse created time for display
        try:
            from datetime import datetime as dt
            created_dt = dt.strptime(created.split('.')[0], "%Y-%m-%d %H:%M:%S")
            time_display = created_dt.strftime("%b %d, %Y at %I:%M %p")
        except:
            time_display = created

        stars = render_star_html(rating, size=16) if rating else ""

        # Top-level review card
        st.markdown(f"""
        <div style="
            background: #1e1e2f;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 8px;
            border-left: 3px solid #FFD700;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="
                        width: 36px; height: 36px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        display: flex; align-items: center; justify-content: center;
                        font-weight: 700; font-size: 15px; color: white;
                    ">{user_name[0].upper()}</div>
                    <div>
                        <div style="font-weight: 600; color: #e0e0e0; font-size: 14px;">{user_name}</div>
                        <div style="font-size: 11px; color: #888;">{time_display}</div>
                    </div>
                </div>
                <div>{stars}</div>
            </div>
            <div style="color: #d0d0d0; font-size: 14px; line-height: 1.6; padding-left: 46px;">{text}</div>
        </div>
        """, unsafe_allow_html=True)

        # Render replies under this review
        review_replies = replies_map.get(review_id, [])
        for reply in review_replies:
            reply_name = reply.get("UserName", "Anonymous")
            reply_text = reply.get("ReviewText", "")
            reply_created = reply.get("CreatedAt", "")
            try:
                reply_dt = dt.strptime(reply_created.split('.')[0], "%Y-%m-%d %H:%M:%S")
                reply_time = reply_dt.strftime("%b %d, %Y at %I:%M %p")
            except:
                reply_time = reply_created

            st.markdown(f"""
            <div style="
                background: #252540;
                border-radius: 10px;
                padding: 12px 16px;
                margin-left: 46px;
                margin-bottom: 6px;
                border-left: 2px solid #667eea;
            ">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <div style="
                        width: 28px; height: 28px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #43e97b, #38f9d7);
                        display: flex; align-items: center; justify-content: center;
                        font-weight: 700; font-size: 12px; color: #1a1a2e;
                    ">{reply_name[0].upper()}</div>
                    <div>
                        <span style="font-weight: 600; color: #b0b0d0; font-size: 13px;">{reply_name}</span>
                        <span style="font-size: 11px; color: #666; margin-left: 8px;">{reply_time}</span>
                    </div>
                </div>
                <div style="color: #b8b8d0; font-size: 13px; line-height: 1.5; padding-left: 36px;">↳ {reply_text}</div>
            </div>
            """, unsafe_allow_html=True)

        # Reply button/form using Streamlit's native widgets
        reply_key = f"reply_toggle_{review_id}"
        if reply_key not in st.session_state:
            st.session_state[reply_key] = False

        col_reply_btn, _ = st.columns([1, 4])
        with col_reply_btn:
            if st.button("Reply", key=f"reply_btn_{review_id}", use_container_width=True):
                st.session_state[reply_key] = not st.session_state[reply_key]

        if st.session_state[reply_key]:
            reply_text_input = st.text_input("Your reply:", key=f"reply_input_{review_id}", placeholder="Type your reply...")
            if st.button("Send Reply", key=f"reply_send_{review_id}", type="primary"):
                if reply_text_input and reply_text_input.strip():
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
                        payload = {
                            "movie_title": movie_title,
                            "parent_review_id": review_id,
                            "review_text": reply_text_input.strip()
                        }
                        resp = requests.post(f"{api_url}/reviews/reply", data=payload, headers=headers)
                        if resp.status_code == 200:
                            st.success("Reply posted!")
                            st.session_state[reply_key] = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Failed to post reply."))
                    except Exception as e:
                        st.error(f"Error posting reply: {e}")
                else:
                    st.warning("Reply cannot be empty.")

        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="
        text-align: center;
        padding: 30px;
        background: #1e1e2f;
        border-radius: 12px;
        border: 1px dashed #444;
        margin-bottom: 16px;
    ">
        <div style="font-size: 40px; margin-bottom: 8px;">🎬</div>
        <div style="color: #888; font-size: 15px;">No reviews yet. Be the first to share your thoughts!</div>
    </div>
    """, unsafe_allow_html=True)

# --- Post a New Review Form ---
st.markdown("---")
st.markdown("#### Write a Review")

with st.container(border=True):
    # Star rating selector
    new_rating = st.select_slider(
        "Your Rating",
        options=[1, 2, 3, 4, 5],
        value=5,
        format_func=lambda x: "⭐" * x,
        key="new_review_rating"
    )
    
    new_review_text = st.text_area(
        "Your Review",
        placeholder="What did you think about this movie? Share your experience...",
        max_chars=1000,
        key="new_review_text",
        height=100
    )
    
    if st.button("Post Review", type="primary", use_container_width=True, key="post_review_btn"):
        if new_review_text and new_review_text.strip():
            try:
                headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
                payload = {
                    "movie_title": movie_title,
                    "rating": new_rating,
                    "review_text": new_review_text.strip()
                }
                resp = requests.post(f"{api_url}/reviews", data=payload, headers=headers)
                if resp.status_code == 200:
                    st.success("🎉 Your review has been posted!")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", "Failed to post review."))
            except Exception as e:
                st.error(f"Error posting review: {e}")
        else:
            st.warning("Please write your review before posting.")

st.divider()

# --- 3. Checkout ---
st.subheader("Checkout!")

col_clear, col_checkout = st.columns([1, 2])
#with col_clear:
if st.button("Clear Selection", use_container_width=True):
    st.session_state['clear_pending'] = True
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
                
                st.session_state['clear_pending'] = True
                st.rerun()
else:
    st.button("Check Out", type="primary", use_container_width=True, disabled=True)
