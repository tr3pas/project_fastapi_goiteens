import asyncio
from aiogram import Bot, Dispatcher, types
import os
from dotenv import load_dotenv
from aiogram.filters import Command
from sqlalchemy import select
from models import User, Users_in_telegram
from settings import async_session
from models import RepairRequest,Users_in_Telegram

load_dotenv()


token = os.getenv("TOKEN_BOT")

bot = Bot(token=token)  # type: ignore
dp: Dispatcher = Dispatcher()


async def send_msg(user_site_id, message):
    async with async_session() as session:
        user_tg_info = await session.execute(select(Users_in_telegram).filter_by(user_in_site=user_site_id))
        user_tg_info = user_tg_info.scalars().one_or_none()
        if user_tg_info and user_tg_info.user_tg_id:
            await bot.send_message(chat_id=user_tg_info.user_tg_id, text=message)


@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Вітаю! Це бот служби підтримки. Будь ласка, введіть ваш унікальний код для авторизації.")


    @dp.message()
    async def get_code(message: types.Message):
        user_code = message.text.strip() if message.text else ""
        user_tg_id = message.chat.id

        async with async_session() as session:
            stmt = select(Users_in_telegram).where(Users_in_telegram.tg_code == user_code)
            user_check = await session.execute(stmt)
            user_check = user_check.scalar_one_or_none()

            if user_check:
                user_check.user_tg_id = str(user_tg_id)
                session.add(user_check)
                await session.commit()
                await message.answer("Ви успішно додані до бота! Будемо інформувати вас про статус ваших заявок.")
            else:
                await message.answer("Невірний код. Будь ласка, перевірте та спробуйте ще раз.")


@dp.message(Command("myrequests"))
async def repairrequests_command(message: types.Message):
    async with async_session() as session:
        stmt = select(RepairRequest).where(RepairRequest.user_id == Users_in_Telegram.user_in_site)
        repairs = await session.execute(stmt)
        repairs = repairs.scalars()

        repairs.all()


@dp.message(Command("messages"))
async def messages_command(message: types.Message):
    await message.answer("Напишіть номер заявки з якої ви хочете побачити повідомлення.")
    @dp.message()
    async def get_id(message: types.Message):
        repair_id = message.text.strip() if message.text else ""
        async with async_session() as session:
            stmt = select(RepairRequest).where(RepairRequest.user_id == Users_in_Telegram.user_in_site and RepairRequest.id == repair_id)
            repairs = await session.execute(stmt)
            repairs = repairs.scalar()

            await message.answer(repairs.messages)



async def start_bot():
    print("--> start bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())