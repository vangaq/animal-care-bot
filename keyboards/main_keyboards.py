from aiogram import types

PET_SPECIES_OPTIONS = [
    "Кошка",
    "Собака",
    "Хомяк",
    "Попугай",
    "Кролик",
    "Черепаха",
    "Другое",
]


def main_reply_keyboard() -> types.ReplyKeyboardMarkup:
    """Главное меню бота."""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Профиль"), types.KeyboardButton(text="Заметки")],
            [types.KeyboardButton(text="Карта"), types.KeyboardButton(text="Посоветоваться с AI")],
            [types.KeyboardButton(text="О нас")],
        ],
        resize_keyboard=True,
    )


def back_to_main_keyboard() -> types.ReplyKeyboardMarkup:
    """Клавиатура с одной кнопкой возврата в главное меню."""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True,
    )


def profile_options_keyboard() -> types.ReplyKeyboardMarkup:
    """Меню раздела 'Профиль'."""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Посмотреть профиль"), types.KeyboardButton(text="Добавить питомца")],
            [types.KeyboardButton(text="Изм. данные питомца"), types.KeyboardButton(text="Удалить питомца")],
            [types.KeyboardButton(text="Изменить имя"), types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True,
    )


def pet_confirm_keyboard() -> types.ReplyKeyboardMarkup:
    """Кнопки подтверждения после ввода данных о питомце или заметке."""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Все верно")],
            [types.KeyboardButton(text="Отмена")],
            [types.KeyboardButton(text="Изменить")]
        ],
        resize_keyboard=True,
    )


def pet_species_keyboard() -> types.ReplyKeyboardMarkup:
    """Кнопки выбора вида питомца."""
    rows = []
    current_row = []
    for option in PET_SPECIES_OPTIONS:
        current_row.append(types.KeyboardButton(text=option))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    rows.append([types.KeyboardButton(text="Отмена")])
    return types.ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def note_period_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
    )


def note_reminder_mode_keyboard() -> types.ReplyKeyboardMarkup:
    """Кнопки выбора режима напоминания для заметки."""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Без напоминания")],
            [types.KeyboardButton(text="Напомнить 1 раз")],
            [types.KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
    )


def notes_menu_keyboard() -> types.ReplyKeyboardMarkup:
    """Меню раздела заметок."""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Добавить заметку"), types.KeyboardButton(text="Изменить заметку")],
            [types.KeyboardButton(text="Удалить заметку"), types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True,
    )


def map_categories_keyboard() -> types.ReplyKeyboardMarkup:
    """Меню раздела карты."""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Ветклиники рядом"), types.KeyboardButton(text="Зоомагазины рядом")],
            [types.KeyboardButton(text="Груминг рядом")],
            [types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True,
    )


def map_input_keyboard() -> types.ReplyKeyboardMarkup:
    """Клавиатура для поиска по геолокации или адресу."""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Отправить местоположение", request_location=True)],
            [types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def location_request_keyboard() -> types.ReplyKeyboardMarkup:
    return map_input_keyboard()
