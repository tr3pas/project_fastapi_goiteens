import asyncio

from werkzeug.security import generate_password_hash

from models import User
from settings import Base, api_config, async_engine, async_session


async def create_bd():
    """Створення структури БД"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def insert_data():
    """Додавання тестових даних"""
    async with async_session() as session:
        # Адмін
        u1 = User(
            username="admin",
            email="admin@ex.com",
            is_admin=True,
            password=generate_password_hash("admin"),
        )
        
        # Звичайні користувачі
        u2 = User(
            username="user",
            email="user@ex.com",
            is_admin=False,
            password=generate_password_hash("user"),
        )
        
        u3 = User(
            username="test",
            email="test@ex.com",
            is_admin=False,
            password=generate_password_hash("test"),
        )
        
        session.add_all([u1, u2, u3])
        await session.commit()
        
        print("✅ Створено користувачів:")
        print(f"   - admin / admin (адмін)")
        print(f"   - user / user (користувач)")
        print(f"   - test / test (користувач)")


async def main():
    print("🔄 Створення бази даних...")
    await create_bd()
    print(f"✅ База даних {api_config.DATABASE_NAME} створена")

    print("\n🔄 Додавання тестових даних...")
    await insert_data()
    print(f"✅ Дані додано до {api_config.DATABASE_NAME}")

    await async_engine.dispose()
    print("\n✅ Готово!")


if __name__ == "__main__":
    asyncio.run(main())