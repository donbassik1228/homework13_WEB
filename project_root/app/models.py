from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    """
    SQLAlchemy User model representing a user in the database.

    Attributes:
        id (int): Unique identifier for the user.
        email (str): Email address of the user.
        hashed_password (str): Hashed password of the user.
        is_active (bool): Indicates if the user is active.
        contacts (list[Contact]): List of contacts associated with the user.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    contacts = relationship("Contact", back_populates="owner")

class Contact(Base):
    """
    SQLAlchemy Contact model representing a contact in the database.

    Attributes:
        id (int): Unique identifier for the contact.
        name (str): Name of the contact.
        email (str): Email address of the contact.
        birthday (DateTime): Birthday of the contact.
        owner_id (int): ID of the user who owns this contact.
        owner (User): The user who owns this contact.
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    birthday = Column(DateTime, index=True, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="contacts")
