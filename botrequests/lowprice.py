import requests
import os
import datetime
from telebot.types import InputMediaPhoto


headers = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': os.environ['RAPIDAPI_KEY']
    }


def get_destination_id(destination):

    params = {
        "query": destination,
        "locale": "ru_RU",
        "currency": "RUB"
    }
    url = "https://hotels4.p.rapidapi.com/locations/v2/search"

    response = requests.request("GET", url, headers=headers, params=params)
    result = response.json()
    return result['suggestions'][0]["entities"][0]["destinationId"] \
        if len(result['suggestions'][0]["entities"]) \
        else None


def get_response(city, hotels_number, upload_photos, photos_number=None):
    url = "https://hotels4.p.rapidapi.com/properties/list"

    destination_id = get_destination_id(city)

    if not destination_id:
        return None

    arrival_date = datetime.date.today()
    departure_date = arrival_date + datetime.timedelta(days=1)
    length_of_stay = (departure_date - arrival_date).days

    querystring = {"destinationId": int(destination_id),
                   "pageNumber": "1",
                   "pageSize": hotels_number,
                   "checkIn": arrival_date,
                   "checkOut": departure_date,
                   "adults1": "1",
                   "sortOrder": "PRICE",
                   "locale": "ru_RU",
                   "currency": "RUB"}

    response = requests.request("GET", url, headers=headers, params=querystring).json()

    if len(response['data']['body']['searchResults']['results']) == 0:
        return None

    if upload_photos:
        result_tuples_list = [
            (f"ru.hotels.com/ho{hotel['id']}/", hotel['name'], hotel['ratePlan']['price']['current'],
             get_hotel_photos(hotel['id'], photos_number))
            for hotel in response['data']['body']['searchResults']['results']]
        return result_tuples_list
    else:
        result_tuples_list = [
            (f"ru.hotels.com/ho{hotel['id']}/", hotel['name'], hotel['ratePlan']['price']['current'])
            for hotel in response['data']['body']['searchResults']['results']]
    return result_tuples_list


def get_hotel_photos(hotel_id, photos_number, photos_size='z'):

    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    querystring = {'id': hotel_id}

    response = requests.request("GET", url, headers=headers, params=querystring).json()

    if len(response['hotelImages']) < photos_number:
        photos_number = len(response['hotelImages'])

    base_urls = [image['baseUrl'] for image in response['hotelImages']][:photos_number]
    valid_urls = [url.replace('{size}', photos_size) for url in base_urls]

    return [InputMediaPhoto(media=url, caption=f"Фотография №{number + 1}") for number, url in enumerate(valid_urls)]
