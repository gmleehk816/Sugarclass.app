"""
JWT verification dependency for microservice security.
Verifies tokens issued by the Orchestrator using the shared SECRET_KEY.
"""
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

ALGORITHM = "HS256"
SECRET_KEY = os.getenv("SECRET_KEY") # No default for security
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable not set")

security_scheme = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """
    Verify the JWT and ensure the user is a superuser.
    Returns the decoded token payload.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not payload.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return payload
