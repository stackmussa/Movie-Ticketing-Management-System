import streamlit as st
from enum import Enum
from dotenv import load_dotenv
import os
import time
import pyodbc 


booking_hold_timer= 10

#DB connection String
CONNECTION_STRING = (
    r"Driver={ODBC Driver 17 for SQL Server};"
    r"Server=localhost\SQLEXPRESS;"
    r"Database=TicketSystem;" 
    r"Trusted_Connection=yes;"
)

SYSTEM_CONFIG = {
    "max_tickets_per_order": 10,
    "convenience_fee": 15,
    "currency": "PKR",
    "supported_payments": ["debit-card", "credit-card", "easypaisa", "jazzcash"]
}


# DB conncection helper function
def get_DB():
    conn = pyodbc.connect(CONNECTION_STRING)
    try:
        yield conn
    finally:
        conn.close()
def get_DB_connection():
    return CONNECTION_STRING

# Helper Class for Dropdown
class SeatCategoryEnum(str, Enum):
    standard = "Standard"
    gold = "Gold"
    platinum = "Platinum"
    recliner = "Recliner"

# Helper Class for Dropdown
class CityEnum(str, Enum):
    karachi = "Karachi"
    lahore = "Lahore"
    islamabad  ="Islamabad"
    rawalpindi = "Rawalpindi"
    faisalabad = "Faisalabad"
    hyderabad = "Hyderabad"
    multan = "Multan"
    peshawar = "Peshawar"
    sialkot = "Sialkot"
    gujranwala= "Gujranwala"
    quetta = "Quetta"

# Helper Class for Dropdown
class PaymentMethodEnum(str, Enum):
    cards = "Debit/Credit Card"
    easypaisa = "Easypaisa"
    jazzcash = "JazzCash"

load_dotenv()
#FASTAPI Url
API_URL = "http://127.0.0.1:8000"

cities_list = ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Hyderabad", "Multan", "Peshawar", "Sialkot", "Gujranwala", "Quetta"]
Seat_Categories = ["Platinum", "Gold", "Standard", "Recliners"]
PaymentMethods = ["Debit/Credit Card", "easypaisa", "jazzcash"]

#JWT Configuration
Secret_Key = os.getenv("JSON_SK")
if not Secret_Key:
    raise ValueError("Fatal Error in loading Secret Key!") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

#pages for frontend
register_page = st.Page("Frontend/Register.py", title="Register User")
login_page = st.Page("Frontend/Login.py", title="Login User")
dashboard_page = st.Page("Frontend/Dashboard.py", title="System Dashboard")
booking_page = st.Page("Frontend/Booking.py", title="Booking Ticket")
My_Orders = st.Page("Frontend/MyOrders.py", title="My Orders")
payment_page = st.Page("Frontend/Payment.py", title="Payment")

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

