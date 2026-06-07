import json
import os
import asyncio
import urllib.parse
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
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

DEFAULT_SETTINGS = {
    "admin_username": 'Game15VoxSupport',
    "admin_password": "AriaAria1389",
    "file_channel": -1003933220851,
    "support_username": "@Audhdudjjs",
    "channel_link": "https://t.me/Game15Vox"
}

# ----------------- توابع مدیریت اطلاعات -----------------
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
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_user(user):
    users = load_users()
    user_id = str(user.id)
    if user_id not in users:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        users[user_id] = {
            "first_name": user.first_name,
            "username": f"@{user.username}" if user.username else "بدون یوزرنیم",
            "join_date": now
        }
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
        except:
            pass

# ----------------- تابع هوشمند بررسی آپدیت اختصاصی APKPure -----------------
async def fetch_latest_version_apkpure(game_name: str):
    """
    این تابع نام بازی را در سایت APKPure جستجو کرده و آخرین نسخه و لینک آن را پیدا می‌کند.
    """
    encoded_name = urllib.parse.quote(game_name)
    search_url = f"https://apkpure.net/search?q={encoded_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    return None, None
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # پیدا کردن اولین نتیجه در صفحه سرچ APKPure
                first_result = soup.find('a', class_='first-item') or soup.find('div', class_='search-res').find('a') if soup.find('div', class_='search-res') else None
                if not first_result:
                    first_result = soup.find('a', class_='title')
                
                if first_result and first_result.get('href'):
                    game_page_url = first_result['href']
                    if not game_page_url.startswith('https'):
                        game_page_url = f"https://apkpure.net{game_page_url}"
                    
                    # ورود به صفحه اختصاصی بازی برای برداشتن ورژن دقیق
                    async with session.get(game_page_url, headers=headers, timeout=10) as game_response:
                        if game_response.status == 200:
                            game_html = await game_response.text()
                            game_soup = BeautifulSoup(game_html, 'html.parser')
                            
                            # پیدا کردن ورژن در تگ اختصاصی APKPure
                            version_info = game_soup.find('span', itemprop='version') or game_soup.find('div', class_='details-sdk').find('span')
                            if version_info:
                                latest_version = version_info.text.strip().lower().replace('v', '')
                                return latest_version, game_page_url
                            
                            # تلاش دوم اگر ساختار صفحه فرق داشت (استخراج از عنوان صفحه)
                            title_div = game_soup.find('div', class_='title-like')
                            if title_div and '(' in title_div.text:
                                text = title_div.text
                                version = text[text.find("(")+1:text.find(")")]
                                return version.strip().lower().replace('v', ''), game_page_url
                                
                    return "نامشخص (نیاز به بررسی لینک)", game_page_url
    except Exception as e:
        print(f"Error scraping {game_name} from APKPure: {e}")
    return None, None

# ----------------- وضعیت‌ها و منوهای ربات -----------------
waiting_for_code = set()
admin_states = {}  
authenticated_admins = set()  

TOKEN = '8907948308:AAEkCcEFkviGA6rgP_6EOaWYg4GLzkBj3lU'  # ⚠️ توکن رباتت را دقیقاً اینجا بذار

menu = ReplyKeyboardMarkup(
    [
        ["📥 دانلود بازی", "👤 حساب کاربری"],
        ["🛠 پشتیبانی", "📢 کانال"]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    [
        ["📊 آمار کاربران", "➕ افزودن بازی", "❌ حذف بازی"],
        ["📋 لیست بازی‌ها", "🔄 بررسی آپدیت بازی‌ها", "📢 ارسال همگانی"],
        ["🎨 ساخت بنر تبلیغاتی", "📈 آمار دانلود", "🔑 تغییر رمز مدیریت"],
        ["⚙️ تنظیمات", "🗑 پاکسازی کاربران", "🏠 بازگشت"]
    ],
    resize_keyboard=True
)

settings_menu = ReplyKeyboardMarkup(
    [
        ["📥 گرفتن بک‌آپ بازی‌ها", "📤 بارگذاری بک‌آپ"],
        ["🔧 تغییر آیدی پشتیبانی", "🔗 تغییر لینک کانال"],
        ["🔙 بازگشت به پنل"]
    ],
    resize_keyboard=True
)

part_menu = ReplyKeyboardMarkup(
    [
        ["📥 ثبت شناسه فایل (پارت جدید)"],
        ["💾 ذخیره و اتمام ثبت"]
    ],
    resize_keyboard=True
)

# ----------------- دستورات اصلی (Commands) -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)    
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
        await update.message.reply_text("🔧 پنل مدیریت Game15Vox\n\nبه پنل مدیریت خوش آمدید.", reply_markup=admin_menu)
        return

    admin_states[user.id] = {"stage": "login"}
    await update.message.reply_text("🔑 لطفا رمز عبور پنل مدیریت را وارد کنید:", reply_markup=ReplyKeyboardRemove())

# ----------------- پردازشگر مرکزی پیام‌ها (Handler) -----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()    
    user_id = update.effective_user.id    
    username = update.effective_user.username    

    save_user(update.effective_user)    
    config = load_settings()

    # ==================== بخش ادمین ====================
    if username == config["admin_username"]:
        
        if user_id in admin_states and admin_states[user_id].get("stage") == "login":
            if text == config["admin_password"]:
                authenticated_admins.add(user_id)
                admin_states.pop(user_id, None)
                await update.message.reply_text("✅ رمز عبور تایید شد.\n\nبه پنل مدیریت خوش آمدید.", reply_markup=admin_menu)
            else:
                await update.message.reply_text("❌ رمز عبور اشتباه است. دوباره تلاش کنید:")
            return

        if user_id in authenticated_admins and user_id in admin_states:
            stage = admin_states[user_id].get("stage")

            if stage == "add_game_code":
                admin_states[user_id]["game_code"] = text.lower()
                admin_states[user_id]["stage"] = "add_game_name"
                await update.message.reply_text(f"🔹 کد بازی «{text}» دریافت شد.\n\n📛 حالا نام دقیق و انگلیسی بازی را وارد کنید (جهت سرچ در APKPure):")
                return
            
            elif stage == "add_game_name":
                admin_states[user_id]["game_name"] = text
                admin_states[user_id]["stage"] = "add_game_version"
                await update.message.reply_text(f"🔹 نام بازی «{text}» ثبت شد.\n\n🔢 نسخه فعلی بازی را وارد کنید (مثال: 1.4.4):")
                return

            elif stage == "add_game_version":
                admin_states[user_id]["game_version"] = text
                admin_states[user_id]["message_ids"] = []
                admin_states[user_id]["stage"] = "manage_parts"
                await update.message.reply_text(
                    f"🔹 نسخه «{text}» ثبت شد.\n\n"
                    "حالا می‌توانید پارت‌های بازی را یکی‌یکی اضافه کنید یا بازی را ذخیره کنید:",
                    reply_markup=part_menu
                )
                return
            
            elif stage == "manage_parts":
                if text == "📥 ثبت شناسه فایل (پارت جدید)":
                    admin_states[user_id]["stage"] = "waiting_for_part_id"
                    await update.message.reply_text("📥 لطفا Message ID فایل (پارت جدید) را بفرستید:", reply_markup=ReplyKeyboardRemove())
                    return
                
                elif text == "💾 ذخیره و اتمام ثبت":
                    game_code = admin_states[user_id]["game_code"]
                    game_name = admin_states[user_id]["game_name"]
                    game_ver = admin_states[user_id]["game_version"]
                    part_ids = admin_states[user_id]["message_ids"]
                    
                    if not part_ids:
                        await update.message.reply_text("⚠️ شما هیچ فایلی ثبت نکرده‌اید! ابتدا حداقل یک پارت ثبت کنید.")
                        return
                    
                    games = load_games()
                    games[game_code] = {
                        "name": game_name,
                        "version": game_ver,
                        "message_ids": part_ids,
                        "downloads": games.get(game_code, {}).get("downloads", 0)
                    }
                    save_games(games)
                    admin_states.pop(user_id, None)
                    await update.message.reply_text(f"✅ بازی «{game_name}» نسخه {game_ver} با موفقیت همراه با {len(part_ids)} پارت ذخیره شد.", reply_markup=admin_menu)
                    return
                
            elif stage == "waiting_for_part_id":
                if not text.isdigit():
                    await update.message.reply_text("❌ خطا: Message ID باید عدد باشد. دوباره ارسال کنید:")
                    return
                
                admin_states[user_id]["message_ids"].append(int(text))
                current_count = len(admin_states[user_id]["message_ids"])
                admin_states[user_id]["stage"] = "manage_parts"
                await update.message.reply_text(
                    f"✅ فایل شماره {current_count} ثبت موقت شد.\n\n"
                    "می‌توانید فایل بعدی را اضافه کنید یا بازی را ذخیره کنید:",
                    reply_markup=part_menu
                )
                return

            elif stage == "delete_game":
                games = load_games()
                if text in games:
                    games.pop(text)
                    save_games(games)
                    await update.message.reply_text(f"✅ بازی با موفقیت حذف شد.", reply_markup=admin_menu)
                else:
                    await update.message.reply_text("❌ چنین کدی پیدا نشد.", reply_markup=admin_menu)
                admin_states.pop(user_id, None)
                return

            elif stage == "broadcast":
                admin_states.pop(user_id, None)
                users = load_users()
                await update.message.reply_text(f"📢 فرآیند ارسال پیام به {len(users)} کاربر شروع شد...", reply_markup=admin_menu)
                success, failed = 0, 0
                for u_id in users.keys():
                    try:
                        await context.bot.forward_message(chat_id=int(u_id), from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
                        success += 1
                        await asyncio.sleep(0.05)
                    except:
                        failed += 1
                await update.message.reply_text(f"📊 نتیجه ارسال:\n✅ موفق: {success}\n❌ ناموفق: {failed}")
                return

            elif stage == "change_password":
                config["admin_password"] = text
                save_settings(config)
                admin_states.pop(user_id, None)
                await update.message.reply_text("🔑 رمز عبور مدیریت تغییر کرد.", reply_markup=admin_menu)
                return

            elif stage == "set_support":
                config["support_username"] = text
                save_settings(config)
                admin_states.pop(user_id, None)
                await update.message.reply_text(f"✅ آیدی پشتیبانی تغییر یافت.", reply_markup=settings_menu)
                return

            elif stage == "set_channel":
                config["channel_link"] = text
                save_settings(config)
                admin_states.pop(user_id, None)
                await update.message.reply_text(f"✅ لینک کانال تغییر یافت.", reply_markup=settings_menu)
                return

            # ==================== پردازش و اعمال بک آپ متنی ====================
            elif stage == "process_backup":
                admin_states.pop(user_id, None)
                lines = text.split("\n")
                games = load_games()
                added_count = 0
                
                for line in lines:
                    line = line.strip()
                    if not line or "|" not in line:
                        continue
                    try:
                        parts = line.split("|")
                        if len(parts) == 4:
                            g_code = parts[0].strip().lower()
                            g_name = parts[1].strip()
                            g_ver = parts[2].strip()
                            g_ids = [int(i) for i in parts[3].strip().split(",") if i.strip().isdigit()]
                            
                            if g_code and g_name and g_ids:
                                games[g_code] = {
                                    "name": g_name,
                                    "version": g_ver,
                                    "message_ids": g_ids,
                                    "downloads": games.get(g_code, {}).get("downloads", 0)
                                }
                                added_count += 1
                    except Exception as e:
                        print(f"Error parsing backup line: {e}")
                
                save_games(games)
                await update.message.reply_text(f"✅ بازیابی کامل شد!\n⚡ تعداد {added_count} بازی با موفقیت مجدداً درون ربات زنده شد.", reply_markup=settings_menu)
                return

        if user_id in authenticated_admins:
            if text == "📊 آمار کاربران":
                games_count = len(load_games())
                users_count = len(load_users())
                await update.message.reply_text(f"📊 آمار ربات\n👥 تعداد کاربران: {users_count}\n🎮 بازی‌های ثبت شده: {games_count}")
                return

            elif text == "➕ افزودن بازی":
                admin_states[user_id] = {"stage": "add_game_code"}
                await update.message.reply_text("➕ یک کد برای بازی ارسال کنید (مثلاً: vector):", reply_markup=ReplyKeyboardRemove())
                return

            elif text == "❌ حذف بازی":
                admin_states[user_id] = {"stage": "delete_game"}
                await update.message.reply_text("❌ کد بازی مورد نظر جهت حذف را ارسال کنید:", reply_markup=ReplyKeyboardRemove())
                return

            # ==================== سیستم هوشمند اسکرپر APKPure برای آخر هفته‌ها ====================
            elif text == "🔄 بررسی آپدیت بازی‌ها":
                games = load_games()
                if not games:
                    await update.message.reply_text("❌ هیچ بازی در دیتابیس جهت بررسی یافت نشد.")
                    return
                
                await update.message.reply_text("🔍 اتصال به APKPure برقرار شد. در حال اسکن کل بازی‌ها و نسخه‌ها، لطفا شکیبا باشید...")
                
                update_alerts = []
                for code, data in games.items():
                    if isinstance(data, dict) and "name" in data:
                        g_name = data["name"]
                        current_version = str(data.get("version", "0")).lower().strip()
                        
                        # اجرای متد خزنده سایت APKPure
                        latest_version, download_link = await fetch_latest_version_apkpure(g_name)
                        
                        if latest_version and latest_version != current_version:
                            update_alerts.append(
                                f"🎮 **بازی:** {g_name} (کد: `{code}`)\n"
                                f"📥 **نسخه شما:** `{current_version}`\n"
                                f"⚡ **جدیدترین نسخه APKPure:** `{latest_version}`\n"
                                f"🔗 [مشاهده و دانلود فایل آپدیت جدید]({download_link})\n"
                                f"──────────────────"
                            )
                        # وقفه ۲ ثانیه‌ای برای جلوگیری از بلاک شدن آیپی توسط کلودفلر APKPure
                        await asyncio.sleep(2)
                
                if update_alerts:
                    report = "🔔 **گزارش آپدیت بازی‌های خارجی شما از APKPure:**\n\n" + "\n".join(update_alerts)
                    if len(report) > 4096:
                        for i in range(0, len(report), 4000):
                            await update.message.reply_text(report[i:i+4000], parse_mode="Markdown", disable_web_page_preview=True)
                    else:
                        await update.message.reply_text(report, parse_mode="Markdown", disable_web_page_preview=True)
                else:
                    await update.message.reply_text("✅ تمام بازی‌های خارجی ربات شما کاملاً با آخرین نسخه سایت APKPure مطابقت دارند!")
                return

            elif text == "📋 لیست بازی‌ها":
                games = load_games()
                if not games:
                    await update.message.reply_text("📋 هیچ بازی ثبت نشده است.")
                    return
                report = "📋 **لیست بازی‌های ثبت شده:**\n\n"
                for code, data in games.items():
                    if isinstance(data, dict):
                        report += f"🎮 **{data.get('name')}** | نسخه: `{data.get('version')}`\n🔑 کد دانلود: `{code}` | تعداد پارت‌ها: `{len(data.get('message_ids', []))}`\n\n"
                await update.message.reply_text(report, parse_mode="Markdown")
                return

            elif text == "🎨 ساخت بنر تبلیغاتی":
                games = load_games()
                if not games:
                    await update.message.reply_text("❌ بازی یافت نشد.")
                    return
                last_games = list(games.items())[-3:]
                last_games.reverse()
                
                banner = "🎮 **جدیدترین بازی‌های اضافه شده به ربات Game15Vox!** 🎮\n\n"
                for code, data in last_games:
                    if isinstance(data, dict):
                        banner += f"🔹 **{data.get('name')}** (نسخه {data.get('version')})\n👈 کد دانلود: `{code}`\n\n"
                banner += f"🤖 آیدی ربات: @Game15VoxBot\n📢 کانال ما: {config['channel_link']}"
                await update.message.reply_text(banner, parse_mode="Markdown")
                return

            elif text == "👥 لیست کاربران":
                users = load_users()
                if not users:
                    await update.message.reply_text("👥 کاربری یافت نشد.")
                    return
                report = "👥 **لیست کاربران:**\n\n"
                for u_id, info in users.items():
                    report += f"🆔 `{u_id}` | نام: {info['first_name']} | آیدی: {info['username']}\n"
                await update.message.reply_text(report, parse_mode="Markdown")
                return

            elif text == "📢 ارسال همگانی":
                admin_states[user_id] = {"stage": "broadcast"}
                await update.message.reply_text("📢 پیام خود را بفرستید:", reply_markup=ReplyKeyboardRemove())
                return

            elif text == "📈 آمار دانلود":
                games = load_games()
                if not games:
                    await update.message.reply_text("📈 آماری وجود ندارد.")
                    return
                sorted_games = sorted(games.items(), key=lambda item: item[1].get("downloads", 0) if isinstance(item[1], dict) else 0, reverse=True)
                report = "📈 آمار دانلود بازی‌ها:\n\n"
                for code, data in sorted_games:
                    g_name = data.get("name", code) if isinstance(data, dict) else code
                    dl = data.get("downloads", 0) if isinstance(data, dict) else 0
                    report += f"🎮 *{g_name}* (کد: `{code}`) ➡️ دانلود: *{dl}*\n"
                await update.message.reply_text(report, parse_mode="Markdown")
                return

            elif text == "🔑 تغییر رمز مدیریت":
                admin_states[user_id] = {"stage": "change_password"}
                await update.message.reply_text("🔑 رمز عبور جدید را بفرستید:", reply_markup=ReplyKeyboardRemove())
                return

            elif text == "🗑 پاکسازی کاربران":
                users = load_users()
                await update.message.reply_text("🗑 در حال پاکسازی کاربران غیرفعال...", reply_markup=admin_menu)
                active_users = {}
                blocked_count = 0
                for u_id, info in users.items():
                    try:
                        await context.bot.send_chat_action(chat_id=int(u_id), action="typing")
                        active_users[u_id] = info
                    except:
                        blocked_count += 1
                try:
                    with open(USERS_FILE, "w", encoding="utf-8") as f:
                        json.dump(active_users, f, ensure_ascii=False, indent=4)
                except:
                    pass
                await update.message.reply_text(f"🗑 پاکسازی انجام شد!\n❌ حذفیات: {blocked_count}\n👥 کاربران فعال: {len(active_users)}")
                return

            elif text == "⚙️ تنظیمات":
                await update.message.reply_text("⚙️ تنظیمات و سیستم پشتیبان‌گیری متنی بازی‌ها:", reply_markup=settings_menu)
                return

            # ==================== تولید خروجی متن پشتیبان (Backup) ====================
            elif text == "📥 گرفتن بک‌آپ بازی‌ها":
                games = load_games()
                if not games:
                    await update.message.reply_text("❌ هیچ بازی برای بک‌آپ گرفتن یافت نشد.")
                    return
                
                backup_text = ""
                for code, data in games.items():
                    if isinstance(data, dict):
                        ids_str = ",".join(map(str, data.get("message_ids", [])))
                        backup_text += f"{code}|{data.get('name')}|{data.get('version')}|{ids_str}\n"
                
                reply_msg = (
                    "📥 **متن بک‌آپ بازی‌های شما با موفقیت ساخته شد:**\n\n"
                    f"`{backup_text.strip()}`\n\n"
                    "⚠️ متن بالا را کپی کرده و در جایی نگه دارید. پس از آپدیت ربات در گیت‌هاب، با زدن دکمه بارگذاری آن را ارسال کنید تا همه بازی‌ها زنده شوند."
                )
                await update.message.reply_text(reply_msg, parse_mode="Markdown")
                return

            elif text == "📤 بارگذاری بک‌آپ":
                admin_states[user_id] = {"stage": "process_backup"}
                await update.message.reply_text("📤 لطفا متن بک‌آپی که قبلاً کپی کرده بودید را عینا و بدون تغییر ارسال کنید:", reply_markup=ReplyKeyboardRemove())
                return

            elif text == "🔧 تغییر آیدی پشتیبانی":
                admin_states[user_id] = {"stage": "set_support"}
                await update.message.reply_text("👤 آیدی جدید پشتیبانی با @:")
                return

            elif text == "🔗 تغییر لینک کانال":
                admin_states[user_id] = {"stage": "set_channel"}
                await update.message.reply_text("🔗 لینک جدید کانال:")
                return

            elif text == "🔙 بازگشت به پنل":
                await update.message.reply_text("🔧 بازگشت به پنل اصلی", reply_markup=admin_menu)
                return

            elif text == "🏠 بازگشت":    
                authenticated_admins.discard(user_id)
                admin_states.pop(user_id, None)
                await update.message.reply_text("🏠 بازگشت به منوی اصلی", reply_markup=menu)    
                return    

    # ==================== بخش منوی عمومی کاربران (دانلود چند پارت) ====================
    if text == "📥 دانلود بازی":    
        waiting_for_code.add(user_id)    
        await update.message.reply_text("📥 کد بازی مورد نظر را ارسال کنید (کد بازی در پست کانال درج شده است):")    
        return    

    elif text == "👤 حساب کاربری":    
        name = update.effective_user.first_name    
        await update.message.reply_text(f"👤 حساب کاربری\n\n🆔 نام: {name}\n✅ وضعیت حساب: فعال\n🎮 دسترسی دانلود: فعال")    
        return    

    elif text == "🛠 پشتیبانی":    
        await update.message.reply_text(f"🛠 مرکز پشتیبانی Game15Vox\n\n👤 {config['support_username']}")    
        return    

    elif text == "📢 کانال":    
        await update.message.reply_text(f"📢 کانال رسمی ما\n\n🔗 {config['channel_link']}")    
        return    

    if user_id in waiting_for_code:    
        games = load_games()
        clean_text = text.lower().strip()
        
        if clean_text in games:    
            try:    
                game_data = games[clean_text]
                if isinstance(game_data, dict) and "message_ids" in game_data:
                    # ارسال تمام فایل‌ها/پارت‌های ثبت شده به نوبت
                    for m_id in game_data["message_ids"]:
                        await context.bot.copy_message(    
                            chat_id=update.effective_chat.id,    
                            from_chat_id=config["file_channel"],    
                            message_id=int(m_id)    
                        )    
                        await asyncio.sleep(0.3)
                    await update.message.reply_text("✅ تمام پارت‌های بازی با موفقیت ارسال شد.\n\n🎮 Game15Vox")
                    
                    # افزایش آمار دانلود بازی
                    games[clean_text]["downloads"] = game_data.get("downloads", 0) + 1
                    save_games(games)
            except Exception:    
                await update.message.reply_text("⚠️ در ارسال فایل‌ها مشکلی پیش آمد.")    
        else:    
            await update.message.reply_text("❌ کد وارد شده معتبر نیست یا بازی حذف شده است.")    

        waiting_for_code.discard(user_id)    
        return    

    await update.message.reply_text("❌ لطفاً از منوی ربات استفاده کنید.")

# ----------------- راه‌اندازی برنامه پایتون -----------------
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Game15Vox Bot is Running perfectly with APKPure Web Scraper...")
app.run_polling()
