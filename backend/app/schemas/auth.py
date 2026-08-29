from pydantic import EmailStr, Field

from app.schemas.base import CamelModel


class RegisterRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=128)


class LoginRequest(CamelModel):
    email: EmailStr
    password: str


class UserOut(CamelModel):
    id: str
    email: str
    display_name: str | None
    role: str


class AuthResponse(CamelModel):
    access_token: str
    user: UserOut
