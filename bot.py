import telebot
from telebot import types
from datetime import datetime

TOKEN = "8273823469:AAETywYPcSdUrkM9H9z2ySe1KN8HNWsN1QM"
GROUP_ID = -1003783425494
bot = telebot.TeleBot(TOKEN)
user_data = {}
request_counter = 1

# --- Старт ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Создать заявку")
    bot.send_message(message.chat.id, "Нажмите кнопку ниже:", reply_markup=markup)

# --- Создание заявки ---
@bot.message_handler(func=lambda message: message.text == "Создать заявку")
def choose_pharmacy(message):
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = [types.InlineKeyboardButton(f"{i}", callback_data=f"pharmacy_{i}") for i in range(1, 26)]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Выберите аптеку:", reply_markup=markup)

# --- Выбор аптеки ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("pharmacy_"))
def choose_problem(call):
    pharmacy_number = call.data.split("_")[1]
    user_data[call.from_user.id] = {"pharmacy": pharmacy_number}
    markup = types.InlineKeyboardMarkup()
    for problem in ["Касса", "Компьютер", "Интернет", "1С", "Другое"]:
        markup.add(types.InlineKeyboardButton(problem, callback_data=f"problem_{problem}"))
    bot.edit_message_text("Выберите тип проблемы:", call.message.chat.id, call.message.message_id, reply_markup=markup)

# --- Выбор проблемы ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("problem_"))
def get_description(call):
    problem = call.data.split("_", 1)[1]
    user_data[call.from_user.id]["problem"] = problem
    user_data[call.from_user.id]["state"] = "waiting_description"
    bot.edit_message_text(
        "Опишите проблему текстом:",
        call.message.chat.id,
        call.message.message_id
    )

# --- Получение текста описания ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "Создать заявку":
        return
    uid = message.from_user.id
    if uid not in user_data or user_data[uid].get("state") != "waiting_description":
        return
    user_data[uid]["description"] = message.text
    user_data[uid]["state"] = "waiting_photo"

    # Сохраняем информацию о пользователе
    user = message.from_user
    if user.username:
        user_data[uid]["requester"] = f"@{user.username}"
    else:
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        user_data[uid]["requester"] = full_name or "Неизвестно"

    # Сохраняем дату и время
    user_data[uid]["datetime"] = datetime.now().strftime("%d.%m.%Y %H:%M")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Без фото")
    bot.send_message(message.chat.id, "Прикрепите фото или нажмите 'Без фото':", reply_markup=markup)

# --- Пропуск фото ---
@bot.message_handler(func=lambda m: m.text == "Без фото")
def skip_photo(message):
    uid = message.from_user.id
    if uid not in user_data or user_data[uid].get("state") != "waiting_photo":
        return
    user_data[uid]["photo"] = None
    send_request(uid, message.chat.id)

# --- Получение фото ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    if uid not in user_data or user_data[uid].get("state") != "waiting_photo":
        return
    user_data[uid]["photo"] = message.photo[-1].file_id
    send_request(uid, message.chat.id)

# --- Отправка заявки ---
def send_request(user_id, chat_id):
    global request_counter
    data = user_data[user_id]
    text = (
        f"📌 Заявка №{request_counter}\n\n"
        f"🏪 Аптека: {data['pharmacy']}\n"
        f"👤 Имя: {data['requester']}\n"
        f"📅 Дата и время: {data['datetime']}\n"
        f"⚙️ Тип проблемы: {data['problem']}\n"
        f"📝 Описание: {data['description']}"
    )
    if data["photo"]:
        bot.send_photo(GROUP_ID, data["photo"], caption=text)
    else:
        bot.send_message(GROUP_ID, text)

    request_counter += 1
    user_data.pop(user_id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Создать заявку")
    bot.send_message(chat_id, "✅ Заявка отправлена!", reply_markup=markup)

print("Бот запущен...")
bot.infinity_polling()
```
