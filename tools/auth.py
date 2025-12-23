import os
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from werkzeug.security import check_password_hash

from models.models import User
from settings import api_config, async_session


def generate_secret_key():
    """Генерація секретного ключа"""
    return os.urandom(32).hex()


def create_access_token(payload: dict, expires_delta: timedelta | None = None):
    """Створення JWT токена"""
    to_encode = payload.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Робимо токен дійсним на 24 години замість 5 хвилин
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    
    print(f"Creating token with payload: {to_encode}")
    
    jwt_token = jwt.encode(
        to_encode, 
        api_config.SECRET_KEY, 
        algorithm=api_config.ALGORITHM
    )
    
    return jwt_token


def decode_access_token(token: str):
    """Декодування JWT токена"""
    print(f"\n{'='*50}")
    print(f"DECODE TOKEN DEBUG")
    print(f"Token received: {token[:30] if token else 'None'}...")
    print(f"Token length: {len(token) if token else 0}")
    print(f"SECRET_KEY: {api_config.SECRET_KEY[:10]}...")
    print(f"ALGORITHM: {api_config.ALGORITHM}")
    
    if not token:
        print("❌ ERROR: Token is empty!")
        print(f"{'='*50}\n")
        return None
    
    try:
        payload = jwt.decode(
            token,
            api_config.SECRET_KEY,
            algorithms=[api_config.ALGORITHM],
            options={"verify_exp": True}
        )
        
        print(f"✅ Token decoded successfully!")
        print(f"   - sub: {payload.get('sub')}")
        print(f"   - username: {payload.get('username')}")
        print(f"   - is_admin: {payload.get('is_admin')}")
        print(f"   - exp: {payload.get('exp')}")
        print(f"{'='*50}\n")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        print("❌ ERROR: Token has expired!")
        print(f"{'='*50}\n")
        return None
        
    except jwt.InvalidTokenError as e:
        print(f"❌ ERROR: Invalid token: {e}")
        print(f"{'='*50}\n")
        return None
        
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*50}\n")
        return None


async def authenticate_user(username: str, password: str):
    """Аутентифікація користувача"""
    print(f"Authenticating user: {username}")
    
    async with async_session() as session:
        user_stmt = select(User).where(User.username == username)
        result = await session.execute(user_stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User {username} not found")
            return False
        
        if not check_password_hash(user.password, password):
            print(f"Invalid password for user {username}")
            return False
        
        print(f"User {username} authenticated successfully. is_admin={user.is_admin}")
        return user

