from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import requests as dbreq
from keyboards.main_keyboards import back_to_main_keyboard, main_reply_keyboard, pet_confirm_keyboard


class PetStates(StatesGroup):
    waiting_breed = State()
    waiting_name = State()
    waiting_age = State()
    waiting_extra = State()
    waiting_photo = State()
    confirm = State()


class EditPetStates(StatesGroup):
    waiting_choose_pet = State()
    waiting_field_choice = State()
    waiting_new_value = State()
    waiting_new_photo = State()


class DeletePetStates(StatesGroup):
    waiting_choose_pet = State()
    waiting_confirm = State()


async def show_pet_summary(message: types.Message, state: FSMContext):
    data = await state.get_data()

    summary = (
        f"Порода: {data.get('breed', '')}\n"
        f"Кличка: {data.get('name', '')}\n"
        f"Возраст: {data.get('age', '')}\n"
        f"Доп. информация: {data.get('extra_info') or '-'}\n"
        f"Фото: {'есть' if data.get('photo_file_id') else 'нет'}"
    )

    await message.answer("Подтвердите данные:\n\n" + summary, reply_markup=pet_confirm_keyboard())
    await state.set_state(PetStates.confirm)


async def start_add_pet(message: types.Message, state: FSMContext):
    if message.text.lower() != "добавить питомца":
        return

    await state.clear()
    await message.answer("Введите породу питомца:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(PetStates.waiting_breed)


async def pet_breed(message: types.Message, state: FSMContext):
    breed = message.text.strip()
    if not breed:
        await message.answer("Порода не может быть пустой. Введите породу ещё раз:")
        return

    await state.update_data(breed=breed)
    await message.answer("Введите кличку питомца:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(PetStates.waiting_name)


async def pet_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Кличка не может быть пустой. Введите кличку:")
        return

    await state.update_data(name=name)
    await message.answer("Введите возраст:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(PetStates.waiting_age)


async def pet_age(message: types.Message, state: FSMContext):
    age = message.text.strip()
    if not age:
        await message.answer("Возраст обязателен. Введите возраст:")
        return

    await state.update_data(age=age)
    await message.answer(
        "Введите доп. информацию (или напишите «Нет»).",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(PetStates.waiting_extra)


async def pet_extra_text(message: types.Message, state: FSMContext):
    extra = message.text.strip()
    if extra.lower() == "нет":
        extra = ""

    await state.update_data(extra_info=extra)
    await message.answer(
        "Теперь отправьте фото питомца или напишите «Нет», если фото не нужно.",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(PetStates.waiting_photo)


async def pet_extra_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    extra = (message.caption or "").strip()

    await state.update_data(
        extra_info=extra,
        photo_file_id=photo.file_id,
    )
    await show_pet_summary(message, state)


async def pet_photo_text(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()
    if text not in {"нет", "пропустить", "без фото"}:
        await message.answer("Пожалуйста, отправьте фото или напишите «Нет».")
        return

    await state.update_data(photo_file_id="")
    await show_pet_summary(message, state)


async def pet_photo_input(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    await show_pet_summary(message, state)


async def pet_confirm(message: types.Message, state: FSMContext):
    text = message.text.lower()

    if text == "все верно":
        data = await state.get_data()

        user_response = await dbreq.get_or_create_user(message.from_user.id)
        if user_response["status"] != "ok":
            await message.answer("Ошибка при нахождении профиля: " + user_response.get("error_msg", ""))
            await state.clear()
            return

        user_id = user_response["data"]["user"]["id"]

        create_response = await dbreq.create_pet(
            user_id=user_id,
            breed=data.get("breed", ""),
            name=data.get("name", ""),
            age=data.get("age", ""),
            extra_info=data.get("extra_info"),
            photo_file_id=data.get("photo_file_id"),
        )

        if create_response["status"] == "ok":
            await message.answer("Питомец добавлен 🐾", reply_markup=main_reply_keyboard())
        else:
            await message.answer("Ошибка при добавлении питомца: " + create_response.get("error_msg", ""),
                                 reply_markup=main_reply_keyboard())

        await state.clear()
        return

    if text == "изменить":
        await message.answer("Введите породу заново:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(PetStates.waiting_breed)
        return

    await message.answer("Операция отменена.", reply_markup=back_to_main_keyboard())
    await state.clear()


async def start_edit_pet(message: types.Message, state: FSMContext):
    if message.text.lower() != "изменить информацию о питомце":
        return

    user_response = await dbreq.get_user_by_telegram(message.from_user.id)
    if user_response["status"] != "ok":
        await message.answer("Пользователь не найден.")
        return

    user_id = user_response["data"]["user"]["id"]
    pets_response = await dbreq.list_pets_for_user(user_id)

    if pets_response["status"] != "ok" or not pets_response["data"]["pets"]:
        await message.answer("У вас нет питомцев.")
        return

    keyboard = [[types.KeyboardButton(text=pet["name"])] for pet in pets_response["data"]["pets"]]
    keyboard.append([types.KeyboardButton(text="На главную")])

    await message.answer(
        "Выберите кличку питомца для изменения:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(EditPetStates.waiting_choose_pet)


async def choose_pet_to_edit(message: types.Message, state: FSMContext):
    selected_name = message.text.strip()

    user_response = await dbreq.get_user_by_telegram(message.from_user.id)
    if user_response["status"] != "ok":
        await message.answer("Пользователь не найден.")
        return

    user_id = user_response["data"]["user"]["id"]
    pets_response = await dbreq.list_pets_for_user(user_id)
    pet = next((pet for pet in pets_response["data"]["pets"] if pet["name"] == selected_name), None)

    if not pet:
        await message.answer("Питомец не найден. Попробуйте снова.")
        return

    await state.update_data(edit_pet_id=pet["id"])

    keyboard = [
        [types.KeyboardButton(text="Порода"), types.KeyboardButton(text="Кличка")],
        [types.KeyboardButton(text="Возраст"), types.KeyboardButton(text="Доп. информация")],
        [types.KeyboardButton(text="Фото"), types.KeyboardButton(text="Удалить фото")],
        [types.KeyboardButton(text="На главную")],
    ]

    await message.answer(
        "Выберите поле для изменения:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(EditPetStates.waiting_field_choice)


async def field_choice(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()

    if text == "на главную":
        await message.answer("Возвращаемся на главную.", reply_markup=main_reply_keyboard())
        await state.clear()
        return

    mapping = {
        "порода": "breed",
        "кличка": "name",
        "возраст": "age",
        "доп. информация": "extra_info",
    }

    if text == "фото":
        await message.answer("Отправьте новое фото питомца.", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(EditPetStates.waiting_new_photo)
        return

    if text == "удалить фото":
        data = await state.get_data()
        response = await dbreq.update_pet_field(data.get("edit_pet_id"), "photo_file_id", "")
        if response["status"] == "ok":
            await message.answer("Фото питомца удалено.", reply_markup=main_reply_keyboard())
        else:
            await message.answer("Ошибка при удалении фото: " + response.get("error_msg", ""))
        await state.clear()
        return

    if text not in mapping:
        await message.answer("Неизвестное поле. Выберите снова.")
        return

    await state.update_data(edit_field=mapping[text])
    await message.answer(f"Введите новое значение для поля '{text}':", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(EditPetStates.waiting_new_value)


async def new_value_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pet_id = data.get("edit_pet_id")
    field = data.get("edit_field")
    value = message.text.strip()

    if not value:
        await message.answer("Значение не может быть пустым.")
        return

    response = await dbreq.update_pet_field(pet_id, field, value)
    if response["status"] == "ok":
        await message.answer("Информация обновлена.", reply_markup=main_reply_keyboard())
    else:
        await message.answer("Ошибка при обновлении: " + response.get("error_msg", ""))

    await state.clear()


async def new_pet_photo_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pet_id = data.get("edit_pet_id")
    photo = message.photo[-1]

    response = await dbreq.update_pet_field(pet_id, "photo_file_id", photo.file_id)
    if response["status"] == "ok":
        await message.answer("Фото питомца обновлено.", reply_markup=main_reply_keyboard())
    else:
        await message.answer("Ошибка при обновлении фото: " + response.get("error_msg", ""))

    await state.clear()


async def start_delete_pet(message: types.Message, state: FSMContext):
    if message.text.lower() != "удалить питомца":
        return

    user_response = await dbreq.get_user_by_telegram(message.from_user.id)
    if user_response["status"] != "ok":
        await message.answer("Пользователь не найден.")
        return

    user_id = user_response["data"]["user"]["id"]
    pets_response = await dbreq.list_pets_for_user(user_id)

    if pets_response["status"] != "ok" or not pets_response["data"]["pets"]:
        await message.answer("У вас нет питомцев для удаления.", reply_markup=main_reply_keyboard())
        return

    keyboard = [[types.KeyboardButton(text=pet["name"])] for pet in pets_response["data"]["pets"]]
    keyboard.append([types.KeyboardButton(text="На главную")])

    await message.answer(
        "Выберите питомца, которого нужно удалить:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(DeletePetStates.waiting_choose_pet)


async def choose_pet_to_delete(message: types.Message, state: FSMContext):
    selected_name = message.text.strip()

    user_response = await dbreq.get_user_by_telegram(message.from_user.id)
    if user_response["status"] != "ok":
        await message.answer("Пользователь не найден.")
        return

    user_id = user_response["data"]["user"]["id"]
    pets_response = await dbreq.list_pets_for_user(user_id)
    pet = next((pet for pet in pets_response["data"]["pets"] if pet["name"] == selected_name), None)

    if not pet:
        await message.answer("Питомец не найден. Попробуйте снова.")
        return

    await state.update_data(delete_pet_id=pet["id"], delete_pet_name=pet["name"])
    keyboard = [
        [types.KeyboardButton(text="Удалить")],
        [types.KeyboardButton(text="Отмена")],
        [types.KeyboardButton(text="На главную")],
    ]

    await message.answer(
        f"Подтвердите удаление питомца '{pet['name']}'. Вместе с ним удалятся и его заметки.",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(DeletePetStates.waiting_confirm)


async def confirm_pet_delete(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()

    if text == "удалить":
        data = await state.get_data()
        response = await dbreq.delete_pet(data.get("delete_pet_id"))
        if response["status"] == "ok":
            await message.answer("Питомец удалён.", reply_markup=main_reply_keyboard())
        else:
            await message.answer("Ошибка при удалении: " + response.get("error_msg", ""))
        await state.clear()
        return

    if text == "отмена":
        await message.answer("Удаление отменено.", reply_markup=main_reply_keyboard())
        await state.clear()
        return

    await message.answer("Выберите: 'Удалить', 'Отмена' или 'На главную'.")
