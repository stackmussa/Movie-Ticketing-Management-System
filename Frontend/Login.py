import streamlit as st
import requests 
import app.config as config
import app.logger as logger

api_url = config.API_URL
st.title("Login to Account")
st.write("Welcome Back! Please Enter your credentials to book tickets.")

with st.form("Login User"):
    log_email = st.text_input("Email")
    log_pass = st.text_input("Password", type="password")
    submit_log = st.form_submit_button("Login")

    if submit_log:
        if not log_email or not log_pass:
            st.warning("All the Required fields must be filled!")
        else:
            login_endpoint = f"{api_url}/login"
            
            response = requests.post(
                login_endpoint, 
                data={"username": log_email, "password": log_pass}
            )

            if response.status_code == 200:
                token_data = response.json()
                st.session_state['token'] = token_data.get("access_token")
                
                st.session_state['logged_in'] = True
                st.session_state['user_email'] = log_email
                st.session_state['flash_message'] = f"User with {log_email} has Logged In Successfully!"
                st.rerun()
            else:
                # Safely attempt to parse JSON, fallback to raw text if it crashes
                try:
                    error_detail = response.json().get("detail", "Login Failed")
                except ValueError:
                    error_detail = f"Server Error ({response.status_code}): {response.text}"
                
                st.error(error_detail)