import jwt
import pyodbc
from fastapi import FastAPI, HTTPException, status, Form, Depends, Response, BackgroundTasks
from typing import Annotated
from pydantic import BaseModel, field_validator
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
import app.config as config
from app.logger import logger


# --- JWT Security Setup ---
# This tells FastAPI where the frontend sends credentials to get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_tokens(data : dict):
    #Generates a secure token with an expiry time
    to_encode = data.copy()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expiry})
    logger.info("Successfully Generated Token!")
    return jwt.encode(to_encode, config.Secret_Key, algorithm=config.ALGORITHM)

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], conn: pyodbc.Connection = Depends(config.get_DB)):
    """Validates the token and fetches the current user from the database."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token using your secret key
        payload = jwt.decode(token, config.Secret_Key, algorithms=[config.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    cursor = conn.cursor()
    cursor.execute("SELECT UserID, Email FROM [User] WHERE Email = ?", (email,))
    user_record = cursor.fetchone()
    
    if user_record is None:
        raise credentials_exception
        
    # Return the secure user details to be used by the endpoint
    return {"user_id": user_record[0], "email": user_record[1]}
