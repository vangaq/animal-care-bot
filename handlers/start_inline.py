from aiogram import types

from db import requests as dbreq
from keyboards.main_keyboards import main_reply_keyboard


async def cmd_start(message: types.Message):
    response = await dbreq.get_or_create_user(message.from_user.id)

    if response["status"] == "ok":
        await message.answer(
            "Привет! Этот бот — школьный проект для управления информацией о питомцах.",
            reply_markup=main_reply_keyboard(),
        )
    else:
        await message.answer("Ошибка при создании профиля: " + response.get("error_msg", "unknown"))


async def cmd_inline(message: types.Message):
    inline_links = [
        {"title": "Документация по кошкам", "url": "https://example.com/cats"},
        {"title": "Документация по собакам", "url": "https://example.com/dogs"},
    ]

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=link["title"], url=link["url"])]
            for link in inline_links
        ]
    )

    await message.answer("Полезные ссылки:", reply_markup=keyboard)
