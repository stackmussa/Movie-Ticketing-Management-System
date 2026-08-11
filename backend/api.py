from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Response
from app.logger import logger
import pyodbc
import os
import app.config as config

# Import your new routers
from backend.routers import auth, shows, bookings

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        
        # 1. Initialize DB schema
        with open("DB/Schema.sql", "r") as file:
            sql_script = file.read()
            # If your script has GO statements, you may need to split and execute them individually
            
        # 2. FAILSAFE: Clean up stuck pending orders older than 5 minutes on server startup
        # Delete the locked seats first
        cursor.execute("""
            DELETE FROM BookingSeat 
            WHERE BookingID IN (
                SELECT BookingID FROM Booking 
                WHERE BookingStatus = 'Pending' 
                AND DATEDIFF(minute, BookingDate, GETDATE()) > 5
            )
        """)
        # Update the parent booking statuses to Cancelled
        cursor.execute("""
            UPDATE Booking 
            SET BookingStatus = 'Cancelled', CancellationReason = 'Server Startup Failsafe'
            WHERE BookingStatus = 'Pending' 
            AND DATEDIFF(minute, BookingDate, GETDATE()) > 5
        """)
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Initialization Failed")
    yield

app = FastAPI(lifespan=lifespan)

# Attach the separated route files to the main app
app.include_router(auth.router)
app.include_router(shows.router)
app.include_router(bookings.router)

@app.get("/")
def read_root():
    return {"Message": "Welcome to Movie Ticket Purchase System."}

@app.get("/health")
def check_health(response: Response, conn: pyodbc.Connection = Depends(config.get_DB)):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return {"status": "healthy", "database": "connected"}
    except pyodbc.Error: 
        response.status_code = 503
        return {"status": "unhealthy", "database": "disconnected", "error": "Database connection failed."}
    
@app.get("/version")
def get_version():
    return {"api_version": "v1.4.2", "environment": os.getenv("ENV", "development")}

@app.get("/config")
def get_config():
    return config.SYSTEM_CONFIG