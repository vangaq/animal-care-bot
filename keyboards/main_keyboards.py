from aiogram import types


def main_reply_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="О нас"), types.KeyboardButton(text="Профиль")],
            [types.KeyboardButton(text="Заметки")],
        ],
        resize_keyboard=True
    )
    return kb


def back_to_main_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True
    )
    return kb


def profile_options_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Посмотреть профиль")],
            [types.KeyboardButton(text="Добавить питомца")],
            [types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True
    )
    return kb


def pet_confirm_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Все верно")],
            [types.KeyboardButton(text="Изменить")],
        ],
        resize_keyboard=True
    )
    return kb


def note_period_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Не повторять")],
            [types.KeyboardButton(text="6 ч")],
            [types.KeyboardButton(text="День")],
            [types.KeyboardButton(text="Неделя")],
            [types.KeyboardButton(text="Месяц")],
            [types.KeyboardButton(text="Год")],
        ],
        resize_keyboard=True
    )
    return kb
