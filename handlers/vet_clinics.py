from __future__ import annotations

import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import (
    YANDEX_GEOCODER_API_KEY,
    YANDEX_MAPS_API_KEY,
    YANDEX_PLACES_API_KEY,
)
from keyboards.main_keyboards import (
    location_request_keyboard,
    main_reply_keyboard,
)
from utils.yandex_maps import build_vet_clinics_payload


class VetClinicsStates(StatesGroup):
    waiting_location = State()


async def start_vet_clinics_search(message: types.Message, state: FSMContext):
    if message.text.lower() != "ветклиники рядом":
        return

    await state.clear()
    await message.answer(
        "Нажмите кнопку ниже и отправьте своё местоположение. "
        "После этого я найду ближайшие ветеринарные клиники и пришлю карту.",
        reply_markup=location_request_keyboard(),
    )
    await state.set_state(VetClinicsStates.waiting_location)


async def location_expected_text(message: types.Message):
    await message.answer(
        "Сейчас нужно отправить именно геолокацию кнопкой «Отправить местоположение»."
    )


async def process_user_location(message: types.Message, state: FSMContext):
    geocoder_key = YANDEX_GEOCODER_API_KEY or YANDEX_MAPS_API_KEY
    places_key = YANDEX_PLACES_API_KEY or YANDEX_MAPS_API_KEY

    if not places_key:
        await message.answer(
            "Не найден ключ Places API.\n\n"
            "В .env нужно добавить минимум:\n"
            "YANDEX_PLACES_API_KEY=ВАШ_КЛЮЧ_ОТ_PLACES_API\n\n"
            "Для красивого адреса пользователя дополнительно можно указать:\n"
            "YANDEX_GEOCODER_API_KEY=ВАШ_КЛЮЧ_ОТ_GEOCODER",
            reply_markup=main_reply_keyboard(),
        )
        await state.clear()
        return

    location = message.location
    if location is None:
        await message.answer("Не удалось получить координаты. Попробуйте ещё раз.")
        return

    wait_message = await message.answer("Ищу ближайшие ветеринарные клиники...")

    try:
        payload = await asyncio.to_thread(
            build_vet_clinics_payload,
            geocoder_api_key=geocoder_key,
            places_api_key=places_key,
            latitude=location.latitude,
            longitude=location.longitude,
        )
    except Exception as error:  # noqa: BLE001 - пользователю нужен понятный ответ
        await wait_message.edit_text(
            "Не удалось получить данные от Яндекс.Карт.\n\n"
            f"Причина: {error}\n\n"
            "Проверьте, что:\n"
            "1) ключ Places API записан без кавычек и скобок;\n"
            "2) если ключ только что создан, прошло хотя бы 15 минут;\n"
            "3) для поиска организаций используется именно ключ Places API, а не только Geocoder."
        )
        await message.answer("Главное меню:", reply_markup=main_reply_keyboard())
        await state.clear()
        return

    clinics = payload["clinics"]
    address_line = payload.get("address") or "Адрес рядом с вашей точкой не определён"

    clinics_lines = []
    for index, clinic in enumerate(clinics, start=1):
        clinics_lines.append(
            f"{index}. {clinic['name']} — {clinic['distance_text']}\n{clinic['address']}"
        )

    caption_parts = [
        "📍 Ближайшие ветеринарные клиники",
        f"Ваше местоположение: {address_line}",
        "",
        *clinics_lines,
    ]

    caption = "\n".join(caption_parts)
    if len(caption) > 1024:
        caption = caption[:1000] + "\n\nСписок сокращён из-за ограничения Telegram."

    photo = types.BufferedInputFile(
        payload["map_image_bytes"],
        filename="vet_clinics_map.png",
    )

    inline_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Открыть подробнее в Яндекс.Картах",
                    url=payload["interactive_map_url"],
                )
            ]
        ]
    )

    await wait_message.delete()
    await message.answer_photo(
        photo=photo,
        caption=caption,
        reply_markup=inline_keyboard,
    )
    await message.answer("Главное меню:", reply_markup=main_reply_keyboard())
    await state.clear()
