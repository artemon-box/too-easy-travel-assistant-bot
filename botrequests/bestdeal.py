import requests
import os
from telebot.types import InputMediaPhoto
from typing import Optional

headers: dict = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': os.environ['RAPIDAPI_KEY']
}


def get_destination_id(destination: str) -> Optional[int]:
    """
    Функция запрашивает идентификатор города и возвращает его, если город не найден возвращает None.
    :param destination: str название города.
    :return: int id города.
    """
    params: dict = {
        "query": destination,
        "locale": "ru_RU",
        "currency": "RUB"
    }
    url = "https://hotels4.p.rapidapi.com/locations/v2/search"

    response = requests.request(method="GET", url=url, headers=headers, params=params)
    if response:
        result = response.json()
        return result['suggestions'][0]["entities"][0]["destinationId"] \
            if len(result['suggestions'][0]["entities"]) \
            else None
    return None


def get_response(city: str, max_price: int, max_distance: int, arrival_date: str, departure_date: str,
                 hotels_number: int, upload_photos: bool, photos_number: int = None) -> Optional[list]:
    """
    Функция запрашивает и возвращает пользователю информацию об отелях на сайте hotels.com в соответствии с параметрами
    пользователя.
    :param city: Название города в котором требуется найти отели.
    :param arrival_date: дата въезда
    :param departure_date: дата выезда
    :param max_price: Максимальная цена за сутки
    :param max_distance: Максимальное расстояние от центра города
    :param hotels_number: количество отелей которые необходимо найти
    :param upload_photos: необходимость загрузки фотографий отеля
    :param photos_number: количество фотографий
    :return: список кортежей с информацией по каждому отелю
    """
    url = "https://hotels4.p.rapidapi.com/properties/list"

    destination_id = get_destination_id(destination=city)

    if not destination_id:
        return None

    querystring: dict = {
        "destinationId": int(destination_id),
        "pageNumber": "1",
        "pageSize": hotels_number,
        "checkIn": arrival_date,
        "checkOut": departure_date,
        "adults1": "1",
        "sortOrder": "DISTANCE_FROM_LANDMARK",
        "locale": "ru_RU",
        "currency": "RUB",
        "priceMin": 0,
        "priceMax": max_price,
        "landmarkIds": "Центр города"
    }

    response = requests.request(method="GET", url=url, headers=headers, params=querystring)

    if response is False:
        return None

    result = response.json()

    if len(result['data']['body']['searchResults']['results']) == 0:
        return None

    if upload_photos:
        result_tuples_list = [
            (
                f"ru.hotels.com/ho{hotel['id']}/",
                hotel['name'],
                hotel['ratePlan']['price']['current'],
                hotel['ratePlan']['price']['exactCurrent'],
                hotel['landmarks'][0]['label'],
                hotel['landmarks'][0]['distance'],
                get_hotel_photos(hotel['id'], photos_number)
            )
            for hotel in result['data']['body']['searchResults']['results'] if
            float(hotel["landmarks"][0]["distance"].split(' ')[0].replace(',', '.')) <= max_distance
            and hotel['ratePlan']['price']['exactCurrent'] <= max_price]

        return sorted(result_tuples_list, key=lambda x: x[3])

    else:
        result_tuples_list = [
            (
                f"ru.hotels.com/ho{hotel['id']}/",
                hotel['name'],
                hotel['ratePlan']['price']['current'],
                hotel['ratePlan']['price']['exactCurrent'],
                hotel['landmarks'][0]['label'],
                hotel['landmarks'][0]['distance'])
            for hotel in result['data']['body']['searchResults']['results'] if
            float(hotel["landmarks"][0]["distance"].split(' ')[0].replace(',', '.')) <= max_distance
            and hotel['ratePlan']['price']['exactCurrent'] <= max_price]

    return sorted(result_tuples_list, key=lambda x: x[3])


def get_hotel_photos(hotel_id: int, photos_number: int, photos_size: str = 'z') -> list[InputMediaPhoto]:
    """
    Функция запрашивает список ссылок на фотографии отеля, возвращает пользователю список с подписанными фотографиями.
    :param hotel_id: id отеля
    :param photos_number: количество фотографий
    :param photos_size: размер фотографий
    :return: список с подписанными фотографиями
    """
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    querystring: dict = {'id': hotel_id}

    response = requests.request(method="GET", url=url, headers=headers, params=querystring).json()

    if len(response['hotelImages']) < photos_number:
        photos_number = len(response['hotelImages'])

    base_urls = [image['baseUrl'] for image in response['hotelImages']][:photos_number]
    valid_urls = [url.replace('{size}', photos_size) for url in base_urls]

    return [InputMediaPhoto(media=url, caption=f"Фотография №{number + 1}") for number, url in enumerate(valid_urls)]
