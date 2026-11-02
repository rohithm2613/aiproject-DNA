from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User
from app.services.user_service import UserService

# Optional Bearer extractor so FastAPI OpenAPI documentation shows the Authorize lock
security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts and validates JWT access token from either:
    1. HttpOnly Cookie: `projectdna_access_token`
    2. Authorization header: `Bearer <token>`
    """
    token: Optional[str] = None

    # 1. Check HttpOnly cookie first (primary browser mechanism)
    cookie_token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if cookie_token:
        token = cookie_token

    # 2. Check Authorization Bearer header (for mobile, programmatic API access, or SPA header token)
    if not token and auth_header and auth_header.credentials:
        token = auth_header.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to access this resource.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this session no longer exists.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user

def get_optional_current_user(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional authentication resolver that does not throw 401 when unauthenticated."""
    try:
        return get_current_user(request=request, auth_header=auth_header, db=db)
    except HTTPException:
        return None

