from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, description="Full legal or preferred name")
    email: EmailStr = Field(..., description="Unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="Secure password (minimum 8 characters)")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Account email address")
    password: str = Field(..., min_length=1, description="Account password")
    remember_me: Optional[bool] = Field(False, description="Extend session duration")

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    message: str = "Authentication successful"

