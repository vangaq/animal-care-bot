#Все в профиле
from aiogram import types
from keyboards.main_keyboards import main_reply_keyboard
from db import requests as dbreq
from keyboards.main_keyboards import profile_options_keyboard, back_to_main_keyboard, main_reply_keyboard
from utils.helpers import make_response_ok, make_response_error

#Кнопка "Посмотреть профиль"
async def on_text_profile(message: types.Message):
    text = message.text.lower()
    if text == "профиль":
        await message.answer("Выберите нужную вам функцию:", reply_markup=profile_options_keyboard())
    elif text == "посмотреть профиль":
        user_resp = await dbreq.get_user_by_telegram(message.from_user.id)
        if user_resp["status"] != "ok":
            await message.answer("Ошибка: " + user_resp.get("error_msg", "user not found"))
            return
        user_id = user_resp["data"]["user"]["id"]

        pets_resp = await dbreq.list_pets_for_user(user_id)
        if pets_resp["status"] != "ok":
            await message.answer("Ошибка при получении питомцев.")
            return
        pets = pets_resp["data"]["pets"]
        if not pets:
            await message.answer("Пока нет животных", reply_markup=back_to_main_keyboard())
            return

        text_out = ""
        for p in pets:
            text_out += (
                f"🐾 Питомец:\n"
                f"Порода: {p['breed']}\n"
                f"Кличка: {p['name']}\n"
                f"Возраст: {p['age']}\n"
                f"Доп. информация: {p['extra_info'] or '-'}\n"
                f"Создан: {p['created_at']}\n"
            )

            notes_resp = await dbreq.list_notes_for_pet(p["id"])
            if notes_resp["status"] == "ok" and notes_resp["data"]["notes"]:
                text_out += "📌 Заметки:\n"
                for n in notes_resp["data"]["notes"]:
                    text_out += (
                        f"- {n['title']} (Период: {n['period']}, "
                        f"Доп. инфо: {n['extra_info'] or '-'})\n"
                    )
            else:
                text_out += " Заметки отсутствуют\n"

            text_out += "\n"

        await message.answer(text_out)
        await message.answer(
            "Главное меню:",
            reply_markup=main_reply_keyboard()
        )
