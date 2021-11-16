import requests
import os

# url = "https://hotels4.p.rapidapi.com/locations/search"
#
# querystring = {"query": "new york", "locale": "en_US"}
#
# headers = {
#     'x-rapidapi-host': "hotels4.p.rapidapi.com",
#     'x-rapidapi-key': os.environ['RAPIDAPI_KEY']
#     }
#
# response = requests.request("GET", url, headers=headers, params=querystring)
#
# print(response.text)


def get_response(city, hotels_number, upload_photos, photos_number=None):
    return f'Запрашиваем город: {city}\nКоличество отелей: {hotels_number}\nЗагружать фото: {upload_photos}' \
           f'\nКоличество фотографий: {photos_number}' if upload_photos \
        else f'Запрашиваем город: {city}\nКоличество отелей: {hotels_number}\nЗагружать фото: {upload_photos}', \
           'Информация для лог-файла'
