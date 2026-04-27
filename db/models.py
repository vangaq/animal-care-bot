from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """Таблица пользователей Telegram."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    owner_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")


class Pet(Base):
    """Таблица питомцев пользователя."""

    __tablename__ = "pets"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uix_user_pet_name"),
    )
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    species = Column(String, nullable=True)  # вид питомца
    breed = Column(String, nullable=False)  # порода
    name = Column(String, nullable=False)  # кличка
    age = Column(String, nullable=False)  # возраст
    extra_info = Column(String, nullable=True)  # дополнительная информация
    photo_file_id = Column(String, nullable=True)  # фото
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="pets")
    notes = relationship("Note", back_populates="pet", cascade="all, delete-orphan")


class Note(Base):
    """Таблица заметок по питомцу."""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, index=True)

    title = Column(String, nullable=False)
    period = Column(String, nullable=False)

    extra_info = Column(String, nullable=True)
    photo_file_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    next_remind_at = Column(DateTime, nullable=True)

    pet = relationship("Pet", back_populates="notes")
