from __future__ import annotations

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import requests as dbreq
from keyboards.main_keyboards import back_to_main_keyboard
from utils.ai_client import ask_local_ai


class AIChatStates(StatesGroup):
    waiting_question = State()


MAX_NOTES_PER_PET_IN_CONTEXT = 5
MAX_NOTE_EXTRA_LEN = 140


def _shorten_text(value: str, max_len: int = MAX_NOTE_EXTRA_LEN) -> str:
    cleaned = " ".join((value or "").split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


async def build_ai_context(telegram_id: int) -> str:
    """Собирает краткий контекст о владельце, питомцах и их заметках для AI."""
    user_response = await dbreq.get_user_by_telegram(telegram_id)
    if user_response["status"] != "ok":
        return ""

    user = user_response["data"]["user"]
    owner_name = (user.get("owner_name") or "").strip() or "Не указано"

    pets_response = await dbreq.list_pets_for_user(user["id"])
    pet_lines: list[str] = []

    if pets_response["status"] == "ok":
        for pet in pets_response["data"].get("pets", []):
            parts = []
            if pet.get("species"):
                parts.append(pet["species"])
            if pet.get("breed"):
                parts.append(f"порода: {pet['breed']}")
            if pet.get("age"):
                parts.append(f"возраст: {pet['age']}")
            if pet.get("extra_info"):
                parts.append(f"доп. информация: {_shorten_text(pet['extra_info'], 100)}")
            details = ", ".join(parts) if parts else "без уточнений"

            pet_block_lines = [f"- {pet.get('name', 'Без имени')}: {details}"]

            notes_response = await dbreq.list_notes_for_pet(pet["id"])
            if notes_response["status"] == "ok":
                notes = notes_response["data"].get("notes", [])
                if notes:
                    pet_block_lines.append("  Заметки:")
                    for note in notes[:MAX_NOTES_PER_PET_IN_CONTEXT]:
                        note_parts = [note.get("title", "Без названия")]
                        if note.get("extra_info"):
                            note_parts.append(_shorten_text(note["extra_info"]))
                        reminder_display = (note.get("reminder_display") or "").strip()
                        if reminder_display:
                            note_parts.append(f"напоминание: {reminder_display}")
                        pet_block_lines.append(f"  • {'; '.join(note_parts)}")
                    if len(notes) > MAX_NOTES_PER_PET_IN_CONTEXT:
                        pet_block_lines.append(
                            f"  • Ещё заметок: {len(notes) - MAX_NOTES_PER_PET_IN_CONTEXT}"
                        )
                else:
                    pet_block_lines.append("  Заметки: нет")
            else:
                pet_block_lines.append("  Заметки: не удалось загрузить")

            pet_lines.append("\n".join(pet_block_lines))

    pets_text = "\n".join(pet_lines) if pet_lines else "- У пользователя пока нет питомцев в базе"
    return (
        "Контекст пользователя:\n"
        f"Имя владельца: {owner_name}\n"
        f"Питомцы и заметки:\n{pets_text}\n"
        "Учитывай этот контекст, если он помогает ответу. "
        "Не выдумывай данные, которых нет. "
        "Если пользователь спрашивает про конкретного питомца, сначала опирайся на его карточку и заметки."
    )


async def start_ai_chat(message: types.Message, state: FSMContext):
    """Переводит пользователя в режим общения с AI."""
    await state.clear()
    user_response = await dbreq.get_user_by_telegram(message.from_user.id)
    owner_name = ""
    if user_response["status"] == "ok":
        owner_name = (user_response["data"]["user"].get("owner_name") or "").strip()

    prefix = f"{owner_name}, " if owner_name else ""
    await message.answer(
        f"{prefix}режим AI включён. Напишите ваш вопрос текстом.\n"
        "Чтобы выйти, нажмите «На главную».",
        reply_markup=back_to_main_keyboard(),
    )
    await state.set_state(AIChatStates.waiting_question)


async def process_ai_message(message: types.Message, state: FSMContext):
    """Отправляет текст пользователя на локальный AI-сервер и возвращает ответ."""
    if not message.text:
        await message.answer("Пожалуйста, отправьте вопрос обычным текстом.")
        return

    user_text = message.text.strip()
    if not user_text:
        await message.answer("Сообщение пустое. Напишите вопрос текстом.")
        return

    waiting_message = await message.answer("Думаю над ответом...")
    extra_context = await build_ai_context(message.from_user.id)
    answer = await ask_local_ai(user_text, extra_system_prompt=extra_context)

    try:
        await waiting_message.delete()
    except Exception:
        pass

    await message.answer(answer, reply_markup=back_to_main_keyboard())
    await state.set_state(AIChatStates.waiting_question)
