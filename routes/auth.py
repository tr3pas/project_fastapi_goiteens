from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash

from models.models import User
from schemas.user import UserInput, UserOut
from settings import get_db
from tools.auth import authenticate_user, create_access_token, decode_access_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: str = Depends(oauth2_scheme)):
    user = decode_access_token(token)
    if not user:
        raise credentials_exception
    return user


def require_admin(user: dict = Depends(get_current_user)):
    if not user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials"
        )
    return user


@router.post("/token")
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Генерація JWT токена для входу"""
    try:
        user = await authenticate_user(form_data.username, form_data.password)

        if not user:
            raise credentials_exception

        data_payload = {
            "sub": str(user.id), 
            "email": user.email, 
            "username": user.username,
            "is_admin": user.is_admin
        }
        access_token = create_access_token(payload=data_payload)
        
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate_token: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.post("/register", response_model=UserOut)
async def register_user(user: UserInput, db: AsyncSession = Depends(get_db)):
    """Реєстрація нового користувача (API endpoint)"""
    
    # Перевірка чи існує користувач з таким email
    existing_user = await db.scalar(
        select(User).where(User.email == user.email)
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Користувач з таким email вже існує"
        )
    
    # Перевірка чи існує користувач з таким username
    existing_username = await db.scalar(
        select(User).where(User.username == user.username)
    )
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Користувач з таким іменем вже існує"
        )
    
    # Створення нового користувача
    new_user = User(**user.model_dump())
    new_user.password = generate_password_hash(user.password)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отримання інформації про поточного користувача"""
    user_id = int(current_user["sub"])
    user = await db.scalar(select(User).where(User.id == user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Користувача не знайдено"
        )
    
    return user