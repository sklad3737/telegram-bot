import telebot
from telebot import types
from datetime import datetime

TOKEN = "8273823469:AAETywYPcSdUrkM9H9z2ySe1KN8HNWsN1QM"
GROUP_ID = -1003783425494

bot = telebot.TeleBot(TOKEN)

user_data = {}
request_counter = 1


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Создать заявку")
    bot.send_message(message.chat.id, "Нажмите кнопку ниже:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Создать заявку")
def choose_pharmacy(message):
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = []

    for i in range(1, 26):
        buttons.append(types.InlineKeyboardButton(f"{i}", callback_data=f"pharmacy_{i}"))

    markup.add(*buttons)
    bot.send_message(message.chat.id, "Выберите аптеку:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("pharmacy_"))
def choose_problem(call):
    pharmacy_number = call.data.split("_")[1]

    user_data[call.from_user.id] = {
        "pharmacy": pharmacy_number,
        "step": "problem"
    }

    markup = types.InlineKeyboardMarkup()
    problems = ["Касса", "Компьютер", "Интернет", "1С", "Другое"]

    for problem in problems:
        markup.add(types.InlineKeyboardButton(problem, callback_data=f"problem_{problem}"))

    bot.edit_message_text(
        "Выберите тип проблемы:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("problem_"))
def ask_description(call):
    problem = call.data.split("_", 1)[1]

    user_data[call.from_user.id]["problem"] = problem
    user_data[call.from_user.id]["step"] = "description"

    bot.edit_message_text(
        "Опишите проблему текстом:",
        call.message.chat.id,
        call.message.message_id
    )


@bot.message_handler(content_types=['text'])
def handle_text(message):

    if message.text == "Создать заявку":
        return

    user_id = message.from_user.id

    if user_id in user_data:

        step = user_data[user_id].get("step")

        # Получаем описание
        if step == "description":
            user_data[user_id]["description"] = message.text
            user_data[user_id]["step"] = "photo_or_no"

            bot.send_message(
                message.chat.id,
                'Отправьте фото проблемы или напишите "нет"'
            )

        # Пользователь написал "нет"
        elif step == "photo_or_no" and message.text.lower() == "нет":
            send_request(user_id, message, photo=None)
            bot.send_message(message.chat.id, "✅ Заявка отправлена")
            user_data.pop(user_id)


@bot.message_handler(content_types=['photo'])
def handle_photo(message):

    user_id = message.from_user.id

    if user_id in user_data and user_data[user_id].get("step") == "photo_or_no":

        photo_id = message.photo[-1].file_id
        send_request(user_id, message, photo=photo_id)

        bot.send_message(message.chat.id, "✅ Заявка отправлена с фото")
        user_data.pop(user_id)


def send_request(user_id, message, photo):
    global request_counter

    data = user_data[user_id]

    first_name = message.from_user.first_name
    username = message.from_user.username

    if username:
        user_name = f"{first_name} (@{username})"
    else:
        user_name = first_name

    # Только дата
    today = datetime.now().strftime("%d.%m.%Y")

    text = (
        f"📌 Заявка №{request_counter}\n\n"
        f"🏥 Аптека: {data['pharmacy']}\n"
        f"👤 Имя: {user_name}\n"
        f"📅 Дата: {today}\n"
        f"⚠ Тип проблемы: {data['problem']}\n"
        f"📝 Описание: {data['description']}"
    )

    if photo:
        bot.send_photo(GROUP_ID, photo, caption=text)
    else:
        bot.send_message(GROUP_ID, text)

    request_counter += 1


print("Бот запущен...")
bot.infinity_polling()
