import streamlit as st
import requests 
import app.config as config
import app.logger as logger

api_url = config.API_URL
st.title("Login to Account")
st.title("Welcome Back! Please Enter your credentials to book tickets.")

with st.form("Login User"):
    log_email = st.text_input("Email")
    log_pass = st.text_input("Password", type="password")
    submit_log = st.form_submit_button("Login")

    if submit_log:
        if not log_email or not log_pass:
            st.warning("All the Required fields must be filled!")
        else:
            response = requests.post(f"{api_url}/login", data={"email" : log_email,
                                                                "password" : log_pass}
            )

            if response.status_code == 200:
                st.session_state['logged_in'] = True
                st.session_state['user_email'] = log_email
                st.success(f"User with {log_email} has Logged In Successfullt=y!")
                st.rerun()
            else:
                error_detail = response.json().get("detail", "Login Failed")
                st.error(error_detail)