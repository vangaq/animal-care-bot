import asyncio

from sqlalchemy import asc, create_engine, inspect
from sqlalchemy.orm import sessionmaker

from config import DB_PATH
from db.models import Base, Note, Pet, User
from utils.helpers import make_response_error, make_response_ok

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

VALID_PERIODS = {"Не повторять", "6 ч", "День", "Неделя", "Месяц", "Год"}


def serialize_pet(pet: Pet) -> dict:
    return {
        "id": pet.id,
        "breed": pet.breed,
        "name": pet.name,
        "age": pet.age,
        "extra_info": pet.extra_info or "",
        "photo_file_id": pet.photo_file_id or "",
        "created_at": pet.created_at.isoformat(),
    }


def serialize_note(note: Note) -> dict:
    return {
        "id": note.id,
        "pet_id": note.pet_id,
        "title": note.title,
        "period": note.period,
        "extra_info": note.extra_info or "",
        "photo_file_id": note.photo_file_id or "",
        "created_at": note.created_at.isoformat(),
    }


def ensure_schema():
    required_columns = {
        "pets": {"photo_file_id": "VARCHAR"},
        "notes": {"photo_file_id": "VARCHAR"},
    }

    for table_name, columns in required_columns.items():
        inspector = inspect(engine)
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}

        for column_name, column_type in columns.items():
            if column_name not in existing_columns:
                with engine.begin() as connection:
                    connection.exec_driver_sql(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    )


def init_db():
    Base.metadata.create_all(bind=engine)
    ensure_schema()


# Работа с пользователями
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
            {
                "user": {
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "created_at": user.created_at.isoformat(),
                }
            }
        )
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


def get_user_by_telegram_sync(telegram_id: int):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()

        if not user:
            return make_response_error("Пользователь не найден")

        return make_response_ok(
            {
                "user": {
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "created_at": user.created_at.isoformat(),
                }
            }
        )
    finally:
        session.close()


def list_pets_for_user_sync(user_id: int):
    session = SessionLocal()
    try:
        pets = session.query(Pet).filter_by(user_id=user_id).order_by(asc(Pet.created_at)).all()
        return make_response_ok({"pets": [serialize_pet(pet) for pet in pets]})
    finally:
        session.close()


def create_pet_sync(
        user_id: int,
        breed: str,
        name: str,
        age: str,
        extra_info: str | None = None,
        photo_file_id: str | None = None,
):
    if not (breed and name and age):
        return make_response_error("Обязательные поля для питомца не заполнены (breed, name, age).")

    session = SessionLocal()
    try:
        exists = session.query(Pet).filter_by(user_id=user_id, name=name.strip()).first()
        if exists:
            return make_response_error("Питомец с такой кличкой уже существует.")

        pet = Pet(
            user_id=user_id,
            breed=breed.strip(),
            name=name.strip(),
            age=age.strip(),
            extra_info=(extra_info or "").strip(),
            photo_file_id=photo_file_id,
        )
        session.add(pet)
        session.commit()
        session.refresh(pet)

        return make_response_ok({"pet": serialize_pet(pet)})
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


def get_pet_by_id_sync(pet_id: int):
    session = SessionLocal()
    try:
        pet = session.get(Pet, pet_id)
        if not pet:
            return make_response_error("Питомец не найден")

        return make_response_ok({"pet": serialize_pet(pet)})
    finally:
        session.close()


def update_pet_field_sync(pet_id: int, field: str, value: str | None):
    allowed_fields = {"breed", "name", "age", "extra_info", "photo_file_id"}
    if field not in allowed_fields:
        return make_response_error("Недопустимое поле для изменения")

    session = SessionLocal()
    try:
        pet = session.get(Pet, pet_id)
        if not pet:
            return make_response_error("Питомец не найден")

        cleaned_value = value.strip() if isinstance(value, str) else value

        if field == "name":
            conflict = (
                session.query(Pet)
                .filter(Pet.user_id == pet.user_id, Pet.name == cleaned_value, Pet.id != pet.id)
                .first()
            )
            if conflict:
                return make_response_error("Питомец с такой кличкой уже существует.")

        setattr(pet, field, cleaned_value)
        session.commit()
        session.refresh(pet)

        return make_response_ok({"pet": serialize_pet(pet)})
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


def delete_pet_sync(pet_id: int):
    session = SessionLocal()
    try:
        pet = session.get(Pet, pet_id)
        if not pet:
            return make_response_error("Питомец не найден")

        session.delete(pet)
        session.commit()
        return make_response_ok({"deleted_pet_id": pet_id})
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


def list_notes_for_pet_sync(pet_id: int):
    session = SessionLocal()
    try:
        notes = session.query(Note).filter_by(pet_id=pet_id).order_by(asc(Note.created_at)).all()
        return make_response_ok({"notes": [serialize_note(note) for note in notes]})
    finally:
        session.close()


def create_note_sync(
        pet_id: int,
        title: str,
        period: str,
        extra_info: str | None = None,
        photo_file_id: str | None = None,
):
    if not (title and period):
        return make_response_error("Обязательные поля для заметки не заполнены (title, period).")

    if period not in VALID_PERIODS:
        return make_response_error(
            "Неправильная периодичность. Выберите одну из: " + ", ".join(sorted(VALID_PERIODS))
        )

    session = SessionLocal()
    try:
        pet = session.get(Pet, pet_id)
        if not pet:
            return make_response_error("Питомец не найден")

        note = Note(
            pet_id=pet_id,
            title=title.strip(),
            period=period,
            extra_info=(extra_info or "").strip(),
            photo_file_id=photo_file_id,
        )
        session.add(note)
        session.commit()
        session.refresh(note)

        return make_response_ok({"note": serialize_note(note)})
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


def get_note_by_id_sync(note_id: int):
    session = SessionLocal()
    try:
        note = session.get(Note, note_id)
        if not note:
            return make_response_error("Заметка не найдена")

        return make_response_ok({"note": serialize_note(note)})
    finally:
        session.close()


def delete_note_sync(note_id: int):
    session = SessionLocal()
    try:
        note = session.get(Note, note_id)
        if not note:
            return make_response_error("Заметка не найдена")

        session.delete(note)
        session.commit()
        return make_response_ok({"deleted_note_id": note_id})
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


def update_note_field_sync(note_id: int, field: str, value: str | None):
    allowed_fields = {"title", "period", "extra_info", "photo_file_id"}
    if field not in allowed_fields:
        return make_response_error("Недопустимое поле для изменения заметки")

    session = SessionLocal()
    try:
        note = session.get(Note, note_id)
        if not note:
            return make_response_error("Заметка не найдена")

        cleaned_value = value.strip() if isinstance(value, str) else value

        if field == "period" and cleaned_value not in VALID_PERIODS:
            return make_response_error("Неправильная периодичность.")

        setattr(note, field, cleaned_value)
        session.commit()
        session.refresh(note)

        return make_response_ok({"note": serialize_note(note)})
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


async def get_or_create_user(telegram_id: int):
    return await asyncio.to_thread(get_or_create_user_sync, telegram_id)


async def get_user_by_telegram(telegram_id: int):
    return await asyncio.to_thread(get_user_by_telegram_sync, telegram_id)


async def list_pets_for_user(user_id: int):
    return await asyncio.to_thread(list_pets_for_user_sync, user_id)


async def create_pet(
        user_id: int,
        breed: str,
        name: str,
        age: str,
        extra_info: str | None = None,
        photo_file_id: str | None = None,
):
    return await asyncio.to_thread(create_pet_sync, user_id, breed, name, age, extra_info, photo_file_id)


async def get_pet_by_id(pet_id: int):
    return await asyncio.to_thread(get_pet_by_id_sync, pet_id)


async def update_pet_field(pet_id: int, field: str, value: str | None):
    return await asyncio.to_thread(update_pet_field_sync, pet_id, field, value)


async def delete_pet(pet_id: int):
    return await asyncio.to_thread(delete_pet_sync, pet_id)


async def list_notes_for_pet(pet_id: int):
    return await asyncio.to_thread(list_notes_for_pet_sync, pet_id)


async def create_note(
        pet_id: int,
        title: str,
        period: str,
        extra_info: str | None = None,
        photo_file_id: str | None = None,
):
    return await asyncio.to_thread(create_note_sync, pet_id, title, period, extra_info, photo_file_id)


async def get_note_by_id(note_id: int):
    return await asyncio.to_thread(get_note_by_id_sync, note_id)


async def delete_note(note_id: int):
    return await asyncio.to_thread(delete_note_sync, note_id)


async def update_note_field(note_id: int, field: str, value: str | None):
    return await asyncio.to_thread(update_note_field_sync, note_id, field, value)
