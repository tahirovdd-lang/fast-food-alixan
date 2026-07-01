import os
import json
import logging
import asyncio
import re

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.filters.command import CommandObject
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

ADMIN_ID = int(os.getenv("ADMIN_ID", "6013591658"))

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://tahirovdd-lang.github.io/fast-food-alixan/?v=1"
)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

WELCOME = (
    "🇷🇺 <b>Добро пожаловать в Fast Food ALIXAN!</b>\n"
    "Откройте меню и оформите заказ.\n\n"
    "🇺🇿 <b>Fast Food ALIXAN ga xush kelibsiz!</b>\n"
    "Menyuni oching va buyurtma bering.\n\n"
    "🇬🇧 <b>Welcome to Fast Food ALIXAN!</b>\n"
    "Open the menu and place your order."
)

MENU_BTN_TEXT = "Ochish / Открыть / Open"


def menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=MENU_BTN_TEXT,
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ]
        ],
        resize_keyboard=True
    )


def safe_html(s):
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def normalize_phone(phone):
    if not phone:
        return ""
    p = re.sub(r"[^\d+]", "", phone.strip())
    if p.startswith("998"):
        p = "+" + p
    return p


def payment_label(v):
    v = str(v or "").lower()
    if v == "cash":
        return "Наличные"
    if v == "click":
        return "Click"
    if v == "online":
        return "Online / карта"
    return v or "—"


def type_label(v):
    v = str(v or "").lower()
    if v == "delivery":
        return "Доставка"
    if v == "pickup":
        return "Самовывоз"
    return v or "—"


async def send_welcome(message: types.Message):
    await message.answer(WELCOME, reply_markup=menu_kb())


@dp.message(CommandStart())
async def start(message: types.Message, command: CommandObject = None):
    await send_welcome(message)


@dp.message(Command("menu"))
async def menu_cmd(message: types.Message):
    await send_welcome(message)


@dp.message(F.text == MENU_BTN_TEXT)
async def menu_button(message: types.Message):
    await send_welcome(message)


@dp.message(F.web_app_data)
async def webapp_order(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        data = {}

    items = data.get("items", [])
    phone = normalize_phone(data.get("phone", ""))
    address = data.get("address", "")
    comment = data.get("comment", "")
    total = data.get("total", 0)
    payment = payment_label(data.get("payment", ""))
    order_type = type_label(data.get("type", ""))

    username = message.from_user.username
    if username:
        user_line = f'👤 Клиент: <a href="https://t.me/{safe_html(username)}">@{safe_html(username)}</a>'
    else:
        user_line = f'👤 Клиент: <a href="tg://user?id={message.from_user.id}">{safe_html(message.from_user.first_name)}</a>'

    lines = []
    for item in items:
        lines.append(
            f"• {safe_html(item.get('name', '—'))} × "
            f"<b>{safe_html(item.get('qty', 1))}</b> — "
            f"{safe_html(item.get('price', 0))} сум"
        )

    if not lines:
        lines.append("• —")

    admin_text = (
        "📩 <b>НОВЫЙ ЗАКАЗ — Fast Food ALIXAN</b>\n\n"
        f"{user_line}\n"
        f"📞 Телефон: <b>{safe_html(phone) if phone else '—'}</b>\n"
        f"🚚 Тип получения: <b>{safe_html(order_type)}</b>\n"
        f"💳 Тип оплаты: <b>{safe_html(payment)}</b>\n"
        f"📍 Адрес: <b>{safe_html(address) if address else '—'}</b>\n"
    )

    if comment:
        admin_text += f"💬 Комментарий: <b>{safe_html(comment)}</b>\n"

    admin_text += "\n🍔 <b>Состав заказа:</b>\n"
    admin_text += "\n".join(lines)
    admin_text += f"\n\n💰 Итого: <b>{safe_html(total)}</b> сум"

    await message.answer(
        "✅ Заказ принят! Спасибо, что выбрали Fast Food ALIXAN 😊",
        reply_markup=menu_kb()
    )

    await bot.send_message(ADMIN_ID, admin_text)


@dp.message()
async def fallback(message: types.Message):
    await send_welcome(message)


async def main():
    logging.info("Fast Food ALIXAN bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
