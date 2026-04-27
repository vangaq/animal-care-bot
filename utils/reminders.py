import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config import NOTE_REMINDER_CHECK_INTERVAL_SECONDS
from db import requests as dbreq

logger = logging.getLogger(__name__)


async def reminder_worker(bot: Bot):
    """Периодически проверяет заметки и отправляет напоминания пользователям."""
    while True:
        try:
            response = await dbreq.get_due_note_reminders()
            if response["status"] == "ok":
                for reminder in response["data"]["reminders"]:
                    text = (
                        "⏰ Напоминание по заметке\n"
                        f"Питомец: {reminder['pet_name']}\n"
                        f"Заметка: {reminder['title']}\n"
                        f"Напоминание: {reminder.get('reminder_display', reminder['period_display'])}"
                    )
                    if reminder.get("extra_info"):
                        text += f"\nДоп. информация: {reminder['extra_info']}"

                    try:
                        if reminder.get("photo_file_id"):
                            await bot.send_photo(
                                reminder["telegram_id"],
                                reminder["photo_file_id"],
                                caption=text,
                            )
                        else:
                            await bot.send_message(reminder["telegram_id"], text)
                    except (TelegramForbiddenError, TelegramBadRequest):
                        logger.warning(
                            "Не удалось отправить напоминание note_id=%s telegram_id=%s",
                            reminder["note_id"],
                            reminder["telegram_id"],
                        )
                    else:
                        await dbreq.mark_note_reminder_sent(reminder["note_id"])
        except Exception:
            logger.exception("Ошибка в reminder_worker")

        await asyncio.sleep(NOTE_REMINDER_CHECK_INTERVAL_SECONDS)
