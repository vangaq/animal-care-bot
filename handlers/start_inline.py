from aiogram import types
from db import requests as dbreq
from keyboards.main_keyboards import main_reply_keyboard
from utils.helpers import make_response_ok

#Функция "/start"
async def cmd_start(message: types.Message):
    resp = await dbreq.get_or_create_user(message.from_user.id)
    if resp["status"] == "ok":
        await message.answer(
            "Привет! Этот бот — школьный проект для управления информацией о питомцах.",
            reply_markup=main_reply_keyboard()
        )
    else:
        await message.answer("Ошибка при создании профиля: " + resp.get("error_msg", "unknown"))

#Функция "/inline"
async def cmd_inline(message: types.Message):
    inline_links = [
        {"title": "Документация по кошкам", "url": "https://example.com/cats"},
        {"title": "Документация по собаками", "url": "https://example.com/dogs"},
    ]
    kb = types.InlineKeyboardMarkup()
    for link in inline_links:
        kb.add(types.InlineKeyboardButton(text=link["title"], url=link["url"]))
    await message.answer("Полезные ссылки:", reply_markup=kb)
    await message.answer(str({"inline_links": inline_links}))
