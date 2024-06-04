# from pydantic import BaseModel, EmailStr
# from datetime import date
# from typing import Optional

# class ContactBase(BaseModel):
#     first_name: str
#     last_name: str
#     email: EmailStr
#     phone: Optional[str] = None
#     birthday: Optional[date] = None
#     additional_info: Optional[str] = None

# class ContactCreate(ContactBase):
#     pass

# class ContactUpdate(ContactBase):
#     pass

# class Contact(ContactBase):
#     id: int

#     class Config:
#         orm_mode = True


# schemas.py
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    birthday: Optional[str] = None
    additional_data: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(ContactBase):
    pass

class Contact(ContactBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

