from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
ph = PasswordHasher()

def hash_Password(UserPass: str)-> str:
    return ph.hash(UserPass)

def verify_Password(hashedPassword : str, plainPassword : str) -> str:
    try:
        return ph.verify(hashedPassword, plainPassword)
    except VerifyMismatchError: 
        return False
