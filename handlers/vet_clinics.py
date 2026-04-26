from __future__ import annotations

import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import (
    YANDEX_GEOCODER_API_KEY,
    YANDEX_PLACES_API_KEY,
)
from keyboards.main_keyboards import (
    main_reply_keyboard,
    map_categories_keyboard,
    map_input_keyboard,
)
from utils.yandex_maps import (
    YandexMapsConfigError,
    YandexMapsError,
    build_places_payload,
    geocode_address,
)

MAP_CATEGORIES: dict[str, dict[str, str]] = {
    "ветклиники рядом": {
        "title": "ветеринарные клиники",
        "search_text": "ветеринарная клиника",
        "fallback_name": "Ветеринарная клиника",
        "filename": "vet_clinics_map.png",
    },
    "зоомагазины рядом": {
        "title": "зоомагазины",
        "search_text": "зоомагазин",
        "fallback_name": "Зоомагазин",
        "filename": "pet_stores_map.png",
    },
    "груминг рядом": {
        "title": "груминг-салоны",
        "search_text": "груминг для животных",
        "fallback_name": "Груминг-салон",
        "filename": "grooming_map.png",
    },
}


class MapSearchStates(StatesGroup):
    waiting_location = State()


async def start_maps_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выберите, что нужно найти рядом:",
        reply_markup=map_categories_keyboard(),
    )


async def start_category_search(message: types.Message, state: FSMContext):
    category_key = message.text.lower()
    category = MAP_CATEGORIES.get(category_key)
    if category is None:
        return

    await state.clear()
    await state.update_data(category_key=category_key)
    await message.answer(
        "Отправьте своё местоположение кнопкой ниже\n"
        "или просто введите адрес вручную текстом.\n\n"
        f"Я найду рядом {category['title']} и пришлю карту.",
        reply_markup=map_input_keyboard(),
    )
    await state.set_state(MapSearchStates.waiting_location)


async def process_user_location(message: types.Message, state: FSMContext):
    location = message.location
    if location is None:
        await message.answer("Не удалось получить координаты. Попробуйте ещё раз.")
        return

    await _process_places_search(
        message=message,
        state=state,
        latitude=location.latitude,
        longitude=location.longitude,
        address_line="",
    )


async def process_user_address(message: types.Message, state: FSMContext):
    geocoder_key = YANDEX_GEOCODER_API_KEY

    address_text = (message.text or "").strip()
    if not address_text:
        await message.answer("Введите адрес текстом или отправьте геолокацию кнопкой ниже.")
        return

    wait_message = await message.answer("Проверяю адрес и ищу места рядом...")

    try:
        geocoded = await asyncio.to_thread(
            geocode_address,
            api_key=geocoder_key,
            address=address_text,
        )
    except YandexMapsConfigError as error:
        await wait_message.edit_text(
            f"{error}\n\n"
            "Для ручного ввода адреса нужен Geocoder API.\n"
            "Но поиск по геолокации можно использовать уже сейчас, если отправить точку кнопкой ниже."
        )
        return
    except YandexMapsError as error:
        await wait_message.edit_text(
            "Не удалось распознать введённый адрес.\n\n"
            f"Причина: {error}"
        )
        return
    except Exception as error:  # noqa: BLE001 - пользователю нужен понятный ответ
        await wait_message.edit_text(
            "Не удалось обработать введённый адрес.\n\n"
            f"Причина: {error}"
        )
        return

    await wait_message.delete()
    await _process_places_search(
        message=message,
        state=state,
        latitude=geocoded["latitude"],
        longitude=geocoded["longitude"],
        address_line=geocoded["address"],
    )


async def _process_places_search(
        message: types.Message,
        state: FSMContext,
        latitude: float,
        longitude: float,
        address_line: str,
):
    data = await state.get_data()
    category_key = data.get("category_key")
    category = MAP_CATEGORIES.get(category_key or "")
    if category is None:
        await message.answer(
            "Сначала откройте раздел «Карта» и выберите категорию поиска.",
            reply_markup=map_categories_keyboard(),
        )
        await state.clear()
        return

    geocoder_key = YANDEX_GEOCODER_API_KEY
    places_key = YANDEX_PLACES_API_KEY

    if not places_key:
        await message.answer(
            "Не найден ключ Places API.\n\n"
            "В .env нужно добавить минимум:\n"
            "YANDEX_PLACES_API_KEY=ВАШ_КЛЮЧ_ОТ_PLACES_API\n\n"
            "Для ручного ввода адреса и красивого определения адреса по точке дополнительно можно указать:\n"
            "YANDEX_GEOCODER_API_KEY=ВАШ_КЛЮЧ_ОТ_GEOCODER",
            reply_markup=main_reply_keyboard(),
        )
        await state.clear()
        return

    wait_message = await message.answer(f"Ищу рядом {category['title']}...")

    try:
        payload = await asyncio.to_thread(
            build_places_payload,
            geocoder_api_key=geocoder_key,
            places_api_key=places_key,
            latitude=latitude,
            longitude=longitude,
            search_text=category["search_text"],
            fallback_name=category["fallback_name"],
            origin_address=address_line,
        )
    except Exception as error:  # noqa: BLE001 - пользователю нужен понятный ответ
        await wait_message.edit_text(
            "Не удалось получить данные от Яндекс.Карт.\n\n"
            f"Причина: {error}\n\n"
            "Проверьте, что:\n"
            "1) ключ Places API записан без кавычек и скобок;\n"
            "2) если ключ только что создан, прошло хотя бы 15 минут;\n"
            "3) для поиска организаций используется именно ключ Places API;\n"
            "4) для ручного ввода адреса указан ключ Geocoder API."
        )
        await message.answer("Главное меню:", reply_markup=main_reply_keyboard())
        await state.clear()
        return

    places = payload["places"]
    resolved_address = payload.get("address") or "Адрес рядом с вашей точкой не определён"

    places_lines = []
    for index, place in enumerate(places, start=1):
        places_lines.append(
            f"{index}. {place['name']} — {place['distance_text']}\n{place['address']}"
        )

    caption_parts = [
        f"📍 Ближайшие {category['title']}",
        f"Точка поиска: {resolved_address}",
        "",
        *places_lines,
    ]

    caption = "\n".join(caption_parts)
    if len(caption) > 1024:
        caption = caption[:1000] + "\n\nСписок сокращён из-за ограничения Telegram."

    photo = types.BufferedInputFile(
        payload["map_image_bytes"],
        filename=category["filename"],
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
