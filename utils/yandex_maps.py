from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote_plus
from urllib.request import urlopen


GEOCODER_URL = "https://geocode-maps.yandex.ru/v1"
PLACES_URL = "https://search-maps.yandex.ru/v1"
STATIC_MAPS_URL = "https://static-maps.yandex.ru/1.x"

# Набор областей поиска: от маленькой к более широкой.
SEARCH_SPANS = [
    (0.03, 0.03, 15),
    (0.06, 0.06, 14),
    (0.12, 0.12, 13),
    (0.25, 0.25, 11),
]


@dataclass(slots=True)
class NearbyPlace:
    name: str
    address: str
    latitude: float
    longitude: float
    distance_meters: float

    @property
    def distance_text(self) -> str:
        if self.distance_meters < 1000:
            return f"{int(round(self.distance_meters))} м"
        return f"{self.distance_meters / 1000:.1f} км"


class YandexMapsError(RuntimeError):
    """Ошибка работы с API Яндекс.Карт."""


class YandexMapsConfigError(YandexMapsError):
    """Ошибка конфигурации ключей для Яндекс.Карт."""


def _extract_error_message_from_payload(payload: str) -> str:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return payload.strip() or "Неизвестная ошибка"

    if isinstance(data, dict):
        return str(data.get("message") or data.get("error") or "Неизвестная ошибка")
    return "Неизвестная ошибка"


def _http_get_json(base_url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urlencode(params, quote_via=quote_plus)
    url = f"{base_url}?{query}"

    try:
        with urlopen(url, timeout=20) as response:  # nosec B310 - URL формируется из констант
            payload = response.read().decode("utf-8")
    except HTTPError as error:
        payload = error.read().decode("utf-8", errors="replace")
        message = _extract_error_message_from_payload(payload)

        if error.code == 403:
            raise YandexMapsError(
                "HTTP 403 Forbidden. Обычно это значит, что указан неверный ключ для этого сервиса. "
                "Для geocode-maps нужен ключ Geocoder, а для search-maps нужен отдельный ключ Places API. "
                f"Ответ Яндекса: {message}"
            ) from error

        raise YandexMapsError(f"HTTP {error.code}. Ответ Яндекса: {message}") from error
    except URLError as error:
        raise YandexMapsError(f"Сетевая ошибка при обращении к Яндекс.Картам: {error}") from error

    data = json.loads(payload)
    if isinstance(data, dict) and data.get("statusCode"):
        raise YandexMapsError(data.get("message", "Ошибка API Яндекс.Карт"))

    return data


def _http_get_bytes(base_url: str, params: dict[str, Any]) -> bytes:
    query = urlencode(params, quote_via=quote_plus)
    url = f"{base_url}?{query}"

    try:
        with urlopen(url, timeout=20) as response:  # nosec B310 - URL формируется из констант
            return response.read()
    except HTTPError as error:
        payload = error.read().decode("utf-8", errors="replace")
        message = payload.strip() or "Неизвестная ошибка"
        raise YandexMapsError(f"Не удалось получить изображение карты. HTTP {error.code}. {message}") from error
    except URLError as error:
        raise YandexMapsError(f"Сетевая ошибка при загрузке статической карты: {error}") from error


def _haversine_distance_meters(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    radius = 6_371_000

    lat1 = math.radians(latitude_1)
    lat2 = math.radians(latitude_2)
    dlat = math.radians(latitude_2 - latitude_1)
    dlon = math.radians(longitude_2 - longitude_1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def reverse_geocode(api_key: str, latitude: float, longitude: float) -> str:
    if not api_key:
        return ""

    data = _http_get_json(
        GEOCODER_URL,
        {
            "apikey": api_key,
            "geocode": f"{longitude},{latitude}",
            "lang": "ru_RU",
            "format": "json",
            "kind": "house",
        },
    )

    collection = data.get("response", {}).get("GeoObjectCollection", {})
    items = collection.get("featureMember", [])
    if not items:
        return ""

    geo_object = items[0].get("GeoObject", {})
    meta = geo_object.get("metaDataProperty", {}).get("GeocoderMetaData", {})
    address = meta.get("Address", {}).get("formatted")
    if address:
        return str(address)

    return str(meta.get("text") or geo_object.get("name") or "")


def geocode_address(api_key: str, address: str) -> dict[str, Any]:
    if not api_key:
        raise YandexMapsConfigError(
            "Для поиска по введённому адресу нужен ключ Geocoder API. "
            "Добавьте в .env строку YANDEX_GEOCODER_API_KEY=ВАШ_КЛЮЧ"
        )

    clean_address = address.strip()
    if not clean_address:
        raise YandexMapsError("Адрес не должен быть пустым.")

    data = _http_get_json(
        GEOCODER_URL,
        {
            "apikey": api_key,
            "geocode": clean_address,
            "lang": "ru_RU",
            "format": "json",
            "results": 1,
        },
    )

    collection = data.get("response", {}).get("GeoObjectCollection", {})
    items = collection.get("featureMember", [])
    if not items:
        raise YandexMapsError(
            "Не удалось распознать этот адрес. Попробуйте написать адрес подробнее: "
            "город, улицу и номер дома."
        )

    geo_object = items[0].get("GeoObject", {})
    point = geo_object.get("Point", {})
    coordinates = str(point.get("pos") or "").split()
    if len(coordinates) != 2:
        raise YandexMapsError("Не удалось получить координаты по введённому адресу.")

    longitude = float(coordinates[0])
    latitude = float(coordinates[1])

    meta = geo_object.get("metaDataProperty", {}).get("GeocoderMetaData", {})
    formatted_address = (
        meta.get("Address", {}).get("formatted")
        or meta.get("text")
        or geo_object.get("name")
        or clean_address
    )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "address": str(formatted_address),
    }


def find_nearest_places(
    api_key: str,
    latitude: float,
    longitude: float,
    search_text: str,
    fallback_name: str,
    limit: int = 5,
) -> tuple[list[NearbyPlace], int]:
    if not api_key:
        raise YandexMapsConfigError(
            "Не указан ключ Places API. Добавьте в .env строку "
            "YANDEX_PLACES_API_KEY=ВАШ_КЛЮЧ"
        )

    found_places: list[NearbyPlace] = []
    chosen_zoom = 13

    for span_x, span_y, zoom in SEARCH_SPANS:
        data = _http_get_json(
            PLACES_URL,
            {
                "apikey": api_key,
                "text": search_text,
                "type": "biz",
                "lang": "ru_RU",
                "ll": f"{longitude},{latitude}",
                "spn": f"{span_x},{span_y}",
                "rspn": 1,
                "results": max(limit * 2, 10),
            },
        )

        features = data.get("features", [])
        parsed: list[NearbyPlace] = []
        for feature in features:
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [])
            if len(coordinates) != 2:
                continue

            place_longitude = float(coordinates[0])
            place_latitude = float(coordinates[1])
            properties = feature.get("properties", {})
            company_meta = properties.get("CompanyMetaData", {})

            name = str(
                company_meta.get("name")
                or properties.get("name")
                or fallback_name
            )
            address = str(
                company_meta.get("address")
                or company_meta.get("Address", {}).get("formatted")
                or properties.get("description")
                or "Адрес не указан"
            )

            distance_meters = _haversine_distance_meters(
                latitude,
                longitude,
                place_latitude,
                place_longitude,
            )
            parsed.append(
                NearbyPlace(
                    name=name,
                    address=address,
                    latitude=place_latitude,
                    longitude=place_longitude,
                    distance_meters=distance_meters,
                )
            )

        parsed.sort(key=lambda place: place.distance_meters)

        unique: list[NearbyPlace] = []
        seen: set[tuple[str, str]] = set()
        for place in parsed:
            key = (place.name.casefold(), place.address.casefold())
            if key in seen:
                continue
            seen.add(key)
            unique.append(place)
            if len(unique) >= limit:
                break

        if unique:
            found_places = unique
            chosen_zoom = zoom
            break

    if not found_places:
        raise YandexMapsError(
            "Рядом не удалось найти подходящие места. Попробуйте указать другой адрес "
            "или выполнить поиск ещё раз в другом месте."
        )

    return found_places, chosen_zoom


def _build_static_map_viewport(
    latitude: float,
    longitude: float,
    places: list[NearbyPlace],
) -> tuple[str, str]:
    longitudes = [longitude, *[place.longitude for place in places]]
    latitudes = [latitude, *[place.latitude for place in places]]

    min_lon = min(longitudes)
    max_lon = max(longitudes)
    min_lat = min(latitudes)
    max_lat = max(latitudes)

    center_lon = (min_lon + max_lon) / 2
    center_lat = (min_lat + max_lat) / 2

    lon_span = max((max_lon - min_lon) * 1.35, 0.015)
    lat_span = max((max_lat - min_lat) * 1.35, 0.015)

    return f"{center_lon},{center_lat}", f"{lon_span},{lat_span}"


def build_static_map_bytes(
    latitude: float,
    longitude: float,
    places: list[NearbyPlace],
) -> bytes:
    ll, spn = _build_static_map_viewport(latitude, longitude, places)

    placemarks = [f"{longitude},{latitude},pm2blm"]
    for index, place in enumerate(places, start=1):
        placemarks.append(f"{place.longitude},{place.latitude},pm2rdm{index}")

    return _http_get_bytes(
        STATIC_MAPS_URL,
        {
            "ll": ll,
            "spn": spn,
            "lang": "ru_RU",
            "size": "650,450",
            "l": "map",
            "pt": "~".join(placemarks),
        },
    )


def build_interactive_map_url(
    latitude: float,
    longitude: float,
    zoom: int,
    search_text: str,
) -> str:
    query = urlencode(
        {
            "ll": f"{longitude},{latitude}",
            "z": zoom,
            "text": search_text,
        },
        quote_via=quote_plus,
    )
    return f"https://yandex.ru/maps/?{query}"


def build_places_payload(
    geocoder_api_key: str,
    places_api_key: str,
    latitude: float,
    longitude: float,
    search_text: str,
    fallback_name: str,
    origin_address: str = "",
) -> dict[str, Any]:
    address = origin_address or reverse_geocode(
        api_key=geocoder_api_key,
        latitude=latitude,
        longitude=longitude,
    )
    places, zoom = find_nearest_places(
        api_key=places_api_key,
        latitude=latitude,
        longitude=longitude,
        search_text=search_text,
        fallback_name=fallback_name,
        limit=5,
    )
    map_image_bytes = build_static_map_bytes(
        latitude=latitude,
        longitude=longitude,
        places=places,
    )

    return {
        "address": address,
        "places": [
            {
                "name": place.name,
                "address": place.address,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "distance_meters": place.distance_meters,
                "distance_text": place.distance_text,
            }
            for place in places
        ],
        "map_image_bytes": map_image_bytes,
        "interactive_map_url": build_interactive_map_url(
            latitude=latitude,
            longitude=longitude,
            zoom=zoom,
            search_text=search_text,
        ),
    }


def build_vet_clinics_payload(
    geocoder_api_key: str,
    places_api_key: str,
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    return build_places_payload(
        geocoder_api_key=geocoder_api_key,
        places_api_key=places_api_key,
        latitude=latitude,
        longitude=longitude,
        search_text="ветеринарная клиника",
        fallback_name="Ветеринарная клиника",
    )
