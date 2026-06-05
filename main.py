import json
import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ----------------- فایل‌های دیتابیس (JSON) -----------------
USERS_FILE = "users.json"
GAMES_FILE = "games.json"
SETTINGS_FILE = "settings.json"

# ----------------- مقادیر پیش‌فرض اولیه -----------------
DEFAULT_SETTINGS = {
    "admin_username": 'Game15VoxSupport' ,
    "admin_password": "AriaAria1389",
    "file_channel": -1003933220851,
    "support_username": "@Audhdudjjs",
    "channel_link": "https://t.me/Game15Vox"
}

# ----------------- توابع ماژولار مدیریت اطلاعات (JSON) -----------------
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=4)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_SETTINGS

def save_settings(settings_dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings_dict, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

def load_games():
    if not os.path.exists(GAMES_FILE):
        return {}
    try:
        with open(GAMES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_games(games_dict):
    try:
        with open(GAMES_FILE, "w", encoding="utf-8") as f:
            json.dump(games_dict, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
        except:
            pass

def update_users_list(users_list):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_list, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

# ----------------- وضعیت‌ها و منوهای ربات -----------------
waiting_for_code = set()
admin_states = {}  
authenticated_admins = set()  

# بارگذاری اولیه تنظیمات برای توکن ربات
current_config = load_settings()
TOKEN = '8907948308:AAEkCcEFkviGA6rgP_6EOaWYg4GLzkBj3lU'  # توکن توکن رباتت رو اینجا بذار

# منوی اصلی کاربر
menu = ReplyKeyboardMarkup(
    [
        ["📥 دانلود بازی", "👤 حساب کاربری"],
        ["🛠 پشتیبانی", "📢 کانال"]
    ],
    resize_keyboard=True
)

# منوی پیشرفته ادمین
admin_menu = ReplyKeyboardMarkup(
    [
        ["📊 آمار کاربران", "➕ افزودن بازی", "❌ حذف بازی"],
        ["📋 لیست بازی‌ها", "📢 ارسال همگانی", "📈 آمار دانلود"],
        ["🔑 تغییر رمز مدیریت", "🗑 پاکسازی کاربران", "⚙️ تنظیمات"],
        ["🚧 به زودی...", "🏠 بازگشت"]
    ],
    resize_keyboard=True
)

# منوی بخش تنظیمات
settings_menu = ReplyKeyboardMarkup(
    [
        ["🔧 تغییر آیدی پشتیبانی", "🔗 تغییر لینک کانال"],
        ["🔙 بازگشت به پنل"]
    ],
    resize_keyboard=True
)

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
    config = load_settings()
    
    if user.username != config["admin_username"]:    
        await update.message.reply_text("⛔ شما دسترسی به پنل مدیریت ندارید.")    
        return    
    
    if user.id in authenticated_admins:
        await update.message.reply_text(
            "🔧 پنل مدیریت Game15Vox\n\nبه پنل مدیریت خوش آمدید.",
            reply_markup=admin_menu
        )
        return

    admin_states[user.id] = {"stage": "login"}
    await update.message.reply_text(
        "🔑 لطفا رمز عبور پنل مدیریت را وارد کنید:",
        reply_markup=ReplyKeyboardRemove()
    )

# ----------------- پردازشگر مرکزی پیام‌ها (Handler) -----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()    
    user_id = update.effective_user.id    
    username = update.effective_user.username    

    save_user(user_id)    
    config = load_settings()

    # ==================== بخش ادمین ====================
    if username == config["admin_username"]:
        
        # ۱. بررسی احراز هویت ادمین
        if user_id in admin_states and admin_states[user_id].get("stage") == "login":
            if text == config["admin_password"]:
                authenticated_admins.add(user_id)
                admin_states.pop(user_id, None)
                await update.message.reply_text(
                    "✅ رمز عبور تایید شد.\n\n🔧 پنل مدیریت Game15Vox\n\nبه پنل مدیریت خوش آمدید.",
                    reply_markup=admin_menu
                )
            else:
                await update.message.reply_text("❌ رمز عبور اشتباه است. دوباره تلاش کنید:")
            return

        # ۲. پردازش مراحل مختلف عملیات ادمین (FSM)
        if user_id in authenticated_admins and user_id in admin_states:
            stage = admin_states[user_id].get("stage")

            # مراحل افزودن بازی
            if stage == "add_game_code":
                admin_states[user_id]["game_code"] = text
                admin_states[user_id]["stage"] = "add_game_id"
                await update.message.reply_text(f"🔹 کد بازی «{text}» دریافت شد.\n\n📥 حالا Message ID فایل را بفرستید:")
                return
            
            elif stage == "add_game_id":
                if not text.isdigit():
                    await update.message.reply_text("❌ خطا: Message ID باید عدد باشد. دوباره ارسال کنید:")
                    return
                game_code = admin_states[user_id]["game_code"]
                games = load_games()
                games[game_code] = {"message_id": int(text), "downloads": games.get(game_code, {}).get("downloads", 0)}
                save_games(games)
                admin_states.pop(user_id, None)
                await update.message.reply_text(f"✅ بازی با کد {game_code} ذخیره شد.", reply_markup=admin_menu)
                return

            # مرحله حذف بازی
            elif stage == "delete_game":
                games = load_games()
                if text in games:
                    games.pop(text)
                    save_games(games)
                    await update.message.reply_text(f"✅ بازی با کد «{text}» با موفقیت حذف شد.", reply_markup=admin_menu)
                else:
                    await update.message.reply_text("❌ چنین کدی در سیستم پیدا نشد.", reply_markup=admin_menu)
                admin_states.pop(user_id, None)
                return

            # مرحله ارسال همگانی
            elif stage == "broadcast":
                admin_states.pop(user_id, None)
                users = load_users()
                await update.message.reply_text(f"📢 فرآیند ارسال پیام به {len(users)} کاربر شروع شد. لطفا صبر کنید...", reply_markup=admin_menu)
                
                success, failed = 0, 0
                for u_id in users:
                    try:
                        await context.bot.forward_message(chat_id=u_id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
                        success += 1
                        await asyncio.sleep(0.05) # جلوگیری از اسپم بلاک تلگرام
                    except:
                        failed += 1
                
                await update.message.reply_text(f"📊 نتیجه ارسال همگانی:\n\n✅ موفق: {success}\n❌ ناموفق: {failed}")
                return

            # مرحله تغییر رمز عبور
            elif stage == "change_password":
                config["admin_password"] = text
                save_settings(config)
                admin_states.pop(user_id, None)
                await update.message.reply_text("🔑 رمز عبور مدیریت با موفقیت تغییر کرد.", reply_markup=admin_menu)
                return

            # مراحل بخش تنظیمات
            elif stage == "set_support":
                config["support_username"] = text
                save_settings(config)
                admin_states.pop(user_id, None)
                await update.message.reply_text(f"✅ آیدی پشتیبانی به {text} تغییر یافت.", reply_markup=settings_menu)
                return

            elif stage == "set_channel":
                config["channel_link"] = text
                save_settings(config)
                admin_states.pop(user_id, None)
                await update.message.reply_text(f"✅ لینک کانال به {text} تغییر یافت.", reply_markup=settings_menu)
                return

        # ۳. کلیک بر روی دکمه‌های منوی ادمین
        if user_id in authenticated_admins:
            if text == "📊 آمار کاربران":
                games_count = len(load_games())
                users_count = len(load_users())
                await update.message.reply_text(f"📊 آمار ربات Game15Vox\n\n👥 تعداد کاربران: {users_count}\n🎮 تعداد بازی‌های ثبت شده: {games_count}")
                return

            elif text == "➕ افزودن بازی":
                admin_states[user_id] = {"stage": "add_game_code"}
                await update.message.reply_text("➕ یک کد برای بازی ارسال کنید (مثلاً: gta5):", reply_markup=ReplyKeyboardRemove())
                return

            elif text == "❌ حذف بازی":
                admin_states[user_id] = {"stage": "delete_game"}
                await update.message.reply_text("❌ کد بازی که قصد حذفش را دارید ارسال کنید:", reply_markup=ReplyKeyboardRemove())
                return

            elif text == "📋 لیست بازی‌ها":
                games = load_games()
                if not games:
                    await update.message.reply_text("📋 هیچ بازی ثبت نشده است.")
                    return
                report = "📋 لیست کامل بازی‌های ثبت شده:\n\n"
                for code, data in games.items():
                    m_id = data.get("message_id") if isinstance(data, dict) else data
                    report += f"🔑 کد: `{code}` ➡️ شناسه پیام: `{m_id}`\n"
                await update.message.reply_text(report, parse_mode="Markdown")
                return

            elif text == "📢 ارسال همگانی":
                admin_states[user_id] = {"stage": "broadcast"}
                await update.message.reply_text("📢 پیام خود را بفرستید (متن، عکس یا فیلم):", reply_markup=ReplyKeyboardRemove())
                return

            elif text == "📈 آمار دانلود":
                games = load_games()
                if not games:
                    await update.message.reply_text("📈 آماری وجود ندارد.")
                    return
                sorted_games = sorted(games.items(), key=lambda item: item[1].get("downloads", 0) if isinstance(item[1], dict) else 0, reverse=True)
                report = "📈 آمار دانلود بازی‌ها (پر بازدیدترین):\n\n"
                for code, data in sorted_games:
                    dl = data.get("downloads", 0) if isinstance(data, dict) else 0
                    report += f"🎮 بازی: `{code}` ➡️ تعداد دانلود: *{dl}*\n"
                await update.message.reply_text(report, parse_mode="Markdown")
                return

            elif text == "🔑 تغییر رمز مدیریت":
                admin_states[user_id] = {"stage": "change_password"}
                await update.message.reply_text("🔑 رمز عبور جدید پنل ادمین را بفرستید:", reply_markup=ReplyKeyboardRemove())
                return

            elif text == "🗑 پاکسازی کاربران":
                users = load_users()
                await update.message.reply_text(f"🔍 در حال بررسی و پاکسازی {len(users)} کاربر...", reply_markup=admin_menu)
                active_users = []
                blocked_count = 0
                for u_id in users:
                    try:
                        await context.bot.send_chat_action(chat_id=u_id, action="typing")
                        active_users.append(u_id)
                    except:
                        blocked_count += 1
                update_users_list(active_users)
                await update.message.reply_text(f"🗑 پاکسازی انجام شد!\n\n❌ کاربران غیرفعال حذف شده: {blocked_count}\n👥 کاربران فعال باقی‌مانده: {len(active_users)}")
                return

            elif text == "⚙️ تنظیمات":
                await update.message.reply_text("⚙️ به بخش تنظیمات پیکربندی ربات خوش آمدید.", reply_markup=settings_menu)
                return

            # دکمه‌های داخل بخش تنظیمات
            elif text == "🔧 تغییر آیدی پشتیبانی":
                admin_states[user_id] = {"stage": "set_support"}
                await update.message.reply_text("👤 آیدی جدید پشتیبانی را همراه با @ ارسال کنید:")
                return

            elif text == "🔗 تغییر لینک کانال":
                admin_states[user_id] = {"stage": "set_channel"}
                await update.message.reply_text("🔗 لینک جدید کانال را ارسال کنید:")
                return

            elif text == "🔙 بازگشت به پنل":
                await update.message.reply_text("🔧 بازگشت به پنل اصلی مدیریت", reply_markup=admin_menu)
                return

            elif text == "🚧 به زودی...":    
                await update.message.reply_text("🚧 این بخش در نسخه‌های بعدی اضافه خواهد شد.")    
                return    

            elif text == "🏠 بازگشت":    
                authenticated_admins.discard(user_id)
                admin_states.pop(user_id, None)
                await update.message.reply_text("🏠 بازگشت به منوی اصلی", reply_markup=menu)    
                return    

    # ==================== بخش منوی عمومی کاربران ====================
    if text == "📥 دانلود بازی":    
        waiting_for_code.add(user_id)    
        await update.message.reply_text(    
            "📥 دانلود بازی\n\n"    
            "🔎 کد بازی مورد نظر را ارسال کنید.\n\n"    
            "💡 کد هر بازی داخل پست همان بازی در کانال قرار دارد."    
        )    
        return    

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

    elif text == "🛠 پشتیبانی":    
        await update.message.reply_text(f"🛠 مرکز پشتیبانی Game15Vox\n\n👤 {config['support_username']}")    
        return    

    elif text == "📢 کانال":    
        await update.message.reply_text(f"📢 کانال رسمی Game15Vox\n\n🔗 {config['channel_link']}")    
        return    

    # پردازش دانلود بازی (دریافت کد از کاربر عادی)
    if user_id in waiting_for_code:    
        games = load_games()
        
        if text in games:    
            try:    
                game_data = games[text]
                # سازگاری با سیستم ذخیره قدیم و جدید (آبجکت یا عدد ساده)
                message_id = game_data["message_id"] if isinstance(game_data, dict) else game_data
                
                await context.bot.copy_message(    
                    chat_id=update.effective_chat.id,    
                    from_chat_id=config["file_channel"],    
                    message_id=int(message_id)    
                )    
                await update.message.reply_text("✅ فایل با موفقیت ارسال شد.\n\n🎮 Game15Vox")
                
                # ثبت آمار دانلود
                if isinstance(game_data, dict):
                    games[text]["downloads"] = game_data.get("downloads", 0) + 1
                else:
                    games[text] = {"message_id": game_data, "downloads": 1}
                save_games(games)

            except Exception:    
                await update.message.reply_text("⚠️ در ارسال فایل مشکلی پیش آمد.")    
        else:    
            await update.message.reply_text("❌ کد وارد شده معتبر نیست.")    

        waiting_for_code.discard(user_id)    
        return    

    # پیام پیش‌فرض در صورت زدن متن اشتباه
    await update.message.reply_text("❌ لطفاً از منوی ربات استفاده کنید.")

# ----------------- راه‌اندازی برنامه -----------------
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot Started...")
app.run_polling()
