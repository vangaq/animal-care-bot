from aiogram import types



def main_reply_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="О нас"), types.KeyboardButton(text="Профиль")],
            [types.KeyboardButton(text="Заметки")],
        ],
        resize_keyboard=True,
    )



def back_to_main_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True,
    )



def profile_options_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Посмотреть профиль")],
            [types.KeyboardButton(text="Добавить питомца")],
            [types.KeyboardButton(text="Изменить информацию о питомце")],
            [types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True,
    )



def pet_confirm_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Все верно")],
            [types.KeyboardButton(text="Изменить")],
            [types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True,
    )



def note_period_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Не повторять")],
            [types.KeyboardButton(text="6 ч")],
            [types.KeyboardButton(text="День")],
            [types.KeyboardButton(text="Неделя")],
            [types.KeyboardButton(text="Месяц")],
            [types.KeyboardButton(text="Год")],
        ],
        resize_keyboard=True,
    )
