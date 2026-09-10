import json
import random
import os
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import TOKEN, ADMIN_ID
from codes import CODES


USERS_FILE = "users.json"
NUMBERS_FILE = "numbers.json"


# ساخت فایل‌ها اگر وجود نداشتند
for file in [USERS_FILE, NUMBERS_FILE]:
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump({}, f)


def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)



keyboard = ReplyKeyboardMarkup(
    [
        ["📩 دریافت کد"]
    ],
    resize_keyboard=True
)	



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "سلام 👋\n\n"
        "برای دریافت کد روی دکمه زیر بزن:",
        reply_markup=keyboard
    )



async def request_code(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["waiting"] = True

    await update.message.reply_text(
        "شماره اکانت قربانی را ارسال کنید:"
    )



async def receive_data(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("waiting"):
        return


    user_id = str(update.message.from_user.id)

    user_input = update.message.text


    users = load_json(USERS_FILE)


    # ساخت صف جدید اگر کاربر جدید بود
    if user_id not in users or len(users[user_id]["queue"]) == 0:

        queue = list(range(len(CODES)))
        random.shuffle(queue)

        users[user_id] = {
            "queue": queue
        }


    # انتخاب کد بعدی
    code_index = users[user_id]["queue"].pop(0)

    code = CODES[code_index]


    save_json(USERS_FILE, users)



    # ذخیره درخواست
    numbers = load_json(NUMBERS_FILE)

    numbers[str(datetime.now())] = {
        "user_id": user_id,
        "input": user_input,
        "code": code
    }

    save_json(NUMBERS_FILE, numbers)



    # ارسال گزارش به ادمین
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"""
📥 درخواست جدید

آیدی کاربر:
{user_id}

شناسه ارسال شده:
{user_input}

کد ارسال شده:
{code}
"""
    )


    context.user_data["waiting"] = False


    await update.message.reply_text(
        f"✅ کد شما:\n\n`{code}`",
        parse_mode="Markdown"
    )



app = Application.builder().token(TOKEN).build()


app.add_handler(
    CommandHandler("start", start)
)


app.add_handler(
    MessageHandler(
        filters.Regex("^📩 دریافت کد$"),
        request_code
    )
)


app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_data
    )
)



print("🤖 Bot Started...")

app.run_polling()
