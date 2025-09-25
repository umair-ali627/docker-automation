# from fastapi import APIRouter, Depends, Response, Cookie
# from jose import JWTError
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import Optional

# from ...core.db.database import async_get_db
# from ...core.exceptions.http_exceptions import UnauthorizedException
# from ...core.security import blacklist_tokens, oauth2_scheme

# router = APIRouter(tags=["login"])


# @router.post("/logout")
# async def logout(
#     response: Response,
#     access_token: str = Depends(oauth2_scheme),
#     refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
#     db: AsyncSession = Depends(async_get_db)
# ) -> dict[str, str]:
#     try:
#         if not refresh_token:
#             raise UnauthorizedException("Refresh token not found")
            
#         await blacklist_tokens(
#             access_token=access_token,
#             refresh_token=refresh_token,
#             db=db
#         )
#         response.delete_cookie(key="refresh_token")

#         return {"message": "Logged out successfully"}

#     except JWTError:
#         raise UnauthorizedException("Invalid token.")


# src/app/api/v1/login.py (partial file)

from fastapi import APIRouter, Depends, Response, Cookie
# ADDED: Import the new security objects
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import UnauthorizedException
# CHANGED: Import 'security' instead of 'oauth2_scheme'
from ...core.security import blacklist_tokens, security

router = APIRouter(tags=["login"])

@router.post("/logout")
async def logout(
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(async_get_db)
) -> dict[str, str]:
    try:
        if not refresh_token:
            raise UnauthorizedException("Refresh token not found")
        access_token = credentials.credentials
            
        await blacklist_tokens(
            access_token=access_token,
            refresh_token=refresh_token,
            db=db
        )
        response.delete_cookie(key="refresh_token")
        response.delete_cookie(key="access_token")

        return {"message": "Logged out successfully"}

    except JWTError:
        raise UnauthorizedException("Invalid token.")