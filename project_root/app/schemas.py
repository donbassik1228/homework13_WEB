from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ContactBase(BaseModel):
    """
    Base schema for contact, containing common fields.

    Attributes:
        name (str): Name of the contact.
        email (str): Email address of the contact.
        birthday (Optional[datetime]): Birthday of the contact.
    """
    name: str
    email: str
    birthday: Optional[datetime] = None

class ContactCreate(ContactBase):
    """
    Schema for creating a new contact.

    Inherits from:
        ContactBase
    """
    pass

class ContactUpdate(ContactBase):
    """
    Schema for updating an existing contact.

    Inherits from:
        ContactBase
    """
    pass

class Contact(ContactBase):
    """
    Schema representing a contact, with ID and owner_id.

    Attributes:
        id (int): Unique identifier for the contact.
        owner_id (int): ID of the user who owns this contact.
    """
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    """
    Base schema for user, containing common fields.

    Attributes:
        email (str): Email address of the user.
    """
    email: str

class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Attributes:
        password (str): Password for the user.
    """
    password: str

class User(UserBase):
    """
    Schema representing a user, with ID and list of contacts.

    Attributes:
        id (int): Unique identifier for the user.
        contacts (List[Contact]): List of contacts associated with the user.
    """
    id: int
    contacts: List[Contact] = []

    class Config:
        orm_mode = True

class Token(BaseModel):
    """
    Schema for JWT token.

    Attributes:
        access_token (str): Access token string.
        token_type (str): Type of the token.
    """
    access_token: str
    token_type: str
