import telebot
from telebot import types
from datetime import datetime

TOKEN = "8273823469:AAETywYPcSdUrkM9H9z2ySe1KN8HNWsN1QM"
GROUP_ID = -1003783425494

bot = telebot.TeleBot(TOKEN)

# ---------------- STORAGE ----------------

user_data = {}
checklist_data = {}
request_counter = 1

CHECKLIST_ITEMS = [
    "Касса",
    "Компьютер",
    "Интернет",
    "1С",
    "Сеть",
    "Принтер",
    "База",
    "VPN",
    "Сервер",
    "Локализация проблемы"
]

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Создать заявку", "Чек-лист")

    bot.send_message(
        message.chat.id,
        "Выберите действие:",
        reply_markup=markup
    )

# ---------------- TEXT ROUTER ----------------

@bot.message_handler(content_types=['text'])
def handle_text(message):

    global user_data

    user_id = message.from_user.id
    text = message.text

    # Главное меню
    if text == "Создать заявку":
        send_pharmacy_keyboard(message.chat.id)
        return

    if text == "Чек-лист":
        open_checklist(message.chat.id, user_id)
        return

    # Если пользователь не в процессе заявки
    if user_id not in user_data:
        return

    step = user_data[user_id]["step"]

    if step == "description":
        user_data[user_id]["description"] = text
        user_data[user_id]["step"] = "photo"

        bot.send_message(
            message.chat.id,
            'Отправьте фото или напишите "нет"'
        )

    elif step == "photo" and text.lower() == "нет":
        send_request(user_id, message, None)
        bot.send_message(message.chat.id, "✅ Заявка отправлена")
        user_data.pop(user_id)

# ---------------- PHOTO ----------------

@bot.message_handler(content_types=['photo'])
def handle_photo(message):

    user_id = message.from_user.id

    if user_id not in user_data:
        return

    if user_data[user_id]["step"] != "photo":
        return

    photo_id = message.photo[-1].file_id

    send_request(user_id, message, photo_id)
    bot.send_message(message.chat.id, "✅ Заявка отправлена")
    user_data.pop(user_id)

# ---------------- CALLBACK ROUTER ----------------

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):

    data = call.data
    user_id = call.from_user.id

    # ---------- ЗАЯВКА ----------

    if data.startswith("pharmacy_"):

        pharmacy = data.split("_")[1]

        user_data[user_id] = {
            "pharmacy": pharmacy,
            "step": "problem"
        }

        markup = types.InlineKeyboardMarkup()

        for p in ["Касса", "Компьютер", "Интернет", "1С", "Другое"]:
            markup.add(types.InlineKeyboardButton(
                p,
                callback_data=f"problem_{p}"
            ))

        bot.edit_message_text(
            "Выберите тип проблемы:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

    elif data.startswith("problem_"):

        problem = data.split("_", 1)[1]

        user_data[user_id]["problem"] = problem
        user_data[user_id]["step"] = "urgency"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 Срочно", callback_data="urgency_Срочно"))
        markup.add(types.InlineKeyboardButton("🟢 Несрочно", callback_data="urgency_Несрочно"))

        bot.edit_message_text(
            "Выберите срочность:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

    elif data.startswith("urgency_"):

        urgency = data.split("_")[1]

        user_data[user_id]["urgency"] = urgency
        user_data[user_id]["step"] = "description"

        bot.edit_message_text(
            "Опишите проблему:",
            call.message.chat.id,
            call.message.message_id
        )

    elif data.startswith("take_"):

        name = call.from_user.username or call.from_user.first_name

        if call.message.caption:
            updated = call.message.caption + f"\n\n🛠 Принял: {name}"

            bot.edit_message_caption(
                caption=updated_text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )

        else:
            updated = call.message.text + f"\n\n🛠 Принял: {name}"

            bot.edit_message_text(
                text=updated_text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )

    # ---------- ЧЕК-ЛИСТ ----------

    elif data.startswith("check_"):

        if user_id not in checklist_data:
            checklist_data[user_id] = {i: False for i in range(len(CHECKLIST_ITEMS))}

        # Подтверждение чек-листа
        if data == "check_confirm":

            result = []

            for i, checked in checklist_data[user_id].items():
                if checked:
                    result.append(f"✅ {CHECKLIST_ITEMS[i]}")

            text = "📋 Итог чек-листа\n\n"
            text += "\n".join(result) if result else "Нет отмеченных пунктов"

            # Отправляем итог в группу
            bot.send_message(GROUP_ID, text)

            # Убираем кнопки
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )

            checklist_data.pop(user_id, None)

            bot.answer_callback_query(call.id)
            return

        # Toggle пунктов
        try:
            index = int(data.split("_")[1])
        except:
            bot.answer_callback_query(call.id)
            return

        checklist_data[user_id][index] = not checklist_data[user_id][index]

        update_checklist(
            call.message.chat.id,
            call.message.message_id,
            user_id
        )

    bot.answer_callback_query(call.id)

# ---------------- FUNCTIONS ----------------

def send_pharmacy_keyboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = [
        types.InlineKeyboardButton(str(i), callback_data=f"pharmacy_{i}")
        for i in range(1, 26)
    ]
    markup.add(*buttons)

    bot.send_message(chat_id, "Выберите аптеку:", reply_markup=markup)


def open_checklist(chat_id, user_id):

    if user_id not in checklist_data:
        checklist_data[user_id] = {i: False for i in range(len(CHECKLIST_ITEMS))}

    markup = types.InlineKeyboardMarkup()

    for i, item in enumerate(CHECKLIST_ITEMS):
        prefix = "✅ " if checklist_data[user_id][i] else ""
        markup.add(
            types.InlineKeyboardButton(
                f"{prefix}{item}",
                callback_data=f"check_{i}"
            )
        )

    markup.add(types.InlineKeyboardButton("✔ Подтвердить", callback_data="check_confirm"))

    bot.send_message(chat_id, "📋 Чек-лист", reply_markup=markup)


def update_checklist(chat_id, message_id, user_id):

    markup = types.InlineKeyboardMarkup()

    for i, item in enumerate(CHECKLIST_ITEMS):
        prefix = "✅ " if checklist_data[user_id][i] else ""
        markup.add(
            types.InlineKeyboardButton(
                f"{prefix}{item}",
                callback_data=f"check_{i}"
            )
        )

    markup.add(types.InlineKeyboardButton("✔ Подтвердить", callback_data="check_confirm"))

    bot.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)


def send_request(user_id, message, photo):

    global request_counter

    data = user_data[user_id]

    first_name = message.from_user.first_name or ""
    username = message.from_user.username
    user_name = f"{first_name} (@{username})" if username else first_name

    today = datetime.now().strftime("%d.%m.%Y")
    urgency = "🔴 Срочно" if data["urgency"] == "Срочно" else "🟢 Несрочно"

    text = (
        f"📌 Заявка №{request_counter}\n"
        f"{urgency}\n"
        f"🏥 Аптека: {data['pharmacy']}\n"
        f"👤 Имя: {user_name}\n"
        f"📅 Дата: {today}\n"
        f"⚠ Тип проблемы: {data['problem']}\n"
        f"📝 Описание: {data['description']}"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Принять", callback_data=f"take_{request_counter}"))

    if photo:
        bot.send_photo(GROUP_ID, photo, caption=text, reply_markup=markup)
    else:
        bot.send_message(GROUP_ID, text, reply_markup=markup)

    request_counter += 1


# ---------------- START BOT ----------------

bot.remove_webhook()
print("Бот запущен...")
bot.infinity_polling()



