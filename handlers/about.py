from aiogram import types
from aiogram.fsm.context import FSMContext
from keyboards.main_keyboards import back_to_main_keyboard


async def about_project(message: types.Message, state: FSMContext):
    await state.clear()

    text = (
        "✨Питомец под контролем✨\n\n"
        "Это учебный проект, созданный школьниками.\n"
        "Бот помогает вести учёт питомцев и важных заметок о них.\n\n"
        " Что умеет бот:\n"
        "• добавлять питомцев🐾\n"
        "• хранить информацию о них👤\n"
        "• создавать заметки и напоминания📝\n\n"
        "🧠Есть идеи или предложения?\n"
        "Пишите: @ferrffil\n\n"
    )

    await message.answer(text, cancel_handler=back_to_main_keyboard())
