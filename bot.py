import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, StateFilter
from aiogram import F

from config import BOT_TOKEN
from db.requests import init_db

from handlers.about import about_project
from aiogram.filters import StateFilter


from handlers import start_inline, profile, pet_flow, notes_flow
from handlers.cancel import cancel_handler
from handlers.start_inline import cmd_start, cmd_inline
from handlers.profile import on_text_profile
from handlers.pet_flow import (
    start_add_pet, pet_breed, pet_name, pet_age, pet_extra, pet_confirm,
    start_edit_pet, choose_pet_to_edit, field_choice, new_value_input
)
from handlers.notes_flow import start_notes
from aiogram.filters import StateFilter
from handlers.notes_flow import (
    NoteStates,
    start_add_note,
    note_choose_pet,
    note_title,
    note_period,
    note_extra,
    note_confirm
)


logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в окружении")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

init_db()

dp.message.register(cmd_start, Command(commands=["start"]))
dp.message.register(cmd_inline, Command(commands=["inline"]))

dp.message.register(note_extra, notes_flow.NoteStates.waiting_extra, F.text)

dp.message.register(
    cancel_handler,
    F.text.casefold() == "на главную",
    StateFilter("*")
)

dp.message.register(
    start_add_pet,
    F.text.lower() == "добавить питомца"
)
dp.message.register(pet_breed, pet_flow.PetStates.waiting_breed, F.text)
dp.message.register(pet_name, pet_flow.PetStates.waiting_name, F.text)
dp.message.register(pet_age, pet_flow.PetStates.waiting_age, F.text)
dp.message.register(pet_extra, pet_flow.PetStates.waiting_extra, F.text)
dp.message.register(pet_confirm, pet_flow.PetStates.confirm, F.text)

dp.message.register(
    start_edit_pet,
    F.text.lower() == "изменить информацию о питомце"
)
dp.message.register(choose_pet_to_edit, pet_flow.EditPetStates.waiting_choose_pet, F.text)
dp.message.register(field_choice, pet_flow.EditPetStates.waiting_field_choice, F.text)
dp.message.register(new_value_input, pet_flow.EditPetStates.waiting_new_value, F.text)

dp.message.register(start_notes, F.text.casefold() == "заметки", StateFilter("*"))
dp.message.register(start_add_pet, F.text.casefold() == "добавить питомца", StateFilter("*"))
dp.message.register(start_edit_pet, F.text.casefold() == "изменить информацию о питомце", StateFilter("*"))

dp.message.register(start_add_note, F.text.casefold() == "добавить заметку")
dp.message.register(note_choose_pet, NoteStates.waiting_pet, F.text)
dp.message.register(note_title, NoteStates.waiting_title, F.text)
dp.message.register(note_period, NoteStates.waiting_period, F.text)
dp.message.register(note_extra, NoteStates.waiting_extra, F.text)
dp.message.register(note_confirm, NoteStates.confirm, F.text)
dp.message.register(
    about_project,
    F.text.casefold() == "о нас",
    StateFilter("*")
)

dp.message.register(on_text_profile, F.text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())