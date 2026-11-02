from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse, AuthResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])

def set_auth_cookie(response: Response, token: str, max_age_seconds: int):
    """Sets a secure, HttpOnly session cookie on the outgoing response."""
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=max_age_seconds,
        expires=max_age_seconds,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/"
    )

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserRegister,
    response: Response,
    db: Session = Depends(get_db)
):
    """Register a new user account, return auth payload and set HttpOnly access cookie."""
    user = UserService.create_user(db=db, user_in=user_in)
    
    # Generate access token
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "name": user.full_name}
    )
    
    # Set HttpOnly cookie
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    set_auth_cookie(response, access_token, max_age)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer",
        message="Registration successful. Welcome to AI ProjectDNA!"
    )

@router.post("/login", response_model=AuthResponse)
def login(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """Authenticate user with email and password, returning JWT token and setting session cookie."""
    user = UserService.authenticate_user(
        db=db,
        email=credentials.email,
        password=credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Session duration: extend to 7 days if remember_me is True
    if credentials.remember_me:
        delta = timedelta(days=7)
        max_age = 7 * 24 * 3600
    else:
        delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "name": user.full_name},
        expires_delta=delta
    )

    set_auth_cookie(response, access_token, max_age)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer",
        message="Authentication successful."
    )

@router.post("/logout")
def logout(response: Response):
    """Log out current user by terminating and clearing the HttpOnly session cookie."""
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/"
    )
    return {"message": "Logged out successfully."}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Fetch authenticated user profile details."""
    return UserResponse.model_validate(current_user)

