from __future__ import annotations

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.main_keyboards import back_to_main_keyboard
from utils.ai_client import ask_local_ai


class AIChatStates(StatesGroup):

    waiting_question = State()


async def start_ai_chat(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Режим AI включён. Напишите ваш вопрос текстом.\n"
        "Чтобы выйти, нажмите «На главную».",
        reply_markup=back_to_main_keyboard(),
    )
    await state.set_state(AIChatStates.waiting_question)


async def process_ai_message(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, отправьте вопрос обычным текстом.")
        return

    user_text = message.text.strip()
    if not user_text:
        await message.answer("Сообщение пустое. Напишите вопрос текстом.")
        return

    waiting_message = await message.answer("Думаю над ответом...")
    answer = await ask_local_ai(user_text)

    try:
        await waiting_message.delete()
    except Exception:
        pass

    await message.answer(answer, reply_markup=back_to_main_keyboard())
    await state.set_state(AIChatStates.waiting_question)
