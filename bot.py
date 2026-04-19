import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db.requests import init_db
from handlers.about import about_project
from handlers.cancel import cancel_handler
from handlers.notes_flow import (
    NoteStates,
    note_choose_pet,
    note_confirm,
    note_extra,
    note_period,
    note_title,
    start_add_note,
    start_notes,
)
from handlers.pet_flow import (
    EditPetStates,
    PetStates,
    choose_pet_to_edit,
    field_choice,
    new_value_input,
    pet_age,
    pet_breed,
    pet_confirm,
    pet_extra,
    pet_name,
    start_add_pet,
    start_edit_pet,
)
from handlers.profile import on_text_profile
from handlers.start_inline import cmd_inline, cmd_start

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не задан. Создайте файл .env и укажите в нём BOT_TOKEN=..."
    )

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

init_db()


dp.message.register(cmd_start, Command(commands=["start"]))
dp.message.register(cmd_inline, Command(commands=["inline"]))


dp.message.register(cancel_handler, F.text.casefold() == "на главную", StateFilter("*"))


dp.message.register(start_add_pet, F.text.casefold() == "добавить питомца", StateFilter("*"))
dp.message.register(pet_breed, PetStates.waiting_breed, F.text)
dp.message.register(pet_name, PetStates.waiting_name, F.text)
dp.message.register(pet_age, PetStates.waiting_age, F.text)
dp.message.register(pet_extra, PetStates.waiting_extra, F.text)
dp.message.register(pet_confirm, PetStates.confirm, F.text)


dp.message.register(
    start_edit_pet,
    F.text.casefold() == "изменить информацию о питомце",
    StateFilter("*"),
)
dp.message.register(choose_pet_to_edit, EditPetStates.waiting_choose_pet, F.text)
dp.message.register(field_choice, EditPetStates.waiting_field_choice, F.text)
dp.message.register(new_value_input, EditPetStates.waiting_new_value, F.text)


dp.message.register(start_notes, F.text.casefold() == "заметки", StateFilter("*"))
dp.message.register(start_add_note, F.text.casefold() == "добавить заметку")
dp.message.register(note_choose_pet, NoteStates.waiting_pet, F.text)
dp.message.register(note_title, NoteStates.waiting_title, F.text)
dp.message.register(note_period, NoteStates.waiting_period, F.text)
dp.message.register(note_extra, NoteStates.waiting_extra, F.text)
dp.message.register(note_confirm, NoteStates.confirm, F.text)


dp.message.register(about_project, F.text.casefold() == "о нас", StateFilter("*"))

dp.message.register(on_text_profile, F.text)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
