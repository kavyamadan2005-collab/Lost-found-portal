"""
Initialize database with test user
Run this script once to add a test user to the database
"""
import sys
import logging
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, engine
from app.models import Base, User
from app.auth.utils import hash_password

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("Initializing Database with Test User")
logger.info("=" * 80)

try:
    # Create all tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created/verified")
    
    # Create a database session
    db = SessionLocal()
    
    # Check if test user already exists
    existing_user = db.query(User).filter(User.email == "a@gmail.com").first()
    if existing_user:
        logger.warning(f"Test user already exists: {existing_user.email}")
        db.close()
        sys.exit(0)
    
    # Create test user
    logger.info("Creating test user...")
    test_user = User(
        name="Test User",
        email="a@gmail.com",
        password_hash=hash_password("123456"),
        role="user"
    )
    
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    logger.info("=" * 80)
    logger.info("✓ Test user created successfully!")
    logger.info("=" * 80)
    logger.info(f"Email: a@gmail.com")
    logger.info(f"Password: 123456")
    logger.info(f"User ID: {test_user.id}")
    logger.info("=" * 80)
    
    db.close()
    
except Exception as e:
    logger.error(f"✗ Failed to initialize database: {e}", exc_info=True)
    sys.exit(1)
