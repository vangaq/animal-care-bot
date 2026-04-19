from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import requests as dbreq
from keyboards.main_keyboards import (
    back_to_main_keyboard,
    main_reply_keyboard,
    note_period_keyboard,
    pet_confirm_keyboard,
)


class NoteStates(StatesGroup):
    waiting_pet = State()
    waiting_title = State()
    waiting_period = State()
    waiting_extra = State()
    confirm = State()


async def start_notes(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выберите нужную вам функцию:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Добавить заметку")],
                [types.KeyboardButton(text="На главную")],
            ],
            resize_keyboard=True,
        ),
    )


async def start_add_note(message: types.Message, state: FSMContext):
    if message.text.lower() != "добавить заметку":
        return

    user_response = await dbreq.get_user_by_telegram(message.from_user.id)
    if user_response["status"] != "ok":
        await message.answer("Пользователь не найден.")
        return

    user_id = user_response["data"]["user"]["id"]
    pets_response = await dbreq.list_pets_for_user(user_id)

    if pets_response["status"] != "ok":
        await message.answer("Не удалось получить список питомцев.")
        return

    if not pets_response["data"]["pets"]:
        await message.answer("У вас нет питомцев.", reply_markup=back_to_main_keyboard())
        return

    keyboard = [[types.KeyboardButton(text=pet["name"])] for pet in pets_response["data"]["pets"]]
    keyboard.append([types.KeyboardButton(text="На главную")])

    await message.answer(
        "Выберите питомца для заметки:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(NoteStates.waiting_pet)


async def note_choose_pet(message: types.Message, state: FSMContext):
    await state.update_data(pet_name=message.text.strip())
    await message.answer("Введите название заметки:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(NoteStates.waiting_title)


async def note_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Введите снова:")
        return

    await state.update_data(title=title)
    await message.answer("Выберите периодичность:", reply_markup=note_period_keyboard())
    await state.set_state(NoteStates.waiting_period)


async def note_period(message: types.Message, state: FSMContext):
    valid_periods = {"Не повторять", "6 ч", "День", "Неделя", "Месяц", "Год"}
    if message.text not in valid_periods:
        await message.answer("Выберите периодичность кнопкой.")
        return

    await state.update_data(period=message.text)
    await message.answer("Введите доп. информацию (или «Нет»):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(NoteStates.waiting_extra)


async def note_extra(message: types.Message, state: FSMContext):
    extra = message.text.strip()
    if extra.lower() == "нет":
        extra = ""

    await state.update_data(extra_info=extra)
    data = await state.get_data()

    summary = (
        f"Питомец: {data['pet_name']}\n"
        f"Название: {data['title']}\n"
        f"Периодичность: {data['period']}\n"
        f"Доп. информация: {data['extra_info'] or '-'}"
    )

    await message.answer("Подтвердите данные:\n\n" + summary, reply_markup=pet_confirm_keyboard())
    await state.set_state(NoteStates.confirm)


async def note_confirm(message: types.Message, state: FSMContext):
    text = message.text.lower()

    if text == "все верно":
        data = await state.get_data()

        user_response = await dbreq.get_user_by_telegram(message.from_user.id)
        if user_response["status"] != "ok":
            await message.answer("Пользователь не найден.", reply_markup=back_to_main_keyboard())
            await state.clear()
            return

        user_id = user_response["data"]["user"]["id"]
        pets_response = await dbreq.list_pets_for_user(user_id)
        pet = next((pet for pet in pets_response["data"]["pets"] if pet["name"] == data["pet_name"]), None)

        if not pet:
            await message.answer("Питомец не найден.", reply_markup=back_to_main_keyboard())
            await state.clear()
            return

        response = await dbreq.create_note(
            pet_id=pet["id"],
            title=data["title"],
            period=data["period"],
            extra_info=data["extra_info"],
        )

        if response["status"] == "ok":
            await message.answer("Заметка добавлена 📝")
            await message.answer("Главное меню:", reply_markup=main_reply_keyboard())
        else:
            await message.answer("Ошибка: " + response.get("error_msg", ""))

        await state.clear()
        return

    if text == "изменить":
        await message.answer("Введите название заметки заново:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(NoteStates.waiting_title)
        return

    await message.answer("Операция отменена.", reply_markup=back_to_main_keyboard())
    await state.clear()
