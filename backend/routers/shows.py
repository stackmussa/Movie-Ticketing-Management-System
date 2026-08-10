from fastapi import APIRouter, HTTPException, Depends
from enum import Enum
import pyodbc
from app.logger import logger
import app.config as config
import app.queries as queries

router = APIRouter(tags=["Shows & Availability"])

@router.get("/shows")
def Get_Shows(conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_shows_query)
        results = cursor.fetchall()
        if not results:
            logger.error("No Upcoming Shows!")
            raise HTTPException(status_code=400, detail="No Upcoming Shows!")
        column_names = [column[0] for column in cursor.description]
        return [dict(zip(column_names, row)) for row in results]
    except HTTPException:
        raise
    except pyodbc.Error as e:
        logger.error("DB Failure!")
        raise HTTPException(status_code=500, detail="Failed to fetch shows from database.") 

@router.get("/show/{title}")
def Get_Specific_Show(title: str, conn : pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_specific_show, (title, title, title))
        results = cursor.fetchall()
        if not results:
            logger.error("No Upcoming Shows!")
            raise HTTPException(status_code=400, detail="No Upcoming Shows!")
        column_names = [column[0] for column in cursor.description]
        return [dict(zip(column_names, row)) for row in results]
    except HTTPException:
        raise
    except pyodbc.Error:
        logger.error("No such record!")
        raise HTTPException(status_code=400, detail="No Such Record Found!") 

@router.get("/availability")
def Check_Availability(title: str, city: str, conn: pyodbc.Connection = Depends(config.get_DB)):
    cursor = conn.cursor()
    try:
        cursor.execute(queries.Select_City_Title_Query, (title, city))
        show_record = cursor.fetchone()
        
        if not show_record:
            raise HTTPException(status_code=400, detail="Show not found")
        
        show_id, base_price, hall_id, cinema_name = show_record
        availability = {}
        for cat in ["Platinum", "Gold", "Standard", "Recliner"]:
            cursor.execute(queries.seat_query, (hall_id, cat, show_id))
            availability[cat] = len(cursor.fetchall())
            
        return availability
    except pyodbc.Error as e:
        logger.error(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

# Helper Function for Dropdown for Cities selection
def get_cities_for_dropdown():
    try:
        conn = pyodbc.connect(config.CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute(queries.Cities_query)
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {"Default": "Default"}

        return {row[0]: row[0] for row in results}
        
    except pyodbc.Error as e:
        print(f"Failed to load categories for dropdown.")
        return {"Error": "Error"}
 
Cities = get_cities_for_dropdown()
DynamicCitiesDropdown = Enum("DynamicCitiesDropdown", Cities)

# Helper Function for Dropdown for Categories selection
def get_categories_for_dropdown():
    try:
        conn = pyodbc.connect(config.CONNECTION_STRING)
        cursor = conn.cursor()
                        
        cursor.execute(queries.Categories_query)
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {"Default": "Default"}
        
        return {row[0]: row[0] for row in results}
        
    except pyodbc.Error as e:
        print(f"Failed to load categories for dropdown.")
        return {"Error": "Error"}
    
Seat_Categories = get_categories_for_dropdown()
DynamicSeatDropdown = Enum("DynamicSeatDropdown", Seat_Categories)