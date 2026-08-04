import streamlit as st
import app.config as config


if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = ''

# Web App Pages

if st.session_state['logged_in']:
    pg = st.navigation([config.dashboard_page, config.booking_page, config.My_Orders, config.payment_page])
else:
    pg = st.navigation([config.login_page, config.register_page])

pg.run()