import telebot
from telebot import types
import os
from loguru import logger
from botrequests import lowprice, highprice, bestdeal, history
from user import User
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import date, timedelta

logger.add(os.path.join('logs', 'total_log.log'),
           encoding='utf-8',
           format='{time} | {level}\t| {message}',
           level='DEBUG',
           rotation='100 KB',
           compression='zip')

logger.info('Запуск бота.')

bot = telebot.TeleBot(os.environ['BOT_KEY'])
help_message: str = 'Список поддерживаемых команд:\n' \
                    '/lowprice - Узнать топ самых дешёвых отелей в городе\n' \
                    '/highprice - Узнать топ самых дорогих отелей в городе \n' \
                    '/bestdeal - Узнать топ отелей, наиболее подходящих по цене и расположению от центра ' \
                    '(самые дешёвые и находятся ближе всего к центру)\n' \
                    '/history - Узнать историю поиска отелей\n' \
                    '/clearhistory - Очистить историю'

numbers_translating: dict = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }


@bot.message_handler(commands=['help'])
@logger.catch
def send_help_message(message) -> None:
    """
    Функция отправляет пользователю сообщение со списком доступных команд.
    :param message: Объект, чат с пользователем.
    :return: None
    """
    user = User.get_user(message.from_user.id)
    logger.info(f'user_id: {user.user_id}\t| function: send_help_message\t| message: {message.text}')

    bot.send_message(user.user_id, help_message)


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
@logger.catch
def starting_function(message) -> None:
    """
        Функция запрашивает город в котором искать отели и запускает цепочку инструкций для получения конечного
        результата запроса в зависимости от выбранной пользователем команды.
        :param message: Объект, чат с пользователем.
        :return: None
    """

    logger.info(f'user_id: {message.from_user.id}\t| function: get_prices\t| message: {message.text}')

    user = User.get_user(message.from_user.id)
    user.command = message.text

    bot.send_message(user.user_id, 'Введите город')
    bot.register_next_step_handler(message, get_city)


@logger.catch
def get_city(message) -> None:
    """
    Функция записывает искомый город в атрибут пользователя, запрашивает дату въезда в гостиницу
    инициализирует первый календарь и выводит его пользователю для ввода даты въезда.
    :param message: Объект, чат с пользователем.
    :return: None
    """

    logger.info(f'user_id: {message.from_user.id}\t| function: get_city\t| message: {message.text}')

    user = User.get_user(message.from_user.id)
    user.city = message.text
    bot.send_message(user.user_id, 'Введите дату въезда')
    calendar, step = DetailedTelegramCalendar(
        calendar_id=1,
        current_date=date.today(),
        min_date=date.today(),
        max_date=date.today() + timedelta(days=365),
        locale='ru'
    ).build()
    bot.send_message(user.user_id, f"Выберите {LSTEP[step]}", reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
@logger.catch
def get_arrival_date(call) -> None:
    """
    Функция записывает дату въезда в атрибут пользователя, запрашивает дату выезда из гостиницы
    инициализирует второй календарь и выводит его пользователю для ввода даты выезда.
    :param call: Объект, чат с пользователем.
    :return: None
    """
    user = User.get_user(call.message.chat.id)
    logger.info(f'user_id: {user.user_id}\t| function: get_arrival_date\t| message: {call.data}')

    result, key, step = DetailedTelegramCalendar(calendar_id=1, min_date=date.today(), locale='ru').process(call.data)
    if not result and key:
        bot.edit_message_text(f"Выберите {LSTEP[step]}", user.user_id, call.message.message_id, reply_markup=key)
    elif result:
        user.arrival_date = result
        bot.edit_message_text(f"Дата въезда: {user.arrival_date}", call.message.chat.id, call.message.message_id)

        bot.send_message(user.user_id, 'Введите дату выезда')
        calendar, step = DetailedTelegramCalendar(
            calendar_id=2,
            min_date=user.arrival_date + timedelta(days=1),
            max_date=user.arrival_date + timedelta(days=365),
            locale='ru'
        ).build()
        bot.send_message(user.user_id, f"Выберите {LSTEP[step]}", reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
@logger.catch
def get_departure_date(call) -> None:
    """
    Функция записывает дату выезда в атрибут пользователя, далее для команд /lowprice и /hiprice запрашивает количество
    отелей которые необходимо вывести в результате, для команды /bestdeal запрашивает максимальную цену.
    :param call: Объект, чат с пользователем.
    :return: None
    """
    user = User.get_user(call.message.chat.id)
    logger.info(f'user_id: {user.user_id}\t| function: get_departure_date\t| message: {call.data}')

    result, key, step = DetailedTelegramCalendar(
        calendar_id=2,
        min_date=user.arrival_date + timedelta(days=1),
        max_date=user.arrival_date + timedelta(days=365),
        locale='ru').process(call.data)

    if not result and key:
        bot.edit_message_text(f"Выберите {LSTEP[step]}", user.user_id, call.message.message_id, reply_markup=key)

    elif result:

        user.departure_date = result
        bot.edit_message_text(f"Дата выезда {user.departure_date}", user.user_id, call.message.message_id)

        if user.command == '/bestdeal':
            bot.send_message(user.user_id, 'Введите максимальную цену за сутки в RUB')
            bot.register_next_step_handler(call.message, price_range)

        else:
            keyboard = types.InlineKeyboardMarkup(row_width=5)
            keys = [types.InlineKeyboardButton(text=f'{i}', callback_data=f'{i}') for i in range(1, 11)]
            keyboard.add(*keys)
            bot.send_message(user.user_id, 'Сколько отелей вывести в результате?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
@logger.catch
def get_hotels_number(call) -> None:
    """
    Функция записывает количество отелей в атрибут пользователя, и запрашивает необходимость загрузки фотографий
    отелей которые необходимо вывести в результате.
    :param call: Объект, чат с пользователем.
    :return: None
    """
    logger.info(f'user_id: {call.message.chat.id}\t| function: get_hotels_number\t| message: {call.data}')
    user = User.get_user(call.message.chat.id)

    user.hotels_number = int(call.data)

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    key_yes = types.InlineKeyboardButton(text='Да', callback_data='Да')
    key_no = types.InlineKeyboardButton(text='Нет', callback_data='Нет')
    keyboard.add(key_yes, key_no)
    bot.send_message(user.user_id, 'Нужны ли фотографии отелей?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ['Да', 'Нет'])
@logger.catch
def upload_photo_question(call) -> None:
    """
    Функция записывает ответ пользователя о необходимости загрузки фотографий в атрибут пользователя. Если ответ "Да" -
    выводит запрос о количестве необходимых фотографий, если ответ "Нет" -  функция запускает процедуру запроса
    информации с сайта hotels.com, вызывает функцию формирующую ответную строку, выводит пользователю результат запроса
    в соответствии с введенной им командой.
    :param call: Объект, чат с пользователем.
    :return: None
    """
    user = User.get_user(call.message.chat.id)
    logger.info(f'user_id: {user.user_id}\t| function: upload_photo_question\t| message: {call.data}')

    if call.data == 'Да':
        user.uploading_photos = True

        keyboard = types.InlineKeyboardMarkup(row_width=5)
        keys = [types.InlineKeyboardButton(text=f'{v}', callback_data=k) for k, v in numbers_translating.items()]
        keyboard.add(*keys)
        bot.send_message(user.user_id, 'Сколько фотографий вывести?', reply_markup=keyboard)

    else:
        user.uploading_photos = False

        if user.command == '/lowprice':
            bot.send_message(user.user_id, '⏳ Идет запрос...')
            hotels_list = lowprice.get_response(city=user.city,
                                                arrival_date=user.arrival_date,
                                                departure_date=user.departure_date,
                                                hotels_number=user.hotels_number,
                                                upload_photos=user.uploading_photos)
            log_data = f'\nГород: {user.city}'

            if hotels_list:
                for i in range(len(hotels_list)):
                    response, log_string = form_response_string(user.user_id, i, hotels_list[i])
                    bot.send_message(user.user_id, response)
                    log_data = '\n'.join((log_data, log_string))
                bot.send_message(user.user_id, f'Запрос завершен.\nВсего найдено отелей: {len(hotels_list)}')

            else:
                bot.send_message(user.user_id, 'К сожалению по заданным параметрам ничего не найдено.')
                log_data = '\n'.join((log_data, 'К сожалению по заданным параметрам ничего не найдено.'))

            history.write_log(user.user_id, user.command, log_data)

        elif user.command == '/highprice':
            bot.send_message(user.user_id, '⏳ Идет запрос...')
            hotels_list = highprice.get_response(city=user.city,
                                                 arrival_date=user.arrival_date,
                                                 departure_date=user.departure_date,
                                                 hotels_number=user.hotels_number,
                                                 upload_photos=user.uploading_photos)
            log_data = f'\nГород: {user.city}'

            if hotels_list:
                for i in range(len(hotels_list)):
                    response, log_string = form_response_string(user.user_id, i, hotels_list[i])
                    bot.send_message(user.user_id, response)
                    log_data = '\n'.join((log_data, log_string))
                bot.send_message(user.user_id, f'Запрос завершен.\nВсего найдено отелей: {len(hotels_list)}')

            else:
                bot.send_message(user.user_id, 'К сожалению по заданным параметрам ничего не найдено.')
                log_data = '\n'.join((log_data, 'К сожалению по заданным параметрам ничего не найдено.'))

            history.write_log(user.user_id, user.command, log_data)

        elif user.command == '/bestdeal':
            bot.send_message(user.user_id, '⏳ Идет запрос...')
            hotels_list = bestdeal.get_response(city=user.city,
                                                max_price=user.max_price,
                                                max_distance=user.max_distance,
                                                arrival_date=user.arrival_date,
                                                departure_date=user.departure_date,
                                                hotels_number=user.hotels_number,
                                                upload_photos=user.uploading_photos)
            log_data = f'\nГород: {user.city}'

            if hotels_list:
                for i in range(len(hotels_list)):
                    response, log_string = form_response_string(user.user_id, i, hotels_list[i])
                    bot.send_message(user.user_id, response)
                    log_data = '\n'.join((log_data, log_string))
                bot.send_message(user.user_id, f'Запрос завершен.\nВсего найдено отелей: {len(hotels_list)}')

            else:
                bot.send_message(user.user_id, 'К сожалению по заданным параметрам ничего не найдено.')
                log_data = '\n'.join((log_data, 'К сожалению по заданным параметрам ничего не найдено.'))

            history.write_log(user.user_id, user.command, log_data)


@bot.callback_query_handler(
    func=lambda call: call.data in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
)
@logger.catch
def get_photos_number(call) -> None:
    """
    Функция записывает количество фотографий в атрибут пользователя и запускает процедуру запроса информации с
    сайта hotels.com, вызывает функцию формирующую ответную строку, выводит пользователю результат запроса в
    соответствии с введенной им командой.
    :param call: Объект, чат с пользователем.
    :return: None
    """
    user = User.get_user(call.message.chat.id)
    logger.info(f'user_id: {user.user_id}\t| function: get_photos_number\t| message: {call.data}')

    user.number_photos = numbers_translating[call.data]

    if user.command == '/lowprice':
        bot.send_message(user.user_id, '⏳ Идет запрос...')

        hotels_list = lowprice.get_response(city=user.city,
                                            arrival_date=user.arrival_date,
                                            departure_date=user.departure_date,
                                            hotels_number=user.hotels_number,
                                            upload_photos=user.uploading_photos,
                                            photos_number=user.number_photos)
        log_data = f'\nГород: {user.city}'

        if hotels_list:
            for i in range(len(hotels_list)):

                response, log_string = form_response_string(user.user_id, i, hotels_list[i])
                bot.send_message(user.user_id, response)

                log_data = '\n'.join((log_data, log_string))
                try:
                    bot.send_media_group(user.user_id, hotels_list[i][6])
                except Exception as error:
                    logger.error(
                        f'user_id: {user.user_id}\t'
                        f'| bot.send_media_group(user.user_id, hotels_list[i][6])\t'
                        f'| message: {error}')
                    bot.send_message(user.user_id, f'Фотографии отеля №{i + 1} загрузить не удалось :(')

            bot.send_message(user.user_id, f'Запрос завершен.\nВсего найдено отелей: {len(hotels_list)}')

        else:
            bot.send_message(user.user_id, 'К сожалению по заданным параметрам ничего не найдено.')
            log_data = '\n'.join((log_data, 'К сожалению по заданным параметрам ничего не найдено.'))

        history.write_log(user.user_id, user.command, log_data)

    elif user.command == '/highprice':
        bot.send_message(user.user_id, '⏳ Идет запрос...')

        hotels_list = highprice.get_response(city=user.city,
                                             arrival_date=user.arrival_date,
                                             departure_date=user.departure_date,
                                             hotels_number=user.hotels_number,
                                             upload_photos=user.uploading_photos,
                                             photos_number=user.number_photos)
        log_data = f'\nГород: {user.city}'

        if hotels_list:
            for i in range(len(hotels_list)):
                response, log_string = form_response_string(user.user_id, i, hotels_list[i])
                bot.send_message(user.user_id, response)

                log_data = '\n'.join((log_data, log_string))
                try:
                    bot.send_media_group(user.user_id, hotels_list[i][6])
                except Exception as error:
                    logger.error(
                        f'user_id: {user.user_id}\t'
                        f'| bot.send_media_group(user.user_id, hotels_list[i][6])\t'
                        f'| message: {error}')
                    bot.send_message(user.user_id, f'Фотографии отеля №{i + 1} загрузить не удалось :(')

            bot.send_message(user.user_id, f'Запрос завершен.\nВсего найдено отелей: {len(hotels_list)}')

        else:
            bot.send_message(user.user_id, 'К сожалению по заданным параметрам ничего не найдено.')
            log_data = '\n'.join((log_data, 'К сожалению по заданным параметрам ничего не найдено.'))

        history.write_log(user.user_id, user.command, log_data)

    elif user.command == '/bestdeal':
        bot.send_message(user.user_id, '⏳ Идет запрос...')

        hotels_list = bestdeal.get_response(city=user.city,
                                            max_price=user.max_price,
                                            max_distance=user.max_distance,
                                            arrival_date=user.arrival_date,
                                            departure_date=user.departure_date,
                                            hotels_number=user.hotels_number,
                                            upload_photos=user.uploading_photos,
                                            photos_number=user.number_photos)
        log_data = f'\nГород: {user.city}'

        if hotels_list:
            for i in range(len(hotels_list)):
                response, log_string = form_response_string(user.user_id, i, hotels_list[i])
                bot.send_message(user.user_id, response)

                log_data = '\n'.join((log_data, log_string))
                try:
                    bot.send_media_group(user.user_id, hotels_list[i][6])
                except Exception as error:
                    logger.error(
                        f'user_id: {user.user_id}\t'
                        f'| bot.send_media_group(user.user_id, hotels_list[i][6])\t'
                        f'| message: {error}')
                    bot.send_message(user.user_id, f'Фотографии отеля №{i + 1} загрузить не удалось :(')

            bot.send_message(user.user_id, f'Запрос завершен.\nВсего найдено отелей: {len(hotels_list)}')

        else:
            bot.send_message(user.user_id, 'К сожалению по заданным параметрам ничего не найдено.')
            log_data = '\n'.join((log_data, 'К сожалению по заданным параметрам ничего не найдено.'))

        history.write_log(user.user_id, user.command, log_data)


@logger.catch
def price_range(message) -> None:
    """
    Функция записывает максимальную цену в атрибут пользователя и запрашивает максимальное расстояние от центра города.
    :param message: Объект, чат с пользователем.
    :return: None
    """
    user = User.get_user(message.from_user.id)
    logger.info(f'user_id: {user.user_id}\t| function: price_range\t| message: {message.text}')

    if not message.text.isdigit():
        bot.send_message(user.user_id, 'Ошибка ввода. Введите число цифрами.')
        bot.register_next_step_handler(message, price_range)

    else:
        user.max_price = int(message.text)
        bot.send_message(user.user_id,
                         'Введите максимальное расстояние от центра города в километрах')
        bot.register_next_step_handler(message, distance_range)


@logger.catch
def distance_range(message) -> None:
    """
    Функция записывает максимальное расстояние в атрибут пользователя и запрашивает количество отелей которые
    необходимо вывести в результате.
    :param message: Объект, чат с пользователем.
    :return: None
    """
    logger.info(f'user_id: {message.from_user.id}\t| function: distance_range\t| message: {message.text}')
    user = User.get_user(message.from_user.id)

    if not message.text.isdigit():
        bot.send_message(user.user_id, 'Ошибка ввода. Введите число цифрами.')
        bot.register_next_step_handler(message, distance_range)
    else:
        user.max_distance = int(message.text)

        keyboard = types.InlineKeyboardMarkup(row_width=5)
        keys = [types.InlineKeyboardButton(text=f'{i}', callback_data=f'{i}') for i in range(1, 11)]
        keyboard.add(*keys)
        bot.send_message(user.user_id, 'Сколько отелей вывести в результате?', reply_markup=keyboard)


@bot.message_handler(commands=['history'])
@logger.catch
def history_command(message) -> None:
    """
    Функция отлавливает команду "/history" и выводит пользователю историю его запросов.
    :param message: Объект, чат с пользователем.
    :return: None
    """
    logger.info(f'user_id: {message.from_user.id}\t| function: history_command\t| message: {message.text}')
    user = User.get_user(message.from_user.id)

    bot.send_message(user.user_id, history.read_log(user.user_id))


@bot.message_handler(commands=['clearhistory'])
@logger.catch
def clear_history_command(message) -> None:
    """
    Функция отлавливает команду "/clearhistory" и спрашивает у пользователя действительно ли он хочет очистить историю
    поиска.
    :param message: Объект, чат с пользователем.
    :return: None
    """
    logger.info(f'user_id: {message.from_user.id}\t| function: clearhistory_command\t| message: {message.text}')
    user = User.get_user(message.from_user.id)

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    key_yes = types.InlineKeyboardButton(text='Да', callback_data='y')
    key_no = types.InlineKeyboardButton(text='Нет', callback_data='n')
    keyboard.add(key_yes, key_no)
    bot.send_message(user.user_id, 'Очистить историю поиска?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ['y', 'n'])
@logger.catch
def clear_history(call) -> None:

    user = User.get_user(call.message.chat.id)
    logger.info(f'user_id: {user.user_id}\t| function: clear_history\t| message: {call.data}')

    if call.data == 'y':
        history.clear_history(user.user_id)
        bot.edit_message_text('История очищена.', call.message.chat.id, call.message.message_id)
    elif call.data == 'n':
        bot.edit_message_text(help_message, call.message.chat.id, call.message.message_id)


@bot.message_handler(content_types=['text'])
@logger.catch
def get_text_messages(message) -> None:
    """
    Функция отлавливает приветственные и прощальные сообщения, выводит пользователю ответы на них.
    Реагирует на некорректные сообщения, предлагает доступные команды.
    :param message:
    :return: None
    """
    logger.info(f'user_id: {message.from_user.id}\t| function: get_text_messages\t| message: {message.text}')

    if message.text.lower() in ['привет', 'hello', 'hi', '/start']:
        bot.send_message(message.from_user.id, 'Привет, я бот-помощник компании "Too Easy Travel", '
                                               'чтобы узнать список доступных команд, напишите /help')
    elif message.text.lower() in ['пока', '/end', 'bye', '/stop']:
        bot.send_message(message.from_user.id, 'До свидания! Спасибо за то что выбрали "Too Easy Travel"!')
    else:
        bot.send_message(message.from_user.id, "Я Вас не понимаю. Напишите /start или /help.")


@logger.catch
def form_response_string(user_id: str, num: int, tpl: tuple) -> tuple[str, str]:
    """
    Функция формирует ответное сообщение пользователю по результатам запроса.
    :param user_id: str Идентификатор пользователя.
    :param num: int Индекс элемента спика, используется для нумерации ответов.
    :param tpl: tuple Кортеж с результатами запроса.
    :return: tuple Кортеж содержит 2 элемента: 1- ответная строка пользователю, 2- строка для записи в файл истории.
    """
    user = User.get_user(user_id)
    logger.info(f'user_id: {user_id}\t| function: form_response_string\t|')

    length_of_stay = user.departure_date - user.arrival_date

    result: str = f'{num + 1}. Название: {tpl[1]}\n' \
                  f'Ссылка: {tpl[0]}\n' \
                  f'Расстояние до "{tpl[4]}": {tpl[5]}\n' \
                  f'Цена за одни сутки: {tpl[2]}\n' \
                  f'Период проживания, дней: {length_of_stay.days}\n' \
                  f'Стоимость за весь период проживания: {length_of_stay.days * int(tpl[3]): ,} RUB\n'

    for_history: str = f'{num + 1}. {tpl[1]}'

    return result, for_history


if __name__ == '__main__':

    bot.polling(none_stop=True, interval=0)
    logger.info('Остановка бота.')
