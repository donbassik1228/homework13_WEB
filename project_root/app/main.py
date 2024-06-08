from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import timedelta
from typing import List
from . import models, crud, schemas, auth, email, utils
from .database import SessionLocal, engine
from .config import settings
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Initialize the Limiter with a key function
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

# Add middleware for rate limiting
app.add_middleware(SlowAPIMiddleware)

# Create the database tables
models.Base.metadata.create_all(bind=engine)

# Set up OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    """
    Generate a new database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get the current user
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Retrieve the current authenticated user.

    Args:
        db (Session): SQLAlchemy session.
        token (str): OAuth2 token.

    Returns:
        schemas.User: The current authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# Endpoint to upload user avatar
@app.post("/users/avatar", response_model=schemas.User)
def upload_user_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    """
    Upload an avatar for the current user.

    Args:
        file (UploadFile): The avatar file to upload.
        db (Session): SQLAlchemy session.
        current_user (schemas.User): Current authenticated user.

    Returns:
        schemas.User: The user with updated avatar URL.
    """
    avatar_url = utils.upload_avatar(file.file)
    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user

# Endpoint to create a new contact
@app.post("/contacts/", response_model=schemas.Contact)
@limiter.limit("5/minute")  # ограничение 5 запросов в минуту
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    """
    Create a new contact for the current user.

    Args:
        contact (schemas.ContactCreate): Contact data.
        db (Session): SQLAlchemy session.
        current_user (schemas.User): Current authenticated user.

    Returns:
        schemas.Contact: The created contact.
    """
    return crud.create_contact(db=db, contact=contact, user_id=current_user.id)

# Endpoint to create a new user
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.

    Args:
        user (schemas.UserCreate): User data.
        db (Session): SQLAlchemy session.
        background_tasks (BackgroundTasks): Background tasks for asynchronous operations.

    Returns:
        schemas.User: The created user.
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    user.password = hashed_password
    new_user = crud.create_user(db=db, user=user)
    token = crud.set_verification_token(db, user_id=new_user.id)
    email.send_verification_email(background_tasks, new_user.email, token)
    return new_user

# Endpoint to verify user's email
@app.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify user's email address.

    Args:
        token (str): Verification token.
        db (Session): SQLAlchemy session.

    Returns:
        dict: Success message if email is verified.
    """
    user = crud.verify_user(db, token=token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")
    return {"message": "Email verified successfully"}

# Endpoint to generate an access token for user login
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Generate an access token for user login.

    Args:
        db (Session): SQLAlchemy session.
        form_data (OAuth2PasswordRequestForm): Form data containing username and password.

    Returns:
        dict: Access token and token type.
    """
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint to retrieve contacts for the current user
@app.get("/contacts/", response_model=List[schemas.Contact])
def read_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    """
    Retrieve contacts for the current user.

    Args:
        skip (int): Number of contacts to skip.
        limit (int): Maximum number of contacts to return.
        db (Session): SQLAlchemy session.
        current_user (schemas.User): Current authenticated user.

    Returns:
        List[schemas.Contact]: List of contacts.
    """
    return crud.get_contacts(db=db, user_id=current_user.id, skip=skip, limit=limit)

# Endpoint to retrieve a specific contact by ID
@app.get("/contacts/{contact_id}", response_model=schemas.Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    """
    Retrieve a specific contact by ID for the current user.

    Args:
        contact_id (int): ID of the contact to retrieve.
        db (Session): SQLAlchemy session.
        current_user (schemas.User): Current authenticated user.

    Returns:
        schemas.Contact: The retrieved contact.
    """
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return db_contact

# Endpoint to update a contact
@app.put("/contacts/{contact_id}", response_model=schemas.Contact)
def update_contact(contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    """
    Update a contact for the current user.

    Args:
        contact_id (int): ID of the contact to update.
        contact (schemas.ContactUpdate): The updated contact data.
        db (Session): SQLAlchemy session.
        current_user (schemas.User): Current authenticated user.

    Returns:
        schemas.Contact: The updated contact.
    """
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return crud.update_contact(db=db, contact_id=contact_id, contact=contact)

# Endpoint to delete a contact
@app.delete("/contacts/{contact_id}", response_model=schemas.Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    """
    Delete a contact for the current user.

    Args:
        contact_id (int): ID of the contact to delete.
        db (Session): SQLAlchemy session.
        current_user (schemas.User): Current authenticated user.

    Returns:
        schemas.Contact: The deleted contact.
    """
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return crud.delete_contact(db=db, contact_id=contact_id)

# Endpoint to search for contacts by query
@app.get("/contacts/search/", response_model=List[schemas.Contact])
def search_contacts(query: str, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    """
    Search for contacts by query for the current user.

    Args:
        query (str): The search query.
        db (Session): SQLAlchemy session.
        current_user (schemas.User): Current authenticated user.

    Returns:
        List[schemas.Contact]: List of contacts matching the query.
    """
    return crud.search_contacts(db=db, query=query, user_id=current_user.id)

# Endpoint to retrieve contacts with upcoming birthdays
@app.get("/contacts/upcoming-birthdays/", response_model=List[schemas.Contact])
def upcoming_birthdays(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    """
    Retrieve contacts with upcoming birthdays for the current user.

    Args:
        db (Session): SQLAlchemy session.
        current_user (schemas.User): Current authenticated user.

    Returns:
        List[schemas.Contact]: List of contacts with upcoming birthdays.
    """
    return crud.get_upcoming_birthdays(db=db, user_id=current_user.id)
