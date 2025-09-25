from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import DuplicateValueException
from ...core.schemas import Token
from ...core.security import get_password_hash, create_access_token, create_refresh_token
from ...crud.crud_users import crud_users
from ...schemas.user import UserCreate, UserCreateInternal, UserRead

router = APIRouter(tags=["signup"])


@router.post("/signup", response_model=Token, status_code=201)
async def signup_user(
    user: UserCreate,
    response: Response,
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, str]:
    """
    Sign up a new user and automatically log them in.
    Returns access token and refresh token.
    """
    try:

        print(f"Starting signup for email: {user.email}")

        # Check if email already exists
        email_row = await crud_users.exists(db=db, email=user.email)
        if email_row:
            raise DuplicateValueException("Email is already registered")

        print("Email check passed")

        # Prepare internal user data
        user_internal_dict = user.model_dump()
        user_internal_dict["hashed_password"] = get_password_hash(
            password=user_internal_dict.pop("password")
        )

        # Remove full_name as it's not in the database model
        user_internal_dict.pop("full_name", None)

        print('-----------------> Here 0')
        print(user_internal_dict)
        print('-----------------> Here 1')

        # Generate username from email (remove @domain.com part)
        email_username = user.email.split('@')[0]
        user_internal_dict["username"] = email_username

        print(f"Generated username: {email_username}")

        # Create the user
        user_internal = UserCreateInternal(**user_internal_dict)
        print("UserCreateInternal created successfully")

        created_user: UserRead = await crud_users.create(db=db, object=user_internal)
        print("User created in database")

        # Generate tokens using email as subject
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        print('-----------------> Here 2')
        print(created_user)
        print('-----------------> Here 3')

        access_token = await create_access_token(
            data={"sub": created_user.email},
            expires_delta=access_token_expires
        )

        refresh_token = await create_refresh_token(
            data={"sub": created_user.email}
        )
        max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 604
        access_max_age = int(access_token_expires.total_seconds())  # Expiry for access_token cookie

        # Set secure=False for localhost development
        is_secure = settings.ENVIRONMENT.lower() != "local"

        # Set refresh token as HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_secure,
            samesite="Lax",
            max_age=max_age,
            path="/",
        )
        # NEW: Set access_token as a cookie (non-HTTP-only for frontend access)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=is_secure,
            samesite="Lax",
            max_age=access_max_age,
            path="/",
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "token": access_token,
            "email": created_user.email,
            "name": created_user.name,
            "username": created_user.username
        }
    except Exception as e:
        print(f"Signup error: {str(e)}")
        import traceback
        # traceback.print_exc()
        raise
