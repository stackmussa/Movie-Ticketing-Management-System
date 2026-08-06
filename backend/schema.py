from pydantic import BaseModel
import app.config as config

class UserRegistery(BaseModel):
    email:str
    password:str

class PaymentRequest(BaseModel):
    booking_id: int
    amount: float
    payment_method: config.PaymentMethodEnum
