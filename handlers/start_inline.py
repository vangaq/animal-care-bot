from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import requests as dbreq
from keyboards.main_keyboards import main_reply_keyboard


class StartStates(StatesGroup):
    waiting_owner_name = State()


def build_help_text(owner_name: str | None = None, *, first_time: bool = False) -> str:
    greeting = f"Привет, {owner_name}!\n\n" if owner_name else "Привет!\n\n"
    intro = (
        "Давайте быстро покажу, что умеет бот и с чего удобно начать.\n\n"
        if first_time
        else "Вот короткий навигатор по возможностям бота.\n\n"
    )

    return (
        f"{greeting}"
        f"{intro}"
        "🐾 Профиль\n"
        "— хранит ваше имя и карточки питомцев\n"
        "— позволяет добавить, изменить или удалить питомца\n"
        "— показывает фото, возраст, вид, заметки и другую информацию\n\n"
        "📝 Заметки\n"
        "— помогают записывать важные детали о питомце\n"
        "— можно прикрепить фото\n"
        "— для заметки можно поставить одноразовое напоминание на точную дату и время\n\n"
        "🤖 AI-помощник\n"
        "— отвечает на вопросы о питомцах\n"
        "— учитывает ваш профиль, список питомцев и их заметки\n\n"
        "🗺 Карта\n"
        "— помогает найти рядом ветклиники, зоомагазины и груминг\n\n"
        "ℹ️ О нас\n"
        "— кратко рассказывает о проекте\n\n"
        "Подсказка: эту памятку можно открыть в любой момент командой /help."
    )


async def cmd_start(message: types.Message, state: FSMContext):
    """Команда /start."""
    await state.clear()
    response = await dbreq.get_or_create_user(message.from_user.id)

    if response["status"] != "ok":
        await message.answer("Ошибка при создании профиля: " + response.get("error_msg", "unknown"))
        return

    user = response["data"]["user"]
    owner_name = (user.get("owner_name") or "").strip()

    if not owner_name:
        await message.answer(
            "Привет! Как мне к вам обращаться? Напишите ваше имя.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.set_state(StartStates.waiting_owner_name)
        return

    await message.answer(
        f"Привет, {owner_name}! Рад снова вас видеть. Если захотите быстро вспомнить возможности бота, отправьте /help.",
        reply_markup=main_reply_keyboard(),
    )


async def save_owner_name(message: types.Message, state: FSMContext):
    """Сохраняет имя владельца и открывает главное меню."""
    owner_name = (message.text or "").strip()
    if not owner_name:
        await message.answer("Имя не может быть пустым. Напишите, как к вам обращаться.")
        return

    response = await dbreq.update_user_owner_name(message.from_user.id, owner_name)
    if response["status"] != "ok":
        await message.answer("Не удалось сохранить имя: " + response.get("error_msg", ""))
        return

    await message.answer(
        build_help_text(owner_name, first_time=True),
        reply_markup=main_reply_keyboard(),
    )
    await state.clear()


async def cmd_help(message: types.Message, state: FSMContext):
    """Показывает пользователю памятку по возможностям бота."""
    await state.clear()
    user_response = await dbreq.get_user_by_telegram(message.from_user.id)
    owner_name = ""
    if user_response["status"] == "ok":
        owner_name = (user_response["data"]["user"].get("owner_name") or "").strip()

    await message.answer(build_help_text(owner_name), reply_markup=main_reply_keyboard())


async def cmd_inline(message: types.Message):
    """Команда /inline."""
    inline_links = [
        {"title": "Документация по кошкам", "url": "https://example.com/cats"},
        {"title": "Документация по собакам", "url": "https://example.com/dogs"},
    ]

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=link["title"], url=link["url"])]
            for link in inline_links
        ]
    )

    await message.answer("Полезные ссылки:", reply_markup=keyboard)
