from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")


class Pet(Base):
    __tablename__ = "pets"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uix_user_pet_name"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    breed = Column(String, nullable=False)  # порода
    name = Column(String, nullable=False)  # кличка (unique per user via constraint)
    age = Column(String, nullable=False)
    extra_info = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="pets")
    notes = relationship("Note", back_populates="pet", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    period = Column(String, nullable=False)  # "не повторять"/"6 ч"/"день"/"неделя"/"месяц"/"год"
    extra_info = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    pet = relationship("Pet", back_populates="notes")
