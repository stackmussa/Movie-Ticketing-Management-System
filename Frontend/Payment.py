import streamlit as st
import requests
import app.config as config
import app.logger as logger

api_url = config.API_URL

if not st.session_state.get('Logged_in'):
    logger.error("Please Login First to Make Payment!")
    st.warning("Please Login First to Make Payment!")
    st.stop()

st.title("Payment Checkout")
st.write("Seamlessly Make Payments against your Order")