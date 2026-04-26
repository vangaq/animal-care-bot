from aiogram import types
from aiogram.fsm.context import FSMContext

from keyboards.main_keyboards import main_reply_keyboard


async def about_project(message: types.Message, state: FSMContext):
    await state.clear()

    text = (
        "✨ Питомец под контролем ✨\n\n"
        "Это учебный проект, созданный школьниками.\n"
        "Мы сделали бота, который помогает удобно организовать всё самое важное о питомце в одном месте.\n\n"
        "С помощью бота вы можете:\n"
        "• добавлять питомцев и сохранять информацию о них\n"
        "• записывать важные заметки\n"
        "• ставить напоминания\n"
        "• получать ответы и советы от AI-помощника\n"
        "• пользоваться картой для поиска нужных мест\n"
        "• хранить и редактировать данные профиля\n\n"
        "Есть идеи или предложения?\n"
        "Пишите: @ferrffil\n"
    )

    await message.answer(text, reply_markup=main_reply_keyboard())
