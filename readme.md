# Movie Ticketing Management System

## Introduction
The Movie Ticketing Management System is a comprehensive web application designed to demonstrate the power and efficiency of FastAPI. It features a high-performance backend serving a Streamlit frontend, providing a seamless platform for users to register, discover upcoming movie shows, check seat availability, book tickets, and securely manage their orders. This project emphasizes best practices in FastAPI development, including efficient routing, robust dependency injection, and secure authentication to show the betterment of FastAPI.

## Features
- High-Performance API: Built with FastAPI for rapid development and execution.
- Secure User Authentication: Implements JWT access tokens and Argon2 password hashing for robust security.
- Movie Discovery & Booking: Browse shows by city and title, check dynamic seat availability for various categories, and book tickets.
- Payment Processing: Simulated checkout for multiple payment methods with validation.
- Order Management: View booking history, check pending orders, and cancel active bookings securely.
- Database Integration: Uses pyodbc to connect with a SQL Server database, complete with automated schema initialization.

## How to Run

1. Database Setup:
   Ensure SQL Server is running locally on 'localhost\SQLEXPRESS' with a database named 'TicketSystem'. The application will automatically execute the schema on startup.

2. Environment Configuration:
   Create a '.env' file in the root directory and define your secret key:
   JSON_SK=your_secure_secret_key

3. Install Dependencies:
   Install all necessary packages via pip:
   pip install -r requirements.txt

4. Launch the Backend:
   Start the FastAPI server using Uvicorn:
   uvicorn app.api:app --reload

5. Launch the Frontend:
   In a separate terminal, start the Streamlit application:
   streamlit run main.py
