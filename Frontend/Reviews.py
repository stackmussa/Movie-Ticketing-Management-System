import streamlit as st
import requests 
import app.config as config
import time
from app.logger import logger 
from Frontend import components 

api_url = config.API_URL

if not st.session_state.get('logged_in'):
    logger.warning("Please log-in to view Reviews!")
    st.warning("Please log-in to view Reviews!")
    st.stop()

if 'Review_target_movie' not in st.session_state:
    logger.error("Please Select a Movie, return to Dashboard!")
    st.warning("Please Select a Movie, return to Dashboard")
    st.stop()

# --- Load Target Data ---
movie_title = st.session_state['Review_target_movie']
movie_details = st.session_state.get('Review_target_details', {})
user_email = st.session_state.get('user_email', '')
current_user_id = st.session_state.get('user_id', None)

st.title(f"Reviews — {movie_title}")

# Show movie info summary
st.markdown(components.render_movie_info_banner(movie_details), unsafe_allow_html=True)
st.divider()

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
st.markdown(components.render_rating_summary(avg_rating, total_reviews), unsafe_allow_html=True)

# --- Separate top-level reviews and replies ---
top_level_reviews = [r for r in all_reviews if r.get("ParentReviewID") is None]
replies_map = {}
for r in all_reviews:
    parent_id = r.get("ParentReviewID")
    if parent_id is not None:
        if parent_id not in replies_map:
            replies_map[parent_id] = []
        replies_map[parent_id].append(r)

# --- Render Reviews ---
if top_level_reviews:
    for review in top_level_reviews:
        review_id = review.get("ReviewID")
        user_name = review.get("UserName", "Anonymous")
        review_user_id = review.get("UserID")
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

        # Top-level review card
        st.markdown(components.render_review_card(user_name, time_display, rating, text), unsafe_allow_html=True)

        # Render replies under this review
        review_replies = replies_map.get(review_id, [])
        for reply in review_replies:
            reply_name = reply.get("UserName", "Anonymous")
            reply_user_id = reply.get("UserID")
            reply_text = reply.get("ReviewText", "")
            reply_created = reply.get("CreatedAt", "")
            reply_id = reply.get("ReviewID")
            try:
                reply_dt = dt.strptime(reply_created.split('.')[0], "%Y-%m-%d %H:%M:%S")
                reply_time = reply_dt.strftime("%b %d, %Y at %I:%M %p")
            except:
                reply_time = reply_created

            st.markdown(components.render_reply_card(reply_name, reply_time, reply_text), unsafe_allow_html=True)

            # Delete button for the reply (only if the reply belongs to the current user)
            if reply_user_id == current_user_id:
                if st.button("Delete Reply", key=f"del_reply_{reply_id}", type="secondary"):
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
                        resp = requests.delete(f"{api_url}/reviews/{reply_id}", headers=headers)
                        if resp.status_code == 200:
                            st.success("Reply deleted!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Failed to delete reply."))
                    except Exception as e:
                        st.error(f"Error deleting reply: {e}")

        # Action buttons row: Reply + Delete (if owner)
        action_cols = st.columns([1, 1, 3])

        # Reply button/form
        reply_key = f"reply_toggle_{review_id}"
        if reply_key not in st.session_state:
            st.session_state[reply_key] = False

        with action_cols[0]:
            if st.button("Reply", key=f"reply_btn_{review_id}", use_container_width=True):
                st.session_state[reply_key] = not st.session_state[reply_key]

        # Delete button for the review (only if the review belongs to the current user)
        with action_cols[1]:
            if review_user_id == current_user_id:
                if st.button("Delete", key=f"del_review_{review_id}", use_container_width=True, type="secondary"):
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
                        resp = requests.delete(f"{api_url}/reviews/{review_id}", headers=headers)
                        if resp.status_code == 200:
                            st.success("Review deleted!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Failed to delete review."))
                    except Exception as e:
                        st.error(f"Error deleting review: {e}")

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
    st.markdown(components.render_no_reviews_placeholder(), unsafe_allow_html=True)

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
                    st.success("Your review has been posted!")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", "Failed to post review."))
            except Exception as e:
                st.error(f"Error posting review.")
        else:
            st.warning("Please write your review before posting.")
