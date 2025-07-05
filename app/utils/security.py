"""
Security related utility functions
"""
import jwt  # pyjwt paketi
from typing import Optional
from datetime import datetime, timedelta

from app.core.config import settings


def generate_password_reset_token(email: str) -> str:
    """
    Email adresini kullanarak şifre sıfırlama tokeni oluşturur.
    
    Args:
        email: Kullanıcının email adresi
        
    Returns:
        JWT token
    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now.timestamp(), "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verilen tokeni doğrular ve kullanıcının email adresini döner.
    
    Args:
        token: JWT token
        
    Returns:
        Kullanıcının email adresi veya None
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_token["sub"]
    except jwt.InvalidTokenError:
        return None 