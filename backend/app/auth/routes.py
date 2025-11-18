import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserOut, Token
from ..config import settings
from ..deps import get_current_user
from .utils import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Register endpoint called - Email: {user_in.email}")
    try:
        existing = db.query(User).filter(User.email == user_in.email).first()
        if existing:
            logger.warning(f"Registration attempt with existing email: {user_in.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        logger.debug(f"Creating new user: {user_in.email}")
        user = User(
            name=user_in.name,
            email=user_in.email,
            password_hash=hash_password(user_in.password),
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✓ User registered successfully: {user.email} (ID: {user.id})")
        return user
    except Exception as e:
        logger.error(f"✗ Registration failed: {e}")
        db.rollback()
        raise


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Login endpoint called - Username/Email: {form_data.username}")
    try:
        logger.debug(f"Querying user with email: {form_data.username}")
        user = db.query(User).filter(User.email == form_data.username).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {form_data.username}")
            logger.debug("Raising 400 Bad Request - User not found")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
        
        logger.debug(f"User found: {user.email} (ID: {user.id}), verifying password...")
        password_valid = verify_password(form_data.password, user.password_hash)
        logger.debug(f"Password verification result: {password_valid}")
        
        if not password_valid:
            logger.warning(f"Login attempt with incorrect password for email: {form_data.username}")
            logger.debug("Raising 400 Bad Request - Password mismatch")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

        logger.debug(f"Password verified for user: {user.email}, generating token...")
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(data={"sub": user.id}, expires_delta=access_token_expires)
        logger.info(f"✓ Login successful for user: {user.email} (ID: {user.id})")
        return Token(access_token=access_token, token_type="bearer")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Unexpected error in login: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    logger.info(f"Get /me endpoint called - User ID: {current_user.id}")
    return current_user
