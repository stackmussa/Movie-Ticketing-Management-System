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