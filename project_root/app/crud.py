from sqlalchemy.orm import Session
from . import models, schemas, auth
import secrets

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, hashed_password=user.password, is_verified=False)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def set_verification_token(db: Session, user_id: int):
    token = secrets.token_urlsafe(32)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.verification_token = token
    db.commit()
    return token

def verify_user(db: Session, token: str):
    user = db.query(models.User).filter(models.User.verification_token == token).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.commit()
        return user
    return None

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, hashed_password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not auth.verify_password(password, user.hashed_password):
        return None
    return user

def create_contact(db: Session, contact: schemas.ContactCreate, user_id: int):
    db_contact = models.Contact(**contact.dict(), owner_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Contact).filter(models.Contact.owner_id == user_id).offset(skip).limit(limit).all()

def get_contact(db: Session, contact_id: int):
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()

def update_contact(db: Session, contact_id: int, contact: schemas.ContactUpdate):
    db_contact = get_contact(db, contact_id)
    for key, value in contact.dict(exclude_unset=True).items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int):
    db_contact = get_contact(db, contact_id)
    db.delete(db_contact)
    db.commit()
    return db_contact

def search_contacts(db: Session, query: str, user_id: int):
    return db.query(models.Contact).filter(models.Contact.owner_id == user_id).filter(
        (models.Contact.first_name.ilike(f'%{query}%')) |
        (models.Contact.last_name.ilike(f'%{query}%')) |
        (models.Contact.email.ilike(f'%{query}%'))
    ).all()

def get_upcoming_birthdays(db: Session, user_id: int):
    pass
