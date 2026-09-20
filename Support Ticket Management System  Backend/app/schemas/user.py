from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.auth import validate_password

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = "Newpass@123"
    role_id: int

    _validate_password = field_validator("password")(validate_password)


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class UserRoleUpdate(BaseModel):
    role_id: int


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    role_id: int
    is_active: bool
    created_at: str
    updated_at: str