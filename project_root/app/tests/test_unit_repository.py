import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Contact
from crud import create_user, get_user_by_email, create_contact, get_contacts

class TestCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up the test database and session for all tests.
        """
        DATABASE_URL = "sqlite:///./test.db"
        cls.engine = create_engine(DATABASE_URL)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)
        cls.db = TestingSessionLocal()

    @classmethod
    def tearDownClass(cls):
        """
        Drop the test database after all tests.
        """
        Base.metadata.drop_all(bind=cls.engine)
        cls.db.close()

    def test_create_user(self):
        """
        Test creating a new user.
        """
        user_data = {"email": "test@example.com", "password": "password"}
        user = create_user(self.db, user_data)
        self.assertEqual(user.email, "test@example.com")

    def test_get_user_by_email(self):
        """
        Test retrieving a user by email.
        """
        user = get_user_by_email(self.db, email="test@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")

    def test_create_contact(self):
        """
        Test creating a new contact.
        """
        user = get_user_by_email(self.db, email="test@example.com")
        contact_data = {"name": "John Doe", "email": "john@example.com", "birthday": None}
        contact = create_contact(self.db, contact_data, user.id)
        self.assertEqual(contact.name, "John Doe")

    def test_get_contacts(self):
        """
        Test retrieving contacts for a user.
        """
        user = get_user_by_email(self.db, email="test@example.com")
        contacts = get_contacts(self.db, user.id)
        self.assertGreater(len(contacts), 0)
