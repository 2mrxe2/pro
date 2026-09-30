import random
import re
import sqlite3
import time
import telebot
from telebot.types import ReactionTypeEmoji

MAIN_BOT_TOKEN = "8699640325:AAGaOfQyY6PyETnZFyiA7n2W6vzk7hJ6efI"
ADMIN_ID = 7329179992  # آيدي حسابك في تليجرام

# قائمة الإيموجيات المتاحة للتفاعل العشوائي
ALLOWED_EMOJIS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", 
    "🙏", "👌", "😍", "💯", "⚡", "🍓", "🏆", "❤️‍🔥"
]

# التفاعل الافتراضي للمنشورات الجديدة (يمكنك تغييره بأمر /emoji)
DEFAULT_EMOJI = "👍"

bot = telebot.TeleBot(MAIN_BOT_TOKEN)

def init_db():
    conn = sqlite3.connect("tokens.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS tokens (token TEXT UNIQUE)")
    conn.commit()
    conn.close()

def get_all_tokens():
    conn = sqlite3.connect("tokens.db")
    cursor = conn.cursor()
    cursor.execute("SELECT token FROM tokens")
    rows = cursor.fetchall()
    conn.close()
    helper_tokens = [row[0] for row in rows]
    return list(set([MAIN_BOT_TOKEN] + helper_tokens))

def add_token_to_db(token):
    try:
        conn = sqlite3.connect("tokens.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tokens (token) VALUES (?)", (token,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_token_from_db(token):
    conn = sqlite3.connect("tokens.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tokens WHERE token = ?", (token,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

init_db()

def add_reaction_from_all(chat_id, message_id, emoji_option):
    """إرسال التفاعلات مع دعم الخيار العشوائي لكل بوت"""
    tokens = get_all_tokens()
    for token in tokens:
        try:
            # إذا كان الخيار random يختار إيموجي عشوائي لكل بوت على حدة
            if emoji_option == "random":
                selected_emoji = random.choice(ALLOWED_EMOJIS)
            else:
                selected_emoji = emoji_option

            helper_bot = telebot.TeleBot(token)
            helper_bot.set_message_reaction(
                chat_id=chat_id,
                message_id=message_id,
                reaction=[ReactionTypeEmoji(selected_emoji)]
            )
            time.sleep(0.3)
        except Exception as e:
            print(f"فشل التفاعل من التوكن {token[:10]}... السبب: {e}")

# --- أوامر التحكم بالإيموجيات والتوكنات ---

@bot.message_handler(commands=['emoji'])
def change_default_emoji(message):
    global DEFAULT_EMOJI
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(
            message,
            f"⚙️ التفاعل التلقائي الحالي هو: `{DEFAULT_EMOJI}`\n\n"
            "لتغييره ارسل:\n"
            "`/emoji 🍓` (لتثبيت إيموجي الفراولة)\n"
            "`/emoji random` (لجعل التفاعل عشوائي للمنشورات الجديدة)",
            parse_mode="Markdown"
        )
        return

    new_emoji = args[1].strip()
    if new_emoji.lower() == "random":
        DEFAULT_EMOJI = "random"
        bot.reply_to(message, "✅ تم ضبط التفاعل التلقائي للمنشورات الجديدة على: **عشوائي** 🎲")
    else:
        DEFAULT_EMOJI = new_emoji
        bot.reply_to(message, f"✅ تم ضبط التفاعل التلقائي للمنشورات الجديدة على: {DEFAULT_EMOJI}")

@bot.message_handler(commands=['add'])
def add_token_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ الاستخدام: `/add {TOKEN}`", parse_mode="Markdown")
        return
    new_token = args[1].strip()
    try:
        test_bot = telebot.TeleBot(new_token)
        bot_info = test_bot.get_me()
        if add_token_to_db(new_token):
            bot.reply_to(message, f"✅ تم إضافة البوت: @{bot_info.username}")
        else:
            bot.reply_to(message, "⚠️ التوكن مضاف مسبقاً.")
    except Exception as e:
        bot.reply_to(message, f"❌ التوكن غير صالح: `{e}`", parse_mode="Markdown")

@bot.message_handler(commands=['unadd'])
def remove_token_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ الاستخدام: `/unadd {TOKEN}`", parse_mode="Markdown")
        return
    target_token = args[1].strip()
    if target_token == MAIN_BOT_TOKEN:
        bot.reply_to(message, "❌ لا يمكنك حذف البوت الرئيسي!")
        return
    if remove_token_from_db(target_token):
        bot.reply_to(message, "✅ تم حذف التوكن بنجاح.")
    else:
        bot.reply_to(message, "❌ التوكن غير موجود.")

@bot.message_handler(commands=['list'])
def list_tokens_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    tokens = get_all_tokens()
    msg_text = f"📋 **عدد البوتات:** {len(tokens)}\n\n"
    for idx, token in enumerate(tokens, 1):
        masked = token[:10] + "..." + token[-5:]
        msg_text += f"{idx}. `{masked}`\n"
    bot.reply_to(message, msg_text, parse_mode="Markdown")

# --- 1. التفاعل مع المنشورات الجديدة ---
@bot.channel_post_handler(func=lambda message: True)
def auto_react_new_post(message):
    add_reaction_from_all(
        chat_id=message.chat.id, 
        message_id=message.message_id, 
        emoji_option=DEFAULT_EMOJI
    )

# --- 2. التفاعل المخصص عبر رابط ---
@bot.message_handler(commands=['reaction'])
def custom_reaction_by_url(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(
                message, 
                "⚠️ الاستخدام:\n"
                "`/reaction {رابط_المنشور} {الإيموجي}`\n\n"
                "أمثلة:\n"
                "`/reaction https://t.me/channel/100 🍓`\n"
                "`/reaction https://t.me/channel/100 random`", 
                parse_mode="Markdown"
            )
            return

        url = args[1]
        selected_emoji = args[2] if len(args) > 2 else DEFAULT_EMOJI

        match_private = re.search(r"t\.me/c/(\d+)/(\d+)", url)
        match_public = re.search(r"t\.me/([^/]+)/(\d+)", url)

        if match_private:
            chat_id = int("-100" + match_private.group(1))
            msg_id = int(match_private.group(2))
        elif match_public:
            chat_id = f"@{match_public.group(1)}"
            msg_id = int(match_public.group(2))
        else:
            bot.reply_to(message, "❌ الرابط غير صحيح.")
            return

        bot.reply_to(message, "جاري إرسال التفاعلات...")
        add_reaction_from_all(chat_id, msg_id, selected_emoji)
        bot.send_message(message.chat.id, "✅ تم إرسال التفاعلات بنجاح!")

    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {e}")

print("البوت يعمل الآن...")
bot.infinity_polling()
