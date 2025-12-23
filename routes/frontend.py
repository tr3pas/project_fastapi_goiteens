# routes/frontend.py - Виправлений файл

from fastapi import APIRouter, Request, Form, Response, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash

from models.models import User
from schemas.user import UserInput
from settings import get_db
from tools.auth import authenticate_user, create_access_token

templates = Jinja2Templates(directory="templates")
router = APIRouter(include_in_schema=False)


@router.get("/")
async def home(request: Request, error: str | None = None):
    """Головна сторінка"""
    return templates.TemplateResponse(
        "index.html", {"request": request, "error": error}
    )


# ==================== AUTH PAGES ====================

@router.get("/auth/login")
async def login_page(request: Request, error: str | None = None, success: str | None = None):
    """Сторінка входу"""
    return templates.TemplateResponse(
        "login.html", 
        {
            "request": request, 
            "error": error,
            "success": success
        }
    )


@router.get("/auth/register")
async def register_page(request: Request, error: str | None = None):
    """Сторінка реєстрації"""
    return templates.TemplateResponse(
        "register.html", 
        {
            "request": request, 
            "error": error
        }
    )


@router.post("/auth/token")
async def login_form(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    """Обробка форми входу через OAuth2"""
    try:
        # Викликаємо функцію authenticate_user безпосередньо
        user = await authenticate_user(username, password)
        
        if not user:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Невірне ім'я користувача або пароль"
                },
                status_code=401
            )
        
        # Створюємо токен
        data_payload = {
            "sub": str(user.id), 
            "email": user.email, 
            "username": user.username,
            "is_admin": user.is_admin
        }
        access_token = create_access_token(payload=data_payload)
        
        # Створюємо redirect response
        redirect = RedirectResponse(url="/", status_code=303)
        
        # Встановлюємо cookie з токеном
        redirect.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=24 * 60 * 60,  # 1 день
            samesite="lax"
        )
        
        return redirect
                
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": f"Помилка при вході: {str(e)}"
            },
            status_code=500
        )


@router.post("/auth/register")
async def register_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Обробка форми реєстрації"""
    
    try:
        # Перевірка чи існує користувач з таким email
        existing_user = await db.scalar(
            select(User).where(User.email == email)
        )
        if existing_user:
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "Користувач з таким email вже існує"
                },
                status_code=400
            )
        
        # Перевірка чи існує користувач з таким username
        existing_username = await db.scalar(
            select(User).where(User.username == username)
        )
        if existing_username:
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "Користувач з таким іменем вже існує"
                },
                status_code=400
            )
        
        # Створення нового користувача
        new_user = User(username=username, email=email)
        new_user.password = generate_password_hash(password)
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # Успішна реєстрація - перенаправляємо на сторінку входу
        return RedirectResponse(
            url="/auth/login?success=Реєстрація успішна! Тепер ви можете увійти",
            status_code=303
        )
                
    except Exception as e:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": f"Помилка при реєстрації: {str(e)}"
            },
            status_code=500
        )


@router.get("/auth/logout")
async def logout():
    """Вихід з системи"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response


@router.get("/auth/forgot-password")
async def forgot_password_page(request: Request):
    """Сторінка відновлення пароля (заглушка)"""
    return templates.TemplateResponse(
        "error.html", 
        {
            "request": request,
            "error_code": 501,
            "error_title": "Не реалізовано",
            "error_description": "Функція відновлення пароля ще не реалізована"
        }
    )