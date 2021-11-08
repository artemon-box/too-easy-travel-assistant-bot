import telebot


key = '2122215025:AAGtIHHyGpB2Y50rLszbt7meDTOjXULwEdU'
bot = telebot.TeleBot(key)
help_message = 'Список поддерживаемых команд:\n' \
               '/lowprice - Узнать топ самых дешёвых отелей в городе\n' \
               '/highprice - Узнать топ самых дорогих отелей в городе \n' \
               '/bestdeal - Узнать топ отелей, наиболее подходящих по цене и расположению от центра ' \
               '(самые дешёвые и находятся ближе всего к центру)\n' \
               '/history - Узнать историю поиска отелей '


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text.lower() in ["привет", '/hello-world']:
        bot.send_message(message.from_user.id, "Привет, я бот-помощник компании 'Too Easy Travel',"
                                               " чем я могу Вам помочь?")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, help_message)
    else:
        bot.send_message(message.from_user.id, "Я Вас не понимаю. Напишите /help.")


if __name__ == '__main__':

    bot.polling(none_stop=True, interval=0)
