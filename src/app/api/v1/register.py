# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import Annotated
# from datetime import timedelta
# from pydantic import BaseModel, Field, EmailStr

# from ...core.db.database import async_get_db
# from ...schemas.user import UserResponse, UserCreateInternal
# from ...models.user import User
# from ...core.security import get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
# from ...crud.crud_users import crud_users

# router = APIRouter()

# class RegisterUser(BaseModel):
#     email: EmailStr
#     password: str
#     full_name: str

# @router.post(
#     "/register",
#     response_model=UserResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Register a new user",
#     description="Create a new user with the provided information"
# )
# async def register_user(
#     user: RegisterUser,
#     db: Annotated[AsyncSession, Depends(async_get_db)]
# ) -> dict:
#     print("register_user")
#     existing_user = await crud_users.get_by_email(db, user.email)
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered"
#         )
    
#     hashed_password = get_password_hash(user.password)

#     print(user)

#     user_create = UserCreateInternal(
#         email=user.email,
#         hashed_password=hashed_password,
#         name=user.full_name,
#         username=user.full_name
#     )
#     print("created user")
#     print(user_create)
#     user_db = await crud_users.create(db, user_create)
    
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = await create_access_token(
#         data={"sub": user.email},
#         expires_delta=access_token_expires
#     )
    
#     username = user.email
#     if len(username) > 20:
#         username = username[:20]
#     print({
#         "email": user.email,
#         "profile_id": user_db.id,
#         "token": access_token,
#         "name": user.full_name,
#         "username": username,
#         "id": user_db.id
#     })
#     return {
#         "email": user.email,
#         "profile_id": user_db.id,
#         "token": access_token,
#         "name": user.full_name,
#         "username": username,
#         "id": user_db.id
#     }


# UPDATED
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import timedelta
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from ...core.config import settings
from ...core.db.database import async_get_db
from ...schemas.user import UserResponse, UserCreateInternal
from ...core.security import get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from ...crud.crud_users import crud_users
from ...services.auth_utils import generate_otp, store_otp, send_otp_email
import uuid
import re
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class RegisterUser(BaseModel):
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]
    password: Annotated[str, Field(min_length=8, examples=["Str1ngst!"])]
    full_name: Annotated[str, Field(min_length=2, max_length=30, examples=["User Userson"])]
    model_config = ConfigDict(extra="forbid")

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user with the provided information and send OTP for email verification"
)
async def register_user(
    user: RegisterUser,
    response: Response,
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> UserResponse:
    logger.info(f"Register attempt for email: {user.email}")
    
    # Check for existing email or username
    if await crud_users.exists(db=db, email=user.email):
        logger.warning(f"Email already registered: {user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    username = re.sub(r'[^a-z0-9]', '', user.full_name.lower())[:20]
    if await crud_users.exists(db=db, username=username):
        username = f"{username}{uuid.uuid4().hex[:4]}"[:20]
    
    # Create internal user
    user_create = UserCreateInternal(
        name=user.full_name,
        username=username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        is_verified=False
    )
    user_db = await crud_users.create(db=db, object=user_create)
    
    # Send OTP
    otp = await generate_otp()
    await store_otp(f"verify_otp:{user.email}", otp)
    try:
        if not await send_otp_email(user.email, otp):
            await crud_users.delete(db=db, id=user_db.id)
            logger.error(f"Failed to send OTP to {user.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP email")
        logger.info(f"Generated OTP {otp} for {user.email}")
    except Exception as e:
        await crud_users.delete(db=db, id=user_db.id)
        logger.error(f"OTP email error for {user.email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP email")
    
    # Generate JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(data={"sub": user_db.username}, expires_delta=access_token_expires)
    
    logger.info(f"User registered successfully: {user.email}")

    is_secure = settings.ENVIRONMENT.lower() != "local"
    access_max_age = int(access_token_expires.total_seconds())  # Expiry for access_token cookie
    
    logger.info(f"User registered successfully: {user.email}")
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="Lax",
        max_age=access_max_age,
        path="/",
    )

    return UserResponse(
        id=user_db.id,
        name=user_db.name,
        username=user_db.username,
        email=user_db.email,
        token=access_token,
        is_active=user_db.is_active,
        is_superuser=user_db.is_superuser,
        is_verified=user_db.is_verified
    )
