import telebot
import os
from botrequests import lowprice, highprice, bestdeal, history

bot = telebot.TeleBot(os.environ['BOT_KEY'])
help_message = 'Список поддерживаемых команд:\n' \
               '/lowprice - Узнать топ самых дешёвых отелей в городе\n' \
               '/highprice - Узнать топ самых дорогих отелей в городе \n' \
               '/bestdeal - Узнать топ отелей, наиболее подходящих по цене и расположению от центра ' \
               '(самые дешёвые и находятся ближе всего к центру)\n' \
               '/history - Узнать историю поиска отелей '


@bot.message_handler(commands=['help'])
def start_message(message):
    bot.send_message(message.chat.id, help_message)


@bot.message_handler(commands=['lowprice', 'highprice'])
def start_message(message):
    # TODO Тут будут запросы (город, количество отелей и т.д.)
    if message.text == '/lowprice':
        bot.send_message(message.from_user.id, lowprice.get_response(message.text))
    elif message.text == '/highprice':
        bot.send_message(message.from_user.id, highprice.get_response(message.text))


@bot.message_handler(commands=['bestdeal'])
def start_message(message):
    # TODO Тут будут запросы (город, диапазон цен, диапазон расстояний, количество отелей и т.д.)
    bot.send_message(message.from_user.id, bestdeal.get_response(message.text))


@bot.message_handler(commands=['history'])
def start_message(message):
    bot.send_message(message.from_user.id, history.get_response(message.text))


@bot.message_handler(content_types=['text'])
def get_text_messages(message):

    if message.text.lower() in ['привет', '/hello-world', '/start']:
        bot.send_message(message.from_user.id, 'Привет, я бот-помощник компании "Too Easy Travel",'
                                               'чтобы узнать список доступных команд, напишите /help')
    else:
        bot.send_message(message.from_user.id, "Я Вас не понимаю. Напишите /start или /help.")


if __name__ == '__main__':

    bot.polling(none_stop=True, interval=0)
