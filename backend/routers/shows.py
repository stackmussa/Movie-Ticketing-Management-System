from fastapi import APIRouter, HTTPException, Depends
from enum import Enum
import pyodbc
from app.logger import logger
import app.config as config
import app.queries as queries
import requests as http_requests
import os

router = APIRouter(tags=["Shows & Availability"])

# In-memory cache for OMDb lookups to avoid redundant API calls
_omdb_cache = {}
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")


@router.get("/genres")
def get_genres(conn: pyodbc.Connection = Depends(config.get_DB)):
    """Fetch distinct genres from the Movie table for filter dropdowns."""
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_distinct_genres)
        results = cursor.fetchall()
        if not results:
            return []
        # Split compound genres like 'Action/Adventure' into individual tags
        raw_genres = [row[0] for row in results if row[0]]
        unique_genres = set()
        for genre_str in raw_genres:
            for part in genre_str.replace("/", ",").split(","):
                stripped = part.strip()
                if stripped:
                    unique_genres.add(stripped)
        return sorted(unique_genres)
    except pyodbc.Error as e:
        logger.error(f"DB Error fetching genres: {e}")
        raise HTTPException(status_code=500, detail="Database Error fetching genres.")


@router.get("/show-date-range")
def get_show_date_range(conn: pyodbc.Connection = Depends(config.get_DB)):
    """Fetch the min and max dates of upcoming shows for calendar filtering."""
    cursor = conn.cursor()
    try:
        cursor.execute(queries.get_show_date_range)
        record = cursor.fetchone()
        if not record or not record[0]:
            return {"min_date": None, "max_date": None}
        return {
            "min_date": str(record[0]),
            "max_date": str(record[1])
        }
    except pyodbc.Error as e:
        logger.error(f"DB Error fetching date range: {e}")
        raise HTTPException(status_code=500, detail="Database Error fetching date range.")


@router.get("/omdb/{movie_title}")
def get_omdb_ratings(movie_title: str):
    """Proxy endpoint to fetch ratings from OMDb API (IMDb, Rotten Tomatoes).
    Results are cached in-memory to minimize external API calls."""
    if not OMDB_API_KEY:
        raise HTTPException(status_code=503, detail="OMDb API key not configured.")

    # Check cache first
    cache_key = movie_title.strip().lower()
    if cache_key in _omdb_cache:
        return _omdb_cache[cache_key]

    try:
        resp = http_requests.get(
            "http://www.omdbapi.com/",
            params={"apikey": OMDB_API_KEY, "t": movie_title},
            timeout=5
        )
        data = resp.json()

        if data.get("Response") == "False":
            result = {"found": False, "title": movie_title}
            _omdb_cache[cache_key] = result
            return result

        # Extract the ratings we care about
        ratings_list = data.get("Ratings", [])
        imdb_rating = data.get("imdbRating", "N/A")
        rotten_tomatoes = "N/A"
        for r in ratings_list:
            if r.get("Source") == "Rotten Tomatoes":
                rotten_tomatoes = r.get("Value", "N/A")

        result = {
            "found": True,
            "title": data.get("Title", movie_title),
            "imdb_rating": imdb_rating,
            "rotten_tomatoes": rotten_tomatoes,
            "metascore": data.get("Metascore", "N/A"),
            "imdb_id": data.get("imdbID", ""),
            "poster": data.get("Poster", ""),
            "year": data.get("Year", ""),
            "rated": data.get("Rated", ""),
        }
        _omdb_cache[cache_key] = result
        return result

    except http_requests.RequestException as e:
        logger.error(f"OMDb API request failed for '{movie_title}': {e}")
        return {"found": False, "title": movie_title}

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