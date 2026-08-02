import streamlit as st

#DB connection String
CONNECTION_STRING = (
    r"Driver={ODBC Driver 17 for SQL Server};"
    r"Server=localhost\SQLEXPRESS;"
    r"Database=TicketSystem;" 
    r"Trusted_Connection=yes;"
)
#FASTAPI Url
API_URL = "http://127.0.0.1:8000"

#pages for frontend
register_page = st.Page("E:\BetaCode Work\Ticketing Management System\Frontend\Register.py", title="Register User")
login_page = st.Page("E:\BetaCode Work\Ticketing Management System\Frontend\Login.py", title="Login User")
dashboard_page = st.Page("E:\BetaCode Work\Ticketing Management System\Frontend\Dashboard.py", title="System Dashboard")


# mulitplier for seating category wise.
def get_Category_Multiplier(Category:str ):
    mulitplier = 1.00
    if Category == "Gold":
        mulitplier = 1.025
    elif Category == "Platinum":
        mulitplier = 1.050
    elif Category == "Recliner":
        mulitplier = 1.100
    return mulitplier