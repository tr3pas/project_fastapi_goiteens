from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

templates = Jinja2Templates(directory="templates")


async def http_exception_handler(request: Request, exc):
    error_messages = {
        400: ("Невірний запит", "Дані запиту некоректні."),
        401: ("Не авторизовано", "Увійдіть до системи."),
        403: ("Доступ заборонено", "У вас немає прав для цієї дії."),
        404: ("Сторінку не знайдено", "Сторінка не існує."),
        500: ("Помилка сервера", "Спробуйте пізніше.")
    }
    
    title, description = error_messages.get(exc.status_code, ("Помилка", "Виникла помилка."))
    
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": exc.status_code,
            "error_title": title,
            "error_description": description
        },
        status_code=exc.status_code
    )


async def validation_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 422,
            "error_title": "Помилка валідації",
            "error_description": "Перевірте правильність введених даних."
        },
        status_code=422
    )


async def general_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 500,
            "error_title": "Помилка сервера",
            "error_description": "Виникла несподівана помилка. Спробуйте пізніше."
        },
        status_code=500
    )