import streamlit as st


def render_interactive_seat_map(selected_category: str, booked_seats: list, max_limit: int):
    """Renders an interactive seat map using native Streamlit columns and checkboxes."""
    
    st.markdown("<div style='text-align: center; background-color: red; color: white; padding: 5px; font-weight: bold; letter-spacing: 5px; margin-bottom: 20px;'>SCREEN</div>", unsafe_allow_html=True)
    
    if 'selected_seats' not in st.session_state:
        st.session_state['selected_seats'] = []

    rows = ['A', 'B', 'C', 'D', 'E']
    
    for row in rows:
        cols = st.columns([0.5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1.2])
        cols[0].write(f"**{row}**")
        
        for seat_num in range(1, 11):
            seat_id = f"{row}{seat_num}"
            
            if row in ['A', 'B']:
                cat = "Platinum"
            elif row in ['C', 'D']:
                cat = "Gold"
            else:
                cat = "Standard"

            is_booked = seat_id in booked_seats
            wrong_category = selected_category != cat
            
            with cols[seat_num]:
                if is_booked:
                    # Renders a checked, disabled box with NO hover text
                    st.checkbox(
                        f"{seat_num}", 
                        key=f"booked_{seat_id}", 
                        disabled=True, 
                        value=True 
                    )
                elif wrong_category:
                    # Renders an unchecked, disabled box with NO hover text
                    st.checkbox(
                        f"{seat_num}", 
                        key=f"wrong_cat_{seat_id}", 
                        disabled=True, 
                        value=False 
                    )
                else:
                    # Renders an interactive, clickable seat WITH hover text
                    is_selected = seat_id in st.session_state['selected_seats']
                    
                    def toggle_seat(s_id=seat_id):
                        if s_id in st.session_state['selected_seats']:
                            st.session_state['selected_seats'].remove(s_id)
                        else:
                            if len(st.session_state['selected_seats']) < max_limit:
                                st.session_state['selected_seats'].append(s_id)
                            else:
                                chk_key = f"chk_{s_id}"
                                # Force the visual checkbox to uncheck if they hit the limit
                                st.session_state[chk_key] = False
                                st.toast(f"You can only select a maximum of {max_limit} tickets.", icon="⚠️")
                                
                    st.checkbox(
                        f"{seat_num}", 
                        key=f"chk_{seat_id}", 
                        value=is_selected, 
                        on_change=toggle_seat,
                        help="Click to select this seat."
                    )

def get_legend_html() -> str:
    """Returns the HTML for the seat map color legend."""
    return """
    <div style="display: flex; gap: 15px; justify-content: center; margin-top: 10px;">
        <div><span style="color: #8A2BE2;">■</span> Platinum (Rows A-B)</div>
        <div><span style="color: #FFD700;">■</span> Gold (Rows C-D)</div>
        <div><span style="color: #808080;">■</span> Standard (Row E)</div>
    </div>
    """
# ============================================================
# REVIEW COMPONENTS
# ============================================================

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


def render_rating_summary(avg_rating, total_reviews):
    """Returns the HTML block for the average rating summary banner."""
    rating_stars_html = render_star_html(avg_rating, size=28)
    return f"""
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
    """


def render_review_card(user_name, time_display, rating, text):
    """Returns the HTML for a single top-level review card."""
    stars = render_star_html(rating, size=16) if rating else ""
    return f"""
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
    """


def render_reply_card(reply_name, reply_time, reply_text):
    """Returns the HTML for a reply card nested under a review."""
    return f"""
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
    """


def render_no_reviews_placeholder():
    """Returns the HTML for the 'no reviews yet' empty state."""
    return """
    <div style="
        text-align: center;
        padding: 30px;
        background: #1e1e2f;
        border-radius: 12px;
        border: 1px dashed #444;
        margin-bottom: 16px;
    ">
        <div style="font-size: 40px; margin-bottom: 8px;"></div>
        <div style="color: #888; font-size: 15px;">No reviews yet. Be the first to share your thoughts!</div>
    </div>
    """


def render_movie_info_banner(movie_details):
    """Returns the HTML banner with movie show details for the Reviews page."""
    cinema = movie_details.get('CinemaName', 'Unknown')
    city = movie_details.get('City', '')
    date = movie_details.get('ShowDate', 'TBD')
    show_time = movie_details.get('ShowTime', 'TBD')
    return f"""
    <div style="
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        border-radius: 12px;
        padding: 16px 22px;
        border: 1px solid #3a3a5c;
        display: flex;
        gap: 24px;
        align-items: center;
        flex-wrap: wrap;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 18px;">Venue: </span>
            <span style="color: #ccc; font-size: 14px;">{cinema} ({city})</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 18px;">Date: </span>
            <span style="color: #ccc; font-size: 14px;">{date}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 18px;">Time: </span>
            <span style="color: #ccc; font-size: 14px;">{show_time}</span>
        </div>
    </div>
    """


#helper function for the 5 minutes timer functionality 
# components.py
def get_timer_html(remaining_seconds: int) -> str:
    return f"""
    <div style="font-family: sans-serif; text-align: center; padding: 12px; background-color: #2b2b2b; border-radius: 8px; border: 1px solid #FF5252;">
        <span style="color: #ffffff; font-size: 16px;">Time Remaining to Pay: </span>
        <strong style="color: #FF5252; font-size: 20px;" id="time">{remaining_seconds // 60}:{(remaining_seconds % 60):02d}</strong>
    </div>
    <script>
        if (window.paymentTimer) {{
            clearInterval(window.paymentTimer);
        }}
        var timeleft = {remaining_seconds};
        window.paymentTimer = setInterval(function(){{
            timeleft -= 1;
            if(timeleft <= 0){{
                clearInterval(window.paymentTimer);
                document.getElementById("time").innerHTML = "Expired!";
                document.getElementById("time").style.color = "#FF5252";
            }} else {{
                var minutes = Math.floor(timeleft / 60);
                var seconds = timeleft % 60;
                document.getElementById("time").innerHTML = minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
            }}
        }}, 1000);
    </script>
    """

def get_movie_card_css() -> str:
    """Returns the CSS for the movie card hover animation."""
    return """
    <style>
    .movie-card {
        position: relative;
        width: 100%;
        height: 380px; /* Controls the height of the poster/details area */
        border-radius: 8px;
        overflow: hidden;
        background: linear-gradient(135deg, #1e1e2f 0%, #16213e 100%);
        border: 1px solid #3a3a5c;
        margin-bottom: 15px;
    }
    .movie-card-content {
        padding: 20px;
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        color: #e0e0e0;
    }
    .movie-card-poster {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        z-index: 2;
        transition: opacity 0.5s ease-in-out; /* The smooth fade animation */
        background-color: #0f0c29;
    }
    .movie-card:hover .movie-card-poster {
        opacity: 0; /* Vanish on hover */
    }
    .movie-title {
        color: #FFD700;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """


def render_movie_card_html(title: str, date: str, show_time: str, cinema: str, address: str, price, poster_url: str) -> str:
    """Returns the HTML for the movie card with injected dynamic data."""
    return f"""
    <div class="movie-card">
        <div class="movie-card-content">
            <div class="movie-title">{title}</div>
            <div style="margin-bottom: 6px;"><strong>Date:</strong> {date}</div>
            <div style="margin-bottom: 6px;"><strong>Time:</strong> {show_time}</div>
            <div style="margin-bottom: 6px;"><strong>Cinema:</strong> {cinema}</div>
            <div style="margin-bottom: 6px; font-size: 13px; color: #aaa;">{address}</div>
            <div style="margin-top: auto; color: #43e97b; font-weight: bold;">Price: Rs.{price}</div>
        </div>
        <img class="movie-card-poster" src="{poster_url}" alt="{title} Poster">
    </div>
    """