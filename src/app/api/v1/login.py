# from datetime import timedelta
# from typing import Annotated

# from fastapi import APIRouter, Depends, Request, Response
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.ext.asyncio import AsyncSession

# from ...core.config import settings
# from ...core.db.database import async_get_db
# from ...core.exceptions.http_exceptions import UnauthorizedException
# from ...core.schemas import Token , LoginRequest
# from ...core.security import (
#     ACCESS_TOKEN_EXPIRE_MINUTES,
#     authenticate_user,
#     create_access_token,
#     create_refresh_token,
#     verify_token,
#     TokenType,
# )

# from dotenv import load_dotenv
# from jose import jwt

# router = APIRouter(tags=["login"])


# @router.post("/login", response_model=Token)
# async def login_for_access_token(
#     login_data: LoginRequest,
#     response: Response,
#     db: Annotated[AsyncSession, Depends(async_get_db)],
# ) -> dict[str, str]:
#     user = await authenticate_user(username_or_email=login_data.username, password=login_data.password, db=db)
#     if not user:
#         raise UnauthorizedException("Wrong username, email or password.")

#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = await create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)

#     refresh_token = await create_refresh_token(data={"sub": user["username"]})
#     max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

#     # Set secure=False for localhost development
#     is_secure = settings.ENVIRONMENT.lower() != "local"

#     print(is_secure)
    
#     response.set_cookie(
#         key="refresh_token", 
#         value=refresh_token, 
#         httponly=True, 
#         secure=is_secure    ,  # Only use secure=True in production
#         samesite="Lax", 
#         max_age=max_age,
#         path="/",
#     )

#     # Truncate username to fit within 20 characters if needed
#     username = user["username"]
#     if len(username) > 20:
#         username = username[:20]
    
#     return {
#         "access_token": access_token, 
#         "refresh_token": refresh_token,
#         "token_type": "bearer",
#         "token": access_token,
#         "email": user["email"],
#         "name": user["name"],
#         "username": username
#     }


# @router.post("/refresh")
# async def refresh_access_token(request: Request, db: AsyncSession = Depends(async_get_db)) -> dict[str, str]:
#     refresh_token = request.cookies.get("refresh_token")
#     if not refresh_token:
#         raise UnauthorizedException("Refresh token missing.")
#     user_data = await verify_token(
#         token=refresh_token,
#         expected_token_type=TokenType.REFRESH,
#         db=db
#     )
    
#     if not user_data:
#         raise UnauthorizedException("Invalid refresh token.")

#     new_access_token = await create_access_token(data={"sub": user_data.username_or_email})
#     return {"access_token": new_access_token, "token_type": "bearer"}


# Updated 
# from datetime import timedelta
# from typing import Annotated
# from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.ext.asyncio import AsyncSession
# from ...core.config import settings
# from ...core.db.database import async_get_db
# from ...core.utils.cache import get_redis_client
# from ...core.exceptions.http_exceptions import UnauthorizedException
# from ...core.schemas import Token, LoginRequest
# from ...core.security import (
#     ACCESS_TOKEN_EXPIRE_MINUTES,
#     authenticate_user,
#     create_access_token,
#     create_refresh_token,
#     verify_token,
#     TokenType,
#     get_password_hash,
# )
# from ...schemas.user import OTPVerify, EmailRequest, ResetPassword
# from ...crud.crud_users import crud_users
# from ...services.auth_utils import generate_otp, store_otp, send_otp_email, verify_and_delete_otp
# from redis.asyncio import Redis
# from datetime import datetime, UTC
# import logging

# logger = logging.getLogger(__name__)

# router = APIRouter(tags=["login"])

# async def rate_limit_otp(data: EmailRequest, redis_client: Redis = Depends(get_redis_client)):
#     key = f"rate_limit:otp:{data.email}"
#     count = await redis_client.get(key)
#     if count and int(count) >= 5:
#         logger.warning(f"Rate limit exceeded for OTP request: {data.email}")
#         raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many OTP requests. Try again later.")
#     await redis_client.incr(key)
#     await redis_client.expire(key, 3600)

# @router.post("/login", response_model=Token)
# async def login_for_access_token(
#     login_data: LoginRequest,
#     response: Response,
#     db: Annotated[AsyncSession, Depends(async_get_db)],
# ) -> dict[str, str]:
#     user = await authenticate_user(username_or_email=login_data.username, password=login_data.password, db=db)
#     if not user:
#         logger.warning(f"Failed login attempt for {login_data.username}")
#         raise UnauthorizedException("Wrong username, email or password.")
    
#     if not user["is_verified"]:
#         logger.warning(f"Unverified user attempted login: {login_data.username}")
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Email not verified. Please verify your email."
#         )

#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = await create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)
#     refresh_token = await create_refresh_token(data={"sub": user["username"]})
#     max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

#     is_secure = settings.ENVIRONMENT.lower() != "local"
#     response.set_cookie(
#         key="refresh_token",
#         value=refresh_token,
#         httponly=True,
#         secure=is_secure,
#         samesite="Lax",
#         max_age=max_age,
#         path="/",
#     )
    
#     username = user["username"][:20]
#     logger.info(f"User logged in: {user['email']}")
#     return {
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "token_type": "bearer",
#         "token": access_token,
#         "email": user["email"],
#         "name": user["name"],
#         "username": username
#     }

# @router.post("/refresh")
# async def refresh_access_token(request: Request, db: AsyncSession = Depends(async_get_db)) -> dict[str, str]:
#     refresh_token = request.cookies.get("refresh_token")
#     if not refresh_token:
#         raise UnauthorizedException("Refresh token missing.")
#     user_data = await verify_token(
#         token=refresh_token,
#         expected_token_type=TokenType.REFRESH,
#         db=db
#     )
    
#     if not user_data:
#         raise UnauthorizedException("Invalid refresh token.")

#     new_access_token = await create_access_token(data={"sub": user_data.username_or_email})
#     return {"access_token": new_access_token, "token_type": "bearer"}

# @router.post("/verify-otp", response_model=dict)
# async def verify_otp(data: OTPVerify, db: AsyncSession = Depends(async_get_db)):
#     if not await verify_and_delete_otp(f"verify_otp:{data.email}", data.otp):
#         logger.warning(f"Invalid OTP attempt for {data.email}")
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    
#     user = await crud_users.get_by_email(db, data.email)
#     if not user:
#         logger.warning(f"User not found for OTP verification: {data.email}")
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
#     if user.is_verified:
#         logger.info(f"Email already verified: {data.email}")
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")
    
#     await crud_users.update(db=db, object={"is_verified": True, "updated_at": datetime.now(UTC)}, id=user.id)
#     logger.info(f"User verified successfully: {data.email}")
#     return {"detail": "Email verified successfully"}

# @router.post("/resend-otp", response_model=dict, dependencies=[Depends(rate_limit_otp)])
# async def resend_otp(data: EmailRequest, db: AsyncSession = Depends(async_get_db)):
#     user = await crud_users.get_by_email(db, data.email)
#     if not user or user.is_verified:
#         logger.warning(f"Invalid resend OTP request for {data.email}")
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
    
#     otp = await generate_otp()
#     await store_otp(f"verify_otp:{data.email}", otp)
#     if not await send_otp_email(data.email, otp):
#         logger.error(f"Failed to resend OTP to {data.email}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP email")
    
#     logger.info(f"OTP resent to {data.email}")
#     return {"detail": "OTP resent successfully"}

# @router.post("/forgot-password", response_model=dict)
# async def forgot_password(data: EmailRequest, db: AsyncSession = Depends(async_get_db)):
#     user = await crud_users.get_by_email(db, data.email)
#     if not user:
#         logger.info(f"Password reset requested for non-existent email: {data.email}")
#         return {"detail": "If this email is registered, a reset OTP has been sent."}
    
#     if not user.is_verified:
#         logger.warning(f"Unverified user requested password reset: {data.email}")
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Email not verified. Please verify your email first."
#         )
    
#     otp = await generate_otp()
#     await store_otp(f"reset_otp:{data.email}", otp)
#     if not await send_otp_email(data.email, otp, subject="Your ConvoiAI Password Reset OTP"):
#         logger.error(f"Failed to send password reset OTP to {data.email}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP email")
    
#     logger.info(f"Password reset OTP sent to {data.email}")
#     return {"detail": "If this email is registered, a reset OTP has been sent."}

# @router.post("/reset-password", response_model=dict)
# async def reset_password(data: ResetPassword, db: AsyncSession = Depends(async_get_db)):
#     if not await verify_and_delete_otp(f"reset_otp:{data.email}", data.otp):
#         logger.warning(f"Invalid password reset OTP for {data.email}")
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    
#     user = await crud_users.get_by_email(db, data.email)
#     if not user:
#         logger.warning(f"User not found for password reset: {data.email}")
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
#     if not user.is_verified:
#         logger.warning(f"Unverified user attempted password reset: {data.email}")
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Email not verified. Please verify your email first."
#         )

#     await crud_users.update(
#         db=db,
#         object={"hashed_password": get_password_hash(data.new_password), "updated_at": datetime.now(UTC)},
#         id=user.id
#     )
#     logger.info(f"Password reset for {data.email}")
#     return {"detail": "Password reset successfully"}

# @router.post("/resend-reset-otp", response_model=dict, dependencies=[Depends(rate_limit_otp)])
# async def resend_reset_otp(data: EmailRequest, db: AsyncSession = Depends(async_get_db)):
#     user = await crud_users.get_by_email(db, data.email)
#     if not user:
#         logger.info(f"Password reset OTP resend requested for non-existent email: {data.email}")
#         return {"detail": "If this email is registered, a new OTP has been sent."}
    
#     if not user.is_verified:
#         logger.warning(f"Unverified user requested resend reset OTP: {data.email}")
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Email not verified. Please verify your email first."
#         )

#     otp = await generate_otp()
#     await store_otp(f"reset_otp:{data.email}", otp)
#     if not await send_otp_email(data.email, otp, subject="Your ConvoiAI Password Reset OTP"):
#         logger.error(f"Failed to resend password reset OTP to {data.email}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP email")
    
#     logger.info(f"Password reset OTP resent to {data.email}")
#     return {"detail": "If this email is registered, a new OTP has been sent."}

from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.config import settings
from ...core.db.database import async_get_db
from ...core.utils.cache import get_redis_client
from ...core.exceptions.http_exceptions import UnauthorizedException
from ...core.schemas import Token, LoginRequest
from ...core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_token,
    TokenType,
    get_password_hash,
)
from ...schemas.user import OTPVerify, EmailRequest, ResetPassword, MessageResponse
from ...crud.crud_users import crud_users
from ...services.auth_utils import generate_otp, store_otp, send_otp_email, verify_and_delete_otp
from redis.asyncio import Redis
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["login"])

async def rate_limit_otp(data: EmailRequest, redis_client: Redis = Depends(get_redis_client)):
    key = f"rate_limit:otp:{data.email}"
    count = await redis_client.get(key)
    if count and int(count) >= 1000:
        logger.warning(f"Rate limit exceeded for OTP request: {data.email}")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many OTP requests. Try again later.")
    await redis_client.incr(key)
    await redis_client.expire(key, 3600)

async def rate_limit_verify_otp(data: OTPVerify, redis_client: Redis = Depends(get_redis_client)):
    key = f"rate_limit:verify_otp:{data.email}"
    count = await redis_client.get(key)
    if count and int(count) >= 5:
        logger.warning(f"Rate limit exceeded for OTP verification: {data.email}")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many OTP verification attempts. Try again later.")
    await redis_client.incr(key)
    await redis_client.expire(key, 3600)

# async def rate_limit_refresh(request: Request, redis_client: Redis = Depends(get_redis_client)):
#         refresh_token = request.cookies.get("refresh_token")
#         if not refresh_token:
#             raise HTTPException(status_code=401, detail="Refresh token missing.")
        
#         try:
#             # Decode token to get email (assuming sub is email)
#             payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
#             email = payload.get("sub")
#             if not email:
#                 raise HTTPException(status_code=401, detail="Invalid token payload.")
#         except Exception as e:
#             raise HTTPException(status_code=401, detail="Invalid refresh token.")

#         key = f"rate_limit:refresh:{email}"
#         count = await redis_client.get(key)
#         if count and int(count) >= 10:  # Limit to 10 refresh attempts per hour
#             logger.warning(f"Rate limit exceeded for refresh token: {email}")
#             raise HTTPException(
#                 status_code=status.HTTP_429_TOO_MANY_REQUESTS,
#                 detail="Too many refresh attempts. Try again later."
#             )
#         await redis_client.incr(key)
#         await redis_client.expire(key, 3600)
#         return None

@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    user = await authenticate_user(username_or_email=login_data.username, password=login_data.password, db=db)
    if not user:
        logger.warning(f"Failed login attempt for {login_data.username}")
        raise UnauthorizedException("Wrong username, email or password.")

    if not user["is_verified"]:
        logger.warning(f"Unverified user attempted login: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email."
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)
    refresh_token = await create_refresh_token(data={"sub": user["username"]})
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    access_max_age = int(access_token_expires.total_seconds())  # Expiry for access_token cookie

    is_secure = settings.ENVIRONMENT.lower() != "local"
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

    username = user["username"][:20]
    logger.info(f"User logged in: {user['email']}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "token": access_token,
        "email": user["email"],
        "name": user["name"],
        "username": username
    }

# @router.post("/refresh", dependencies=[Depends(rate_limit_refresh)])
@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(async_get_db)
) -> dict[str, str]:
    refresh_token = request.cookies.get("refresh_token")
    logger.info(f"Received refresh_token: {refresh_token}")
    if not refresh_token:
        logger.warning("Refresh token missing in request")
        raise UnauthorizedException("Refresh token missing.")
    user_data = await verify_token(
        token=refresh_token,
        expected_token_type=TokenType.REFRESH,
        db=db
    )
    if not user_data:
        logger.error(f"Token verification failed for refresh token: {refresh_token}")
        raise UnauthorizedException("Invalid refresh token.")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = await create_access_token(
        data={"sub": user_data.username_or_email},
        expires_delta=access_token_expires
    )
    is_secure = settings.ENVIRONMENT.lower() != "local"
    access_max_age = int(access_token_expires.total_seconds())
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=is_secure,
        samesite="Lax",
        max_age=access_max_age,
        path="/",
    )
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/verify-otp", response_model=MessageResponse, dependencies=[Depends(rate_limit_verify_otp)])
async def verify_otp(data: OTPVerify, db: AsyncSession = Depends(async_get_db)):
    if not await verify_and_delete_otp(f"verify_otp:{data.email}", data.otp):
        logger.warning(f"Invalid OTP attempt for {data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    
    user = await crud_users.get_by_email(db, data.email)
    if not user:
        logger.warning(f"Invalid OTP verification request for {data.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")
    
    if user.is_verified:
        logger.info(f"Email already verified: {data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")
    
    await crud_users.update(db=db, object={"is_verified": True, "updated_at": datetime.now(UTC)}, id=user.id)
    logger.info(f"User verified successfully: {data.email}")
    return MessageResponse(detail="Email verified successfully")

@router.post("/resend-otp", response_model=MessageResponse, dependencies=[Depends(rate_limit_otp)])
async def resend_otp(data: EmailRequest, db: AsyncSession = Depends(async_get_db)):
    user = await crud_users.get_by_email(db, data.email)
    if not user:
        logger.info(f"OTP resend requested for non-existent email: {data.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")
    if user.is_verified:
        logger.info(f"OTP resend requested for already verified email: {data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")
    
    otp = await generate_otp()
    await store_otp(f"verify_otp:{data.email}", otp)
    if not await send_otp_email(data.email, otp):
        logger.error(f"Failed to resend OTP to {data.email}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP email")
    
    logger.info(f"OTP resent to {data.email}")
    return MessageResponse(detail="OTP resent successfully")

@router.post("/forgot-password", response_model=MessageResponse, dependencies=[Depends(rate_limit_otp)])
async def forgot_password(data: EmailRequest, db: AsyncSession = Depends(async_get_db)):
    user = await crud_users.get_by_email(db, data.email)
    if not user:
        logger.info(f"Password reset requested for non-existent email: {data.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")
    
    if not user.is_verified:
        logger.warning(f"Unverified user requested password reset: {data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )
    
    otp = await generate_otp()
    await store_otp(f"reset_otp:{data.email}", otp)
    if not await send_otp_email(data.email, otp, subject="Your ConvoiAI Password Reset OTP"):
        logger.error(f"Failed to send password reset OTP to {data.email}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP email")
    
    logger.info(f"Password reset OTP sent to {data.email}")
    return MessageResponse(detail="Password reset OTP sent successfully")

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPassword, db: AsyncSession = Depends(async_get_db)):
    if not await verify_and_delete_otp(f"reset_otp:{data.email}", data.otp):
        logger.warning(f"Invalid password reset OTP for {data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    
    user = await crud_users.get_by_email(db, data.email)
    if not user:
        logger.warning(f"User not found for password reset: {data.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")
    
    if not user.is_verified:
        logger.warning(f"Unverified user attempted password reset: {data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )

    await crud_users.update(
        db=db,
        object={"hashed_password": get_password_hash(data.new_password), "updated_at": datetime.now(UTC)},
        id=user.id
    )
    logger.info(f"Password reset for {data.email}")
    return MessageResponse(detail="Password reset successfully")


@router.post("/resend-reset-otp", response_model=MessageResponse, dependencies=[Depends(rate_limit_otp)])
async def resend_reset_otp(data: EmailRequest, db: AsyncSession = Depends(async_get_db)):
    user = await crud_users.get_by_email(db, data.email)
    if not user:
        logger.info(f"Password reset OTP resend requested for non-existent email: {data.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")
    
    if not user.is_verified:
        logger.warning(f"Unverified user requested resend reset OTP: {data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )

    otp = await generate_otp()
    await store_otp(f"reset_otp:{data.email}", otp)
    if not await send_otp_email(data.email, otp, subject="Your ConvoiAI Password Reset OTP"):
        logger.error(f"Failed to resend password reset OTP to {data.email}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP email")
    
    logger.info(f"Password reset OTP resent to {data.email}")
    return MessageResponse(detail="Password reset OTP resent successfully")

