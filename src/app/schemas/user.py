import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema


class UserBase(BaseModel):
    name: Annotated[str, Field(
        min_length=2, max_length=30, examples=["User Userson"])]
    username: Annotated[str, Field(
        min_length=2, max_length=50, examples=["userson"])]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]
    full_name: str | None = None


class User(TimestampSchema, UserBase, UUIDSchema, PersistentDeletion):
    profile_image_url: Annotated[str, Field(
        default="https://www.profileimageurl.com")]
    hashed_password: str
    is_superuser: bool = False
    tier_id: int | None = None
    is_verified: bool = False


class UserRead(BaseModel):
    id: uuid.UUID

    name: Annotated[str, Field(
        min_length=2, max_length=30, examples=["User Userson"])]
    username: Annotated[str, Field(
        min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"])]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]
    profile_image_url: str
    tier_id: int | None
    is_verified: bool = False


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(
        min_length=2, max_length=30, examples=["User Userson"])]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]
    full_name: str | None = None
    password: Annotated[str, Field(min_length=8, examples=["Str1ngst!"])]


class UserCreateInternal(BaseModel):
    name: str
    username: str
    email: EmailStr
    # full_name: str | None = None
    hashed_password: str
    is_verified: bool = False


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str | None, Field(min_length=2, max_length=50, examples=[
                                      "User Userberg"], default=None)]
    username: Annotated[
        str | None, Field(min_length=2, max_length=50,
                          pattern=r"^[a-z0-9]+$", examples=["userberg"], default=None)
    ]
    email: Annotated[EmailStr | None, Field(
        examples=["user.userberg@example.com"], default=None)]
    profile_image_url: Annotated[
        str | None,
        Field(
            pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", examples=["https://www.profileimageurl.com"], default=None
        ),
    ]


class UserUpdateInternal(UserUpdate):
    updated_at: datetime
    is_verified: bool = False


class UserTierUpdate(BaseModel):
    tier_id: int


class UserDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime


class UserRestoreDeleted(BaseModel):
    is_deleted: bool


class UserResponse(UserBase):
    id: uuid.UUID
    token: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    class Config:
        from_attributes = True


# Authentication Schemas
class OTPVerify(BaseModel):
    email: EmailStr
    otp: str
    model_config = ConfigDict(extra="forbid")

class EmailRequest(BaseModel):
    email: EmailStr
    model_config = ConfigDict(extra="forbid")

class ResetPassword(BaseModel):
    email: EmailStr
    otp: str
    new_password: Annotated[str, Field(min_length=8, examples=["NewStr1ng!"])]
    model_config = ConfigDict(extra="forbid")
    
class MessageResponse(BaseModel):
    detail: str

    