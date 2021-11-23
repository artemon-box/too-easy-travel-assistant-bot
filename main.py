import telebot
from telebot import types
import os
from loguru import logger
from botrequests import lowprice, highprice, bestdeal, history

logger.add(os.path.join('logs', 'total_log.log'),
           encoding='utf-8',
           format='{time} | {level}\t| {message}',
           level='DEBUG',
           rotation='100 KB',
           compression='zip')

logger.info('Запуск бота.')

bot = telebot.TeleBot(os.environ['BOT_KEY'])
help_message = 'Список поддерживаемых команд:\n' \
               '/lowprice - Узнать топ самых дешёвых отелей в городе\n' \
               '/highprice - Узнать топ самых дорогих отелей в городе \n' \
               '/bestdeal - Узнать топ отелей, наиболее подходящих по цене и расположению от центра ' \
               '(самые дешёвые и находятся ближе всего к центру)\n' \
               '/history - Узнать историю поиска отелей\n' \
               '/clearhistory - Очистить историю'


class User:
    users = dict()

    def __init__(self, user_id):
        self.user_id = user_id
        User.add_user(user_id, self)
        self.command = ''
        self.city = ''
        self.hotels_number = 0
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
@logger.catch
def send_help_message(message):
    logger.info(f'user_id: {message.from_user.id}\t| function: send_help_message\t| message: {message.text}')
    bot.send_message(message.from_user.id, help_message)


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
@logger.catch
def get_prices(message):
    logger.info(f'user_id: {message.from_user.id}\t| function: get_prices\t| message: {message.text}')
    user = User.get_user(message.from_user.id)
    user.command = message.text
    bot.send_message(user.user_id, 'Введите город')
    bot.register_next_step_handler(message, get_city)


@logger.catch
def get_city(message):
    logger.info(f'user_id: {message.from_user.id}\t| function: get_city\t| message: {message.text}')
    user = User.get_user(message.from_user.id)
    user.city = message.text

    if user.command == '/bestdeal':
        bot.send_message(user.user_id, 'Введите диапазон цен за сутки, в USD, через тире (например: 50-300)')
        bot.register_next_step_handler(message, price_range)

    else:
        bot.send_message(user.user_id, 'Сколько отелей вывести в результате (максимум 10)?')
        bot.register_next_step_handler(message, get_hotels_number)


@logger.catch
def get_hotels_number(message):
    logger.info(f'user_id: {message.from_user.id}\t| function: get_hotels_number\t| message: {message.text}')
    user = User.get_user(message.from_user.id)

    if not message.text.isdigit():
        bot.send_message(user.user_id, 'Ошибка ввода. Введите число цифрами.')
        bot.register_next_step_handler(message, get_hotels_number)

    else:
        user.hotels_number = int(message.text) if 0 < int(message.text) < 11 else 10
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='Да')
        keyboard.add(key_yes)
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='Нет')
        keyboard.add(key_no)
        bot.send_message(user.user_id, 'Нужны ли фотографии отелей?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
@logger.catch
def upload_photo_question(call):
    user = User.get_user(call.message.chat.id)
    logger.info(f'user_id: {user.user_id}\t| function: upload_photo_question\t| message: {call.data}')

    if call.data == 'Да':
        user.uploading_photos = True
        bot.send_message(user.user_id, 'Сколько фотографий вывести (максимум 10)?')
        bot.register_next_step_handler(call.message, get_photos_number)

    else:
        user.uploading_photos = False

        if user.command == '/lowprice':
            bot.send_message(user.user_id, '⏳ Идет запрос...')
            hotels_list = lowprice.get_response(user.city, user.hotels_number, user.uploading_photos)
            log_data = ''

            if hotels_list:
                for i in range(len(hotels_list)):
                    response, log_string = form_response_string(user.user_id, i, hotels_list[i])
                    bot.send_message(user.user_id, response)
                    log_data = '\n'.join((log_data, log_string))
                    bot.send_message(user.user_id, f'Всего найдено отелей: {len(hotels_list)}')

            else:
                bot.send_message(user.user_id, 'К сожалению ничего не найдено.')
                log_data = '\nК сожалению ничего не найдено.'

            history.write_log(user.user_id, user.command, log_data)

        elif user.command == '/highprice':
            bot.send_message(user.user_id, '⏳ Идет запрос...')
            response, log_data = highprice.get_response(user.city, user.hotels_number, user.uploading_photos)
            bot.send_message(user.user_id, response)
            history.write_log(user.user_id, user.command, log_data)

        elif user.command == '/bestdeal':
            bot.send_message(user.user_id, '⏳ Идет запрос...')
            response, log_data = bestdeal.get_response(user.city, user.hotels_number, user.uploading_photos,
                                                       photos_number=None, price_range=user.price_range,
                                                       distance_range=user.distance_range)
            bot.send_message(user.user_id, response)
            history.write_log(user.user_id, user.command, log_data)


@logger.catch
def get_photos_number(message):
    logger.info(f'user_id: {message.from_user.id}\t| function: get_photos_number\t| message: {message.text}')
    user = User.get_user(message.from_user.id)

    if not message.text.isdigit():
        bot.send_message(user.user_id, 'Ошибка ввода. Введите число цифрами.')
        bot.register_next_step_handler(message, get_photos_number)

    else:
        user.number_photos = int(message.text) if 0 < int(message.text) < 11 else 10

        if user.command == '/lowprice':
            bot.send_message(user.user_id, '⏳ Идет запрос...')
            hotels_list = lowprice.get_response(
                user.city, user.hotels_number, user.uploading_photos, user.number_photos
            )
            log_data = ''

            if hotels_list:
                for i in range(len(hotels_list)):
                    response, log_string = form_response_string(user.user_id, i, hotels_list[i])
                    bot.send_message(user.user_id, response)
                    log_data = '\n'.join((log_data, log_string))
                    bot.send_media_group(user.user_id, hotels_list[i][3])
                bot.send_message(user.user_id, f'Всего найдено отелей: {len(hotels_list)}')

            else:
                bot.send_message(user.user_id, 'К сожалению ничего не найдено.')
                log_data = '\nК сожалению ничего не найдено.'

            history.write_log(user.user_id, user.command, log_data)

        elif user.command == '/highprice':
            bot.send_message(user.user_id, '⏳ Идет запрос...')
            response, log_data = highprice.get_response(
                user.city, user.hotels_number, user.uploading_photos, user.number_photos)
            bot.send_message(user.user_id, response)
            history.write_log(user.user_id, user.command, log_data)

        elif user.command == '/bestdeal':
            bot.send_message(user.user_id, '⏳ Идет запрос...')
            response, log_data = bestdeal.get_response(
                user.city, user.hotels_number, user.uploading_photos, user.number_photos, user.price_range,
                user.distance_range)
            bot.send_message(user.user_id, response)
            history.write_log(user.user_id, user.command, log_data)


@logger.catch
def price_range(message):
    logger.info(f'user_id: {message.from_user.id}\t| function: price_range\t| message: {message.text}')
    user = User.get_user(message.from_user.id)
    user.price_range = message.text
    bot.send_message(user.user_id,
                     'Введите диапазон расстояния, на котором находится отель от центра, в метрах (например: 100-3000.')
    bot.register_next_step_handler(message, distance_range)


@logger.catch
def distance_range(message):
    logger.info(f'user_id: {message.from_user.id}\t| function: distance_range\t| message: {message.text}')
    user = User.get_user(message.from_user.id)
    user.distance_range = message.text
    bot.send_message(user.user_id, 'Сколько отелей вывести в результате (максимум 10)?')
    bot.register_next_step_handler(message, get_hotels_number)


@bot.message_handler(commands=['history'])
@logger.catch
def history_command(message):
    logger.info(f'user_id: {message.from_user.id}\t| function: history_command\t| message: {message.text}')
    user = User.get_user(message.from_user.id)
    bot.send_message(user.user_id, history.read_log(user.user_id))


@bot.message_handler(commands=['clearhistory'])
@logger.catch
def clear_history_command(message):
    logger.info(f'user_id: {message.from_user.id}\t| function: clearhistory_command\t| message: {message.text}')
    user = User.get_user(message.from_user.id)
    history.clear_history(user.user_id)
    bot.send_message(user.user_id, 'История очищена.')


@bot.message_handler(content_types=['text'])
@logger.catch
def get_text_messages(message):
    logger.info(f'user_id: {message.from_user.id}\t| function: get_text_messages\t| message: {message.text}')

    if message.text.lower() in ['привет', '/hello-world', '/start']:
        bot.send_message(message.from_user.id, 'Привет, я бот-помощник компании "Too Easy Travel", '
                                               'чтобы узнать список доступных команд, напишите /help')
    elif message.text.lower() in ['пока', '/end', 'bye', '/stop']:
        bot.send_message(message.from_user.id, 'До свидания! Спасибо за то что выбрали "Too Easy Travel"!')
    else:
        bot.send_message(message.from_user.id, "Я Вас не понимаю. Напишите /start или /help.")


@logger.catch
def form_response_string(user_id, num, tpl: tuple):
    logger.info(f'user_id: {user_id}\t| function: form_response_string\t|')

    result_string = f'{num + 1}. Название: {tpl[1]}\nСсылка: {tpl[0]}\nЦена за одни сутки: {tpl[2]}\n'
    for_history = f'{num + 1}. {tpl[1]}'
    return result_string, for_history


if __name__ == '__main__':

    bot.polling(none_stop=True, interval=0)
    logger.info('Остановка бота.')
