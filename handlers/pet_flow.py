from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import requests as dbreq
from keyboards.main_keyboards import (
    PET_SPECIES_OPTIONS,
    main_reply_keyboard,
    pet_confirm_keyboard,
    pet_species_keyboard,
)
from utils.helpers import (
    get_species_detail_empty_text,
    get_species_detail_label,
    get_species_detail_prompt,
)


class PetStates(StatesGroup):
    """Состояния сценария добавления питомца."""
    waiting_species = State()
    waiting_breed = State()
    waiting_name = State()
    waiting_age = State()
    waiting_extra = State()
    waiting_photo = State()
    confirm = State()


class EditPetStates(StatesGroup):
    """Состояния сценария редактирования питомца."""
    waiting_choose_pet = State()
    waiting_field_choice = State()
    waiting_new_value = State()
    waiting_new_photo = State()


class DeletePetStates(StatesGroup):
    """Состояния сценария удаления питомца."""
    waiting_choose_pet = State()
    waiting_confirm = State()


async def show_edit_pet_fields_menu(message: types.Message, state: FSMContext, notice: str | None = None):
    """Показывает меню выбора полей для редактирования питомца."""
    data = await state.get_data()
    detail_button_text = get_species_detail_label(data.get("edit_species"))
    await state.update_data(edit_detail_button=detail_button_text.lower())

    keyboard = [
        [types.KeyboardButton(text="Вид"), types.KeyboardButton(text=detail_button_text)],
        [types.KeyboardButton(text="Кличка"), types.KeyboardButton(text="Возраст")],
        [types.KeyboardButton(text="Доп. информация"), types.KeyboardButton(text="Фото")],
        [types.KeyboardButton(text="Удалить фото"), types.KeyboardButton(text="Отмена")],
    ]

    await message.answer(
        notice or "Выберите поле для изменения:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(EditPetStates.waiting_field_choice)


async def show_pet_summary(message: types.Message, state: FSMContext):
    """Показывает итоговую сводку по питомцу перед сохранением."""
    data = await state.get_data()
    species = data.get("species", "")
    detail_label = get_species_detail_label(species)

    summary = (
        f"Вид: {species}\n"
        f"{detail_label}: {data.get('breed', '')}\n"
        f"Кличка: {data.get('name', '')}\n"
        f"Возраст: {data.get('age', '')}\n"
        f"Доп. информация: {data.get('extra_info') or '-'}\n"
        f"Фото: {'есть' if data.get('photo_file_id') else 'нет'}"
    )

    await message.answer("Подтвердите данные:\n\n" + summary, reply_markup=pet_confirm_keyboard())
    await state.set_state(PetStates.confirm)


async def start_add_pet(message: types.Message, state: FSMContext):
    """Запускает сценарий добавления питомца."""
    if message.text.lower() != "добавить питомца":
        return

    await state.clear()
    await message.answer("Выберите, кто это:", reply_markup=pet_species_keyboard())
    await state.set_state(PetStates.waiting_species)


async def pet_species(message: types.Message, state: FSMContext):
    """Сохраняет вид питомца и переходит к уточняющему полю."""
    species = message.text.strip()
    if species not in PET_SPECIES_OPTIONS:
        await message.answer("Выберите вид питомца кнопкой.")
        return

    await state.update_data(species=species)
    await message.answer(get_species_detail_prompt(species), reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(PetStates.waiting_breed)


async def pet_breed(message: types.Message, state: FSMContext):
    """Сохраняет уточнение по виду/породе и переходит к запросу клички."""
    breed = message.text.strip()
    data = await state.get_data()
    species = data.get("species")
    if not breed:
        await message.answer(get_species_detail_empty_text(species))
        return

    await state.update_data(breed=breed)
    await message.answer("Введите кличку питомца:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(PetStates.waiting_name)


async def pet_name(message: types.Message, state: FSMContext):
    """Сохраняет кличку и переходит к возрасту."""
    name = message.text.strip()
    if not name:
        await message.answer("Кличка не может быть пустой. Введите кличку:")
        return

    await state.update_data(name=name)
    await message.answer("Введите возраст:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(PetStates.waiting_age)


async def pet_age(message: types.Message, state: FSMContext):
    """Сохраняет возраст и переходит к дополнительной информации."""
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
    """Сохраняет текст доп. информации и предлагает отправить фото."""
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
    """Позволяет сразу отправить фото на шаге доп. информации."""
    photo = message.photo[-1]
    extra = (message.caption or "").strip()

    await state.update_data(
        extra_info=extra,
        photo_file_id=photo.file_id,
    )
    await show_pet_summary(message, state)


async def pet_photo_text(message: types.Message, state: FSMContext):
    """Обрабатывает отказ от фото после ввода текста."""
    text = message.text.strip().lower()
    if text not in {"нет", "пропустить", "без фото"}:
        await message.answer("Пожалуйста, отправьте фото или напишите «Нет».")
        return

    await state.update_data(photo_file_id="")
    await show_pet_summary(message, state)


async def pet_photo_input(message: types.Message, state: FSMContext):
    """Сохраняет фото питомца перед подтверждением."""
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    await show_pet_summary(message, state)


async def pet_confirm(message: types.Message, state: FSMContext):
    """Финальный шаг: сохраняет питомца или отправляет пользователя на повторный ввод."""
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
            species=data.get("species", ""),
            breed=data.get("breed", ""),
            name=data.get("name", ""),
            age=data.get("age", ""),
            extra_info=data.get("extra_info"),
            photo_file_id=data.get("photo_file_id"),
        )

        if create_response["status"] == "ok":
            await message.answer("Питомец добавлен 🐾", reply_markup=main_reply_keyboard())
        else:
            await message.answer(
                "Ошибка при добавлении питомца: " + create_response.get("error_msg", ""),
                reply_markup=main_reply_keyboard(),
            )

        await state.clear()
        return

    if text == "изменить":
        await message.answer("Выберите вид питомца заново:", reply_markup=pet_species_keyboard())
        await state.set_state(PetStates.waiting_species)
        return

    await state.clear()
    await message.answer("Операция отменена.", reply_markup=main_reply_keyboard())


async def start_edit_pet(message: types.Message, state: FSMContext):
    """Запускает сценарий редактирования уже существующего питомца."""
    if message.text.lower() != "изм. данные питомца":
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
    keyboard.append([types.KeyboardButton(text="Отмена")])

    await message.answer(
        "Выберите кличку питомца для изменения:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(EditPetStates.waiting_choose_pet)


async def choose_pet_to_edit(message: types.Message, state: FSMContext):
    """Определяет, какого именно питомца пользователь хочет изменить."""
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

    detail_button_text = get_species_detail_label(pet.get("species"))
    await state.update_data(
        edit_pet_id=pet["id"],
        edit_species=pet.get("species") or "",
        edit_detail_button=detail_button_text.lower(),
    )

    await show_edit_pet_fields_menu(message, state)


async def field_choice(message: types.Message, state: FSMContext):
    """Сохраняет, какое поле пользователь хочет изменить."""
    raw_text = message.text.strip()
    text = raw_text.lower()
    data = await state.get_data()
    detail_button_text = data.get("edit_detail_button", "порода")

    if text == "на главную":
        await message.answer("Возвращаемся на главную.", reply_markup=main_reply_keyboard())
        await state.clear()
        return

    mapping = {
        "вид": "species",
        "кличка": "name",
        "возраст": "age",
        "доп. информация": "extra_info",
    }
    mapping[detail_button_text] = "breed"

    if text == "фото":
        await message.answer("Отправьте новое фото питомца.", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(EditPetStates.waiting_new_photo)
        return

    if text == "удалить фото":
        response = await dbreq.update_pet_field(data.get("edit_pet_id"), "photo_file_id", "")
        if response["status"] == "ok":
            await show_edit_pet_fields_menu(message, state, "Фото питомца удалено. Выберите следующее поле:")
        else:
            await message.answer("Ошибка при удалении фото: " + response.get("error_msg", ""))
        return

    if text not in mapping:
        await message.answer("Неизвестное поле. Выберите снова.")
        return

    field = mapping[text]
    await state.update_data(edit_field=field)
    if field == "species":
        await message.answer("Выберите новый вид питомца:", reply_markup=pet_species_keyboard())
    elif field == "breed":
        await message.answer(
            get_species_detail_prompt(data.get("edit_species")),
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        await message.answer(f"Введите новое значение для поля '{raw_text}':", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(EditPetStates.waiting_new_value)


async def new_value_input(message: types.Message, state: FSMContext):
    """Сохраняет новое значение выбранного поля питомца."""
    data = await state.get_data()
    pet_id = data.get("edit_pet_id")
    field = data.get("edit_field")
    value = message.text.strip()

    if not value:
        if field == "breed":
            await message.answer(get_species_detail_empty_text(data.get("edit_species")))
        else:
            await message.answer("Значение не может быть пустым.")
        return

    if field == "species":
        if value not in PET_SPECIES_OPTIONS:
            await message.answer("Выберите вид питомца кнопкой.")
            return
        await state.update_data(edit_species=value)

    response = await dbreq.update_pet_field(pet_id, field, value)
    if response["status"] == "ok":
        await show_edit_pet_fields_menu(message, state, "Информация обновлена. Выберите следующее поле:")
    else:
        await message.answer("Ошибка при обновлении: " + response.get("error_msg", ""))


async def new_pet_photo_input(message: types.Message, state: FSMContext):
    """Сохраняет новое фото для существующего питомца."""
    data = await state.get_data()
    pet_id = data.get("edit_pet_id")
    photo = message.photo[-1]

    response = await dbreq.update_pet_field(pet_id, "photo_file_id", photo.file_id)
    if response["status"] == "ok":
        await show_edit_pet_fields_menu(message, state, "Фото питомца обновлено. Выберите следующее поле:")
    else:
        await message.answer("Ошибка при обновлении фото: " + response.get("error_msg", ""))


async def start_delete_pet(message: types.Message, state: FSMContext):
    """Запускает сценарий удаления питомца."""
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
    keyboard.append([types.KeyboardButton(text="Отмена")])

    await message.answer(
        "Выберите питомца, которого нужно удалить:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(DeletePetStates.waiting_choose_pet)


async def choose_pet_to_delete(message: types.Message, state: FSMContext):
    """Сохраняет питомца, которого пользователь хочет удалить."""
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
    ]

    await message.answer(
        f"Подтвердите удаление питомца '{pet['name']}'. Вместе с ним удалятся и его заметки.",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
    )
    await state.set_state(DeletePetStates.waiting_confirm)


async def confirm_pet_delete(message: types.Message, state: FSMContext):
    """Удаляет питомца после подтверждения."""
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

    await message.answer("Выберите: 'Удалить' или 'Отмена'.")
