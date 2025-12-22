# routes/frontend.py - Виправлений файл

from fastapi import (APIRouter, Cookie, Depends, Form, Request, Response)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash

from models.models import RepairRequest, User
from settings import get_db
from tools.auth import authenticate_user, create_access_token, decode_access_token

templates = Jinja2Templates(directory="templates")
router = APIRouter(include_in_schema=False)


# Helper function to get current user from cookie
async def get_current_user_from_cookie(
    access_token: str | None = Cookie(None), 
    db: AsyncSession = Depends(get_db)
):
    """Отримати поточного користувача з cookie"""
    print(f"=== GET USER FROM COOKIE DEBUG ===")
    print(f"access_token: {access_token}")
    
    if not access_token:
        print("No access_token in cookie!")
        return None
    
    try:
        user_data = decode_access_token(access_token)
        print(f"user_data from token: {user_data}")
        
        if not user_data:
            print("decode_access_token returned None!")
            return None
        
        user_id = int(user_data["sub"])
        print(f"user_id: {user_id}")
        
        user = await db.scalar(select(User).where(User.id == user_id))
        print(f"user from DB: {user}")
        print(f"is_admin: {user.is_admin if user else None}")
        print(f"==================================")
        
        return user
    except Exception as e:
        print(f"Error getting user from cookie: {e}")
        import traceback
        traceback.print_exc()
        return None


@router.get("/")
async def home(
    request: Request,
    error: str | None = None,
    current_user: User | None = Depends(get_current_user_from_cookie),
):
    """Головна сторінка"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "error": error,
            "current_user": current_user,
            "is_authenticated": current_user is not None,
        },
    )


# ==================== AUTH PAGES ====================


@router.get("/auth/login")
async def login_page(
    request: Request, 
    error: str | None = None, 
    success: str | None = None
):
    """Сторінка входу"""
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "error": error, "success": success}
    )


@router.get("/auth/register")
async def register_page(request: Request, error: str | None = None):
    """Сторінка реєстрації"""
    return templates.TemplateResponse(
        "register.html", 
        {"request": request, "error": error}
    )


@router.post("/auth/token")
async def login_form(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    """Обробка форми входу через OAuth2"""
    print(f"\n{'='*50}")
    print(f"LOGIN ATTEMPT")
    print(f"Username: {username}")
    print(f"Password length: {len(password)}")
    print(f"{'='*50}\n")
    
    try:
        user = await authenticate_user(username, password)
        print(f"Authentication result: {user}")

        if not user:
            print("❌ Authentication FAILED - returning error page")
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Невірне ім'я користувача або пароль"},
                status_code=401,
            )

        print(f"✅ User authenticated: {user.username}, is_admin={user.is_admin}")

        # Створюємо токен
        data_payload = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin,
        }
        access_token = create_access_token(payload=data_payload)
        print(f"✅ Token created: {access_token[:50]}...")

        # Перенаправляємо адміна на адмін-панель, звичайного користувача на головну
        redirect_url = "/admin" if user.is_admin else "/"
        print(f"✅ Redirecting to: {redirect_url}")
        
        redirect = RedirectResponse(url=redirect_url, status_code=303)

        # Встановлюємо cookie з токеном
        redirect.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=24 * 60 * 60,  # 1 день
            samesite="lax",
        )
        
        print(f"✅ Cookie set")
        print(f"{'='*50}\n")

        return redirect

    except Exception as e:
        print(f"❌ LOGIN ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": f"Помилка при вході: {str(e)}"},
            status_code=500,
        )


@router.post("/auth/register")
async def register_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Обробка форми реєстрації"""
    try:
        # Перевірка чи існує користувач з таким email
        existing_user = await db.scalar(select(User).where(User.email == email))
        if existing_user:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Користувач з таким email вже існує"},
                status_code=400,
            )

        # Перевірка чи існує користувач з таким username
        existing_username = await db.scalar(
            select(User).where(User.username == username)
        )
        if existing_username:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Користувач з таким іменем вже існує"},
                status_code=400,
            )

        # Створення нового користувача
        new_user = User(username=username, email=email, is_admin=False)
        new_user.password = generate_password_hash(password)

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Успішна реєстрація - перенаправляємо на сторінку входу
        return RedirectResponse(
            url="/auth/login?success=Реєстрація успішна! Тепер ви можете увійти",
            status_code=303,
        )

    except Exception as e:
        print(f"Registration error: {e}")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Помилка при реєстрації: {str(e)}"},
            status_code=500,
        )


@router.get("/auth/logout")
async def logout():
    """Вихід з системи"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response


# ==================== ADMIN PANEL ====================


@router.get("/admin")
async def admin_panel(
    request: Request,
    current_user: User | None = Depends(get_current_user_from_cookie),
):
    """Адмін-панель"""
    # DEBUG
    print(f"=== ADMIN PANEL DEBUG ===")
    print(f"Current user: {current_user}")
    print(f"Is admin: {current_user.is_admin if current_user else 'No user'}")
    print(f"========================")
    
    # Якщо користувач не авторизований
    if not current_user:
        print("Redirecting to login - no user")
        return RedirectResponse(url="/auth/login", status_code=303)
    
    # Якщо користувач не адмін
    if not current_user.is_admin:
        print("User is not admin")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_code": 403,
                "error_title": "Доступ заборонено",
                "error_description": "У вас немає прав для доступу до адмін-панелі",
            },
            status_code=403,
        )
    
    # Все OK - показуємо адмін-панель
    print("Showing admin panel")
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "current_user": current_user,
        },
    )


@router.get("/admin/repair/{repair_id}")
async def admin_repair_detail(
    request: Request,
    repair_id: int,
    current_user: User | None = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_db),
):
    """Деталі заявки на ремонт"""
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    repair = await db.scalar(
        select(RepairRequest).where(RepairRequest.id == repair_id)
    )
    
    if not repair:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_code": 404,
                "error_title": "Заявку не знайдено",
                "error_description": f"Заявка #{repair_id} не існує",
            },
            status_code=404,
        )
    
    return templates.TemplateResponse(
        "repair_detail.html",
        {
            "request": request,
            "current_user": current_user,
            "repair": repair,
        },
    )





@router.get("/requests/new")
async def create_request_page(
    request: Request,
    current_user: User | None = Depends(get_current_user_from_cookie),
):
    """Сторінка створення нової заявки"""
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    return templates.TemplateResponse(
        "create_request.html",
        {
            "request": request,
            "current_user": current_user,
        },
    )

@router.get("/requests")
async def my_requests_page(
    request: Request,
    current_user: User | None = Depends(get_current_user_from_cookie),
):
    """Сторінка моїх заявок"""
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 501,
            "error_title": "Не реалізовано",
            "error_description": "Сторінка моїх заявок ще в розробці.",
        },
    )


@router.get("/help")
async def help_page(request: Request):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 501,
            "error_title": "Не реалізовано",
            "error_description": "Сторінка допомоги ще в розробці",
        },
    )


@router.get("/contacts")
async def contacts_page(request: Request):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 501,
            "error_title": "Не реалізовано",
            "error_description": "Сторінка контактів ще в розробці",
        },
    )


@router.get("/faq")
async def faq_page(request: Request):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 501,
            "error_title": "Не реалізовано",
            "error_description": "Сторінка FAQ ще в розробці",
        },
    )