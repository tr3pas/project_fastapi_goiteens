import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from routes import auth_router, frontend_router, user_account_router, admin_panel_router, bot_code_router
from routes.errors import http_exception_handler, validation_exception_handler, general_exception_handler
from tg_bot import start
import threading

app = FastAPI(title="RepairHub API", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers (БЕЗ ДУБЛЮВАННЯ!)
app.include_router(frontend_router, prefix="", tags=["frontend"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_account_router, prefix="/account", tags=["account"])
app.include_router(admin_panel_router, prefix="/admin", tags=["admin"])
app.include_router(bot_code_router, prefix="/admin", tags=["admin"])

# Error handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start())

if __name__ == "__main__":
    uvicorn.run("main:app", port=8001, reload=True, host="localhost")