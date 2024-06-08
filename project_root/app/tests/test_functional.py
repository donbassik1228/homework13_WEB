import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    """
    Fixture to set up and tear down the test database.
    """
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_user(db):
    """
    Functional test for creating a user.
    """
    response = client.post("/users/", json={"email": "testuser@example.com", "password": "password"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"

def test_login(db):
    """
    Functional test for logging in and receiving a token.
    """
    response = client.post("/token", data={"username": "testuser@example.com", "password": "password"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_create_contact(db):
    """
    Functional test for creating a contact.
    """
    response = client.post("/token", data={"username": "testuser@example.com", "password": "password"})
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/contacts/", json={"name": "Jane Doe", "email": "jane@example.com"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"

def test_get_contacts(db):
    """
    Functional test for retrieving contacts.
    """
    response = client.post("/token", data={"username": "testuser@example.com", "password": "password"})
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/contacts/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
