import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings
from .database import get_db
from .models import User, to_object_id

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations=100_000
    ).hex()
    return f"{salt}${key}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against salt$key format."""
    try:
        salt, key = hashed_password.split('$')
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations=100_000
        ).hex()
        return secrets.compare_digest(key, new_key)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    # Query user from MongoDB by _id or fallback to email
    user_doc = await db.users.find_one({"_id": to_object_id(user_id_str)})
    if not user_doc:
        user_doc = await db.users.find_one({"email": payload.get("email")})
        
    if user_doc is None:
        raise credentials_exception
    return User(user_doc)

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        
        user_doc = await db.users.find_one({"_id": to_object_id(user_id_str)})
        if not user_doc and payload.get("email"):
            user_doc = await db.users.find_one({"email": payload.get("email")})
        if user_doc:
            return User(user_doc)
        return None
    except Exception:
        return None
