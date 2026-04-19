from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db.models import Base, User, Pet, Note
from config import DB_PATH
from utils.helpers import make_response_ok, make_response_error
from datetime import datetime
import asyncio

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_or_create_user_sync(telegram_id: int):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            session.commit()
            session.refresh(user)
        return make_response_ok(
            {"user": {"id": user.id, "telegram_id": user.telegram_id, "created_at": user.created_at.isoformat()}})
    except Exception as e:
        session.rollback()
        return make_response_error(f"DB error: {e}")
    finally:
        session.close()


def get_user_by_telegram_sync(telegram_id: int):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return make_response_error("Пользователь не найден")
        return make_response_ok(
            {"user": {"id": user.id, "telegram_id": user.telegram_id, "created_at": user.created_at.isoformat()}})
    finally:
        session.close()


def list_pets_for_user_sync(user_id: int):
    session = SessionLocal()
    try:
        pets = session.query(Pet).filter_by(user_id=user_id).order_by(asc(Pet.created_at)).all()
        pets_data = [
            {
                "id": p.id,
                "breed": p.breed,
                "name": p.name,
                "age": p.age,
                "extra_info": p.extra_info or "",
                "created_at": p.created_at.isoformat()
            } for p in pets
        ]
        return make_response_ok({"pets": pets_data})
    finally:
        session.close()


def create_pet_sync(user_id: int, breed: str, name: str, age: str, extra_info: str = None):
    if not (breed and name and age):
        return make_response_error("Обязательные поля для питомца не заполнены (breed, name, age).")
    session = SessionLocal()
    try:
        exists = session.query(Pet).filter_by(user_id=user_id, name=name).first()
        if exists:
            return make_response_error("Питомец с такой кличкой уже существует.")
        pet = Pet(user_id=user_id, breed=breed.strip(), name=name.strip(), age=age.strip(), extra_info=extra_info)
        session.add(pet)
        session.commit()
        session.refresh(pet)
        return make_response_ok({"pet": {
            "id": pet.id,
            "breed": pet.breed,
            "name": pet.name,
            "age": pet.age,
            "extra_info": pet.extra_info or "",
            "created_at": pet.created_at.isoformat()
        }})
    except Exception as e:
        session.rollback()
        return make_response_error(f"DB error: {e}")
    finally:
        session.close()


def get_pet_by_id_sync(pet_id: int):
    session = SessionLocal()
    try:
        pet = session.query(Pet).get(pet_id)
        if not pet:
            return make_response_error("Питомец не найден")
        return make_response_ok({"pet": {
            "id": pet.id, "breed": pet.breed, "name": pet.name, "age": pet.age, "extra_info": pet.extra_info or "",
            "created_at": pet.created_at.isoformat()
        }})
    finally:
        session.close()


def update_pet_field_sync(pet_id: int, field: str, value: str):
    allowed = {"breed", "name", "age", "extra_info"}
    if field not in allowed:
        return make_response_error("Недопустимое поле для изменения")
    session = SessionLocal()
    try:
        pet = session.query(Pet).get(pet_id)
        if not pet:
            return make_response_error("Питомец не найден")
        if field == "name":
            conflict = session.query(Pet).filter(Pet.user_id == pet.user_id, Pet.name == value,
                                                 Pet.id != pet.id).first()
            if conflict:
                return make_response_error("Питомец с такой кличкой уже существует.")
        setattr(pet, field, value)
        session.commit()
        session.refresh(pet)
        return make_response_ok({"pet": {
            "id": pet.id, "breed": pet.breed, "name": pet.name, "age": pet.age, "extra_info": pet.extra_info or ""
        }})
    except Exception as e:
        session.rollback()
        return make_response_error(f"DB error: {e}")
    finally:
        session.close()


def list_notes_for_pet_sync(pet_id: int):
    session = SessionLocal()
    try:
        notes = session.query(Note).filter_by(pet_id=pet_id).order_by(asc(Note.created_at)).all()
        notes_data = [
            {
                "id": n.id,
                "title": n.title,
                "period": n.period,
                "extra_info": n.extra_info or "",
                "created_at": n.created_at.isoformat()
            } for n in notes
        ]
        return make_response_ok({"notes": notes_data})
    finally:
        session.close()


def create_note_sync(pet_id: int, title: str, period: str, extra_info: str = None):
    if not (title and period):
        return make_response_error("Обязательные поля для заметки не заполнены (title, period).")
    valid_periods = {"Не повторять", "6 ч", "День", "Неделя", "Месяц", "Год"}
    if period not in valid_periods:
        return make_response_error("Неправильная периодичность. Выберите одну из: " + ", ".join(valid_periods))
    session = SessionLocal()
    try:
        pet = session.query(Pet).get(pet_id)
        if not pet:
            return make_response_error("Питомец не найден")
        note = Note(pet_id=pet_id, title=title.strip(), period=period, extra_info=extra_info)
        session.add(note)
        session.commit()
        session.refresh(note)
        return make_response_ok({"note": {
            "id": note.id, "title": note.title, "period": note.period, "extra_info": note.extra_info or "",
            "created_at": note.created_at.isoformat()
        }})
    except Exception as e:
        session.rollback()
        return make_response_error(f"DB error: {e}")
    finally:
        session.close()


def delete_note_sync(note_id: int):
    session = SessionLocal()
    try:
        note = session.query(Note).get(note_id)
        if not note:
            return make_response_error("Заметка не найдена")
        session.delete(note)
        session.commit()
        return make_response_ok({"deleted_note_id": note_id})
    except Exception as e:
        session.rollback()
        return make_response_error(f"DB error: {e}")
    finally:
        session.close()


def update_note_field_sync(note_id: int, field: str, value: str):
    allowed = {"title", "period", "extra_info"}
    if field not in allowed:
        return make_response_error("Недопустимое поле для изменения заметки")
    session = SessionLocal()
    try:
        note = session.query(Note).get(note_id)
        if not note:
            return make_response_error("Заметка не найдена")
        if field == "period":
            valid_periods = {"Не повторять", "6 ч", "День", "Неделя", "Месяц", "Год"}
            if value not in valid_periods:
                return make_response_error("Неправильная периодичность.")
        setattr(note, field, value)
        session.commit()
        session.refresh(note)
        return make_response_ok({"note": {
            "id": note.id, "title": note.title, "period": note.period, "extra_info": note.extra_info or ""
        }})
    except Exception as e:
        session.rollback()
        return make_response_error(f"DB error: {e}")
    finally:
        session.close()


async def get_or_create_user(telegram_id: int):
    return await asyncio.to_thread(get_or_create_user_sync, telegram_id)


async def get_user_by_telegram(telegram_id: int):
    return await asyncio.to_thread(get_user_by_telegram_sync, telegram_id)


async def list_pets_for_user(user_id: int):
    return await asyncio.to_thread(list_pets_for_user_sync, user_id)


async def create_pet(user_id: int, breed: str, name: str, age: str, extra_info: str = None):
    return await asyncio.to_thread(create_pet_sync, user_id, breed, name, age, extra_info)


async def get_pet_by_id(pet_id: int):
    return await asyncio.to_thread(get_pet_by_id_sync, pet_id)


async def update_pet_field(pet_id: int, field: str, value: str):
    return await asyncio.to_thread(update_pet_field_sync, pet_id, field, value)


async def list_notes_for_pet(pet_id: int):
    return await asyncio.to_thread(list_notes_for_pet_sync, pet_id)


async def create_note(pet_id: int, title: str, period: str, extra_info: str = None):
    return await asyncio.to_thread(create_note_sync, pet_id, title, period, extra_info)


async def delete_note(note_id: int):
    return await asyncio.to_thread(delete_note_sync, note_id)


async def update_note_field(note_id: int, field: str, value: str):
    return await asyncio.to_thread(update_note_field_sync, note_id, field, value)
