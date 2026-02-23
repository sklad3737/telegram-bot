import telebot
from telebot import types

TOKEN = "8273823469:AAETywYPcSdUrkM9H9z2ySe1KN8HNWsN1QM"
GROUP_ID = -1003783425494

bot = telebot.TeleBot(TOKEN)

user_data = {}
request_counter = 1


# Старт
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Создать заявку")
    bot.send_message(message.chat.id, "Нажмите кнопку ниже:", reply_markup=markup)


# Создание заявки
@bot.message_handler(func=lambda message: message.text == "Создать заявку")
def choose_pharmacy(message):
    markup = types.InlineKeyboardMarkup(row_width=5)

    buttons = []
    for i in range(1, 26):
        buttons.append(types.InlineKeyboardButton(f"{i}", callback_data=f"pharmacy_{i}"))

    markup.add(*buttons)
    bot.send_message(message.chat.id, "Выберите аптеку:", reply_markup=markup)


# Выбор аптеки
@bot.callback_query_handler(func=lambda call: call.data.startswith("pharmacy_"))
def choose_problem(call):
    pharmacy_number = call.data.split("_")[1]
    user_data[call.from_user.id] = {"pharmacy": pharmacy_number}

    markup = types.InlineKeyboardMarkup()
    problems = [
        "1С/Касса",
        "Компьютер",
        "Интернет",
        "Освещение",
        "Другое"
    ]

    for problem in problems:
        markup.add(types.InlineKeyboardButton(problem, callback_data=f"problem_{problem}"))

    bot.edit_message_text(
        "Выберите тип проблемы:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


# Выбор проблемы
@bot.callback_query_handler(func=lambda call: call.data.startswith("problem_"))
def get_description(call):
    problem = call.data.split("_", 1)[1]
    user_data[call.from_user.id]["problem"] = problem

    bot.edit_message_text(
        "Опишите проблему текстом.\nМожно прикрепить фото следующим сообщением.",
        call.message.chat.id,
        call.message.message_id
    )


# Получение текста
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "Создать заявку":
        return

    if message.from_user.id in user_data:
        user_data[message.from_user.id]["description"] = message.text
        user_data[message.from_user.id]["photo"] = None

        bot.send_message(message.chat.id, "Отправьте фото (если нужно) или напишите /done для отправки заявки")

       @bot.message_handler(commands=['done'])
def finish_request(message):
    if message.from_user.id in user_data:
        send_request(message.from_user.id)
        bot.send_message(message.chat.id, "✅ Заявка отправлена")


# Получение фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.from_user.id in user_data:
        user_data[message.from_user.id]["photo"] = message.photo[-1].file_id
        bot.send_message(message.chat.id, "Фото добавлено. Напишите /done для отправки заявки")


def send_request(user_id):
    global request_counter

    data = user_data[user_id]

from datetime import datetime

user_info = bot.get_chat(user_id)

if user_info.username:
    username = "@" + user_info.username
else:
    username = user_info.first_name

time_now = datetime.now().strftime("%d.%m.%Y %H:%M")

   text = (
    f"📌 Заявка №{request_counter}\n"
    f"👤 От: {username}\n"
    f"🕒 Дата: {time_now}\n"
    f"Аптека: {data['pharmacy']}\n"
    f"Тип: {data['problem']}\n"
    f"Описание: {data['description']}"
)
    if data["photo"]:
        bot.send_photo(GROUP_ID, data["photo"], caption=text)
    else:
        bot.send_message(GROUP_ID, text)

    request_counter += 1
    user_data.pop(user_id)


print("Бот запущен...")
bot.infinity_polling()


