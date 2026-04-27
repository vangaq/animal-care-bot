from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import requests as dbreq
from keyboards.main_keyboards import (
    back_to_main_keyboard,
    main_reply_keyboard,
    note_reminder_mode_keyboard,
    notes_menu_keyboard,
    pet_confirm_keyboard,
)

NO_REMINDER_PERIOD = dbreq.NO_REMINDER_PERIOD
ONE_TIME_PERIOD = dbreq.ONE_TIME_PERIOD


class NoteStates(StatesGroup):
    """Состояния сценария добавления заметки."""
    waiting_pet = State()
    waiting_title = State()
    waiting_reminder_mode = State()
    waiting_period = State()
    waiting_custom_period = State()
    waiting_extra = State()
    waiting_photo = State()
    confirm = State()


class EditNoteStates(StatesGroup):
    """Состояния сценария редактирования заметки."""
    waiting_pet = State()
    waiting_note = State()
    waiting_field = State()
    waiting_value = State()
    waiting_reminder_mode = State()
    waiting_period = State()
    waiting_custom_period = State()
    waiting_photo = State()


class DeleteNoteStates(StatesGroup):
    """Состояния сценария удаления заметки."""
    waiting_pet = State()
    waiting_note = State()
    waiting_confirm = State()


async def show_edit_note_fields_menu(message: types.Message, state: FSMContext, notice: str | None = None):
    """Показывает меню выбора полей для редактирования заметки."""
    keyboard = [
        [types.KeyboardButton(text="Название"), types.KeyboardButton(text="Напоминание")],
        [types.KeyboardButton(text="Доп. информация"), types.KeyboardButton(text="Фото")],
        [types.KeyboardButton(text="Удалить фото"), types.KeyboardButton(text="Отмена")],
    ]

    await message.answer(
        notice or "Что нужно изменить в заметке?",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(EditNoteStates.waiting_field)


async def get_current_user_pets(message: types.Message):
    """Возвращает список питомцев текущего пользователя или None при ошибке."""
    user_response = await dbreq.get_user_by_telegram(message.from_user.id)
    if user_response["status"] != "ok":
        await message.answer("Пользователь не найден.")
        return None

    user_id = user_response["data"]["user"]["id"]
    pets_response = await dbreq.list_pets_for_user(user_id)

    if pets_response["status"] != "ok":
        await message.answer("Не удалось получить список питомцев.")
        return None

    return pets_response["data"]["pets"]


async def choose_pet_keyboard(message: types.Message, text: str, state: FSMContext, next_state: State):
    """Показывает список питомцев кнопками."""
    pets = await get_current_user_pets(message)
    if pets is None:
        return False

    if not pets:
        await message.answer("У вас нет питомцев.", reply_markup=back_to_main_keyboard())
        return False

    keyboard = [[types.KeyboardButton(text=pet["name"])] for pet in pets]
    keyboard.append([types.KeyboardButton(text="Отмена")])

    await message.answer(
        text,
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(next_state)
    return True


async def get_pet_by_name_for_user(message: types.Message, pet_name: str):
    """Находит питомца пользователя по имени."""
    pets = await get_current_user_pets(message)
    if pets is None:
        return None
    return next((pet for pet in pets if pet["name"] == pet_name), None)


async def show_note_summary(message: types.Message, state: FSMContext):
    """Показывает итоговую сводку по заметке."""
    data = await state.get_data()
    summary = (
        f"Питомец: {data['pet_name']}\n"
        f"Название: {data['title']}\n"
        f"Напоминание: {dbreq.format_reminder_for_display(data['period'], data.get('next_remind_at'))}\n"
        f"Доп. информация: {data['extra_info'] or '-'}\n"
        f"Фото: {'есть' if data.get('photo_file_id') else 'нет'}"
    )

    await message.answer("Подтвердите данные:\n\n" + summary, reply_markup=pet_confirm_keyboard())
    await state.set_state(NoteStates.confirm)


async def show_notes_for_pet_keyboard(
        message: types.Message,
        state: FSMContext,
        pet_id: int,
        next_state: State,
        ask_text: str,
):
    """Показывает список заметок одного питомца кнопками."""
    notes_response = await dbreq.list_notes_for_pet(pet_id)
    if notes_response["status"] != "ok":
        await message.answer("Не удалось получить заметки.", reply_markup=main_reply_keyboard())
        return False

    notes = notes_response["data"]["notes"]
    if not notes:
        await message.answer("У этого питомца пока нет заметок.", reply_markup=main_reply_keyboard())
        return False

    keyboard = [
        [types.KeyboardButton(text=f"#{note['id']} | {note['title']}")] for note in notes
    ]
    keyboard.append([types.KeyboardButton(text="Отмена")])

    await message.answer(
        ask_text,
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(next_state)
    return True


def parse_note_id_from_button(text: str) -> int | None:
    """Достаёт ID заметки из текста кнопки вида."""
    value = text.strip()
    if not value.startswith("#"):
        return None

    note_id_text = value.split("|", maxsplit=1)[0].replace("#", "").strip()
    if not note_id_text.isdigit():
        return None

    return int(note_id_text)


async def start_notes(message: types.Message, state: FSMContext):
    """Открывает раздел 'Заметки'."""
    await state.clear()
    await message.answer("Выберите нужную вам функцию:", reply_markup=notes_menu_keyboard())


async def start_add_note(message: types.Message, state: FSMContext):
    """Запускает сценарий добавления заметки."""
    if message.text.lower() != "добавить заметку":
        return

    await choose_pet_keyboard(message, "Выберите питомца для заметки:", state, NoteStates.waiting_pet)


async def note_choose_pet(message: types.Message, state: FSMContext):
    """Сохраняет выбранного питомца."""
    pet = await get_pet_by_name_for_user(message, message.text.strip())
    if not pet:
        await message.answer("Питомец не найден. Выберите питомца кнопкой.")
        return

    await state.update_data(pet_id=pet["id"], pet_name=pet["name"])
    await message.answer("Введите название заметки:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(NoteStates.waiting_title)


async def note_title(message: types.Message, state: FSMContext):
    """Сохраняет заголовок заметки."""
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Введите снова:")
        return

    await state.update_data(title=title)
    await message.answer("Как работать с напоминанием?", reply_markup=note_reminder_mode_keyboard())
    await state.set_state(NoteStates.waiting_reminder_mode)


async def note_reminder_mode(message: types.Message, state: FSMContext):
    """Сохраняет режим напоминания и при необходимости просит точную дату."""
    text = message.text.strip()

    if text == "Без напоминания":
        await state.update_data(period=NO_REMINDER_PERIOD, next_remind_at="")
        await message.answer(
            "Введите доп. информацию (или напишите «Нет»).",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.set_state(NoteStates.waiting_extra)
        return

    if text != "Напомнить 1 раз":
        await message.answer("Выберите вариант кнопкой.")
        return

    await state.update_data(period=ONE_TIME_PERIOD)
    await message.answer(
        "Введите точные дату и время напоминания.\n"
        "Примеры: 25.12.2026 18:30 или 2026-12-25 18:30",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(NoteStates.waiting_period)


async def note_period(message: types.Message, state: FSMContext):
    """Сохраняет точную дату и время одноразового напоминания."""
    remind_at = dbreq.parse_reminder_datetime_input(message.text)
    if remind_at is None:
        await message.answer(
            "Не понял дату и время.\n"
            "Напишите так: 25.12.2026 18:30 или 2026-12-25 18:30"
        )
        return

    await state.update_data(next_remind_at=remind_at.isoformat(), period=ONE_TIME_PERIOD)
    await message.answer(
        "Введите доп. информацию (или напишите «Нет»).",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(NoteStates.waiting_extra)


async def note_custom_period(message: types.Message, state: FSMContext):
    await note_period(message, state)


async def note_extra_text(message: types.Message, state: FSMContext):
    """Сохраняет текст доп. информации и предлагает отправить фото."""
    extra = message.text.strip()
    if extra.lower() == "нет":
        extra = ""

    await state.update_data(extra_info=extra)
    await message.answer("Теперь отправьте фото или напишите «Нет».", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(NoteStates.waiting_photo)


async def note_extra_photo(message: types.Message, state: FSMContext):
    """Позволяет сразу отправить фото на шаге доп. информации."""
    photo = message.photo[-1]
    extra = (message.caption or "").strip()

    await state.update_data(extra_info=extra, photo_file_id=photo.file_id)
    await show_note_summary(message, state)


async def note_photo_text(message: types.Message, state: FSMContext):
    """Обрабатывает отказ от фото после ввода текста."""
    text = message.text.strip().lower()
    if text not in {"нет", "пропустить", "без фото"}:
        await message.answer("Пожалуйста, отправьте фото или напишите «Нет».")
        return

    await state.update_data(photo_file_id="")
    await show_note_summary(message, state)


async def note_photo_input(message: types.Message, state: FSMContext):
    """Сохраняет фото заметки перед подтверждением."""
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    await show_note_summary(message, state)


async def note_confirm(message: types.Message, state: FSMContext):
    """Финальный шаг: создаёт заметку или отправляет на повторный ввод."""
    text = message.text.lower()

    if text == "все верно":
        data = await state.get_data()

        response = await dbreq.create_note(
            pet_id=data["pet_id"],
            title=data["title"],
            period=data["period"],
            extra_info=data.get("extra_info"),
            photo_file_id=data.get("photo_file_id"),
            next_remind_at=data.get("next_remind_at"),
        )

        if response["status"] == "ok":
            await message.answer("Заметка добавлена 📝", reply_markup=main_reply_keyboard())
        else:
            await message.answer("Ошибка: " + response.get("error_msg", ""))

        await state.clear()
        return

    if text == "изменить":
        await message.answer("Введите название заметки заново:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(NoteStates.waiting_title)
        return

    await state.clear()
    await message.answer("Операция отменена.", reply_markup=main_reply_keyboard())


async def start_edit_note(message: types.Message, state: FSMContext):
    """Запускает сценарий добавления заметки."""
    if message.text.lower() != "изменить заметку":
        return

    await choose_pet_keyboard(
        message,
        "Выберите питомца, у которого хотите изменить заметку:",
        state,
        EditNoteStates.waiting_pet,
    )


async def edit_note_choose_pet(message: types.Message, state: FSMContext):
    """Сохраняет питомца и показывает его заметки."""
    pet = await get_pet_by_name_for_user(message, message.text.strip())
    if not pet:
        await message.answer("Питомец не найден. Выберите питомца кнопкой.")
        return

    await state.update_data(edit_pet_id=pet["id"], edit_pet_name=pet["name"])
    await show_notes_for_pet_keyboard(
        message,
        state,
        pet["id"],
        EditNoteStates.waiting_note,
        "Выберите заметку для изменения:",
    )


async def edit_note_choose_note(message: types.Message, state: FSMContext):
    """Сохраняет заметку, которую нужно изменить."""
    note_id = parse_note_id_from_button(message.text)
    if note_id is None:
        await message.answer("Выберите заметку кнопкой.")
        return

    note_response = await dbreq.get_note_by_id(note_id)
    if note_response["status"] != "ok":
        await message.answer("Заметка не найдена.")
        return

    note = note_response["data"]["note"]
    data = await state.get_data()
    if note["pet_id"] != data.get("edit_pet_id"):
        await message.answer("Эта заметка не относится к выбранному питомцу.")
        return

    await state.update_data(edit_note_id=note_id)
    await show_edit_note_fields_menu(message, state)


async def edit_note_choose_field(message: types.Message, state: FSMContext):
    """Определяет поле заметки для изменения."""
    text = message.text.strip().lower()

    if text == "на главную":
        await message.answer("Возвращаемся на главную.", reply_markup=main_reply_keyboard())
        await state.clear()
        return

    mapping = {
        "название": "title",
        "доп. информация": "extra_info",
    }

    if text == "напоминание":
        await message.answer("Как изменить напоминание?", reply_markup=note_reminder_mode_keyboard())
        await state.set_state(EditNoteStates.waiting_reminder_mode)
        return

    if text == "фото":
        await message.answer("Отправьте новое фото для заметки.", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(EditNoteStates.waiting_photo)
        return

    if text == "удалить фото":
        data = await state.get_data()
        response = await dbreq.update_note_field(data.get("edit_note_id"), "photo_file_id", "")
        if response["status"] == "ok":
            await show_edit_note_fields_menu(message, state, "Фото заметки удалено. Выберите следующее поле:")
        else:
            await message.answer("Ошибка при удалении фото: " + response.get("error_msg", ""))
        return

    if text not in mapping:
        await message.answer("Неизвестное поле. Выберите снова.")
        return

    await state.update_data(edit_field=mapping[text])
    await message.answer("Введите новое значение:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(EditNoteStates.waiting_value)


async def edit_note_new_value(message: types.Message, state: FSMContext):
    """Сохраняет новое текстовое значение поля заметки."""
    value = message.text.strip()
    if not value:
        await message.answer("Значение не может быть пустым.")
        return

    data = await state.get_data()
    response = await dbreq.update_note_field(data.get("edit_note_id"), data.get("edit_field"), value)
    if response["status"] == "ok":
        await show_edit_note_fields_menu(message, state, "Заметка обновлена. Выберите следующее поле:")
    else:
        await message.answer("Ошибка при обновлении: " + response.get("error_msg", ""))


async def edit_note_reminder_mode(message: types.Message, state: FSMContext):
    """Сохраняет новый режим напоминания перед вводом точной даты."""
    text = message.text.strip()
    data = await state.get_data()

    if text == "Без напоминания":
        response = await dbreq.update_note_reminder(data.get("edit_note_id"), NO_REMINDER_PERIOD, None)
        if response["status"] == "ok":
            await show_edit_note_fields_menu(message, state, "Режим напоминания обновлён. Выберите следующее поле:")
        else:
            await message.answer("Ошибка при обновлении: " + response.get("error_msg", ""))
        return

    if text != "Напомнить 1 раз":
        await message.answer("Выберите вариант кнопкой.")
        return

    await message.answer(
        "Введите новые дату и время напоминания.\n"
        "Примеры: 25.12.2026 18:30 или 2026-12-25 18:30",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(EditNoteStates.waiting_period)


async def edit_note_new_period(message: types.Message, state: FSMContext):
    """Сохраняет новую точную дату и время напоминания."""
    remind_at = dbreq.parse_reminder_datetime_input(message.text)
    if remind_at is None:
        await message.answer(
            "Не понял дату и время.\n"
            "Напишите так: 25.12.2026 18:30 или 2026-12-25 18:30"
        )
        return

    data = await state.get_data()
    response = await dbreq.update_note_reminder(
        data.get("edit_note_id"),
        ONE_TIME_PERIOD,
        remind_at.isoformat(),
    )
    if response["status"] == "ok":
        await show_edit_note_fields_menu(message, state, "Напоминание заметки обновлено. Выберите следующее поле:")
    else:
        await message.answer("Ошибка при обновлении: " + response.get("error_msg", ""))


async def edit_note_custom_period(message: types.Message, state: FSMContext):
    await edit_note_new_period(message, state)


async def edit_note_new_photo(message: types.Message, state: FSMContext):
    """Сохраняет новое фото заметки."""
    data = await state.get_data()
    photo = message.photo[-1]
    response = await dbreq.update_note_field(data.get("edit_note_id"), "photo_file_id", photo.file_id)

    if response["status"] == "ok":
        await show_edit_note_fields_menu(message, state, "Фото заметки обновлено. Выберите следующее поле:")
    else:
        await message.answer("Ошибка при обновлении фото: " + response.get("error_msg", ""))


async def start_delete_note(message: types.Message, state: FSMContext):
    """Запускает сценарий удаления заметки."""
    if message.text.lower() != "удалить заметку":
        return

    await choose_pet_keyboard(
        message,
        "Выберите питомца, у которого хотите удалить заметку:",
        state,
        DeleteNoteStates.waiting_pet,
    )


async def delete_note_choose_pet(message: types.Message, state: FSMContext):
    """Сохраняет питомца и показывает список его заметок."""
    pet = await get_pet_by_name_for_user(message, message.text.strip())
    if not pet:
        await message.answer("Питомец не найден. Выберите питомца кнопкой.")
        return

    await state.update_data(delete_pet_id=pet["id"], delete_pet_name=pet["name"])
    await show_notes_for_pet_keyboard(
        message,
        state,
        pet["id"],
        DeleteNoteStates.waiting_note,
        "Выберите заметку для удаления:",
    )


async def delete_note_choose_note(message: types.Message, state: FSMContext):
    note_id = parse_note_id_from_button(message.text)
    if note_id is None:
        await message.answer("Выберите заметку кнопкой.")
        return

    note_response = await dbreq.get_note_by_id(note_id)
    if note_response["status"] != "ok":
        await message.answer("Заметка не найдена.")
        return

    note = note_response["data"]["note"]
    data = await state.get_data()
    if note["pet_id"] != data.get("delete_pet_id"):
        await message.answer("Эта заметка не относится к выбранному питомцу.")
        return

    await state.update_data(delete_note_id=note_id, delete_note_title=note["title"])

    keyboard = [
        [types.KeyboardButton(text="Удалить")],
        [types.KeyboardButton(text="Отмена")],
    ]

    await message.answer(
        f"Подтвердите удаление заметки '{note['title']}'.",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(DeleteNoteStates.waiting_confirm)


async def delete_note_confirm(message: types.Message, state: FSMContext):
    """Удаляет заметку после подтверждения."""
    text = message.text.strip().lower()

    if text == "удалить":
        data = await state.get_data()
        response = await dbreq.delete_note(data.get("delete_note_id"))
        if response["status"] == "ok":
            await message.answer("Заметка удалена.", reply_markup=main_reply_keyboard())
        else:
            await message.answer("Ошибка при удалении: " + response.get("error_msg", ""))
        await state.clear()
        return

    if text == "отмена":
        await message.answer("Удаление отменено.", reply_markup=main_reply_keyboard())
        await state.clear()
        return

    await message.answer("Выберите: 'Удалить' или 'Отмена'.")
