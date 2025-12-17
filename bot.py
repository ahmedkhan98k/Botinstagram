#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تليجرام لإرسال متابعين انستغرام
المطور: AHMED KHANA
"""

import os
import sys
import time
import json
import logging
import asyncio
import requests
from typing import Dict, Optional
from datetime import datetime

# مكتبات تليجرام
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# تكوين اللوجر
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== إعدادات البوت ====================
TOKEN = os.environ.get("8440366624:AAHUFv8EnYpJ_hgbBXm_Zty5SS8FaZR8skk", "")
ADMIN_IDS = [int(x) for x in os.environ.get("110484930", "").split(",") if x]
BOT_USERNAME = "instagram_followers_ahmed_bot"

# ==================== فئات المستخدمين ====================
class User:
    def __init__(self, user_id: int):
        self.id = user_id
        self.insta_username = None
        self.insta_password = None
        self.session_cookies = {}
        self.balance = 1000  # رصيد افتراضي
        self.is_premium = False
        self.last_activity = datetime.now()
        
    def to_dict(self):
        return {
            'id': self.id,
            'insta_username': self.insta_username,
            'balance': self.balance,
            'is_premium': self.is_premium,
            'last_activity': self.last_activity.isoformat()
        }

class InstaFollowerBot:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.requests_log = []
        self.load_data()
    
    def load_data(self):
        """تحميل بيانات المستخدمين"""
        try:
            if os.path.exists('users.json'):
                with open('users.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_data in data:
                        user = User(user_data['id'])
                        user.insta_username = user_data['insta_username']
                        user.balance = user_data['balance']
                        user.is_premium = user_data['is_premium']
                        user.last_activity = datetime.fromisoformat(user_data['last_activity'])
                        self.users[user.id] = user
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    
    def save_data(self):
        """حفظ بيانات المستخدمين"""
        try:
            data = [user.to_dict() for user in self.users.values()]
            with open('users.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def get_user(self, user_id: int) -> User:
        """الحصول على مستخدم أو إنشاء جديد"""
        if user_id not in self.users:
            self.users[user_id] = User(user_id)
        self.users[user_id].last_activity = datetime.now()
        return self.users[user_id]

# إنشاء كائن البوت
bot_core = InstaFollowerBot()

# ==================== دوال instamoda.org ====================
def login_to_instamoda(username: str, password: str) -> Optional[dict]:
    """تسجيل الدخول إلى instamoda.org"""
    try:
        headers = {
            'authority': 'instamoda.org',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'ar-AE,ar;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://instamoda.org',
            'referer': 'https://instamoda.org/login',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = {
            'username': username,
            'password': password,
            'userid': '',
            'antiForgeryToken': '92e040589f9f0237f5ddd02297bbcf92',
        }
        
        response = requests.post(
            'https://instamoda.org/login',
            headers=headers,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                cookies = {}
                for cookie in response.cookies:
                    cookies[cookie.name] = cookie.value
                return {'success': True, 'cookies': cookies}
            else:
                return {'success': False, 'error': 'فشل تسجيل الدخول'}
        else:
            return {'success': False, 'error': f'خطأ في الخادم: {response.status_code}'}
            
    except Exception as e:
        return {'success': False, 'error': f'خطأ في الاتصال: {str(e)}'}

def send_instagram_followers(target_username: str, count: int, cookies: dict) -> dict:
    """إرسال متابعين انستغرام عبر instamoda.org"""
    try:
        # 1. البحث عن ID المستخدم
        headers = {
            'authority': 'instamoda.org',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'ar-AE,ar;q=0.9,en-US;q=0.8,en;q=0.7',
            'cookie': '; '.join([f'{k}={v}' for k, v in cookies.items()]),
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        params = {'formType': 'findUserID'}
        data = {'username': target_username}
        
        response = requests.post(
            'https://instamoda.org/tools/send-follower',
            params=params,
            headers=headers,
            data=data,
            timeout=30
        )
        
        if response.status_code != 200:
            return {'success': False, 'error': 'فشل في البحث عن المستخدم'}
        
        # استخراج ID المستخدم
        try:
            id_start = response.text.find('name="userID" value="') + len('name="userID" value="')
            id_end = response.text.find('"', id_start)
            user_id = response.text[id_start:id_end]
        except:
            return {'success': False, 'error': 'لم يتم العثور على المستخدم'}
        
        # 2. إرسال المتابعين
        headers = {
            'authority': 'instamoda.org',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'ar-AE,ar;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://instamoda.org',
            'referer': f'https://instamoda.org/tools/send-follower/{user_id}',
            'cookie': '; '.join([f'{k}={v}' for k, v in cookies.items()]),
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        params = {'formType': 'send'}
        data = {
            'adet': str(count),
            'userID': user_id,
            'userName': target_username,
        }
        
        response = requests.post(
            f'https://instamoda.org/tools/send-follower/{user_id}',
            params=params,
            headers=headers,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                return {
                    'success': True,
                    'message': f'تم طلب إرسال {count} متابع إلى @{target_username}',
                    'task_id': f'TASK_{int(time.time())}'
                }
            else:
                return {'success': False, 'error': f'فشل الإرسال: {result}'}
        else:
            return {'success': False, 'error': f'خطأ في الخادم: {response.status_code}'}
            
    except Exception as e:
        return {'success': False, 'error': f'خطأ في العملية: {str(e)}'}

# ==================== أوامر البوت ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    user = bot_core.get_user(update.effective_user.id)
    
    welcome_text = """
🚀 *مرحباً بك في بوت احمد خان رشق متابعين انستغرام*

👨‍💻 *المطور:* AHMED KHANA
📸 *انستغرام:* @_98sf
🎵 *تيك توك:* @_98ak

💰 *رصيدك الحالي:* {} متابع
👑 *الحالة:* {}

📋 *الأوامر المتاحة:*
/start - عرض هذه الرسالة
/login - تسجيل الدخول إلى instamoda.org
/send - إرسال متابعين
/balance - عرض رصيدك
/help - المساعدة

⚠️ *تنبيه:* هذا البوت يستخدم instamoda.org
    """.format(user.balance, "بريميوم" if user.is_premium else "عادي")
    
    keyboard = [
        [InlineKeyboardButton("🔐 تسجيل الدخول", callback_data='login')],
        [InlineKeyboardButton("📨 إرسال متابعين", callback_data='send')],
        [InlineKeyboardButton("💰 رصيدي", callback_data='balance')],
        [InlineKeyboardButton("🆘 المساعدة", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /help"""
    help_text = """
🆘 *مساعدة بوت رشق متابعين انستغرام*

📖 *كيفية الاستخدام:*
1. أولاً، سجل دخول باستخدام /login
2. ثم أرسل متابعين باستخدام /send
3. تابع رصيدك باستخدام /balance

🔐 *تسجيل الدخول:*
- يجب أن يكون لديك حساب في instamoda.org
- أدخل اسم المستخدم وكلمة المرور

📨 *إرسال المتابعين:*
- أدخل اسم المستخدم الهدف (بدون @)
- اختر عدد المتابعين (10-1000)

⚠️ *ملاحظات هامة:*
- الخدمة تستخدم instamoda.org
- قد تحدث أخطاء إذا كان الموقع محظوراً
- استخدم VPN إذا واجهت مشاكل

📞 *للتواصل والدعم:*
📸 @_98sf
🎵 @_98ak
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /balance"""
    user = bot_core.get_user(update.effective_user.id)
    
    balance_text = """
💰 *معلومات حسابك*

👤 *المستخدم:* {}
🆔 *رقم العضو:* #{}
💰 *الرصيد:* {} متابع
👑 *الحالة:* {}
📅 *آخر نشاط:* {}

💎 *لزيادة الرصيد:*
- تواصل مع المطور @_98sf
- أو انتظر التحديثات القادمة
    """.format(
        update.effective_user.first_name,
        user.id,
        user.balance,
        "بريميوم" if user.is_premium else "عادي",
        user.last_activity.strftime("%Y-%m-%d %H:%M")
    )
    
    await update.message.reply_text(balance_text, parse_mode='Markdown')

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /login"""
    await update.message.reply_text(
        "🔐 *يرجى إرسال بيانات الدخول بهذا الشكل:*\n\n"
        "اسم_المستخدم\nكلمة_المرور\n\n"
        "*مثال:*\n"
        "ahmed_khana\nmypassword123",
        parse_mode='Markdown'
    )

async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /send"""
    user = bot_core.get_user(update.effective_user.id)
    
    if not user.insta_username:
        await update.message.reply_text(
            "⚠️ *يجب تسجيل الدخول أولاً!*\n"
            "استخدم /login لتسجيل الدخول",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        "📨 *أرسل اسم المستخدم الهدف وعدد المتابعين:*\n\n"
        "اسم_المستخدم\nالعدد\n\n"
        "*مثال:*\n"
        "target_user\n300\n\n"
        "*ملاحظة:* العدد من 10 إلى 1000",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    user = bot_core.get_user(update.effective_user.id)
    text = update.message.text.strip()
    
    if '\n' in text:
        lines = text.split('\n')
        
        if len(lines) == 2 and not user.insta_username:
            # تسجيل الدخول
            username, password = lines[0].strip(), lines[1].strip()
            
            await update.message.reply_text(
                "🔐 *جارٍ تسجيل الدخول إلى instamoda.org...*",
                parse_mode='Markdown'
            )
            
            # محاكاة عملية تسجيل الدخول
            await asyncio.sleep(2)
            
            login_result = login_to_instamoda(username, password)
            
            if login_result['success']:
                user.insta_username = username
                user.insta_password = password
                user.session_cookies = login_result.get('cookies', {})
                bot_core.save_data()
                
                await update.message.reply_text(
                    "✅ *تم تسجيل الدخول بنجاح!*\n\n"
                    f"👤 المستخدم: {username}\n"
                    "💰 يمكنك الآن استخدام /send لإرسال المتابعين",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ *فشل تسجيل الدخول!*\n\n"
                    f"الخطأ: {login_result.get('error', 'غير معروف')}",
                    parse_mode='Markdown'
                )
                
        elif len(lines) == 2 and user.insta_username:
            # إرسال متابعين
            target_user, count_str = lines[0].strip(), lines[1].strip()
            
            try:
                count = int(count_str)
                if count < 10 or count > 1000:
                    await update.message.reply_text(
                        "❌ *العدد يجب أن يكون بين 10 و 1000!*",
                        parse_mode='Markdown'
                    )
                    return
                    
                if count > user.balance:
                    await update.message.reply_text(
                        f"❌ *رصيدك غير كافي!*\n\n"
                        f"💰 رصيدك: {user.balance}\n"
                        f"📨 المطلوب: {count}",
                        parse_mode='Markdown'
                    )
                    return
                    
                await update.message.reply_text(
                    f"🚀 *جارٍ إرسال {count} متابع إلى @{target_user}...*",
                    parse_mode='Markdown'
                )
                
                # محاكاة عملية الإرسال
                await asyncio.sleep(2)
                
                send_result = send_instagram_followers(
                    target_user, 
                    count, 
                    user.session_cookies
                )
                
                if send_result['success']:
                    user.balance -= count
                    bot_core.save_data()
                    
                    await update.message.reply_text(
                        f"✅ *تم الإرسال بنجاح!*\n\n"
                        f"👤 الهدف: @{target_user}\n"
                        f"📊 العدد: {count} متابع\n"
                        f"🆔 رقم المهمة: {send_result.get('task_id', 'N/A')}\n"
                        f"💰 الرصيد الجديد: {user.balance}\n\n"
                        f"⏳ سيتم الإضافة خلال 3-5 دقائق",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        f"❌ *فشل الإرسال!*\n\n"
                        f"الخطأ: {send_result.get('error', 'غير معروف')}",
                        parse_mode='Markdown'
                    )
                    
            except ValueError:
                await update.message.reply_text(
                    "❌ *الرجاء إدخال عدد صحيح!*",
                    parse_mode='Markdown'
                )
    
    else:
        await update.message.reply_text(
            "📝 *الرجاء إرسال البيانات بالشكل الصحيح:*\n\n"
            "للدخول: اسم_المستخدم\\nكلمة_المرور\n"
            "للإرسال: اسم_المستخدم\\nالعدد",
            parse_mode='Markdown'
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ضغطات الأزرار"""
    query = update.callback_query
    await query.answer()
    
    user = bot_core.get_user(query.from_user.id)
    
    if query.data == 'login':
        await query.edit_message_text(
            "🔐 *يرجى إرسال بيانات الدخول بهذا الشكل:*\n\n"
            "اسم_المستخدم\nكلمة_المرور",
            parse_mode='Markdown'
        )
        
    elif query.data == 'send':
        if not user.insta_username:
            await query.edit_message_text(
                "⚠️ *يجب تسجيل الدخول أولاً!*",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "📨 *أرسل اسم المستخدم الهدف وعدد المتابعين:*\n\n"
                "اسم_المستخدم\nالعدد",
                parse_mode='Markdown'
            )
            
    elif query.data == 'balance':
        balance_text = f"""
💰 *رصيدك الحالي:* {user.balance} متابع
👑 *الحالة:* {"بريميوم" if user.is_premium else "عادي"}
        """
        await query.edit_message_text(balance_text, parse_mode='Markdown')
        
    elif query.data == 'help':
        await query.edit_message_text(
            "🆘 *للحصول على المساعدة:*\n\n"
            "استخدم /help لعرض الأوامر\n"
            "أو تواصل مع المطور @_98sf",
            parse_mode='Markdown'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء"""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        error_text = f"⚠️ *حدث خطأ:*\n\n```\n{str(context.error)[:100]}...\n```"
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_text,
                parse_mode='Markdown'
            )
    except:
        pass

# ==================== الدالة الرئيسية ====================
def main():
    """الدالة الرئيسية لتشغيل البوت"""
    if not TOKEN:
        print("❌ يجب تعيين TELEGRAM_BOT_TOKEN في متغيرات البيئة!")
        sys.exit(1)
    
    print("=" * 50)
    print("🤖 بوت رشق متابعين انستغرام")
    print("👨‍💻 المطور: AHMED KHANA")
    print("📸 انستغرام: @_98sf")
    print("🎵 تيك توك: @_98ak")
    print("=" * 50)
    
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # إضافة handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("send", send_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # معالجة الأخطاء
    application.add_error_handler(error_handler)
    
    # تشغيل البوت
    print("🚀 جاري تشغيل البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# ==================== ملفات إضافية ====================
# ملف requirements.txt
REQUIREMENTS = """python-telegram-bot==20.3
requests==2.31.0
aiohttp==3.8.5
python-dotenv==1.0.0
"""

# ملف railway.json للـ Railway
RAILWAY_CONFIG = {
    "$schema": "https://railway.com/railway.schema.json",
    "build": {
        "builder": "NIXPACKS",
        "buildCommand": "pip install -r requirements.txt"
    },
    "deploy": {
        "startCommand": "python bot.py",
        "healthcheckPath": "/",
        "healthcheckTimeout": 100,
        "restartPolicyType": "ON_FAILURE"
    }
}

# ==================== ملف Dockerfile ====================
DOCKERFILE = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
"""

if __name__ == '__main__':
    # إنشاء ملفات التهيئة إذا لم تكن موجودة
    if not os.path.exists('requirements.txt'):
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write(REQUIREMENTS)
    
    if not os.path.exists('railway.json'):
        with open('railway.json', 'w', encoding='utf-8') as f:
            json.dump(RAILWAY_CONFIG, f, indent=2)
    
    if not os.path.exists('Dockerfile'):
        with open('Dockerfile', 'w', encoding='utf-8') as f:
            f.write(DOCKERFILE)
    
    main()
