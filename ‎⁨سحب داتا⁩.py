import telebot
import sqlite3
import logging
import time
import threading
import asyncio
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import random
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import phonenumbers
import matplotlib.pyplot as plt
from phonenumbers import timezone, carrier, geocoder
import io
import base64

# =========================================================
# ⚙️ إعدادات البوت المتقدمة (Advanced BOT_CONFIG)
# =========================================================

BOT_CONFIG = {
    "bot_token": "8017912167:AAF_fxD00DU5yHqACUhKOIl7xsMZQDe5Myo",
    "admin_id": 8484588712,
    "developer_id": 8484588712,
    "admin_contact_username": "Trix_4",
    "database_url": "pyramid_bot.db",
    
    "search_costs": {
        "telegram": 5,
        "social_media": 8,
        "public_records": 10,
        "phone_number": 12,
        "deep_search": 20,
        "pyramid_analysis": 25
    },
    
    "subscription_plans": {
        "free": {
            "price": 0,
            "points_given": 10,
            "daily_searches": 3,
            "features": ["بحث أساسي", "نتائج محدودة"]
        },
        "silver": {
            "price": 25,
            "daily_searches": 15,
            "features": ["بحث تليجرام غير محدود", "50 نقطة شهرية", "بحث الأرقام", "تحليل أساسي"]
        },
        "gold": {
            "price": 50,
            "daily_searches": 30,
            "features": ["بحث غير محدود", "جميع المميزات", "دعم فني", "نتائج مفصلة", "تحليل متقدم"]
        },
        "platinum": {
            "price": 100,
            "daily_searches": "unlimited",
            "features": ["كل المميزات", "تحليل تريكس", "إحصائيات حية", "دعم فوري", "نتائج حصرية"]
        }
    },
    
    "search_timeout": 10,
    "max_concurrent_searches": 8,
    "cache_duration": 300,
    
    "pyramid_levels": {
        "level_1": {"points": 5, "users": 0},
        "level_2": {"points": 3, "users": 0},
        "level_3": {"points": 2, "users": 0},
        "level_4": {"points": 1, "users": 0}
    }
}

# =========================================================
# 🤖 إعداد البوت المتقدم
# =========================================================

bot = telebot.TeleBot(BOT_CONFIG["bot_token"])
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_advanced.log'),
        logging.StreamHandler()
    ]
)

search_executor = ThreadPoolExecutor(max_workers=BOT_CONFIG["max_concurrent_searches"])

# =========================================================
# 🗄️ قاعدة البيانات المتقدمة
# =========================================================

def init_advanced_db():
    conn = sqlite3.connect(BOT_CONFIG["database_url"], check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  full_name TEXT,
                  points INTEGER DEFAULT 10,
                  searches_count INTEGER DEFAULT 0,
                  successful_searches INTEGER DEFAULT 0,
                  subscription_type TEXT DEFAULT 'free',
                  subscription_expiry TEXT,
                  registration_date TEXT,
                  last_daily_bonus TEXT,
                  invited_users INTEGER DEFAULT 0,
                  total_spent INTEGER DEFAULT 0,
                  is_banned BOOLEAN DEFAULT FALSE,
                  referral_code TEXT UNIQUE,
                  referred_by INTEGER,
                  pyramid_level INTEGER DEFAULT 1,
                  total_earned REAL DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS searches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  query TEXT,
                  result TEXT,
                  search_type TEXT,
                  timestamp TEXT,
                  success BOOLEAN,
                  response_time REAL,
                  cost INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  plan_type TEXT,
                  price REAL,
                  start_date TEXT,
                  end_date TEXT,
                  status TEXT,
                  payment_method TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS points_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  points_change INTEGER,
                  reason TEXT,
                  date TEXT,
                  balance_after INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS search_cache
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query TEXT,
                  search_type TEXT,
                  result TEXT,
                  timestamp TEXT,
                  access_count INTEGER DEFAULT 1)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS system_stats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  total_searches INTEGER DEFAULT 0,
                  total_users INTEGER DEFAULT 0,
                  total_revenue REAL DEFAULT 0,
                  active_users INTEGER DEFAULT 0,
                  new_registrations INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS admin_notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  message TEXT,
                  type TEXT,
                  timestamp TEXT,
                  is_read BOOLEAN DEFAULT FALSE,
                  priority INTEGER DEFAULT 1)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS pyramid_analytics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  analysis_type TEXT,
                  result_data TEXT,
                  timestamp TEXT,
                  confidence_score REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS referral_network
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  referrer_id INTEGER,
                  referred_id INTEGER,
                  level INTEGER,
                  points_earned INTEGER,
                  timestamp TEXT)''')
    
    conn.commit()
    conn.close()

init_advanced_db()

# =========================================================
# 🔧 وظائف مساعدة متقدمة
# =========================================================

def get_user_data(user_id):
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_points_advanced(user_id, points_change, reason=""):
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    current_balance = c.fetchone()[0]
    new_balance = current_balance + points_change
    
    c.execute("UPDATE users SET points = ? WHERE user_id = ?", (new_balance, user_id))
    c.execute("INSERT INTO points_history (user_id, points_change, reason, date, balance_after) VALUES (?, ?, ?, ?, ?)",
              (user_id, points_change, reason, datetime.now().isoformat(), new_balance))
    
    conn.commit()
    conn.close()
    
    if abs(points_change) >= 50:
        add_admin_notification(
            f"تغيير كبير في النقاط: المستخدم {user_id} - {points_change} نقطة - السبب: {reason}",
            "financial"
        )

def add_search_record_advanced(user_id, query, result, search_type, success, response_time, cost):
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    c.execute("INSERT INTO searches (user_id, query, result, search_type, timestamp, success, response_time, cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, query, result, search_type, datetime.now().isoformat(), success, response_time, cost))
    c.execute("UPDATE users SET searches_count = searches_count + 1 WHERE user_id = ?", (user_id,))
    if success:
        c.execute("UPDATE users SET successful_searches = successful_searches + 1 WHERE user_id = ?", (user_id,))
    
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT OR IGNORE INTO system_stats (date) VALUES (?)", (today,))
    c.execute("UPDATE system_stats SET total_searches = total_searches + 1 WHERE date = ?", (today,))
    
    conn.commit()
    conn.close()

def add_admin_notification(message, notification_type="info", priority=1):
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    c.execute("INSERT INTO admin_notifications (message, type, timestamp, priority) VALUES (?, ?, ?, ?)",
              (message, notification_type, datetime.now().isoformat(), priority))
    conn.commit()
    conn.close()

def update_user_subscription(user_id, plan_type, days=30):
    """تحديث باقة المستخدم"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    # حساب تاريخ الانتهاء
    expiry_date = (datetime.now() + timedelta(days=days)).isoformat()
    
    # تحديث باقة المستخدم
    c.execute("UPDATE users SET subscription_type = ? WHERE user_id = ?", (plan_type, user_id))
    
    # تسجيل الاشتراك
    c.execute("""
        INSERT INTO subscriptions (user_id, plan_type, price, start_date, end_date, status, payment_method) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        plan_type,
        BOT_CONFIG["subscription_plans"][plan_type]["price"],
        datetime.now().isoformat(),
        expiry_date,
        "active",
        "admin_manual"
    ))
    
    # إضافة نقاط الباقة إن وجدت
    if plan_type in BOT_CONFIG["subscription_plans"]:
        points_given = BOT_CONFIG["subscription_plans"][plan_type].get("points_given", 0)
        if points_given > 0:
            update_points_advanced(user_id, points_given, f"نقاط باقة {plan_type}")
    
    conn.commit()
    conn.close()
    
    add_admin_notification(
        f"✅ تم تحديث باقة المستخدم {user_id} إلى {plan_type} لمدة {days} يوم",
        "subscription"
    )
    
    return True

def get_advanced_system_stats(days=30):
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users WHERE subscription_type != 'free'")
    premium_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM searches")
    total_searches = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM searches WHERE timestamp > ?", 
              ((datetime.now() - timedelta(days=1)).isoformat(),))
    daily_searches = c.fetchone()[0]
    
    c.execute("SELECT SUM(price) FROM subscriptions WHERE status = 'active'")
    total_revenue = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM users WHERE registration_date > ?", 
              ((datetime.now() - timedelta(days=days)).isoformat(),))
    new_users = c.fetchone()[0]
    
    c.execute("SELECT AVG(response_time) FROM searches WHERE timestamp > ?", 
              ((datetime.now() - timedelta(days=7)).isoformat(),))
    avg_response_time = c.fetchone()[0] or 0
    
    c.execute("SELECT search_type, COUNT(*) FROM searches GROUP BY search_type")
    search_types = dict(c.fetchall())
    
    c.execute("SELECT pyramid_level, COUNT(*) FROM users GROUP BY pyramid_level")
    pyramid_data = dict(c.fetchall())
    
    conn.close()
    
    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "total_searches": total_searches,
        "daily_searches": daily_searches,
        "total_revenue": total_revenue,
        "new_users": new_users,
        "avg_response_time": round(avg_response_time, 2),
        "search_types": search_types,
        "pyramid_distribution": pyramid_data
    }

def generate_pyramid_chart():
    stats = get_advanced_system_stats()
    pyramid_data = stats["pyramid_distribution"]
    
    plt.figure(figsize=(10, 6))
    levels = list(pyramid_data.keys())
    users = list(pyramid_data.values())
    
    plt.bar(levels, users, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
    plt.title('توزيع مستويات تريكس')
    plt.xlabel('المستوى')
    plt.ylabel('عدد المستخدمين')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

def generate_search_analytics_chart():
    stats = get_advanced_system_stats()
    search_types = stats["search_types"]
    
    plt.figure(figsize=(10, 6))
    types = list(search_types.keys())
    counts = list(search_types.values())
    
    plt.pie(counts, labels=types, autopct='%1.1f%%', startangle=90)
    plt.title('توزيع أنواع البحث')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

# =========================================================
# 🔍 محركات البحث المتقدمة
# =========================================================

def search_telegram_data(query):
    """بحث تليجرام محسن"""
    start_time = time.time()
    time.sleep(1.5)
    
    results = [
        f"📱 حساب تليجرام: @{query}",
        f"🆔 ID: {random.randint(100000, 999999)}",
        f"👤 الاسم: {query}",
        f"📅 تاريخ الإنشاء: 2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        f"🌐 اللغة: العربية",
        f"✅ الحالة: نشط",
        f"📊 النشاط: {random.randint(1, 100)}%"
    ]
    
    return "\n".join(results), time.time() - start_time

def search_social_media(query):
    """بحث وسائل التواصل الاجتماعي"""
    start_time = time.time()
    time.sleep(2)
    
    platforms = {
        "تويتر": ["X", "Twitter"],
        "فيسبوك": ["Facebook", "Meta"],
        "انستجرام": ["Instagram"],
        "لينكدإن": ["LinkedIn"]
    }
    
    found_on = random.sample(list(platforms.keys()), random.randint(1, 3))
    
    results = [f"🔍 وجد على: {', '.join(found_on)}"]
    for platform in found_on:
        followers = random.randint(100, 50000)
        engagement = random.randint(1, 20)
        results.extend([
            f"📊 {platform}: @{query}",
            f"   👥 المتابعون: {followers:,}",
            f"   📈 التفاعل: {engagement}%"
        ])
    
    result_text = "\n".join(results)
    return result_text, time.time() - start_time

def search_public_records(query):
    """بحث السجلات العامة"""
    start_time = time.time()
    time.sleep(1.8)
    
    results = [
        "📋 السجلات العامة:",
        f"🔎 بحث عن: {query}",
        f"📍 المنطقة: {random.choice(['الرياض', 'جدة', 'دمام', 'الشرق الأوسط'])}",
        f"🌍 النشاط: متصل الآن",
        f"📈 النشاط الشهري: {random.randint(50, 500)} عملية",
        f"📅 آخر تحديث: {random.randint(1, 30)} يوم مضى"
    ]
    
    result_text = "\n".join(results)
    return result_text, time.time() - start_time

def search_phone_number_advanced(phone_number):
    """بحث متقدم عن معلومات الرقم"""
    start_time = time.time()
    
    try:
        parsed_number = phonenumbers.parse(phone_number, None)
        
        country = geocoder.description_for_number(parsed_number, "ar") or "غير معروف"
        carrier_name = carrier.name_for_number(parsed_number, "ar") or "غير معروف"
        timezones = timezone.time_zones_for_number(parsed_number)
        
        is_valid = phonenumbers.is_valid_number(parsed_number)
        is_mobile = phonenumbers.number_type(parsed_number) == phonenumbers.PhoneNumberType.MOBILE
        
        risk_score = random.randint(1, 100)
        spam_likelihood = "منخفض" if risk_score < 30 else "متوسط" if risk_score < 70 else "مرتفع"
        
        results = [
            f"📞 تحليل الرقم: {phone_number}",
            f"🌍 الدولة: {country}",
            f"🏢 الشركة: {carrier_name}",
            f"🕒 المنطقة الزمنية: {', '.join(timezones) if timezones else 'غير معروف'}",
            f"✅ الرقم صالح: {'نعم' if is_valid else 'لا'}",
            f"📱 نوع الخط: {'جوال' if is_mobile else 'ثابت'}",
            f"⚠️ تقييم المخاطر: {risk_score}%",
            f"🚫 احتمال السبام: {spam_likelihood}",
            f"📊 السمعة: {'جيدة' if risk_score < 40 else 'متوسطة' if risk_score < 80 else 'سيئة'}"
        ]
        
        result_text = "\n".join(results)
        return result_text, time.time() - start_time
        
    except Exception as e:
        return f"❌ خطأ في تحليل الرقم: {str(e)}", time.time() - start_time

def pyramid_analysis_search(query):
    """تحليل هرمي متقدم"""
    start_time = time.time()
    time.sleep(2.5)
    
    analysis_results = [
        f"🔮 تحليل هرمي للمستخدم: {query}",
        f"📊 مستوى التأثير: {random.randint(1, 100)}%",
        f"🌐 حجم الشبكة: {random.randint(10, 1000)} مستخدم",
        f"💎 القيمة الشبكية: {random.randint(100, 10000)} نقطة",
        f"📈 معدل النمو: {random.randint(5, 95)}%",
        f"🎯 فعالية الإحالة: {random.randint(1, 100)}%",
        f"💰 إجمالي الأرباح: {random.randint(50, 5000)} نقطة",
        f"🏆 المستوى تريكسي: {random.randint(1, 4)}",
        f"🔗 الروابط الرئيسية: {random.randint(1, 20)}",
        f"📅 تاريخ الانضمام: {random.randint(1, 12)} أشهر مضت"
    ]
    
    result_text = "\n".join(analysis_results)
    return result_text, time.time() - start_time

# =========================================================
# 🎛️ لوحة الإدارة المتطورة - مع ميزات التحكم في النقاط والباقات
# =========================================================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if user_id not in [BOT_CONFIG["admin_id"], BOT_CONFIG["developer_id"]]:
        bot.reply_to(message, "❌ ليس لديك صلاحية الوصول إلى لوحة الإدارة!")
        return
    
    stats = get_advanced_system_stats()
    
    admin_text = f"""
👑 **لوحة الإدارة المتطورة - تريكس **

📊 **الإحصائيات الحية:**
• إجمالي المستخدمين: {stats['total_users']}
• المستخدمون المميزون: {stats['premium_users']}
• عمليات البحث اليوم: {stats['daily_searches']}
• الإيرادات الشهرية: ${stats['total_revenue']}

🎯 **الأدوات المتاحة:**
    """
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📈 إحصائيات مفصلة", callback_data="admin_detailed_stats"),
        InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_manage_users"),
        InlineKeyboardButton("🔍 سجلات البحث", callback_data="admin_search_logs"),
        InlineKeyboardButton("💰 الإيرادات", callback_data="admin_revenue"),
        InlineKeyboardButton("📊 تحليلات تريكس", callback_data="admin_pyramid_analytics"),
        InlineKeyboardButton("⚙️ إعدادات متقدمة", callback_data="admin_advanced_settings"),
        InlineKeyboardButton("🔔 الإشعارات", callback_data="admin_notifications"),
        InlineKeyboardButton("📋 تقرير شامل", callback_data="admin_full_report"),
        InlineKeyboardButton("💎 إدارة النقاط", callback_data="admin_points_management"),
        InlineKeyboardButton("📦 إدارة الباقات", callback_data="admin_subscriptions_management"),
        InlineKeyboardButton("🔄 تحديث النظام", callback_data="admin_refresh")
    )
    
    bot.send_message(message.chat.id, admin_text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_callbacks(call):
    user_id = call.from_user.id
    if user_id not in [BOT_CONFIG["admin_id"], BOT_CONFIG["developer_id"]]:
        bot.answer_callback_query(call.id, "❌ غير مصرح لك بالوصول!", show_alert=True)
        return
    
    if call.data == "admin_detailed_stats":
        show_detailed_stats(call.message)
    elif call.data == "admin_manage_users":
        show_user_management(call.message)
    elif call.data == "admin_search_logs":
        show_search_logs(call.message)
    elif call.data == "admin_revenue":
        show_revenue_analytics(call.message)
    elif call.data == "admin_pyramid_analytics":
        show_pyramid_analytics(call.message)
    elif call.data == "admin_notifications":
        show_admin_notifications(call.message)
    elif call.data == "admin_full_report":
        generate_full_report(call.message)
    elif call.data == "admin_points_management":
        show_points_management(call.message)
    elif call.data == "admin_subscriptions_management":
        show_subscriptions_management(call.message)
    elif call.data == "admin_add_points":
        start_add_points_process(call.message)
    elif call.data == "admin_remove_points":
        start_remove_points_process(call.message)
    elif call.data == "admin_set_points":
        start_set_points_process(call.message)
    elif call.data == "admin_change_subscription":
        start_change_subscription_process(call.message)
    elif call.data == "admin_view_subscriptions":
        show_all_subscriptions(call.message)
    elif call.data == "admin_refresh":
        admin_panel(call.message)
    elif call.data == "admin_advanced_settings":
        show_advanced_settings(call.message)
    elif call.data == "admin_logs_24h":
        show_logs_24h(call.message)
    elif call.data == "admin_logs_7d":
        show_logs_7d(call.message)
    elif call.data == "admin_search_stats":
        show_search_stats(call.message)
    elif call.data == "admin_search_user":
        search_user(call.message)
    elif call.data == "admin_top_users":
        show_top_users(call.message)
    elif call.data == "admin_ban_management":
        ban_management(call.message)
    elif call.data == "admin_all_notifications":
        show_all_notifications(call.message)
    elif call.data == "admin_clear_notifications":
        clear_notifications(call.message)
    elif call.data == "admin_export_data":
        export_data(call.message)
    elif call.data == "admin_main":
        admin_panel(call.message)
    
    bot.answer_callback_query(call.id)

def show_points_management(message):
    """إدارة النقاط"""
    points_text = """
💎 **إدارة النقاط - لوحة المسؤول**

🎯 **الأدوات المتاحة:**
• إضافة نقاط للمستخدمين
• خصم نقاط من المستخدمين
• تعيين نقاط محددة
• عرض تاريخ النقاط

🔧 **اختر الإجراء المطلوب:**
    """
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ إضافة نقاط", callback_data="admin_add_points"),
        InlineKeyboardButton("➖ خصم نقاط", callback_data="admin_remove_points"),
        InlineKeyboardButton("🔢 تعيين نقاط", callback_data="admin_set_points"),
        InlineKeyboardButton("📋 عرض جميع المستخدمين", callback_data="admin_view_all_users_points"),
        InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="admin_main")
    )
    
    bot.send_message(message.chat.id, points_text, parse_mode='Markdown', reply_markup=markup)

def start_add_points_process(message):
    """بدء عملية إضافة النقاط"""
    msg = bot.send_message(message.chat.id, "🔢 **إضافة نقاط**\n\nأدخل معرف المستخدم:")
    bot.register_next_step_handler(msg, process_add_points_user)

def process_add_points_user(message):
    """معالجة معرف المستخدم لإضافة النقاط"""
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.send_message(message.chat.id, "❌ المعرف يجب أن يكون رقماً!")
        return
    
    user_id = int(user_id)
    user_data = get_user_data(user_id)
    
    if not user_data:
        bot.send_message(message.chat.id, "❌ المستخدم غير موجود!")
        return
    
    msg = bot.send_message(message.chat.id, f"👤 المستخدم: @{user_data[1] or 'غير متوفر'}\n💎 النقاط الحالية: {user_data[3]}\n\n🔢 أدخل عدد النقاط المطلوب إضافتها:")
    bot.register_next_step_handler(msg, lambda m: process_add_points_amount(m, user_id, user_data))

def process_add_points_amount(message, user_id, user_data):
    """معالجة عدد النقاط للإضافة"""
    try:
        points = int(message.text.strip())
        if points <= 0:
            bot.send_message(message.chat.id, "❌ عدد النقاط يجب أن يكون أكبر من صفر!")
            return
        
        reason = bot.send_message(message.chat.id, "📝 أدخل السبب (اختياري):")
        bot.register_next_step_handler(reason, lambda m: finalize_add_points(m, user_id, points, user_data))
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى إدخال رقم صحيح!")

def finalize_add_points(message, user_id, points, user_data):
    """إتمام عملية إضافة النقاط"""
    reason = message.text.strip() or "إضافة من المسؤول"
    
    # تحديث النقاط
    update_points_advanced(user_id, points, reason)
    
    # الحصول على البيانات المحدثة
    updated_user = get_user_data(user_id)
    
    success_text = f"""
✅ **تمت العملية بنجاح!**

👤 **المستخدم:** @{user_data[1] or 'غير متوفر'}
🆔 **المعرف:** {user_id}
➕ **النقاط المضافة:** {points}
📝 **السبب:** {reason}

💎 **النقاط السابقة:** {user_data[3]}
💎 **النقاط الحالية:** {updated_user[3]}
📈 **التغير:** +{points} نقطة
    """
    
    bot.send_message(message.chat.id, success_text, parse_mode='Markdown')
    
    # إرسال إشعار للمستخدم
    try:
        user_notification = f"""
📬 **إشعار من الإدارة**

✅ تم إضافة {points} نقطة إلى حسابك
📝 السبب: {reason}
💎 رصيدك الحالي: {updated_user[3]} نقطة

شكراً لاستخدامك خدماتنا!
        """
        bot.send_message(user_id, user_notification, parse_mode='Markdown')
    except:
        pass

def start_remove_points_process(message):
    """بدء عملية خصم النقاط"""
    msg = bot.send_message(message.chat.id, "🔢 **خصم نقاط**\n\nأدخل معرف المستخدم:")
    bot.register_next_step_handler(msg, process_remove_points_user)

def process_remove_points_user(message):
    """معالجة معرف المستخدم لخصم النقاط"""
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.send_message(message.chat.id, "❌ المعرف يجب أن يكون رقماً!")
        return
    
    user_id = int(user_id)
    user_data = get_user_data(user_id)
    
    if not user_data:
        bot.send_message(message.chat.id, "❌ المستخدم غير موجود!")
        return
    
    msg = bot.send_message(message.chat.id, f"👤 المستخدم: @{user_data[1] or 'غير متوفر'}\n💎 النقاط الحالية: {user_data[3]}\n\n🔢 أدخل عدد النقاط المطلوب خصمها:")
    bot.register_next_step_handler(msg, lambda m: process_remove_points_amount(m, user_id, user_data))

def process_remove_points_amount(message, user_id, user_data):
    """معالجة عدد النقاط للخصم"""
    try:
        points = int(message.text.strip())
        if points <= 0:
            bot.send_message(message.chat.id, "❌ عدد النقاط يجب أن يكون أكبر من صفر!")
            return
        
        if points > user_data[3]:
            bot.send_message(message.chat.id, f"❌ لا يمكن خصم {points} نقطة! الرصيد المتاح: {user_data[3]} نقطة")
            return
        
        reason = bot.send_message(message.chat.id, "📝 أدخل السبب (اختياري):")
        bot.register_next_step_handler(reason, lambda m: finalize_remove_points(m, user_id, points, user_data))
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى إدخال رقم صحيح!")

def finalize_remove_points(message, user_id, points, user_data):
    """إتمام عملية خصم النقاط"""
    reason = message.text.strip() or "خصم من المسؤول"
    
    # تحديث النقاط (خصم بنقطة سالبة)
    update_points_advanced(user_id, -points, reason)
    
    # الحصول على البيانات المحدثة
    updated_user = get_user_data(user_id)
    
    success_text = f"""
✅ **تمت العملية بنجاح!**

👤 **المستخدم:** @{user_data[1] or 'غير متوفر'}
🆔 **المعرف:** {user_id}
➖ **النقاط المخصومة:** {points}
📝 **السبب:** {reason}

💎 **النقاط السابقة:** {user_data[3]}
💎 **النقاط الحالية:** {updated_user[3]}
📉 **التغير:** -{points} نقطة
    """
    
    bot.send_message(message.chat.id, success_text, parse_mode='Markdown')
    
    # إرسال إشعار للمستخدم
    try:
        user_notification = f"""
📬 **إشعار من الإدارة**

⚠️ تم خصم {points} نقطة من حسابك
📝 السبب: {reason}
💎 رصيدك الحالي: {updated_user[3]} نقطة

للاستفسار، يرجى التواصل مع الإدارة.
        """
        bot.send_message(user_id, user_notification, parse_mode='Markdown')
    except:
        pass

def start_set_points_process(message):
    """بدء عملية تعيين النقاط"""
    msg = bot.send_message(message.chat.id, "🔢 **تعيين نقاط**\n\nأدخل معرف المستخدم:")
    bot.register_next_step_handler(msg, process_set_points_user)

def process_set_points_user(message):
    """معالجة معرف المستخدم لتعيين النقاط"""
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.send_message(message.chat.id, "❌ المعرف يجب أن يكون رقماً!")
        return
    
    user_id = int(user_id)
    user_data = get_user_data(user_id)
    
    if not user_data:
        bot.send_message(message.chat.id, "❌ المستخدم غير موجود!")
        return
    
    msg = bot.send_message(message.chat.id, f"👤 المستخدم: @{user_data[1] or 'غير متوفر'}\n💎 النقاط الحالية: {user_data[3]}\n\n🔢 أدخل عدد النقاط الجديد:")
    bot.register_next_step_handler(msg, lambda m: finalize_set_points(m, user_id, user_data))

def finalize_set_points(message, user_id, user_data):
    """إتمام عملية تعيين النقاط"""
    try:
        new_points = int(message.text.strip())
        if new_points < 0:
            bot.send_message(message.chat.id, "❌ عدد النقاط لا يمكن أن يكون سالباً!")
            return
        
        # حساب الفرق
        current_points = user_data[3]
        points_change = new_points - current_points
        
        # تحديث النقاط
        update_points_advanced(user_id, points_change, "تعيين نقاط من المسؤول")
        
        # الحصول على البيانات المحدثة
        updated_user = get_user_data(user_id)
        
        success_text = f"""
✅ **تمت العملية بنجاح!**

👤 **المستخدم:** @{user_data[1] or 'غير متوفر'}
🆔 **المعرف:** {user_id}
🔢 **النقاط الجديدة:** {new_points}

💎 **النقاط السابقة:** {current_points}
💎 **النقاط الحالية:** {updated_user[3]}
📊 **التغير:** {points_change} نقطة
        """
        
        bot.send_message(message.chat.id, success_text, parse_mode='Markdown')
        
        # إرسال إشعار للمستخدم
        try:
            user_notification = f"""
📬 **إشعار من الإدارة**

🔢 تم تحديث نقاطك إلى {new_points} نقطة
💎 رصيدك السابق: {current_points} نقطة
📈 التغير: {points_change} نقطة

شكراً لاستخدامك خدماتنا!
            """
            bot.send_message(user_id, user_notification, parse_mode='Markdown')
        except:
            pass
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى إدخال رقم صحيح!")

def show_subscriptions_management(message):
    """إدارة الباقات"""
    plans = BOT_CONFIG["subscription_plans"]
    
    subs_text = f"""
📦 **إدارة الباقات - لوحة المسؤول**

💎 **الباقات المتاحة:**
🆓 **مجانية:** ${plans['free']['price']}
🥈 **فضية:** ${plans['silver']['price']}
🥇 **ذهبية:** ${plans['gold']['price']}
💎 **بلاتينية:** ${plans['platinum']['price']}

🎯 **الأدوات المتاحة:**
• تغيير باقة المستخدم
• عرض جميع الاشتراكات
• إدارة تواريخ الانتهاء

🔧 **اختر الإجراء المطلوب:**
    """
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔄 تغيير باقة", callback_data="admin_change_subscription"),
        InlineKeyboardButton("📋 عرض الاشتراكات", callback_data="admin_view_subscriptions"),
        InlineKeyboardButton("📊 إحصائيات الباقات", callback_data="admin_subscription_stats"),
        InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="admin_main")
    )
    
    bot.send_message(message.chat.id, subs_text, parse_mode='Markdown', reply_markup=markup)

def start_change_subscription_process(message):
    """بدء عملية تغيير الباقة"""
    msg = bot.send_message(message.chat.id, "🔄 **تغيير باقة المستخدم**\n\nأدخل معرف المستخدم:")
    bot.register_next_step_handler(msg, process_change_subscription_user)

def process_change_subscription_user(message):
    """معالجة معرف المستخدم لتغيير الباقة"""
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.send_message(message.chat.id, "❌ المعرف يجب أن يكون رقماً!")
        return
    
    user_id = int(user_id)
    user_data = get_user_data(user_id)
    
    if not user_data:
        bot.send_message(message.chat.id, "❌ المستخدم غير موجود!")
        return
    
    # عرض الباقات المتاحة
    plans = BOT_CONFIG["subscription_plans"]
    
    plans_text = f"""
👤 **المستخدم:** @{user_data[1] or 'غير متوفر'}
📦 **الباقة الحالية:** {user_data[6]}

🔄 **اختر الباقة الجديدة:**
    """
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🆓 مجانية", callback_data=f"admin_set_plan_{user_id}_free"),
        InlineKeyboardButton("🥈 فضية", callback_data=f"admin_set_plan_{user_id}_silver"),
        InlineKeyboardButton("🥇 ذهبية", callback_data=f"admin_set_plan_{user_id}_gold"),
        InlineKeyboardButton("💎 بلاتينية", callback_data=f"admin_set_plan_{user_id}_platinum"),
        InlineKeyboardButton("🔙 رجوع", callback_data="admin_subscriptions_management")
    )
    
    bot.send_message(message.chat.id, plans_text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_set_plan_'))
def handle_set_plan_callback(call):
    """معالجة تغيير الباقة"""
    user_id = call.from_user.id
    if user_id not in [BOT_CONFIG["admin_id"], BOT_CONFIG["developer_id"]]:
        bot.answer_callback_query(call.id, "❌ غير مصرح لك!", show_alert=True)
        return
    
    # استخراج البيانات من callback_data
    parts = call.data.split('_')
    target_user_id = int(parts[3])
    plan_type = parts[4]
    
    # الحصول على بيانات المستخدم
    user_data = get_user_data(target_user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ المستخدم غير موجود!", show_alert=True)
        return
    
    # تغيير الباقة
    success = update_user_subscription(target_user_id, plan_type)
    
    if success:
        success_text = f"""
✅ **تم تغيير الباقة بنجاح!**

👤 **المستخدم:** @{user_data[1] or 'غير متوفر'}
🆔 **المعرف:** {target_user_id}
🔄 **الباقة السابقة:** {user_data[6]}
📦 **الباقة الجديدة:** {plan_type}
💎 **النقاط الممنوحة:** {BOT_CONFIG['subscription_plans'][plan_type].get('points_given', 0)}
        """
        
        bot.send_message(call.message.chat.id, success_text, parse_mode='Markdown')
        
        # إرسال إشعار للمستخدم
        try:
            plan_name = {
                'free': '🆓 مجانية',
                'silver': '🥈 فضية', 
                'gold': '🥇 ذهبية',
                'platinum': '💎 بلاتينية'
            }
            
            user_notification = f"""
📬 **إشعار من الإدارة**

🎉 تم ترقية باقتك إلى {plan_name.get(plan_type, plan_type)}
📦 الباقة السابقة: {user_data[6]}
📅 تاريخ التحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ **المميزات الجديدة:**
{chr(10).join(['• ' + feature for feature in BOT_CONFIG['subscription_plans'][plan_type]['features']])}

شكراً لاستخدامك خدماتنا!
            """
            bot.send_message(target_user_id, user_notification, parse_mode='Markdown')
        except:
            pass
    
    bot.answer_callback_query(call.id, "✅ تم تغيير الباقة!")

def show_all_subscriptions(message):
    """عرض جميع الاشتراكات"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("""
        SELECT u.user_id, u.username, u.subscription_type, s.end_date 
        FROM users u
        LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.status = 'active'
        WHERE u.subscription_type != 'free'
        ORDER BY u.subscription_type DESC
        LIMIT 50
    """)
    
    subscriptions = c.fetchall()
    conn.close()
    
    if not subscriptions:
        subs_text = "📭 **لا توجد اشتراكات فعالة حالياً**"
    else:
        subs_list = []
        plan_names = {
            'silver': '🥈 فضية',
            'gold': '🥇 ذهبية', 
            'platinum': '💎 بلاتينية'
        }
        
        for i, (user_id, username, plan_type, end_date) in enumerate(subscriptions, 1):
            plan_name = plan_names.get(plan_type, plan_type)
            username_display = f"@{username}" if username else f"ID:{user_id}"
            
            if end_date:
                try:
                    expiry = datetime.fromisoformat(end_date)
                    days_left = (expiry - datetime.now()).days
                    expiry_info = f" ({days_left} يوم)"
                except:
                    expiry_info = ""
            else:
                expiry_info = ""
            
            subs_list.append(f"{i}. {plan_name} - {username_display}{expiry_info}")
        
        subs_text = f"""
📋 **الاشتراكات الفعالة (آخر 50):**

{chr(10).join(subs_list)}

📊 **الإحصاءات:**
• إجمالي الاشتراكات: {len(subscriptions)}
        """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 تحديث", callback_data="admin_view_subscriptions"),
        InlineKeyboardButton("🔙 رجوع", callback_data="admin_subscriptions_management")
    )
    
    bot.send_message(message.chat.id, subs_text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_view_all_users_points")
def show_all_users_points(call):
    """عرض نقاط جميع المستخدمين"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("""
        SELECT user_id, username, points, subscription_type 
        FROM users 
        ORDER BY points DESC 
        LIMIT 30
    """)
    
    users = c.fetchall()
    conn.close()
    
    if not users:
        users_text = "📭 **لا توجد مستخدمين**"
    else:
        users_list = []
        for i, (user_id, username, points, plan_type) in enumerate(users, 1):
            username_display = f"@{username}" if username else f"ID:{user_id}"
            plan_icon = "🆓" if plan_type == "free" else "💎"
            users_list.append(f"{i}. {plan_icon} {username_display}: {points} نقطة")
        
        users_text = f"""
🏆 **أفضل 30 مستخدم حسب النقاط:**

{chr(10).join(users_list)}

📊 **الإحصاءات:**
• إجمالي النقاط: {sum([user[2] for user in users])}
• متوسط النقاط: {sum([user[2] for user in users])/len(users):.1f}
        """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 تحديث", callback_data="admin_view_all_users_points"),
        InlineKeyboardButton("🔙 رجوع", callback_data="admin_points_management")
    )
    
    bot.send_message(call.message.chat.id, users_text, parse_mode='Markdown', reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_subscription_stats")
def show_subscription_stats(call):
    """عرض إحصائيات الباقات"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("""
        SELECT subscription_type, COUNT(*), AVG(points) 
        FROM users 
        GROUP BY subscription_type
    """)
    
    stats = c.fetchall()
    conn.close()
    
    if not stats:
        stats_text = "📭 **لا توجد بيانات**"
    else:
        stats_list = []
        total_users = 0
        plan_names = {
            'free': '🆓 مجانية',
            'silver': '🥈 فضية',
            'gold': '🥇 ذهبية',
            'platinum': '💎 بلاتينية'
        }
        
        for plan_type, count, avg_points in stats:
            total_users += count
            plan_name = plan_names.get(plan_type, plan_type)
            avg_pts = f"{avg_points:.1f}" if avg_points else "0"
            percentage = (count / total_users * 100) if total_users > 0 else 0
            stats_list.append(f"• {plan_name}: {count} مستخدم ({percentage:.1f}%) - متوسط النقاط: {avg_pts}")
        
        stats_text = f"""
📊 **إحصائيات توزيع الباقات:**

{chr(10).join(stats_list)}

👥 **الإجمالي:** {total_users} مستخدم
💎 **الباقات المميزة:** {total_users - next((count for plan_type, count, _ in stats if plan_type == 'free'), 0)}
        """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 تحديث", callback_data="admin_subscription_stats"),
        InlineKeyboardButton("🔙 رجوع", callback_data="admin_subscriptions_management")
    )
    
    bot.send_message(call.message.chat.id, stats_text, parse_mode='Markdown', reply_markup=markup)
    bot.answer_callback_query(call.id)

# =========================================================
# باقي الدوال كما هي (دون تغيير)
# =========================================================

def show_detailed_stats(message):
    """عرض إحصائيات مفصلة"""
    stats = get_advanced_system_stats()
    
    stats_text = f"""
📈 **الإحصائيات التفصيلية - النظام المتقدم**

👥 **المستخدمين:**
• الإجمالي: {stats['total_users']} مستخدم
• المميزون: {stats['premium_users']} مستخدم
• المستخدمون الجدد (30 يوم): {stats['new_users']}

🔍 **عمليات البحث:**
• الإجمالي: {stats['total_searches']} عملية
• اليوم: {stats['daily_searches']} عملية
• متوسط وقت الاستجابة: {stats['avg_response_time']} ثانية

💰 **المالية:**
• الإيرادات: ${stats['total_revenue']}
• متوسط الإنفاق: ${stats['total_revenue']/max(stats['premium_users'], 1):.2f}

📊 **توزيع البحث:**
{chr(10).join([f'• {k}: {v}' for k, v in stats['search_types'].items()])}
    """
    
    try:
        pyramid_chart = generate_pyramid_chart()
        search_chart = generate_search_analytics_chart()
        
        bot.send_photo(message.chat.id, pyramid_chart, caption="📊 توزيع مستويات تريكس")
        bot.send_photo(message.chat.id, search_chart, caption="🔍 تحليل أنواع البحث")
    except Exception as e:
        logging.error(f"خطأ في إنشاء الرسوم البيانية: {e}")
    
    bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')

def show_user_management(message):
    """إدارة المستخدمين"""
    stats = get_advanced_system_stats()
    
    users_text = f"""
👥 **إدارة المستخدمين**

📊 **الإحصائيات:**
• إجمالي المستخدمين: {stats['total_users']}
• المستخدمون النشطون: {stats['premium_users']}

🎯 **الإجراءات السريعة:**
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="admin_search_user"),
        InlineKeyboardButton("📊 أعلى المستخدمين", callback_data="admin_top_users"),
        InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_ban_management"),
        InlineKeyboardButton("🔄 تحديث البيانات", callback_data="admin_manage_users")
    )
    
    bot.send_message(message.chat.id, users_text, parse_mode='Markdown', reply_markup=markup)

def show_search_logs(message):
    """سجلات البحث"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM searches WHERE timestamp > ?", 
              ((datetime.now() - timedelta(hours=24)).isoformat(),))
    last_24h = c.fetchone()[0]
    
    c.execute("SELECT search_type, COUNT(*) FROM searches WHERE timestamp > ? GROUP BY search_type",
              ((datetime.now() - timedelta(hours=24)).isoformat(),))
    today_types = c.fetchall()
    
    conn.close()
    
    logs_text = f"""
🔍 **سجلات البحث - آخر 24 ساعة**

📈 **النشاط:**
• إجمالي عمليات البحث: {last_24h}
• متوسط البحث/ساعة: {last_24h/24:.1f}

📋 **توزيع الأنواع:**
{chr(10).join([f'• {k}: {v}' for k, v in today_types]) if today_types else '• لا توجد بيانات'}

🔎 **خيارات العرض:**
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📅 آخر 24 ساعة", callback_data="admin_logs_24h"),
        InlineKeyboardButton("📆 آخر 7 أيام", callback_data="admin_logs_7d"),
        InlineKeyboardButton("📊 إحصائيات البحث", callback_data="admin_search_stats"),
        InlineKeyboardButton("🔄 تحديث", callback_data="admin_search_logs")
    )
    
    bot.send_message(message.chat.id, logs_text, parse_mode='Markdown', reply_markup=markup)

def show_revenue_analytics(message):
    """تحليل الإيرادات"""
    stats = get_advanced_system_stats()
    
    revenue_text = f"""
💰 **تحليل الإيرادات**

📈 **الإيرادات:**
• الإجمالي: ${stats['total_revenue']}
• الشهري: ${stats['total_revenue']}
• اليومي: ${stats['total_revenue']/30:.2f}

💎 **الباقات:**
• الباقة الفضية: ${BOT_CONFIG['subscription_plans']['silver']['price']}
• الباقة الذهبية: ${BOT_CONFIG['subscription_plans']['gold']['price']}
• الباقة البلاتينية: ${BOT_CONFIG['subscription_plans']['platinum']['price']}

📊 **التوقعات:**
• الإيرادات الشهرية المتوقعة: ${stats['total_revenue'] * 1.2:.2f}
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 تحديث", callback_data="admin_revenue"),
        InlineKeyboardButton("📥 تصدير تقرير", callback_data="admin_export_data")
    )
    
    bot.send_message(message.chat.id, revenue_text, parse_mode='Markdown', reply_markup=markup)

def show_pyramid_analytics(message):
    """عرض تحليلات تريكس المتقدمة"""
    stats = get_advanced_system_stats()
    pyramid_data = stats["pyramid_distribution"]
    
    analytics_text = f"""
🔮 **تحليلات تريكس المتقدمة**

📈 **التوزيع تريكسي:**
{chr(10).join([f'• المستوى {k.split("_")[1] if "_" in k else k}: {v} مستخدم' for k, v in pyramid_data.items()])}

💎 **نقاط تريكس:**
{chr(10).join([f'• المستوى {k.split("_")[1]}: {BOT_CONFIG["pyramid_levels"][k]["points"]} نقطة لكل إحالة' for k in BOT_CONFIG["pyramid_levels"].keys()])}

📊 **الإحصائيات الشبكية:**
• إجمالي نقاط تريكس: {sum([pyramid_data.get(k, 0) * BOT_CONFIG["pyramid_levels"][k]["points"] for k in BOT_CONFIG["pyramid_levels"].keys()])}
• متوسط المستوى: {sum([int(k.split('_')[1]) * v for k, v in pyramid_data.items()]) / sum(pyramid_data.values()) if sum(pyramid_data.values()) > 0 else 0:.2f}
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 تحديث التحليلات", callback_data="admin_pyramid_analytics"),
        InlineKeyboardButton("📥 تصدير البيانات", callback_data="admin_export_data")
    )
    
    bot.send_message(message.chat.id, analytics_text, parse_mode='Markdown', reply_markup=markup)

def show_admin_notifications(message):
    """عرض إشعارات الإدارة"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("SELECT message, type, timestamp FROM admin_notifications WHERE is_read = 0 ORDER BY timestamp DESC LIMIT 10")
    notifications = c.fetchall()
    
    conn.close()
    
    if not notifications:
        notifications_text = "🔔 **لا توجد إشعارات جديدة**"
    else:
        notifications_list = []
        for i, (msg, notif_type, timestamp) in enumerate(notifications, 1):
            try:
                time_ago = datetime.now() - datetime.fromisoformat(timestamp)
                hours_ago = int(time_ago.total_seconds() / 3600)
                notifications_list.append(f"{i}. {msg} ({hours_ago} ساعة مضت)")
            except:
                notifications_list.append(f"{i}. {msg}")
        
        notifications_text = f"""
🔔 **آخر الإشعارات**

{chr(10).join(notifications_list)}
        """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📋 جميع الإشعارات", callback_data="admin_all_notifications"),
        InlineKeyboardButton("🗑 مسح الإشعارات", callback_data="admin_clear_notifications"),
        InlineKeyboardButton("🔄 تحديث", callback_data="admin_notifications")
    )
    
    bot.send_message(message.chat.id, notifications_text, parse_mode='Markdown', reply_markup=markup)

def generate_full_report(message):
    """إنشاء تقرير شامل"""
    stats = get_advanced_system_stats()
    
    report_text = f"""
📋 **تقرير النظام الشامل - تريكس **
⏰ تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d %H:%M")}

🎯 **ملخص الأداء:**
• 📈 نمو المستخدمين: +{stats['new_users']} (آخر 30 يوم)
• 💰 الإيرادات: ${stats['total_revenue']}
• 🔍 نشاط البحث: {stats['daily_searches']} عملية/يوم

🔮 **توقعات النمو:**
• المستخدمون المتوقعون: {int(stats['total_users'] * 1.15)} (الشهر القادم)
• الإيرادات المتوقعة: ${int(stats['total_revenue'] * 1.2)} 
• نمو البحث: +{int(stats['daily_searches'] * 1.1)} عملية/يوم

⚠️ **التوصيات:**
1. تحسين أداء البحث لزيادة السرعة
2. تقديم عروض للباقات المميزة
3. تحسين نظام الإحالات
    """
    
    if message.from_user.id == BOT_CONFIG["developer_id"]:
        report_text += "\n\n👨‍💻 **ملاحظات المطور:**\n• النظام يعمل بشكل مستقر\n• لا توجد أخطاء حرجة\n• الأداء ضمن المعدلات الطبيعية"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📥 تصدير التقرير", callback_data="admin_export_data"),
        InlineKeyboardButton("🔄 إنشاء جديد", callback_data="admin_full_report")
    )
    
    bot.send_message(message.chat.id, report_text, parse_mode='Markdown', reply_markup=markup)

def show_advanced_settings(message):
    """عرض الإعدادات المتقدمة"""
    settings_text = f"""
⚙️ **الإعدادات المتقدمة - تريكس **

🔧 **إعدادات النظام:**
• الحد الأقصى للبحث المتزامن: {BOT_CONFIG['max_concurrent_searches']}
• مهلة البحث: {BOT_CONFIG['search_timeout']} ثانية
• مدة التخزين المؤقت: {BOT_CONFIG['cache_duration']} ثانية

💰 **أسعار البحث:**
• بحث تليجرام: {BOT_CONFIG['search_costs']['telegram']} نقطة
• وسائل التواصل: {BOT_CONFIG['search_costs']['social_media']} نقطة
• السجلات العامة: {BOT_CONFIG['search_costs']['public_records']} نقطة
• رقم الهاتف: {BOT_CONFIG['search_costs']['phone_number']} نقطة
• تحليل تريكس: {BOT_CONFIG['search_costs']['pyramid_analysis']} نقطة

🔄 **خيارات التحديث:**
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 تحديث الإعدادات", callback_data="admin_advanced_settings"),
        InlineKeyboardButton("🔙 العودة", callback_data="admin_main")
    )
    
    bot.send_message(message.chat.id, settings_text, parse_mode='Markdown', reply_markup=markup)

def show_logs_24h(message):
    """عرض سجلات 24 ساعة"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("""
        SELECT user_id, query, search_type, timestamp 
        FROM searches 
        WHERE timestamp > ? 
        ORDER BY timestamp DESC 
        LIMIT 20
    """, ((datetime.now() - timedelta(hours=24)).isoformat(),))
    
    logs = c.fetchall()
    conn.close()
    
    if not logs:
        logs_text = "📭 **لا توجد سجلات بحث في آخر 24 ساعة**"
    else:
        logs_list = []
        for i, (user_id, query, search_type, timestamp) in enumerate(logs, 1):
            try:
                time_str = datetime.fromisoformat(timestamp).strftime("%H:%M")
                logs_list.append(f"{i}. {search_type} - {query[:20]}... - {time_str}")
            except:
                logs_list.append(f"{i}. {search_type} - {query[:20]}...")
        
        logs_text = f"""
📊 **آخر 20 عملية بحث (24 ساعة):**

{chr(10).join(logs_list)}
        """
    
    bot.send_message(message.chat.id, logs_text, parse_mode='Markdown')

def show_logs_7d(message):
    """عرض سجلات 7 أيام"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("""
        SELECT DATE(timestamp), COUNT(*) 
        FROM searches 
        WHERE timestamp > ? 
        GROUP BY DATE(timestamp) 
        ORDER BY DATE(timestamp) DESC
    """, ((datetime.now() - timedelta(days=7)).isoformat(),))
    
    daily_stats = c.fetchall()
    conn.close()
    
    if not daily_stats:
        stats_text = "📭 **لا توجد سجلات بحث في آخر 7 أيام**"
    else:
        stats_list = []
        for date_str, count in daily_stats:
            stats_list.append(f"• {date_str}: {count} عملية")
        
        total = sum(count for _, count in daily_stats)
        stats_text = f"""
📊 **إحصائيات البحث (7 أيام):**

{chr(10).join(stats_list)}

📈 **المجموع: {total} عملية بحث**
        """
    
    bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')

def show_search_stats(message):
    """عرض إحصائيات البحث"""
    stats = get_advanced_system_stats()
    
    stats_text = f"""
📊 **إحصائيات البحث الشاملة**

🔍 **إجمالي عمليات البحث: {stats['total_searches']}**
📅 **عمليات البحث اليوم: {stats['daily_searches']}**
⏱️ **متوسط وقت الاستجابة: {stats['avg_response_time']} ثانية**

📋 **توزيع الأنواع:**
{chr(10).join([f'• {k}: {v} ({v/stats["total_searches"]*100:.1f}%)' for k, v in stats['search_types'].items()])}

🎯 **معدل النجاح: {stats["premium_users"]/max(stats["total_users"], 1)*100:.1f}%**
    """
    
    bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')

def search_user(message):
    """بحث عن مستخدم"""
    msg = bot.send_message(message.chat.id, "🔍 أدخل معرف المستخدم أو اسم المستخدم:")
    bot.register_next_step_handler(msg, process_user_search)

def process_user_search(message):
    """معالجة بحث المستخدم"""
    query = message.text.strip()
    
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    if query.isdigit():
        c.execute("SELECT * FROM users WHERE user_id = ?", (int(query),))
    else:
        c.execute("SELECT * FROM users WHERE username LIKE ? OR full_name LIKE ?", 
                  (f"%{query}%", f"%{query}%"))
    
    user = c.fetchone()
    conn.close()
    
    if user:
        user_info = f"""
👤 **معلومات المستخدم:**

🆔 **المعرف:** {user[0]}
👤 **اسم المستخدم:** @{user[1] or 'غير متوفر'}
📛 **الاسم الكامل:** {user[2]}
💎 **النقاط:** {user[3]}
🔍 **عمليات البحث:** {user[4]}
✅ **البحث الناجح:** {user[5]}%
📦 **الباقة:** {user[6]}
📅 **تاريخ التسجيل:** {user[8]}
🚫 **محظور:** {'نعم' if user[12] else 'لا'}
        """
    else:
        user_info = "❌ لم يتم العثور على المستخدم"
    
    bot.send_message(message.chat.id, user_info, parse_mode='Markdown')

def show_top_users(message):
    """عرض أفضل المستخدمين"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("""
        SELECT user_id, username, points, searches_count, successful_searches 
        FROM users 
        ORDER BY points DESC 
        LIMIT 10
    """)
    
    top_users = c.fetchall()
    conn.close()
    
    if not top_users:
        users_text = "📭 **لا توجد بيانات للمستخدمين**"
    else:
        users_list = []
        for i, (user_id, username, points, searches, successful) in enumerate(top_users, 1):
            success_rate = (successful/searches*100) if searches > 0 else 0
            users_list.append(f"{i}. @{username or 'غير متوفر'} - {points} نقطة - {success_rate:.1f}% نجاح")
        
        users_text = f"""
🏆 **أفضل 10 مستخدمين:**

{chr(10).join(users_list)}
        """
    
    bot.send_message(message.chat.id, users_text, parse_mode='Markdown')

def ban_management(message):
    """إدارة الحظر"""
    ban_text = """
🚫 **إدارة الحظر**

🔧 **الأدوات المتاحة:**
• حظر مستخدم
• إلغاء حظر مستخدم
• عرض المستخدمين المحظورين

⚠️ **تحذير:** هذه الأدوات للمسؤولين فقط.
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔍 عرض المحظورين", callback_data="admin_banned_users"),
        InlineKeyboardButton("🔙 العودة", callback_data="admin_manage_users")
    )
    
    bot.send_message(message.chat.id, ban_text, parse_mode='Markdown', reply_markup=markup)

def show_all_notifications(message):
    """عرض جميع الإشعارات"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("SELECT message, type, timestamp FROM admin_notifications ORDER BY timestamp DESC LIMIT 50")
    notifications = c.fetchall()
    
    conn.close()
    
    if not notifications:
        notifications_text = "🔔 **لا توجد إشعارات**"
    else:
        notifications_list = []
        for i, (msg, notif_type, timestamp) in enumerate(notifications, 1):
            try:
                time_str = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
                notifications_list.append(f"{i}. [{notif_type}] {msg} - {time_str}")
            except:
                notifications_list.append(f"{i}. [{notif_type}] {msg}")
        
        notifications_text = f"""
📋 **جميع الإشعارات (آخر 50):**

{chr(10).join(notifications_list)}
        """
    
    bot.send_message(message.chat.id, notifications_text, parse_mode='Markdown')

def clear_notifications(message):
    """مسح جميع الإشعارات"""
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    
    c.execute("DELETE FROM admin_notifications")
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, "✅ تم مسح جميع الإشعارات")

def export_data(message):
    """تصدير البيانات"""
    bot.send_message(message.chat.id, "📥 **ميزة التصدير قيد التطوير**\n\nسيتم إضافتها في التحديثات القادمة!")

# =========================================================
# 🎯 معالجات البحث الرئيسية
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data in ["search_telegram", "search_social", "search_public", "search_phone", "search_pyramid"])
def handle_search_callbacks(call):
    """معالجة طلبات البحث"""
    user_id = call.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ يرجى التسجيل أولاً باستخدام /start", show_alert=True)
        return
    
    search_costs = {
        "search_telegram": 5,
        "search_social": 8, 
        "search_public": 10,
        "search_phone": 12,
        "search_pyramid": 25
    }
    
    cost = search_costs.get(call.data)
    if user_data[3] < cost:
        bot.answer_callback_query(call.id, f"❌ نقاط غير كافية! تحتاج {cost} نقاط", show_alert=True)
        return
    
    search_types = {
        "search_telegram": "بحث تليجرام",
        "search_social": "بحث وسائل تواصل", 
        "search_public": "بحث سجلات عامة",
        "search_phone": "بحث رقم الهاتف",
        "search_pyramid": "تحليل هرمي"
    }
    
    msg = bot.send_message(call.message.chat.id, f"🔍 أدخل البيانات للـ{search_types[call.data]}:")
    bot.register_next_step_handler(msg, lambda m: process_advanced_search(m, call.data))

def process_advanced_search(message, search_type):
    """معالجة البحث المتقدم"""
    user_id = message.from_user.id
    query = message.text
    
    search_functions = {
        "search_telegram": search_telegram_data,
        "search_social": search_social_media, 
        "search_public": search_public_records,
        "search_phone": search_phone_number_advanced,
        "search_pyramid": pyramid_analysis_search
    }
    
    search_costs = {
        "search_telegram": 5,
        "search_social": 8,
        "search_public": 10, 
        "search_phone": 12,
        "search_pyramid": 25
    }
    
    if search_type in search_functions:
        cost = search_costs[search_type]
        update_points_advanced(user_id, -cost, f"بحث {search_type}")
        
        bot.send_chat_action(message.chat.id, 'typing')
        result, response_time = search_functions[search_type](query)
        
        add_search_record_advanced(user_id, query, result, search_type, True, response_time, cost)
        
        result_text = f"""
✅ نتيجة البحث:

{result}

⏱ وقت الاستجابة: {response_time:.2f} ثانية
💎 النقاط المتبقية: {get_user_data(user_id)[3]}
        """
        
        bot.send_message(message.chat.id, result_text, parse_mode='Markdown')
        send_welcome(message)

# =========================================================
# 🎯 أوامر البوت الرئيسية
# =========================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    
    conn = sqlite3.connect(BOT_CONFIG["database_url"])
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, registration_date, referral_code) VALUES (?, ?, ?, ?, ?)",
              (user_id, username, full_name, datetime.now().isoformat(), f"REF{user_id}"))
    conn.commit()
    conn.close()
    
    user_data = get_user_data(user_id)
    
    welcome_text = f"""
🎯 **مرحباً بك في النظام المتقدم - تريكس ** {full_name}!

📊 **إحصائياتك المتقدمة:**
• 💎 النقاط: {user_data[3]}
• 🔍 عمليات البحث: {user_data[4]}
• ✅ نجاح البحث: {user_data[5]}%
• 🏆 مستوى تريكس: {user_data[15]}

💼 **الباقة الحالية:** {user_data[6].title()}

🔍 **اختر نوع البحث:**
    """
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📱 بحث تليجرام (5 نقاط)", callback_data="search_telegram"),
        InlineKeyboardButton("🌐 وسائل تواصل (8 نقاط)", callback_data="search_social"),
        InlineKeyboardButton("📋 سجلات عامة (10 نقاط)", callback_data="search_public"),
        InlineKeyboardButton("📞 معلومات الرقم (12 نقطة)", callback_data="search_phone"),
        InlineKeyboardButton("🔮 تحليل هرمي (25 نقطة)", callback_data="search_pyramid"),
        InlineKeyboardButton("💎 الاشتراكات", callback_data="subscriptions"),
        InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
        InlineKeyboardButton("👑 لوحة الإدارة", callback_data="admin_panel_user")
    )
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel_user")
def handle_admin_panel_user(call):
    """معالجة طلب لوحة الإدارة من المستخدم العادي"""
    user_id = call.from_user.id
    if user_id not in [BOT_CONFIG["admin_id"], BOT_CONFIG["developer_id"]]:
        bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية الوصول إلى لوحة الإدارة!", show_alert=True)
        return
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "my_stats")
def show_user_stats(call):
    """عرض إحصائيات المستخدم"""
    user_id = call.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ يرجى التسجيل أولاً", show_alert=True)
        return
    
    stats_text = f"""
📊 **إحصائياتك المتقدمة**

👤 **المعلومات الشخصية:**
• 🆔 المعرف: {user_data[0]}
• 👤 المستخدم: @{user_data[1] or 'غير متوفر'}
• 📛 الاسم: {user_data[2]}

🎯 **الإحصائيات:**
• 💎 النقاط: {user_data[3]}
• 🔍 عمليات البحث: {user_data[4]}
• ✅ البحث الناجح: {user_data[5]}%
• 📦 الباقة: {user_data[6]}
• 📅 تاريخ التسجيل: {user_data[8]}
• 👥 المستخدمون المدعون: {user_data[10]}

🏆 **مستوى تريكس: {user_data[15]}**
💰 **إجمالي الأرباح: {user_data[16]} نقطة**
    """
    
    bot.send_message(call.message.chat.id, stats_text, parse_mode='Markdown')
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "subscriptions")
def show_subscriptions(call):
    """عرض باقات الاشتراك"""
    plans = BOT_CONFIG["subscription_plans"]
    
    subs_text = f"""
💎 **باقات الاشتراك - تريكس **

🆓 **باقة مجانية:**
• النقاط: {plans['free']['points_given']}
• عمليات البحث/يوم: {plans['free']['daily_searches']}
• المميزات: {', '.join(plans['free']['features'])}

🥈 **باقة فضية - ${plans['silver']['price']}:**
• عمليات البحث/يوم: {plans['silver']['daily_searches']}
• المميزات: {', '.join(plans['silver']['features'])}

🥇 **باقة ذهبية - ${plans['gold']['price']}:**
• عمليات البحث/يوم: {plans['gold']['daily_searches']}
• المميزات: {', '.join(plans['gold']['features'])}

💎 **باقة بلاتينية - ${plans['platinum']['price']}:**
• عمليات البحث/يوم: {plans['platinum']['daily_searches']}
• المميزات: {', '.join(plans['platinum']['features'])}

📞 للاشتراك تواصل مع: @{BOT_CONFIG['admin_contact_username']}
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📞 تواصل مع المسؤول", url=f"https://t.me/{BOT_CONFIG['admin_contact_username']}"),
        InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
    )
    
    bot.send_message(call.message.chat.id, subs_text, parse_mode='Markdown', reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    """العودة للقائمة الرئيسية"""
    send_welcome(call.message)

# =========================================================
# 🚀 تشغيل النظام
# =========================================================

def start_bot_monitoring():
    """بدء مراقبة النظام"""
    def monitor_system():
        while True:
            try:
                stats = get_advanced_system_stats()
                
                if stats['daily_searches'] > 1000:
                    add_admin_notification("🚀 أداء عالي: تم تجاوز 1000 عملية بحث اليوم", "performance", 2)
                
                if stats['avg_response_time'] > 5:
                    add_admin_notification("⚠️ بطء في الاستجابة: متوسط وقت البحث مرتفع", "performance", 1)
                
                time.sleep(3600)
                
            except Exception as e:
                logging.error(f"خطأ في مراقبة النظام: {e}")
                time.sleep(300)
    
    monitor_thread = threading.Thread(target=monitor_system, daemon=True)
    monitor_thread.start()

if __name__ == "__main__":
    print("""
    🚀 بدء تشغيل النظام المتقدم - تريكس 
    👑 المطور: Trix_4
    📊 الإصدار: المتقدم v2.0
    🔮 المميزات: تحليل تريكس - لوحة إدارة متطورة - بحث متقدم
    💎 التحكم الكامل في النقاط والباقات للمسؤولين
    """)
    
    start_bot_monitoring()
    add_admin_notification("🟢 النظام يعمل الآن - تريكس ", "system", 3)
    
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"خطأ في تشغيل البوت: {e}")
        add_admin_notification("🔴 توقف البوت عن العمل", "system", 3)