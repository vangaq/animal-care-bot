from datetime import datetime

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import requests as dbreq
from keyboards.main_keyboards import (
    back_to_main_keyboard,
    main_reply_keyboard,
    profile_options_keyboard,
)
from utils.helpers import get_species_detail_label


class ProfileStates(StatesGroup):
    waiting_owner_name = State()


def format_created_at(value: str) -> str:
    dt = datetime.fromisoformat(value)
    return dt.strftime("%d.%m.%Y %H:%M")


async def start_change_owner_name(message: types.Message, state: FSMContext):
    """Запрашивает новое имя владельца из раздела профиля."""
    await state.set_state(ProfileStates.waiting_owner_name)
    await message.answer(
        "Напишите новое имя, которое бот будет использовать в обращении к вам.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


async def save_changed_owner_name(message: types.Message, state: FSMContext):
    """Сохраняет новое имя владельца."""
    owner_name = (message.text or "").strip()
    if not owner_name:
        await message.answer("Имя не может быть пустым. Напишите новое имя ещё раз.")
        return

    response = await dbreq.update_user_owner_name(message.from_user.id, owner_name)
    if response["status"] != "ok":
        await message.answer("Не удалось обновить имя: " + response.get("error_msg", ""))
        return

    await state.clear()
    await message.answer(
        f'Готово, теперь я буду обращаться к вам "{owner_name}".',
        reply_markup=profile_options_keyboard(),
    )


async def on_text_profile(message: types.Message):
    """Обрабатывает текстовые команды, относящиеся к профилю."""
    text = message.text.lower()

    if text == "профиль":
        user_response = await dbreq.get_user_by_telegram(message.from_user.id)
        owner_name = ""
        if user_response["status"] == "ok":
            owner_name = (user_response["data"]["user"].get("owner_name") or "").strip()
        prefix = f"{owner_name}, " if owner_name else ""
        await message.answer(f"{prefix}выберите нужную вам функцию:", reply_markup=profile_options_keyboard())
        return

    if text == "посмотреть профиль":
        user_response = await dbreq.get_user_by_telegram(message.from_user.id)
        if user_response["status"] != "ok":
            await message.answer("Ошибка: " + user_response.get("error_msg", "user not found"))
            return

        user = user_response["data"]["user"]
        user_id = user["id"]
        owner_name = (user.get("owner_name") or "").strip()

        pets_response = await dbreq.list_pets_for_user(user_id)
        if pets_response["status"] != "ok":
            await message.answer("Ошибка при получении питомцев.")
            return

        pets = pets_response["data"]["pets"]
        if owner_name:
            await message.answer(f"Профиль владельца: {owner_name}")

        if not pets:
            await message.answer("Пока нет животных.", reply_markup=back_to_main_keyboard())
            return

        for pet in pets:
            detail_label = get_species_detail_label(pet.get("species"))
            pet_text = (
                f"🐾 Питомец:\n"
                f"Вид: {pet.get('species') or '-'}\n"
                f"{detail_label}: {pet['breed']}\n"
                f"Кличка: {pet['name']}\n"
                f"Возраст: {pet['age']}\n"
                f"Доп. информация: {pet['extra_info'] or '-'}\n"
                f"Фото: {'есть' if pet['photo_file_id'] else 'нет'}\n"
                f"Создан: {format_created_at(pet['created_at'])}"
            )

            if pet["photo_file_id"]:
                await message.answer_photo(photo=pet["photo_file_id"], caption=pet_text)
            else:
                await message.answer(pet_text)

            notes_response = await dbreq.list_notes_for_pet(pet["id"])
            if notes_response["status"] == "ok" and notes_response["data"]["notes"]:
                for note in notes_response["data"]["notes"]:
                    note_text = (
                        f"📌 Заметка для питомца {pet['name']}:\n"
                        f"Название: {note['title']}\n"
                        f"Напоминание: {note.get('reminder_display') or dbreq.format_reminder_for_display(note['period'], note.get('next_remind_at'))}\n"
                        f"Доп. инфо: {note['extra_info'] or '-'}\n"
                        f"Фото: {'есть' if note['photo_file_id'] else 'нет'}"
                    )

                    if note["photo_file_id"]:
                        await message.answer_photo(photo=note["photo_file_id"], caption=note_text)
                    else:
                        await message.answer(note_text)
            else:
                await message.answer(f"У питомца {pet['name']} заметки отсутствуют.")

        await message.answer("Главное меню:", reply_markup=main_reply_keyboard())
