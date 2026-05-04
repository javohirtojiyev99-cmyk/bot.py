import telebot
from telebot import types
import sqlite3
import time

TOKEN = "8617775431:AAFtZHNDKXVqa2zyGx0uIKi9nz_oHSLG6QM"
ADMIN_ID = 6968399046
CHANNEL = "@java_cpm"

bot = telebot.TeleBot(TOKEN)

# ===== DATABASE =====
conn = sqlite3.connect("kino.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    code TEXT PRIMARY KEY,
    file_id TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    premium_until INTEGER
)
""")

conn.commit()

# ===== SUB CHECK =====
def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member","creator","administrator"]
    except:
        return False

# ===== PREMIUM CHECK =====
def is_premium(user_id):
    cursor.execute("SELECT premium_until FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()

    if res:
        return res[0] > int(time.time())
    return False

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    if not check_sub(msg.from_user.id):
        bot.send_message(msg.chat.id, "❗ Avval kanalga obuna bo‘ling")
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎬 Kino olish", "💎 Premium olish")

    bot.send_message(msg.chat.id, "Xush kelibsiz", reply_markup=kb)

# ===== PREMIUM OLISH =====
@bot.message_handler(func=lambda m: m.text == "💎 Premium olish")
def buy_premium(msg):
    text = """
💎 Premium narxi: 10 000 so‘m (1 oy)

To‘lov qilish uchun admin bilan bog‘laning:
"""
    bot.send_message(msg.chat.id, text)

# ===== ADMIN PREMIUM BERISH =====
@bot.message_handler(commands=['give'])
def give_premium(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    try:
        parts = msg.text.split()
        user_id = int(parts[1])
        days = int(parts[2])

        expire = int(time.time()) + days*86400

        cursor.execute("INSERT OR REPLACE INTO users VALUES (?,?)", (user_id, expire))
        conn.commit()

        bot.send_message(msg.chat.id, "✅ Premium berildi")
    except:
        bot.send_message(msg.chat.id, "Format: /give user_id kun")

# ===== ADD MOVIE =====
@bot.message_handler(commands=['add'])
def add_movie(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(msg.chat.id, "Kod:")
    bot.register_next_step_handler(msg, add_code)

def add_code(msg):
    code = msg.text
    msg = bot.send_message(msg.chat.id, "Video:")
    bot.register_next_step_handler(msg, add_video, code)

def add_video(msg, code):
    if msg.video:
        cursor.execute("INSERT OR REPLACE INTO movies VALUES (?,?)", (code, msg.video.file_id))
        conn.commit()
        bot.send_message(msg.chat.id, "✅ Qo‘shildi")

# ===== GET MOVIE =====
@bot.message_handler(func=lambda m: m.text == "🎬 Kino olish")
def ask_code(msg):
    bot.send_message(msg.chat.id, "Kod yubor:")

@bot.message_handler(func=lambda m: True)
def get_movie(msg):
    if not check_sub(msg.from_user.id):
        bot.send_message(msg.chat.id, "❗ Obuna bo‘ling")
        return

    if not is_premium(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ Premium kerak")
        return

    cursor.execute("SELECT file_id FROM movies WHERE code=?", (msg.text,))
    res = cursor.fetchone()

    if res:
        bot.send_video(msg.chat.id, res[0])
    else:
        bot.send_message(msg.chat.id, "Topilmadi")

# ===== RUN =====
while True:
    try:
        bot.infinity_polling()
    except:
        time.sleep(3)