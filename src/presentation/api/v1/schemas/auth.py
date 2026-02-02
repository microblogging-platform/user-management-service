from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    surname: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    email: EmailStr
    phone_number: PhoneNumber

class SignupResponse(BaseModel):
    id: UUID
    name: str
    surname: str
    username: str
    email: EmailStr
    phone_number: str
    role: str