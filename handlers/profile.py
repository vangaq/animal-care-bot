"""Обработчики раздела 'Профиль'."""

from aiogram import types

from db import requests as dbreq
from keyboards.main_keyboards import (
    back_to_main_keyboard,
    main_reply_keyboard,
    profile_options_keyboard,
)


async def on_text_profile(message: types.Message):
    text = message.text.lower()

    if text == "профиль":
        await message.answer("Выберите нужную вам функцию:", reply_markup=profile_options_keyboard())
        return

    if text == "посмотреть профиль":
        user_response = await dbreq.get_user_by_telegram(message.from_user.id)
        if user_response["status"] != "ok":
            await message.answer("Ошибка: " + user_response.get("error_msg", "user not found"))
            return

        user_id = user_response["data"]["user"]["id"]

        pets_response = await dbreq.list_pets_for_user(user_id)
        if pets_response["status"] != "ok":
            await message.answer("Ошибка при получении питомцев.")
            return

        pets = pets_response["data"]["pets"]
        if not pets:
            await message.answer("Пока нет животных.", reply_markup=back_to_main_keyboard())
            return

        text_out = ""
        for pet in pets:
            text_out += (
                f"🐾 Питомец:\n"
                f"Порода: {pet['breed']}\n"
                f"Кличка: {pet['name']}\n"
                f"Возраст: {pet['age']}\n"
                f"Доп. информация: {pet['extra_info'] or '-'}\n"
                f"Создан: {pet['created_at']}\n"
            )

            notes_response = await dbreq.list_notes_for_pet(pet["id"])
            if notes_response["status"] == "ok" and notes_response["data"]["notes"]:
                text_out += "📌 Заметки:\n"
                for note in notes_response["data"]["notes"]:
                    text_out += (
                        f"- {note['title']} (Период: {note['period']}, "
                        f"Доп. инфо: {note['extra_info'] or '-'})\n"
                    )
            else:
                text_out += "Заметки отсутствуют\n"

            text_out += "\n"

        await message.answer(text_out)
        await message.answer("Главное меню:", reply_markup=main_reply_keyboard())
