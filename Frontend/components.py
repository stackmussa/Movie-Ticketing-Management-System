import streamlit as st


def get_seat_map_html(selected_category: str) -> str:
    """Generates the HTML for the 5x10 visual seat map."""
    
    seat_map_html = """
    <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; text-align: center; font-family: monospace;">
        <div style="background-color: red; color: white; padding: 5px; margin-bottom: 20px; font-weight: bold; letter-spacing: 5px;">SCREEN</div>
        <div style="display: grid; gap: 5px; justify-content: center;">
    """

    rows = ['A', 'B', 'C', 'D', 'E']
    for row in rows:
        seat_map_html += f'<div style="display: flex; gap: 5px; align-items: center; justify-content: center;">'
        seat_map_html += f'<span style="color: white; width: 20px; text-align: left;">{row}</span>'

        for seat_num in range(1, 11):
            if row in ['A', 'B']:
                color, cat = "#8A2BE2", "Platinum"
            elif row in ['C', 'D']:
                color, cat = "#FFD700", "Gold"
            else:
                color, cat = "#808080", "Standard"

            opacity = "1.0" if selected_category == cat else "0.3"
            
            # HTML kept on one line to prevent Streamlit Markdown interference
            seat_map_html += f'<div style="width: 30px; height: 30px; background-color: {color}; opacity: {opacity}; border-radius: 5px; display: flex; align-items: center; justify-content: center; color: black; font-size: 12px; font-weight: bold;">{seat_num}</div>'
            
        seat_map_html += f'<span style="color: white; width: 20px; text-align: right;">{row}</span></div>'

    seat_map_html += "</div></div>"
    return seat_map_html


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
def get_timer_html(remaining_seconds: int) -> str:
    """Generates the HTML and JS for the live countdown timer."""
    return f"""
    <div style="font-family: sans-serif; text-align: center; padding: 12px; background-color: #2b2b2b; border-radius: 8px; border: 1px solid #FF5252;">
        <span style="color: #ffffff; font-size: 16px;">Time Remaining to Pay: </span>
        <strong style="color: #FF5252; font-size: 20px;" id="time">{remaining_seconds // 60}:{(remaining_seconds % 60):02d}</strong>
    </div>
    <script>
        var timeleft = {remaining_seconds};
        var timer = setInterval(function(){{
            timeleft -= 1;
            if(timeleft <= 0){{
                clearInterval(timer);
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