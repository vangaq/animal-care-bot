from aiogram import types
from aiogram.fsm.context import FSMContext
from keyboards.main_keyboards import main_reply_keyboard


async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено. Возвращаемся на главную",
        reply_markup=main_reply_keyboard()
    )
