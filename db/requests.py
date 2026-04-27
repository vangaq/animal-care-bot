import asyncio
import re
from datetime import datetime, timedelta

from sqlalchemy import asc, create_engine, inspect
from sqlalchemy.orm import sessionmaker

from config import DB_PATH
from db.models import Base, Note, Pet, User
from utils.helpers import make_response_error, make_response_ok

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

CUSTOM_PERIOD_BUTTON = "Свое время"
CUSTOM_PERIOD_PREFIX = "CUSTOM:"
ONCE_PERIOD_PREFIX = "ONCE:"
NO_REMINDER_PERIOD = "Без напоминания"
ONE_TIME_PERIOD = "Один раз"
REMINDER_MODE_NONE = "WITHOUT"
REMINDER_MODE_ONCE = "ONCE"
REMINDER_MODE_REPEAT = "REPEAT"
VALID_PERIODS = {
    "6 ч",
    "День",
    "Неделя",
    "Месяц",
    "Год",
    CUSTOM_PERIOD_BUTTON,
    ONE_TIME_PERIOD,
}
VALID_REMINDER_MODES = {REMINDER_MODE_NONE, REMINDER_MODE_ONCE, REMINDER_MODE_REPEAT}
DATE_TIME_INPUT_FORMATS = (
    "%d.%m.%Y %H:%M",
    "%d.%m.%y %H:%M",
    "%Y-%m-%d %H:%M",
)
DATE_TIME_DISPLAY_FORMAT = "%d.%m.%Y %H:%M"


def build_custom_period(minutes: int) -> str:
    """Кодирует пользовательский интервал в строку period."""
    return f"{CUSTOM_PERIOD_PREFIX}{minutes}"


def parse_reminder_datetime_input(text: str) -> datetime | None:
    """Парсит точную дату и время напоминания из текста пользователя."""
    value = text.strip()
    for fmt in DATE_TIME_INPUT_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            if dt <= datetime.now():
                return None
            return dt
        except ValueError:
            continue
    return None


def normalize_remind_at(value: str | datetime | None) -> datetime | None:
    """Приводит дату напоминания к datetime."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_remind_at_value(value: str | datetime | None) -> str:
    """Красиво форматирует дату напоминания."""
    dt = normalize_remind_at(value)
    if dt is None:
        return ""
    return dt.strftime(DATE_TIME_DISPLAY_FORMAT)


def get_reminder_mode(period: str | None) -> str:
    """Определяет режим напоминания по сохранённому полю period."""
    if not period or period in {"Не повторять", NO_REMINDER_PERIOD}:
        return REMINDER_MODE_NONE
    if period in {ONE_TIME_PERIOD} or period.startswith(ONCE_PERIOD_PREFIX):
        return REMINDER_MODE_ONCE
    return REMINDER_MODE_REPEAT


def get_base_period(period: str | None) -> str:
    """Возвращает базовый интервал без служебного префикса режима."""
    if not period:
        return ""
    if period.startswith(ONCE_PERIOD_PREFIX):
        return period.replace(ONCE_PERIOD_PREFIX, "", 1)
    return period


def build_period_value(reminder_mode: str, base_period: str | None = None) -> str:
    """Собирает итоговое значение поля period для БД."""
    if reminder_mode == REMINDER_MODE_NONE:
        return NO_REMINDER_PERIOD

    if reminder_mode == REMINDER_MODE_ONCE and base_period == ONE_TIME_PERIOD:
        return ONE_TIME_PERIOD

    if not base_period:
        raise ValueError("Для режима напоминания нужен интервал")

    if reminder_mode == REMINDER_MODE_ONCE:
        return f"{ONCE_PERIOD_PREFIX}{base_period}"

    return base_period


def extract_custom_period_minutes(period: str | None) -> int | None:
    """Достаёт количество минут из period вида CUSTOM:90."""
    base_period = get_base_period(period)
    if not base_period or not base_period.startswith(CUSTOM_PERIOD_PREFIX):
        return None

    raw_minutes = base_period.replace(CUSTOM_PERIOD_PREFIX, "", 1).strip()
    if not raw_minutes.isdigit():
        return None

    minutes = int(raw_minutes)
    return minutes if minutes > 0 else None


def parse_custom_period_input(text: str) -> int | None:
    """Парсит введённый пользователем интервал."""
    value = text.strip().lower().replace(",", ".")
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([а-яa-z]+)", value)
    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2)

    minute_units = {"м", "мин", "минута", "минуты", "минут", "minute", "minutes", "min"}
    hour_units = {"ч", "час", "часа", "часов", "h", "hr", "hour", "hours"}
    day_units = {"д", "день", "дня", "дней", "day", "days"}

    if unit in minute_units:
        minutes = int(amount)
    elif unit in hour_units:
        minutes = int(amount * 60)
    elif unit in day_units:
        minutes = int(amount * 24 * 60)
    else:
        return None

    return minutes if minutes > 0 else None


def format_minutes_human(minutes: int) -> str:
    """Форматирует количество минут."""
    days, rem = divmod(minutes, 24 * 60)
    hours, mins = divmod(rem, 60)

    parts = []
    if days:
        parts.append(f"{days} д")
    if hours:
        parts.append(f"{hours} ч")
    if mins:
        parts.append(f"{mins} мин")

    return " ".join(parts) if parts else "0 мин"


def format_period_for_display(period: str) -> str:
    """Показывает только интервал напоминания без режима."""
    base_period = get_base_period(period)
    if base_period == ONE_TIME_PERIOD:
        return ONE_TIME_PERIOD
    minutes = extract_custom_period_minutes(base_period)
    if minutes is None:
        return base_period
    return f"Свое время ({format_minutes_human(minutes)})"


def format_reminder_for_display(period: str, next_remind_at: str | datetime | None = None) -> str:
    """Показывает режим напоминания в понятном виде."""
    mode = get_reminder_mode(period)
    if mode == REMINDER_MODE_NONE:
        return NO_REMINDER_PERIOD

    if get_base_period(period) == ONE_TIME_PERIOD:
        formatted_dt = format_remind_at_value(next_remind_at)
        return f"Один раз: {formatted_dt}" if formatted_dt else ONE_TIME_PERIOD

    interval_text = format_period_for_display(period)
    if mode == REMINDER_MODE_ONCE:
        return f"Один раз через {interval_text}"

    return f"Каждые {interval_text}"


def get_period_delta(period: str) -> timedelta | None:
    """Возвращает интервал напоминания для старых вариантов периодичности."""
    base_period = get_base_period(period)
    if base_period == ONE_TIME_PERIOD:
        return None
    custom_minutes = extract_custom_period_minutes(base_period)
    if custom_minutes is not None:
        return timedelta(minutes=custom_minutes)

    mapping = {
        "6 ч": timedelta(hours=6),
        "День": timedelta(days=1),
        "Неделя": timedelta(weeks=1),
        "Месяц": timedelta(days=30),
        "Год": timedelta(days=365),
    }
    return mapping.get(base_period)


def calculate_next_remind_at(period: str, base_dt: datetime | None = None) -> datetime | None:
    """Считает ближайшее время напоминания по периоду."""
    if get_reminder_mode(period) == REMINDER_MODE_NONE:
        return None

    delta = get_period_delta(period)
    if delta is None:
        return None

    if base_dt is None:
        base_dt = datetime.now()

    return base_dt + delta


def serialize_pet(pet: Pet) -> dict:
    """Преобразует объект питомца в обычный словарь."""
    return {
        "id": pet.id,
        "species": pet.species or "",
        "breed": pet.breed,
        "name": pet.name,
        "age": pet.age,
        "extra_info": pet.extra_info or "",
        "photo_file_id": pet.photo_file_id or "",
        "created_at": pet.created_at.isoformat(),
    }


def serialize_note(note: Note) -> dict:
    """Преобразует объект заметки в обычный словарь."""
    next_remind_at = note.next_remind_at.isoformat() if note.next_remind_at else ""
    return {
        "id": note.id,
        "pet_id": note.pet_id,
        "title": note.title,
        "period": note.period,
        "period_display": format_period_for_display(note.period),
        "reminder_display": format_reminder_for_display(note.period, next_remind_at),
        "reminder_mode": get_reminder_mode(note.period),
        "extra_info": note.extra_info or "",
        "photo_file_id": note.photo_file_id or "",
        "created_at": note.created_at.isoformat(),
        "next_remind_at": next_remind_at,
        "next_remind_at_display": format_remind_at_value(next_remind_at),
    }


def ensure_schema():
    required_columns = {
        "users": {"owner_name": "VARCHAR"},
        "pets": {
            "photo_file_id": "VARCHAR",
            "species": "VARCHAR",
        },
        "notes": {
            "photo_file_id": "VARCHAR",
            "next_remind_at": "DATETIME",
        },
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


# Инициализация базы данных
def init_db():
    Base.metadata.create_all(bind=engine)
    ensure_schema()


# Работа с пользователями
def get_or_create_user_sync(telegram_id: int):
    """Ищет пользователя по Telegram ID."""
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
                    "owner_name": user.owner_name or "",
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
    """Возвращает пользователя по его Telegram ID."""
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
                    "owner_name": user.owner_name or "",
                    "created_at": user.created_at.isoformat(),
                }
            }
        )
    finally:
        session.close()


def update_user_owner_name_sync(telegram_id: int, owner_name: str):
    """Сохраняет имя владельца по Telegram ID."""
    cleaned_name = owner_name.strip()
    if not cleaned_name:
        return make_response_error("Имя не может быть пустым")

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, owner_name=cleaned_name)
            session.add(user)
        else:
            user.owner_name = cleaned_name
        session.commit()
        session.refresh(user)
        return make_response_ok(
            {
                "user": {
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "owner_name": user.owner_name or "",
                    "created_at": user.created_at.isoformat(),
                }
            }
        )
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


# Работа с питомцами
def list_pets_for_user_sync(user_id: int):
    """Возвращает список питомцев конкретного пользователя."""
    session = SessionLocal()
    try:
        pets = session.query(Pet).filter_by(user_id=user_id).order_by(asc(Pet.created_at)).all()
        return make_response_ok({"pets": [serialize_pet(pet) for pet in pets]})
    finally:
        session.close()


def create_pet_sync(
        user_id: int,
        species: str,
        breed: str,
        name: str,
        age: str,
        extra_info: str | None = None,
        photo_file_id: str | None = None,
):
    """Создаёт нового питомца для пользователя."""
    if not (species and breed and name and age):
        return make_response_error("Обязательные поля для питомца не заполнены (species, breed, name, age).")

    session = SessionLocal()
    try:
        exists = session.query(Pet).filter_by(user_id=user_id, name=name.strip()).first()
        if exists:
            return make_response_error("Питомец с такой кличкой уже существует.")

        pet = Pet(
            user_id=user_id,
            species=species.strip(),
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
    """Возвращает питомца по ID."""
    session = SessionLocal()
    try:
        pet = session.get(Pet, pet_id)
        if not pet:
            return make_response_error("Питомец не найден")

        return make_response_ok({"pet": serialize_pet(pet)})
    finally:
        session.close()


def update_pet_field_sync(pet_id: int, field: str, value: str | None):
    """Изменяет одно поле у питомца."""
    allowed_fields = {"species", "breed", "name", "age", "extra_info", "photo_file_id"}
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
    """Удаляет питомца по ID вместе со всеми его заметками."""
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


# Работа с заметками
def list_notes_for_pet_sync(pet_id: int):
    """Возвращает все заметки одного питомца."""
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
        next_remind_at: str | datetime | None = None,
):
    """Создаёт заметку для питомца."""
    if not (title and period):
        return make_response_error("Обязательные поля для заметки не заполнены (title, period).")

    mode = get_reminder_mode(period)
    base_period = get_base_period(period)
    remind_at_dt = normalize_remind_at(next_remind_at)

    if mode not in VALID_REMINDER_MODES:
        return make_response_error("Неправильный режим напоминания.")

    if base_period == ONE_TIME_PERIOD:
        if remind_at_dt is None:
            return make_response_error("Для одноразового напоминания нужна точная дата и время.")
        if remind_at_dt <= datetime.now():
            return make_response_error("Дата напоминания должна быть в будущем.")
    elif mode != REMINDER_MODE_NONE and base_period not in VALID_PERIODS and extract_custom_period_minutes(
            base_period) is None:
        return make_response_error(
            "Неправильная периодичность. Выберите одну из: " + ", ".join(sorted(VALID_PERIODS))
        )
    elif mode == REMINDER_MODE_NONE:
        remind_at_dt = None

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
            next_remind_at=remind_at_dt if base_period == ONE_TIME_PERIOD else calculate_next_remind_at(period),
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
    """Возвращает заметку по ID."""
    session = SessionLocal()
    try:
        note = session.get(Note, note_id)
        if not note:
            return make_response_error("Заметка не найдена")

        return make_response_ok({"note": serialize_note(note)})
    finally:
        session.close()


def delete_note_sync(note_id: int):
    """Удаляет заметку по ID."""
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
    """Изменяет одно поле заметки."""
    allowed_fields = {"title", "period", "extra_info", "photo_file_id", "next_remind_at"}
    if field not in allowed_fields:
        return make_response_error("Недопустимое поле для изменения заметки")

    session = SessionLocal()
    try:
        note = session.get(Note, note_id)
        if not note:
            return make_response_error("Заметка не найдена")

        cleaned_value = value.strip() if isinstance(value, str) else value

        if field == "period":
            mode = get_reminder_mode(cleaned_value)
            if mode not in VALID_REMINDER_MODES:
                return make_response_error("Неправильный режим напоминания.")
            if mode == REMINDER_MODE_NONE:
                note.next_remind_at = None
            elif get_base_period(cleaned_value) != ONE_TIME_PERIOD:
                note.next_remind_at = calculate_next_remind_at(cleaned_value)

        if field == "next_remind_at":
            cleaned_value = normalize_remind_at(cleaned_value)

        setattr(note, field, cleaned_value)
        session.commit()
        session.refresh(note)

        return make_response_ok({"note": serialize_note(note)})
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


def update_note_reminder_sync(note_id: int, period: str, next_remind_at: str | datetime | None = None):
    """Атомарно обновляет режим напоминания и дату отправки."""
    session = SessionLocal()
    try:
        note = session.get(Note, note_id)
        if not note:
            return make_response_error("Заметка не найдена")

        mode = get_reminder_mode(period)
        if mode not in VALID_REMINDER_MODES:
            return make_response_error("Неправильный режим напоминания.")

        remind_at_dt = normalize_remind_at(next_remind_at)

        if mode == REMINDER_MODE_NONE:
            note.period = NO_REMINDER_PERIOD
            note.next_remind_at = None
        elif get_base_period(period) == ONE_TIME_PERIOD:
            if remind_at_dt is None:
                return make_response_error("Для одноразового напоминания нужна точная дата и время.")
            if remind_at_dt <= datetime.now():
                return make_response_error("Дата напоминания должна быть в будущем.")
            note.period = ONE_TIME_PERIOD
            note.next_remind_at = remind_at_dt
        else:
            note.period = period
            note.next_remind_at = calculate_next_remind_at(period)

        session.commit()
        session.refresh(note)
        return make_response_ok({"note": serialize_note(note)})
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


def get_due_note_reminders_sync(limit: int = 20):
    """Возвращает заметки, для которых уже пора отправить напоминание."""
    session = SessionLocal()
    try:
        now = datetime.now()
        notes = (
            session.query(Note)
            .join(Pet, Note.pet_id == Pet.id)
            .join(User, Pet.user_id == User.id)
            .filter(Note.next_remind_at.isnot(None), Note.next_remind_at <= now)
            .order_by(asc(Note.next_remind_at))
            .limit(limit)
            .all()
        )

        reminders = [
            {
                "note_id": note.id,
                "telegram_id": note.pet.owner.telegram_id,
                "pet_name": note.pet.name,
                "title": note.title,
                "period": note.period,
                "period_display": format_period_for_display(note.period),
                "reminder_display": format_reminder_for_display(note.period, note.next_remind_at),
                "reminder_mode": get_reminder_mode(note.period),
                "extra_info": note.extra_info or "",
                "photo_file_id": note.photo_file_id or "",
                "next_remind_at": note.next_remind_at.isoformat() if note.next_remind_at else "",
            }
            for note in notes
        ]
        return make_response_ok({"reminders": reminders})
    finally:
        session.close()


def mark_note_reminder_sent_sync(note_id: int):
    """Сдвигает следующее напоминание после успешной отправки."""
    session = SessionLocal()
    try:
        note = session.get(Note, note_id)
        if not note:
            return make_response_error("Заметка не найдена")

        if note.period == ONE_TIME_PERIOD or get_reminder_mode(note.period) == REMINDER_MODE_ONCE:
            note.next_remind_at = None
        else:
            note.next_remind_at = calculate_next_remind_at(note.period)

        session.commit()
        session.refresh(note)
        return make_response_ok({"note": serialize_note(note)})
    except Exception as error:
        session.rollback()
        return make_response_error(f"DB error: {error}")
    finally:
        session.close()


# Асинхронные обёртки
async def get_or_create_user(telegram_id: int):
    return await asyncio.to_thread(get_or_create_user_sync, telegram_id)


async def get_user_by_telegram(telegram_id: int):
    return await asyncio.to_thread(get_user_by_telegram_sync, telegram_id)


async def update_user_owner_name(telegram_id: int, owner_name: str):
    return await asyncio.to_thread(update_user_owner_name_sync, telegram_id, owner_name)


async def list_pets_for_user(user_id: int):
    return await asyncio.to_thread(list_pets_for_user_sync, user_id)


async def create_pet(
        user_id: int,
        species: str,
        breed: str,
        name: str,
        age: str,
        extra_info: str | None = None,
        photo_file_id: str | None = None,
):
    return await asyncio.to_thread(create_pet_sync, user_id, species, breed, name, age, extra_info, photo_file_id)


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
        next_remind_at: str | datetime | None = None,
):
    return await asyncio.to_thread(create_note_sync, pet_id, title, period, extra_info, photo_file_id, next_remind_at)


async def get_note_by_id(note_id: int):
    return await asyncio.to_thread(get_note_by_id_sync, note_id)


async def delete_note(note_id: int):
    return await asyncio.to_thread(delete_note_sync, note_id)


async def update_note_field(note_id: int, field: str, value: str | None):
    return await asyncio.to_thread(update_note_field_sync, note_id, field, value)


async def update_note_reminder(note_id: int, period: str, next_remind_at: str | datetime | None = None):
    return await asyncio.to_thread(update_note_reminder_sync, note_id, period, next_remind_at)


async def get_due_note_reminders(limit: int = 20):
    return await asyncio.to_thread(get_due_note_reminders_sync, limit)


async def mark_note_reminder_sent(note_id: int):
    return await asyncio.to_thread(mark_note_reminder_sent_sync, note_id)
