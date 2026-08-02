import streamlit as st
import requests 
import app.config as config
import app.logger as logger 

api_url = config.API_URL

st.title("Create An Account")
st.write("Join Now to Start Purchasing Movie Tickets")


with st.form("Register User"):
    first_Name = st.text_input("First Name")
    last_Name = st.text_input("Last Name")
    reg_email = st.text_input("Email")
    reg_password = st.text_input("Password", type="password")
    submit_reg = st.form_submit_button("Register")

    if submit_reg:
        if not first_Name or not last_Name or not reg_email or not reg_password:
            st.warning("All the Required fields must be filled!")
        else:
            Payload={
                "firstName" : first_Name,
                "lastName" : last_Name,
                "email" : reg_email,
                "password" : reg_password
            }
        response = requests.post(f"{api_url}/register", data=Payload)

        if response.status_code == 200:
            st.success("Account Created Sucessfully!")
            st.switch_page("Frontend/Login.py")
        else:
            error_detail = response.json().get("detail", "Registration failed")
            st.error(error_detail)