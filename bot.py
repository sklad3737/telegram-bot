import telebot
from telebot import types
from datetime import datetime

# ===== CONFIG =====
TOKEN = "8273823469:AAETywYPcSdUrkM9H9z2ySe1KN8HNWsN1QM"
GROUP_ID = -1003783425494

bot = telebot.TeleBot(TOKEN)

# ===== STORAGE =====
user_data = {}
user_state = {}

request_counter = 1

# ===== START MENU =====
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Создать заявку")

    bot.send_message(
        message.chat.id,
        "👋 Нажмите кнопку ниже:",
        reply_markup=markup
    )

# ===== CREATE REQUEST =====
@bot.message_handler(func=lambda m: m.text == "Создать заявку")
def choose_pharmacy(message):

    markup = types.InlineKeyboardMarkup(row_width=5)

    buttons = []
    for i in range(1, 26):
        buttons.append(
            types.InlineKeyboardButton(
                str(i),
                callback_data=f"pharmacy_{i}"
            )
        )

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "🏪 Выберите аптеку:",
        reply_markup=markup
    )

# ===== PHARMACY SELECT =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("pharmacy_"))
def choose_problem(call):

    pharmacy_number = call.data.split("_")[1]

    user_data[call.from_user.id] = {
        "pharmacy": pharmacy_number
    }

    markup = types.InlineKeyboardMarkup()

    problems = ["1С\Касса", "Компьютер", "Интернет", "Освещение", "Другое"]

    for p in problems:
        markup.add(
            types.InlineKeyboardButton(
                p,
                callback_data=f"problem_{p}"
            )
        )

    bot.edit_message_text(
        "🔧 Выберите тип проблемы:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

# ===== PROBLEM SELECT =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("problem_"))
def ask_description(call):

    problem = call.data.split("_", 1)[1]

    user_data[call.from_user.id]["problem"] = problem
    user_state[call.from_user.id] = "wait_description"

    bot.edit_message_text(
        "📝 Опишите проблему текстом.\nМожно прикрепить фото следующим сообщением.",
        call.message.chat.id,
        call.message.message_id
    )

# ===== TEXT HANDLER =====
@bot.message_handler(content_types=["text"])
def handle_text(message):

    if message.text == "Создать заявку":
        return

    user_id = message.from_user.id

    if user_id in user_state and user_state[user_id] == "wait_description":

        user_data[user_id]["description"] = message.text
        user_state[user_id] = "wait_photo"

        bot.send_message(
            message.chat.id,
            "📷 Прикрепите фото (если есть)\nили напишите 'Пропустить'"
        )

# ===== PHOTO HANDLER =====
@bot.message_handler(content_types=["photo"])
def handle_photo(message):

    user_id = message.from_user.id

    if user_id in user_state and user_state[user_id] == "wait_photo":

        user_data[user_id]["photo"] = message.photo[-1].file_id

        send_request(user_id)

        bot.send_message(message.chat.id, "✅ Заявка отправлена")

# ===== SKIP PHOTO =====
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "пропустить")
def skip_photo(message):

    user_id = message.from_user.id

    if user_id in user_state and user_state[user_id] == "wait_photo":

        user_data[user_id]["photo"] = None

        send_request(user_id)

        bot.send_message(message.chat.id, "✅ Заявка отправлена")

# ===== SEND REQUEST =====
def send_request(user_id):

    global request_counter

    data = user_data[user_id]

    time_now = datetime.now().strftime("%Y-%m-%d %H:%M")

    username = data.get("username", "")

    text = f"""
🆕 Заявка #{request_counter}

🏪 Аптека: {data['pharmacy']}
🔧 Тип: {data['problem']}
👤 Пользователь: @{username}

📝 {data['description']}

🕒 {time_now}
"""

    if data.get("photo"):
        bot.send_photo(
            GROUP_ID,
            data["photo"],
            caption=text
        )
    else:
        bot.send_message(GROUP_ID, text)

    request_counter += 1

    user_data.pop(user_id, None)
    user_state.pop(user_id, None)

# ===== RUN =====
print("Bot running...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
