import json
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ----------------- تنظیمات اولیه -----------------
TOKEN = '8907948308:AAEkCcEFkviGA6rgP_6EOaWYg4GLzkBj3lU'
ADMIN_USERNAME = "Audhdudjjs"
ADMIN_PASSWORD = "AriaAria1389"
FILE_CHANNEL = -1003933220851

USERS_FILE = "users.json"
GAMES_FILE = "games.json"

# دیتابیس‌های موقت در حافظه برای مدیریت وضعیت کاربران
waiting_for_code = set()
admin_states = {}  # برای ذخیره وضعیت ادمین در مراحل مختلف (مثلا دریافت کد یا ID)
authenticated_admins = set()  # ذخیره ادمین‌هایی که رمز رو درست زدن

# ----------------- منوها -----------------
menu = ReplyKeyboardMarkup(
    [
        ["📥 دانلود بازی", "👤 حساب کاربری"],
        ["🛠 پشتیبانی", "📢 کانال"]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    [
        ["📊 آمار کاربران", "➕ افزودن بازی"],
        ["🚧 به زودی...", "🏠 بازگشت"]
    ],
    resize_keyboard=True
)

# ----------------- توابع مدیریت فایل (سیستم ذخیره) -----------------
def load_games():
    """بارگذاری بازی‌ها از فایل JSON"""
    if not os.path.exists(GAMES_FILE):
        return {}
    try:
        with open(GAMES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_games(games_dict):
    """ذخیره بازی‌ها در فایل JSON"""
    try:
        with open(GAMES_FILE, "w", encoding="utf-8") as f:
            json.dump(games_dict, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

def save_user(user_id):
    """ذخیره شناسه کاربران در فایل JSON"""
    users = []
    if os.path.exists(USERS_FILE):    
        try:    
            with open(USERS_FILE, "r", encoding="utf-8") as f:    
                users = json.load(f)    
        except:    
            users = []    

    if user_id not in users:    
        users.append(user_id)    
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:    
                json.dump(users, f, ensure_ascii=False, indent=4)
        except:
            pass

def get_users_count():
    """دریافت تعداد کل کاربران"""
    if not os.path.exists(USERS_FILE):
        return 0
    try:    
        with open(USERS_FILE, "r", encoding="utf-8") as f:    
            users = json.load(f)    
        return len(users)    
    except:    
        return 0

# ----------------- دستورات اصلی (Commands) -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)    
    await update.message.reply_text(    
        "🎮 به Game15Vox خوش آمدید\n\n"    
        "📥 دانلود مستقیم بازی‌های PC و Android\n"    
        "⚡ دانلود سریع و آسان\n"    
        "🛡 فایل‌های تست شده\n\n"    
        "از منوی زیر گزینه مورد نظر را انتخاب کنید.",    
        reply_markup=menu    
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:    
        await update.message.reply_text("⛔ شما دسترسی به پنل مدیریت ندارید.")    
        return    
    
    # اگر قبلاً رمز رو زده بود مستقیم بره منو
    if user.id in authenticated_admins:
        await update.message.reply_text(
            "🔧 پنل مدیریت Game15Vox\n\nبه پنل مدیریت خوش آمدید.",
            reply_markup=admin_menu
        )
        return

    # درخواست رمز عبور
    admin_states[user.id] = {"stage": "login"}
    await update.message.reply_text(
        "🔑 لطفا رمز عبور پنل مدیریت را وارد کنید:",
        reply_markup=ReplyKeyboardRemove()
    )

# ----------------- پردازشگر پیام‌ها (Handler) -----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()    
    user_id = update.effective_user.id    
    username = update.effective_user.username    

    save_user(user_id)    

    # --- سیستم احراز هویت و مراحل پنل ادمین ---
    if username == ADMIN_USERNAME:
        # ۱. بررسی مرحله لاگین و وارد کردن پسورد
        if user_id in admin_states and admin_states[user_id].get("stage") == "login":
            if text == ADMIN_PASSWORD:
                authenticated_admins.add(user_id)
                admin_states.pop(user_id, None)
                await update.message.reply_text(
                    "✅ رمز عبور تایید شد.\n\n🔧 پنل مدیریت Game15Vox\n\nبه پنل مدیریت خوش آمدید.",
                    reply_markup=admin_menu
                )
            else:
                await update.message.reply_text("❌ رمز عبور اشتباه است. دوباره تلاش کنید:")
            return

        # اگر ادمین لاگین شده بود، دستورات پنل رو چک کن
        if user_id in authenticated_admins:
            
            # مرحله اول افزودن بازی: دریافت کد بازی
            if user_id in admin_states and admin_states[user_id].get("stage") == "add_game_code":
                admin_states[user_id]["game_code"] = text
                admin_states[user_id]["stage"] = "add_game_id"
                await update.message.reply_text(
                    f"🔹 کد بازی «{text}» ثبت شد.\n\n"
                    f"📥 حالا Message ID فایل را در کانال ارسال کنید:"
                )
                return

            # مرحله دوم افزودن بازی: دریافت Message ID و ذخیره دائم
            elif user_id in admin_states and admin_states[user_id].get("stage") == "add_game_id":
                if not text.isdigit():
                    await update.message.reply_text("❌ خطا: Message ID باید فقط شامل عدد باشد. دوباره ارسال کنید:")
                    return
                
                game_code = admin_states[user_id]["game_code"]
                message_id = int(text)
                
                # خواندن، آپدیت و ذخیره در فایل
                current_games = load_games()
                current_games[game_code] = message_id
                
                if save_games(current_games):
                    await update.message.reply_text(
                        f"✅ بازی با موفقیت اضافه شد!\n\n"
                        f"🔑 کد بازی: {game_code}\n"
                        f"🆔 شناسه پیام: {message_id}",
                        reply_markup=admin_menu
                    )
                else:
                    await update.message.reply_text("⚠️ خطا در ذخیره فایل games.json", reply_markup=admin_menu)
                
                admin_states.pop(user_id, None) # پاک کردن وضعیت ادمین بعد از اتمام کار
                return

            # دکمه‌های منوی ادمین
            if text == "📊 آمار کاربران":    
                await update.message.reply_text(    
                    f"📊 آمار ربات\n\n👥 تعداد کاربران: {get_users_count()}"    
                )    
                return    

            elif text == "➕ افزودن بازی":
                admin_states[user_id] = {"stage": "add_game_code"}
                await update.message.reply_text(
                    "➕ بخش افزودن بازی\n\n"
                    "🔎 لطفاً یک کد برای بازی تعیین و ارسال کنید (مثلاً: 1 یا gta5):",
                    reply_markup=ReplyKeyboardRemove()
                )
                return

            elif text == "🚧 به زودی...":    
                await update.message.reply_text("🚧 این بخش در نسخه‌های بعدی اضافه خواهد شد.")    
                return    

            elif text == "🏠 بازگشت":    
                authenticated_admins.discard(user_id) # خروج امن از پنل ادمین
                admin_states.pop(user_id, None)
                await update.message.reply_text("🏠 بازگشت به منوی اصلی", reply_markup=menu)    
                return    

    # --- منوی عمومی کاربران ---
    # ۱. کلیک روی دکمه دانلود بازی
    if text == "📥 دانلود بازی":    
        waiting_for_code.add(user_id)    
        await update.message.reply_text(    
            "📥 دانلود بازی\n\n"    
            "🔎 کد بازی مورد نظر را ارسال کنید.\n\n"    
            "💡 کد هر بازی داخل پست همان بازی در کانال قرار دارد."    
        )    
        return    

    # ۲. دکمه حساب کاربری
    elif text == "👤 حساب کاربری":    
        name = update.effective_user.first_name    
        await update.message.reply_text(    
            f"👤 حساب کاربری\n\n"    
            f"🆔 نام: {name}\n\n"    
            f"✅ وضعیت حساب: فعال\n"    
            f"🎮 دسترسی دانلود: فعال\n\n"    
            f"از همراهی شما با Game15Vox سپاسگزاریم."    
        )    
        return    

    # ۳. دکمه پشتیبانی
    elif text == "🛠 پشتیبانی":    
        await update.message.reply_text(    
            "🛠 مرکز پشتیبانی Game15Vox\n\n"    
            "👤 @Audhdudjjs"    
        )    
        return    

    # ۴. دکمه کانال
    elif text == "📢 کانال":    
        await update.message.reply_text(    
            "📢 کانال رسمی Game15Vox\n\n"    
            "🔗 https://t.me/Game15Vox"    
        )    
        return    

    # ۵. بررسی ارسال کد بازی توسط کاربر (دانلود فایل)
    if user_id in waiting_for_code:    
        games = load_games() # خواندن آنلاین از فایل JSON
        
        if text in games:    
            try:    
                await context.bot.copy_message(    
                    chat_id=update.effective_chat.id,    
                    from_chat_id=FILE_CHANNEL,    
                    message_id=int(games[text])    
                )    
                await update.message.reply_text(    
                    "✅ فایل با موفقیت ارسال شد.\n\n"    
                    "🎮 Game15Vox"    
                )    
            except Exception:    
                await update.message.reply_text("⚠️ در ارسال فایل مشکلی پیش آمد. احتمالاً شناسه پیام اشتباه است یا ربات در کانال ادمین نیست.")    
        else:    
            await update.message.reply_text("❌ کد وارد شده معتبر نیست.")    

        waiting_for_code.discard(user_id)    
        return    

    # پیام پیش‌فرض برای متون خارج از منو
    await update.message.reply_text("❌ لطفاً از منوی ربات استفاده کنید.")

# ----------------- اجرای ربات -----------------
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot Started...")
app.run_polling()
          
