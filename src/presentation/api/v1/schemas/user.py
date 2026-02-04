from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber


class UpdateUserRequest(BaseModel):
    name: str | None = None
    surname: str | None = None
    username: str | None = None
    phone_number: PhoneNumber | None = None
    email: EmailStr | None = None