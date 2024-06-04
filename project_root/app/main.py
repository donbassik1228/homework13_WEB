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

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.add_middleware(SlowAPIMiddleware)

models.Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
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

@app.post("/users/", response_model=schemas.User)
def create_user(background_tasks: BackgroundTasks, user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    user.password = hashed_password
    new_user = crud.create_user(db=db, user=user)
    token = crud.set_verification_token(db, user_id=new_user.id)
    email.send_verification_email(background_tasks, new_user.email, token)
    return new_user

@app.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = crud.verify_user(db, token=token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")
    return {"message": "Email verified successfully"}

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
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

@app.post("/users/avatar", response_model=schemas.User)
def upload_user_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    avatar_url = utils.upload_avatar(file.file)
    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user

@app.post("/contacts/", response_model=schemas.Contact)
@limiter.limit("5/minute")  # обмеження 5 запитів на хвилину
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.create_contact(db=db, contact=contact, user_id=current_user.id)

@app.get("/contacts/", response_model=List[schemas.Contact])
def read_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_contacts(db=db, user_id=current_user.id, skip=skip, limit=limit)

@app.get("/contacts/{contact_id}", response_model=schemas.Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return db_contact

@app.put("/contacts/{contact_id}", response_model=schemas.Contact)
def update_contact(contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return crud.update_contact(db=db, contact_id=contact_id, contact=contact)

@app.delete("/contacts/{contact_id}", response_model=schemas.Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return crud.delete_contact(db=db, contact_id=contact_id)

@app.get("/contacts/search/", response_model=List[schemas.Contact])
def search_contacts(query: str, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.search_contacts(db=db, query=query, user_id=current_user.id)

@app.get("/contacts/upcoming-birthdays/", response_model=List[schemas.Contact])
def upcoming_birthdays(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_upcoming_birthdays(db=db, user_id=current_user.id)
