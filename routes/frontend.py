# routes/frontend.py - Виправлений файл
from starlette.responses import HTMLResponse
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
    username: str = Form(...),
    password: str = Form(...),
):
    print(f"\n{'='*50}")
    print(f"LOGIN ATTEMPT: {username}")
    
    try:
        user = await authenticate_user(username, password)

        if not user:
            print("❌ Authentication FAILED")
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
        print(f"✅ Token created")
        print(f"{'='*50}\n")

        # Повертаємо HTML з JavaScript для встановлення cookie
        redirect_url = "/admin" if user.is_admin else "/"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Redirecting...</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .loader {{
                    text-align: center;
                }}
                .spinner {{
                    border: 4px solid rgba(255, 255, 255, 0.3);
                    border-top: 4px solid white;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 1rem;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="loader">
                <div class="spinner"></div>
                <p>Авторизація успішна...</p>
            </div>
            <script>
                // Встановлюємо cookie
                const token = "{access_token}";
                const maxAge = 86400; // 24 години
                const expires = new Date(Date.now() + maxAge * 1000).toUTCString();
                
                document.cookie = `access_token=${{token}}; path=/; max-age=${{maxAge}}; SameSite=Lax`;
                
                console.log('Token set:', token.substring(0, 30) + '...');
                console.log('Cookie:', document.cookie);
                
                // Перевірка
                setTimeout(() => {{
                    if (document.cookie.includes('access_token')) {{
                        console.log('✅ Cookie confirmed!');
                        window.location.href = "{redirect_url}";
                    }} else {{
                        console.error('❌ Cookie not set!');
                        alert('Помилка встановлення cookie. Перевірте налаштування браузера.');
                    }}
                }}, 500);
            </script>
        </body>
        </html>
        """
        
        from starlette.responses import HTMLResponse
        return HTMLResponse(content=html_content)

    except Exception as e:
        print(f"❌ LOGIN ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Помилка при вході"},
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


async def get_current_user_from_cookie(
    access_token: str | None = Cookie(None), 
    db: AsyncSession = Depends(get_db)
):
    """Отримати поточного користувача з cookie"""
    print(f"\n{'='*50}")
    print(f"GET USER FROM COOKIE")
    print(f"Cookie access_token: {access_token[:30] if access_token else 'None'}...")
    
    if not access_token:
        print("❌ No access_token in cookie!")
        print(f"{'='*50}\n")
        return None
    
    try:
        user_data = decode_access_token(access_token)
        print(f"User data from decode: {user_data}")
        
        if not user_data:
            print("❌ decode_access_token returned None!")
            print(f"{'='*50}\n")
            return None
        
        user_id = int(user_data["sub"])
        print(f"Looking for user_id: {user_id}")
        
        user = await db.scalar(select(User).where(User.id == user_id))
        
        if user:
            print(f"✅ User found: {user.username}, is_admin={user.is_admin}")
        else:
            print(f"❌ User NOT found in database!")
        
        print(f"{'='*50}\n")
        return user
        
    except Exception as e:
        print(f"❌ Error getting user from cookie: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*50}\n")
        return None