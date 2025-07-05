from typing import Dict
import random
import string
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.schemas.user import UserCreate

def random_lower_string() -> str:
    """Generate random lowercase string"""
    return "".join(random.choices(string.ascii_lowercase, k=32))

def random_email() -> str:
    """Generate random email"""
    return f"{random_lower_string()}@example.com"

def create_random_user(db: Session) -> User:
    """Create random user for testing"""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=email,
        username=email.split("@")[0],
        password=password,
        full_name=random_lower_string(),
        role=UserRole.INSTRUCTOR
    )
    user = User(
        email=email,
        username=user_in.username,
        hashed_password=get_password_hash(password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authentication_token_from_email(db: Session, email: str) -> Dict[str, str]:
    """Get authentication token for user by email"""
    user = db.query(User).filter(User.email == email).first()
    return {
        "Authorization": f"Bearer {create_access_token(user.id)}"
    } 