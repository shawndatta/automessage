from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class AppStateResponse(BaseModel):
    onboarded: bool
    channel_status: str | None = None
    version: str
    authenticated: bool = False
    default_user_mode: bool = False
    has_users: bool = False


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    is_default: bool = False

    model_config = {"from_attributes": True}


class AuthMeResponse(BaseModel):
    authenticated: bool
    user: UserOut | None = None
    default_user_mode: bool = False


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthOkResponse(BaseModel):
    ok: bool = True
    user: UserOut
