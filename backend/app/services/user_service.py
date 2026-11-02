import logging
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserRegister
from app.core.security import hash_password, verify_password

logger = logging.getLogger("uvicorn.error")

class UserService:
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch user by case-insensitive email address."""
        return db.query(User).filter(User.email == email.strip().lower()).first()

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        """Fetch user by unique primary key ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, user_in: UserRegister) -> User:
        """Register a new user, ensuring email uniqueness and secure password hashing."""
        clean_email = user_in.email.strip().lower()
        existing = UserService.get_by_email(db, clean_email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists. Please sign in instead."
            )

        hashed = hash_password(user_in.password)
        user = User(
            full_name=user_in.full_name.strip(),
            email=clean_email,
            hashed_password=hashed
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Registered new user account: {user.email} (ID: {user.id})")
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Verify user credentials against stored bcrypt hash."""
        clean_email = email.strip().lower()
        user = UserService.get_by_email(db, clean_email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

