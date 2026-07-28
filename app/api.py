from fastapi import FastAPI, HTTPException, status, Form
from pydantic import BaseModel, field_validator
from contextlib import asynccontextmanager
from typing import Annotated
import re
import pyodbc
import app.config as config
import app.passHash as passHash

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        conn = pyodbc.connect(config.CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        with open("E:\BetaCode Work\Ticketing Management System\DB\Schema.sql", "r") as file:
            sql_script = file.read()
        conn.commit()
        conn.close()
        yield
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error Loading DB")
    finally:
        if 'conn' in locals():
            conn.commit()
    yield

app = FastAPI(lifespan=lifespan)

class UserRegistery(BaseModel):
    email:str
    password:str
    @field_validator("email")
    @classmethod
    def validateEmail(cls, value : str) -> str:
        email_regex = r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, value):
            raise ValueError("Invalid Email Format. Must be in the Format user@domain.com")
        return value.lower()
    
@app.post("/register")
def Register_User(firstName: Annotated[str, Form()], lastName: Annotated[str, Form()], email: Annotated[str, Form()], password: Annotated[str, Form()]):
    conn = pyodbc.connect(config.CONNECTION_STRING)
    cursor = conn.cursor()
    email_regex = r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        raise ValueError("Invalid Email Format. Must be in the Format user@domain.com")
    email =  email.lower()
    try:
        cursor.execute("SELECT UserID FROM [User] WHERE Email = ?", (email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"User with Email {email} already exists!")
        
        hashed_pass = passHash.hash_Password(password)
        query = "INSERT INTO [User] (firstName, lastName, Email, PasswordHash) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (firstName, lastName,email, hashed_pass))
        conn.commit()

        return {"message" : f"User with {email} has been registered sucessfully"}
    except HTTPException:
        raise
    finally:
        conn.close()

@app.post("/login")
def Login_User(email : Annotated[str, Form()], password : Annotated[str, Form()]):
    conn = pyodbc.connect(config.CONNECTION_STRING)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT PasswordHash FROM [User] WHERE Email = ?", (email,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=400, detail="Invalid Email / Password")
        hashed_pass = result[0]
        is_valid = passHash.verify_Password(hashed_pass, password)

        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid Email / Password")
        return {"message" : "Welcome To Ticketing System"}
    except HTTPException :
        raise HTTPException(status_code=400, detail="Invalid Email / Password")
    finally:
            conn.close()
