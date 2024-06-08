from sqlalchemy.orm import Session
from . import models, schemas

def get_user_by_email(db: Session, email: str):
    """
    Retrieve a user by their email address.

    Args:
        db (Session): SQLAlchemy session.
        email (str): Email address to search for.

    Returns:
        models.User: User object if found, else None.
    """
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """
    Create a new user in the database.

    Args:
        db (Session): SQLAlchemy session.
        user (schemas.UserCreate): User data to create.

    Returns:
        models.User: The created user.
    """
    db_user = models.User(
        email=user.email,
        hashed_password=user.password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    """
    Retrieve contacts for a specific user.

    Args:
        db (Session): SQLAlchemy session.
        user_id (int): ID of the user.
        skip (int): Number of contacts to skip.
        limit (int): Maximum number of contacts to return.

    Returns:
        list[models.Contact]: List of contacts.
    """
    return db.query(models.Contact).filter(models.Contact.owner_id == user_id).offset(skip).limit(limit).all()

def create_contact(db: Session, contact: schemas.ContactCreate, user_id: int):
    """
    Create a new contact for a user.

    Args:
        db (Session): SQLAlchemy session.
        contact (schemas.ContactCreate): Contact data to create.
        user_id (int): ID of the user creating the contact.

    Returns:
        models.Contact: The created contact.
    """
    db_contact = models.Contact(
        **contact.dict(),
        owner_id=user_id,
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contact(db: Session, contact_id: int):
    """
    Retrieve a specific contact by ID.

    Args:
        db (Session): SQLAlchemy session.
        contact_id (int): ID of the contact to retrieve.

    Returns:
        models.Contact: The retrieved contact.
    """
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()

def update_contact(db: Session, contact_id: int, contact: schemas.ContactUpdate):
    """
    Update a contact for a user.

    Args:
        db (Session): SQLAlchemy session.
        contact_id (int): ID of the contact to update.
        contact (schemas.ContactUpdate): The updated contact data.

    Returns:
        models.Contact: The updated contact.
    """
    db_contact = get_contact(db, contact_id)
    if db_contact:
        for key, value in contact.dict().items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int):
    """
    Delete a contact for a user.

    Args:
        db (Session): SQLAlchemy session.
        contact_id (int): ID of the contact to delete.

    Returns:
        models.Contact: The deleted contact.
    """
    db_contact = get_contact(db, contact_id)
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def search_contacts(db: Session, query: str, user_id: int):
    """
    Search contacts for a specific user.

    Args:
        db (Session): SQLAlchemy session.
        query (str): Search query.
        user_id (int): ID of the user.

    Returns:
        list[models.Contact]: List of contacts matching the search query.
    """
    return db.query(models.Contact).filter(models.Contact.owner_id == user_id, models.Contact.name.contains(query)).all()

def get_upcoming_birthdays(db: Session, user_id: int):
    """
    Retrieve contacts with upcoming birthdays for a specific user.

    Args:
        db (Session): SQLAlchemy session.
        user_id (int): ID of the user.

    Returns:
        list[models.Contact]: List of contacts with upcoming birthdays.
    """
    return db.query(models.Contact).filter(models.Contact.owner_id == user_id).order_by(models.Contact.birthday).all()
