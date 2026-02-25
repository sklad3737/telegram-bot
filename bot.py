import telebot
from telebot import types
from datetime import datetime

TOKEN = "8273823469:AAETywYPcSdUrkM9H9z2ySe1KN8HNWsN1QM"
GROUP_ID = -1003783425494

bot = telebot.TeleBot(TOKEN)

# ---------------- MEMORY STORAGE ----------------

user_data = {}
request_messages = {}
request_counter = 1

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Создать заявку")

    bot.send_message(
        message.chat.id,
        "Нажмите кнопку ниже:",
        reply_markup=markup
    )

# ---------------- CREATE REQUEST ----------------

@bot.message_handler(func=lambda message: message.text == "Создать заявку")
def choose_pharmacy(message):

    markup = types.InlineKeyboardMarkup(row_width=5)

    buttons = [
        types.InlineKeyboardButton(
            str(i),
            callback_data=f"pharmacy_{i}"
        ) for i in range(1, 26)
    ]

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "Выберите аптеку:",
        reply_markup=markup
    )

# ---------------- PHARMACY ----------------

@bot.callback_query_handler(func=lambda call: call.data.startswith("pharmacy_"))
def choose_problem(call):

    pharmacy_number = call.data.split("_")[1]

    user_data[call.from_user.id] = {
        "pharmacy": pharmacy_number,
        "step": "problem"
    }

    markup = types.InlineKeyboardMarkup()

    problems = ["Касса", "Компьютер", "Интернет", "1С", "Другое"]

    for p in problems:
        markup.add(
            types.InlineKeyboardButton(
                p,
                callback_data=f"problem_{p}"
            )
        )

    bot.edit_message_text(
        "Выберите тип проблемы:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

# ---------------- PROBLEM ----------------

@bot.callback_query_handler(func=lambda call: call.data.startswith("problem_"))
def choose_urgency(call):

    problem = call.data.split("_", 1)[1]

    user_data[call.from_user.id]["problem"] = problem
    user_data[call.from_user.id]["step"] = "urgency"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔴 Срочно", callback_data="urgency_Срочно"))
    markup.add(types.InlineKeyboardButton("🟢 Несрочно", callback_data="urgency_Несрочно"))

    bot.edit_message_text(
        "Выберите срочность:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

# ---------------- URGENCY ----------------

@bot.callback_query_handler(func=lambda call: call.data.startswith("urgency_"))
def ask_description(call):

    urgency = call.data.split("_", 1)[1]

    user_data[call.from_user.id]["urgency"] = urgency
    user_data[call.from_user.id]["step"] = "description"

    bot.edit_message_text(
        "Опишите проблему текстом:",
        call.message.chat.id,
        call.message.message_id
    )

# ---------------- TEXT HANDLER ----------------

@bot.message_handler(content_types=['text'])
def handle_text(message):

    if message.text == "Создать заявку":
        return

    user_id = message.from_user.id

    if user_id not in user_data:
        return

    step = user_data[user_id].get("step")

    if step == "description":

        user_data[user_id]["description"] = message.text
        user_data[user_id]["step"] = "photo_or_no"

        bot.send_message(
            message.chat.id,
            'Если нет фото, напишите слово "нет"'
        )

    elif step == "photo_or_no" and message.text.lower() == "нет":

        send_request(user_id, message, photo=None)

        bot.send_message(message.chat.id, "✅ Заявка отправлена")

        user_data.pop(user_id, None)

# ---------------- PHOTO HANDLER ----------------

@bot.message_handler(content_types=['photo'])
def handle_photo(message):

    user_id = message.from_user.id

    if user_id not in user_data:
        return

    if user_data[user_id].get("step") != "photo_or_no":
        return

    photo_id = message.photo[-1].file_id

    send_request(user_id, message, photo=photo_id)

    bot.send_message(message.chat.id, "✅ Заявка отправлена")

    user_data.pop(user_id, None)

# ---------------- SEND REQUEST ----------------

def send_request(user_id, message, photo):

    global request_counter

    if user_id not in user_data:
        return

    data = user_data[user_id]

    first_name = message.from_user.first_name or ""
    username = message.from_user.username

    user_name = f"{first_name} (@{username})" if username else first_name

    today = datetime.now().strftime("%d.%m.%Y")

    urgency_text = "🔴 Срочно" if data.get("urgency") == "Срочно" else "🟢 Несрочно"

    pharmacy = data.get("pharmacy", "-")
    problem = data.get("problem", "-")
    description = data.get("description", "-")

    text = (
        f"📌 Заявка №{request_counter}\n"
        f"{urgency_text}\n"
        f"🏥 Аптека: {pharmacy}\n"
        f"👤 Имя: {user_name}\n"
        f"📅 Дата: {today}\n"
        f"⚠ Тип проблемы: {problem}\n"
        f"📝 Описание: {description}"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "✅ Принять",
            callback_data=f"take_{request_counter}"
        )
    )

    if photo:
        sent = bot.send_photo(
            GROUP_ID,
            photo,
            caption=text,
            reply_markup=markup,
        )
    else:
        sent = bot.send_message(
            GROUP_ID,
            text,
            reply_markup=markup,
        )

    request_messages[request_counter] = sent.message_id

    request_counter += 1

# ---------------- TAKE REQUEST ----------------

@bot.callback_query_handler(func=lambda call: call.data.startswith("take_"))
def take_request(call):

    username = call.from_user.username
    name = f"@{username}" if username else call.from_user.first_name

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=None
    )

    if call.message.caption:
        updated_text = call.message.caption + f"\n\n🛠 Принял: {name}"

        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=updated_text,
            parse_mode="HTML"
        )
    else:
        updated_text = call.message.text + f"\n\n🛠 Принял: {name}"

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=updated_text,
            parse_mode="HTML"
        )

print("Бот запущен...")
bot.infinity_polling()


