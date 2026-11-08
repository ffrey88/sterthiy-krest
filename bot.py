import telebot
import sqlite3
import os
from flask import Flask
from threading import Thread

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9199244262:AAGZn_wmWP0MuNFxZKI-0x0N0oSDcOGnjYo"
GROUP_ID = -9199244262
# -----------------

bot = telebot.TeleBot(BOT_TOKEN)

# Подключение к базе данных (чтобы связь не терялась при перезапуске)
conn = sqlite3.connect('support.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                  (group_msg_id INTEGER PRIMARY KEY, user_id INTEGER)''')
conn.commit()

# 1. Ловим сообщения от пользователей в боте
@bot.message_handler(func=lambda message: message.chat.type == 'private', content_types=['text', 'photo', 'voice', 'video', 'document'])
def handle_user_message(message):
    user_id = message.chat.id
    try:
        if message.content_type == 'text':
            sent_msg = bot.send_message(GROUP_ID, f"📩 Сообщение:\n\n{message.text}")
        else:
            sent_msg = bot.copy_message(GROUP_ID, user_id, message.message_id, caption="📩 Медиа-сообщение:")
        
        cursor.execute("INSERT INTO messages (group_msg_id, user_id) VALUES (?, ?)", (sent_msg.message_id, user_id))
        conn.commit()
        bot.reply_to(message, "✅ Сообщение отправлено. Ожидай ответа.")
    except Exception as e:
        bot.reply_to(message, "⚠️ Ошибка. Попробуй позже.")

# 2. Ловим ответы админов из группы
@bot.message_handler(func=lambda message: message.chat.id == GROUP_ID, content_types=['text', 'photo', 'voice', 'video', 'document'])
def handle_admin_reply(message):
    if message.reply_to_message:
        replied_msg_id = message.reply_to_message.message_id
        cursor.execute("SELECT user_id FROM messages WHERE group_msg_id = ?", (replied_msg_id,))
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            try:
                if message.content_type == 'text':
                    bot.send_message(user_id, f"💬 Ответ:\n\n{message.text}")
                else:
                    bot.copy_message(user_id, GROUP_ID, message.message_id, caption="💬 Ответ:")
                bot.reply_to(message, "✅ Доставлено.")
            except Exception:
                bot.reply_to(message, "⚠️ Пользователь заблокировал бота.")
        else:
            bot.reply_to(message, "⚠️ Не найдено в базе.")

# 3. Команда /start
@bot.message_handler(commands=['start'], func=lambda message: message.chat.type == 'private')
def send_welcome(message):
    bot.reply_to(message, "Привет. Это анонимный чат. Напиши сюда всё, что тебя тревожит, и админы ответят тебе.\n\n⚠️ *Важно:* мы не психологи. Если тебе угрожает опасность, позвони: 8-800-2000-122", parse_mode='Markdown')

# --- БЛОК ДЛЯ RENDER (чтобы сервер не засыпал и не ругался) ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

if __name__ == '__main__':
    keep_alive()
    print("Бот запущен...")
    bot.infinity_polling()