import telebot
from telebot import types
import os
from botrequests import lowprice, highprice, bestdeal, history

bot = telebot.TeleBot(os.environ['BOT_KEY'])
help_message = 'Список поддерживаемых команд:\n' \
               '/lowprice - Узнать топ самых дешёвых отелей в городе\n' \
               '/highprice - Узнать топ самых дорогих отелей в городе \n' \
               '/bestdeal - Узнать топ отелей, наиболее подходящих по цене и расположению от центра ' \
               '(самые дешёвые и находятся ближе всего к центру)\n' \
               '/history - Узнать историю поиска отелей '


class User:
    users = dict()

    def __init__(self, user_id):
        self.user_id = user_id
        User.add_user(user_id, self)
        self.command = ''
        self.city = ''
        self.hotels_number = ''
        self.uploading_photos = False
        self.number_photos = 0
        self.price_range = ''
        self.distance_range = ''

    @classmethod
    def add_user(cls, user_id, user):
        cls.users[user_id] = user

    @classmethod
    def get_user(cls, user_id):
        if user_id in cls.users:
            return cls.users[user_id]
        User(user_id)
        return cls.users[user_id]


@bot.message_handler(commands=['help'])
def send_help_message(message):
    bot.send_message(message.from_user.id, help_message)


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def get_prices(message):
    user = User.get_user(message.from_user.id)
    user.command = message.text
    bot.send_message(user.user_id, 'Введите город')
    bot.register_next_step_handler(message, get_city)


def get_city(message):
    user = User.get_user(message.from_user.id)
    user.city = message.text
    if user.command == '/bestdeal':
        bot.send_message(user.user_id, 'Введите диапазон цен за сутки, в USD, через тире (например: 50-300)')
        bot.register_next_step_handler(message, price_range)
    else:
        bot.send_message(user.user_id, 'Сколько отелей вывести в результате?')
        bot.register_next_step_handler(message, get_hotels_number)


def get_hotels_number(message):
    user = User.get_user(message.from_user.id)
    user.hotels_number = message.text
    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text='Да', callback_data='Да')
    keyboard.add(key_yes)
    key_no = types.InlineKeyboardButton(text='Нет', callback_data='Нет')
    keyboard.add(key_no)
    bot.send_message(user.user_id, 'Нужны ли фотографии отелей?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def upload_photo_question(call):
    user = User.get_user(call.message.chat.id)
    if call.data == 'Да':
        user.uploading_photos = True
        bot.send_message(user.user_id, 'Сколько фотографий вывести?')
        bot.register_next_step_handler(call.message, get_photos_number)
    else:
        user.uploading_photos = False
        if user.command == '/lowprice':
            response, log_data = lowprice.get_response(user.city, user.hotels_number, user.uploading_photos)
            bot.send_message(user.user_id, response)
            history.write_log(user.user_id, user.command, log_data)
        elif user.command == '/highprice':
            response, log_data = highprice.get_response(user.city, user.hotels_number, user.uploading_photos)
            bot.send_message(user.user_id, response)
            history.write_log(user.user_id, user.command, log_data)
        elif user.command == '/bestdeal':
            response, log_data = bestdeal.get_response(user.city, user.hotels_number, user.uploading_photos,
                                                       photos_number=None, price_range=user.price_range,
                                                       distance_range=user.distance_range)
            bot.send_message(user.user_id, response)
            history.write_log(user.user_id, user.command, log_data)


def get_photos_number(message):
    user = User.get_user(message.from_user.id)
    user.number_photos = message.text
    if user.command == '/lowprice':
        response, log_data = lowprice.get_response(
            user.city, user.hotels_number, user.uploading_photos, user.number_photos)
        bot.send_message(user.user_id, response)
        history.write_log(user.user_id, user.command, log_data)
    elif user.command == '/highprice':
        response, log_data = highprice.get_response(
            user.city, user.hotels_number, user.uploading_photos, user.number_photos)
        bot.send_message(user.user_id, response)
        history.write_log(user.user_id, user.command, log_data)
    elif user.command == '/bestdeal':
        response, log_data = bestdeal.get_response(
            user.city, user.hotels_number, user.uploading_photos, user.number_photos, user.price_range,
            user.distance_range)
        bot.send_message(user.user_id, response)
        history.write_log(user.user_id, user.command, log_data)


def price_range(message):
    user = User.get_user(message.from_user.id)
    user.price_range = message.text
    bot.send_message(user.user_id,
                     'Введите диапазон расстояния, на котором находится отель от центра, в метрах (например: 100-3000.')
    bot.register_next_step_handler(message, distance_range)


def distance_range(message):
    user = User.get_user(message.from_user.id)
    user.distance_range = message.text
    bot.send_message(user.user_id, 'Сколько отелей вывести в результате?')
    bot.register_next_step_handler(message, get_hotels_number)


@bot.message_handler(commands=['history'])
def history_command(message):
    user = User.get_user(message.from_user.id)
    bot.send_message(user.user_id, history.read_log(user.user_id))


@bot.message_handler(content_types=['text'])
def get_text_messages(message):

    if message.text.lower() in ['привет', '/hello-world', '/start']:
        bot.send_message(message.from_user.id, 'Привет, я бот-помощник компании "Too Easy Travel", '
                                               'чтобы узнать список доступных команд, напишите /help')
    else:
        bot.send_message(message.from_user.id, "Я Вас не понимаю. Напишите /start или /help.")


if __name__ == '__main__':

    bot.polling(none_stop=True, interval=0)
