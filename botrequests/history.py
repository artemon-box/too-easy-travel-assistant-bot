import requests
import os
import math

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


def get_response(command):
    return f'Тут будет ответ на команду {command}, а пока вот вам число пи 4 раза {math.pi, math.pi, math.pi, math.pi}'
