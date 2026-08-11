from fastapi import APIRouter, HTTPException, Form, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
import re
import pyodbc
from app.logger import logger
import app.config as config
import app.queries as queries
import app.passHash as passHash
import app.jwt_Security as jwt_Security

router = APIRouter(tags=["Authentication"])

@router.post("/register")
def Register_User(
    firstName: Annotated[str, Form()], lastName: Annotated[str, Form()],
    email: Annotated[str, Form()], password: Annotated[str, Form()], 
    conn: pyodbc.Connection = Depends(config.get_DB)
):
    cursor = conn.cursor()
    if not cursor:
        logger.error("Server Down")
        raise HTTPException(status_code=400, detail="Server Down")

    email_regex = r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        logger.error("Invalid Email Format. Must be in the Format user@domain.com")
        raise ValueError("Invalid Email Format. Must be in the Format user@domain.com")
    
    email = email.lower()
    try:
        cursor.execute(queries.verify_email, (email,))
        if cursor.fetchone():
            logger.info(f"User with the same email {email} already exists!")
            raise HTTPException(status_code=400, detail=f"User with Email {email} already exists!")
        
        hashed_pass = passHash.hash_Password(password)
        query = "INSERT INTO [User] (firstName, lastName, Email, PasswordHash) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (firstName, lastName, email, hashed_pass))
        conn.commit()
        logger.info(f"User with {email} has been registered sucessfully")
        return {"message": f"User with {email} has been registered sucessfully"}
    except HTTPException:
        raise

@router.post("/login")
def Login_User(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    conn: pyodbc.Connection = Depends(config.get_DB)
):
    cursor = conn.cursor()
    email = form_data.username.lower()
    password = form_data.password
    email_regex = r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$"

    if not re.match(email_regex, email):
        logger.error("Invalid Email Format.")
        raise HTTPException(status_code=400, detail="Invalid Email Format. Must be in the Format user@domain.com")

    try:
        cursor.execute(queries.verify_password, (email,))
        result = cursor.fetchone()
        if not result:
            logger.error("Invalid Email / Password")
            raise HTTPException(status_code=400, detail="Invalid Email / Password")
            
        hashed_pass = result[0]
        if not passHash.verify_Password(hashed_pass, password):
            raise HTTPException(status_code=400, detail="Invalid Email / Password")

        # Fetch UserID to return alongside the token
        cursor.execute(queries.verify_email, (email,))
        user_record = cursor.fetchone()
        user_id = user_record[0] if user_record else None

        access_token = jwt_Security.create_access_tokens(data={"sub": email})
        logger.info(f"User {email} has logged in & recieved a token!")
        return {"access_token": access_token, "token_type": "bearer", "user_id": user_id}
    except HTTPException:
        raise HTTPException(status_code=400, detail="Invalid Email / Password")