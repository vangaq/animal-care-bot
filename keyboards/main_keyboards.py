from aiogram import types


def main_reply_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="О нас"), types.KeyboardButton(text="Профиль")],
            [types.KeyboardButton(text="Заметки"), types.KeyboardButton(text="Карта")],
            [types.KeyboardButton(text="Посоветоваться с AI")],
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
            [types.KeyboardButton(text="Посмотреть профиль"), types.KeyboardButton(text="Добавить питомца")],
            [types.KeyboardButton(text="Изм. данные питомца"), types.KeyboardButton(text="Удалить питомца")],
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
            [types.KeyboardButton(text="Не повторять"), types.KeyboardButton(text="6 ч")],
            [types.KeyboardButton(text="День"), types.KeyboardButton(text="Неделя")],
            [types.KeyboardButton(text="Месяц"), types.KeyboardButton(text="Год")],
        ],
        resize_keyboard=True,
    )


def notes_menu_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Добавить заметку"), types.KeyboardButton(text="Изменить заметку")],
            [types.KeyboardButton(text="Удалить заметку"), types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True,
    )


def map_categories_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Ветклиники рядом"), types.KeyboardButton(text="Зоомагазины рядом")],
            [types.KeyboardButton(text="Груминг рядом")],
            [types.KeyboardButton(text="На главную")],
        ],
        resize_keyboard=True,
    )


def map_input_keyboard() -> types.ReplyKeyboardMarkup:
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
