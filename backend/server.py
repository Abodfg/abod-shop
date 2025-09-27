from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Telegram Bots
USER_BOT_TOKEN = "7933553585:AAHNAAxp2ZCVV_KqohmF2Mx5WL66__HYnno"
ADMIN_BOT_TOKEN = "7835622090:AAGLTeEv-zUdNNkUrkS_L_FCd3zSUOosVeU"
ADMIN_ID = 7040570081  # إيدي الإدارة الرئيسية (جميع الإشعارات)
SYSTEM_ADMIN_ID = 1573526135  # إيدي إدارة النظام (نبض النظام فقط)
ADMIN_IDS = [ADMIN_ID, SYSTEM_ADMIN_ID]  # قائمة جميع الإداريين

user_bot = Bot(token=USER_BOT_TOKEN)
admin_bot = Bot(token=ADMIN_BOT_TOKEN)

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    balance: float = 0.0
    join_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    orders_count: int = 0
    is_banned: bool = False
    ban_reason: Optional[str] = None
    banned_at: Optional[datetime] = None

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category_type: str
    price: float
    delivery_type: str  # "code", "phone", "email", "manual"
    redemption_method: str
    terms: str
    image_url: Optional[str] = None
    product_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    terms: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Code(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    description: str
    terms: str
    category_id: str
    code_type: str  # "text", "number", "dual" (code + serial)
    serial_number: Optional[str] = None  # for dual type
    is_used: bool = False
    used_by: Optional[str] = None
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    telegram_id: int
    product_name: str
    category_name: str
    category_id: str
    price: float
    delivery_type: str  # "code", "phone", "email", "manual"
    status: str  # "pending", "completed", "failed"
    code_sent: Optional[str] = None
    user_input_data: Optional[str] = None  # phone/email entered by user
    admin_notes: Optional[str] = None
    order_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completion_date: Optional[datetime] = None

class TelegramSession(BaseModel):
    telegram_id: int
    state: str
    data: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Session management
async def get_session(telegram_id: int, is_admin: bool = False):
    collection = db.admin_sessions if is_admin else db.user_sessions
    session = await collection.find_one({"telegram_id": telegram_id})
    if session:
        return TelegramSession(**session)
    return None

async def save_session(session: TelegramSession, is_admin: bool = False):
    collection = db.admin_sessions if is_admin else db.user_sessions
    session.updated_at = datetime.now(timezone.utc)
    await collection.replace_one(
        {"telegram_id": session.telegram_id},
        session.dict(),
        upsert=True
    )

async def clear_session(telegram_id: int, is_admin: bool = False):
    collection = db.admin_sessions if is_admin else db.user_sessions
    await collection.delete_one({"telegram_id": telegram_id})

# User bot handlers
async def send_user_message(telegram_id: int, text: str, keyboard: Optional[InlineKeyboardMarkup] = None):
    try:
        await user_bot.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except TelegramError as e:
        logging.error(f"Failed to send user message to {telegram_id}: {e}")

async def set_persistent_menu(telegram_id: int):
    """تثبيت زر القائمة في البوت"""
    from telegram import MenuButton, MenuButtonCommands
    try:
        await user_bot.set_chat_menu_button(
            chat_id=telegram_id,
            menu_button=MenuButtonCommands()
        )
        
        # Set bot commands for menu
        from telegram import BotCommand
        commands = [
            BotCommand("start", "العودة للقائمة الرئيسية"),
            BotCommand("menu", "عرض جميع الأوامر"),
            BotCommand("help", "المساعدة وكيفية الاستخدام"),
            BotCommand("shop", "متجر المنتجات"),
            BotCommand("wallet", "عرض المحفظة"),
            BotCommand("orders", "طلباتي وتاريخي"),
            BotCommand("support", "الدعم الفني")
        ]
        await user_bot.set_my_commands(commands)
    except Exception as e:
        logging.error(f"Failed to set persistent menu: {e}")

async def send_admin_message(telegram_id: int, text: str, keyboard: Optional[InlineKeyboardMarkup] = None):
    try:
        await admin_bot.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except TelegramError as e:
        logging.error(f"Failed to send admin message to {telegram_id}: {e}")

async def create_user_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛒 الشراء", callback_data="browse_products")],
        [InlineKeyboardButton("💰 عرض المحفظة", callback_data="view_wallet")],
        [InlineKeyboardButton("📞 الدعم الفني", callback_data="support")],
        [InlineKeyboardButton("📋 تاريخ الطلبات", callback_data="order_history")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def create_modern_user_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🛍️ متجر المنتجات", callback_data="browse_products"),
            InlineKeyboardButton("💎 محفظتي الرقمية", callback_data="view_wallet")
        ],
        [
            InlineKeyboardButton("📦 طلباتي وتاريخي", callback_data="order_history"),
            InlineKeyboardButton("🔥 العروض الحصرية", callback_data="special_offers")
        ],
        [
            InlineKeyboardButton("💬 الدعم المباشر", callback_data="support"),
            InlineKeyboardButton("ℹ️ معلومات المتجر", callback_data="about_store")
        ],
        [
            InlineKeyboardButton("🔄 تحديث الحساب", callback_data="refresh_data"),
            InlineKeyboardButton("🎁 مفاجآت اليوم", callback_data="daily_surprises")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def create_visual_buttons_menu():
    """قائمة أزرار مرئية مع الكيبورد العادي"""
    visual_text = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃               🎮 القائمة الرئيسية 🎮                ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                         ┃
┃  🛍️  [1] متجر المنتجات - أحدث الألعاب          ┃
┃  💎  [2] محفظتي الرقمية - إدارة الأموال         ┃  
┃  📦  [3] طلباتي وتاريخي - متابعة المشتريات      ┃
┃  🔥  [4] العروض الحصرية - وفر أكثر            ┃
┃  💬  [5] الدعم المباشر - مساعدة فورية         ┃
┃  ℹ️  [6] معلومات المتجر - تعرف علينا          ┃
┃  🔄  [7] تحديث الحساب - بيانات محدثة          ┃
┃  🎁  [8] مفاجآت اليوم - عروض يومية           ┃
┃                                                         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

💡 *يمكنك أيضاً إرسال رقم الخيار (1-8) مباشرة!*"""
    return visual_text

async def create_simple_menu():
    """قائمة بسيطة وسريعة"""
    menu_text = """الأرقام السريعة:

🛍️ [1] التسوق
💰 [2] المحفظة  
📦 [3] الطلبات
🔥 [4] العروض
💬 [5] الدعم
ℹ️ [6] معلومات
🔄 [7] تحديث
🎁 [8] مفاجآت"""
    return menu_text

async def create_main_keyboard():
    """كيبورد أساسي سريع ومبسط"""
    keyboard = [
        [
            InlineKeyboardButton("🛍️ التسوق", callback_data="browse_products"),
            InlineKeyboardButton("💰 المحفظة", callback_data="view_wallet")
        ],
        [
            InlineKeyboardButton("📦 طلباتي", callback_data="order_history"),
            InlineKeyboardButton("💬 الدعم", callback_data="support")
        ],
        [
            InlineKeyboardButton("🔥 العروض", callback_data="special_offers"),
            InlineKeyboardButton("📋 القائمة", callback_data="show_full_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def create_enhanced_user_keyboard():
    """كيبورد محسن مع خيارات إضافية"""
    return await create_main_keyboard()  # استخدام الكيبورد البسيط لتحسين الأداء

async def create_animated_menu():
    """قائمة تفاعلية محسنة مع أنيميشن"""
    animated_text = """
🎯 **اختر من الخيارات التالية:**

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🛍️  **[1]** متجر المنتجات - أحدث الألعاب والبرامج  ┃
┃  💎  **[2]** محفظتي الرقمية - إدارة الأموال والرصيد   ┃  
┃  📦  **[3]** طلباتي وتاريخي - متابعة جميع المشتريات   ┃
┃  🔥  **[4]** العروض الحصرية - خصومات وعروض مميزة    ┃
┃  💬  **[5]** الدعم المباشر - مساعدة فورية ومتخصصة   ┃
┃  ℹ️  **[6]** معلومات المتجر - تعرف على خدماتنا      ┃
┃  🔄  **[7]** تحديث الحساب - بيانات محدثة ودقيقة     ┃
┃  🎁  **[8]** مفاجآت اليوم - عروض يومية حصرية       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"""
    return animated_text

async def create_enhanced_user_keyboard():
    """كيبورد محسن مع خيارات إضافية"""
    keyboard = [
        [
            InlineKeyboardButton("🛍️ متجر المنتجات", callback_data="browse_products"),
            InlineKeyboardButton("💎 محفظتي الرقمية", callback_data="view_wallet")
        ],
        [
            InlineKeyboardButton("📦 طلباتي وتاريخي", callback_data="order_history"),
            InlineKeyboardButton("🔥 العروض الحصرية", callback_data="special_offers")
        ],
        [
            InlineKeyboardButton("💬 الدعم المباشر", callback_data="support"),
            InlineKeyboardButton("ℹ️ معلومات المتجر", callback_data="about_store")
        ],
        [
            InlineKeyboardButton("🔄 تحديث الحساب", callback_data="refresh_data"),
            InlineKeyboardButton("🎁 مفاجآت اليوم", callback_data="daily_surprises")
        ],
        [
            InlineKeyboardButton("📋 القائمة الكاملة", callback_data="show_full_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def create_back_to_main_keyboard():
    """إنشاء كيبورد العودة للقائمة الرئيسية"""
    keyboard = [
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_back_button(telegram_id: int, is_admin: bool = False):
    """دالة شاملة للتعامل مع زر الرجوع مع مسح كامل للجلسة"""
    # مسح الجلسة الحالية بالكامل
    await clear_session(telegram_id, is_admin)
    
    # إنشاء الكيبورد المناسب
    if is_admin:
        keyboard = await create_admin_keyboard()
        message = """🔧 *لوحة تحكم الإدارة*

تم إلغاء العملية السابقة وإعادة تعيين الحالة.
اختر العملية المطلوبة:"""
        await send_admin_message(telegram_id, message, keyboard)
    else:
        # الحصول على بيانات المستخدم المحدثة
        user = await db.users.find_one({"telegram_id": telegram_id})
        balance = user.get('balance', 0) if user else 0
        name = user.get('first_name', 'صديق') if user else 'صديق'
        
        keyboard = await create_modern_user_keyboard()
        message = f"""🏠 *مرحباً بك مرة أخرى {name}!*

💰 رصيدك الحالي: *${balance:.2f}*

تم إلغاء العملية السابقة. اختر ما تريد القيام به:"""
        await send_user_message(telegram_id, message, keyboard)

async def handle_special_offers(telegram_id: int):
    """عرض العروض الخاصة"""
    # استيراد العروض من ملف التكوين
    from offers_config import get_offers_text
    offers_text = get_offers_text()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ تسوق الآن", callback_data="browse_products")],
        [InlineKeyboardButton("💬 تواصل للعروض", callback_data="support")],
        [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
    ])
    
    await send_user_message(telegram_id, offers_text, keyboard)

async def handle_about_store(telegram_id: int):
    """معلومات عن المتجر"""
    about_text = """ℹ️ *معلومات عن Abod Card*

━━━━━━━━━━━━━━━━━━━━━━━━━

🏢 *من نحن؟*
متجر رقمي موثوق متخصص في بيع المنتجات الرقمية والاشتراكات

🎯 *رؤيتنا:*
تقديم خدمة سريعة وآمنة لجميع احتياجاتك الرقمية

⚡ *مميزاتنا:*
• تسليم فوري للأكواد المتوفرة
• دعم فني 24/7  
• أمان وثقة مضمونة
• أسعار تنافسية
• طرق دفع متنوعة

📞 *للتواصل:*
@AbodStoreVIP

🔒 *الأمان أولويتنا*"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ ابدأ التسوق", callback_data="browse_products")],
        [InlineKeyboardButton("💬 تواصل معنا", callback_data="support")],
        [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
    ])
    
    await send_user_message(telegram_id, about_text, keyboard)

async def handle_refresh_user_data(telegram_id: int):
    """تحديث بيانات المستخدم"""
    # الحصول على بيانات المستخدم الحديثة
    user = await db.users.find_one({"telegram_id": telegram_id})
    
    if user:
        orders_count = user.get('orders_count', 0)
        balance = user.get('balance', 0)
        join_date = user.get('join_date')
        
        if join_date:
            join_date_str = join_date.strftime('%Y-%m-%d')
        else:
            join_date_str = "غير محدد"
        
        refresh_text = f"""🔄 *تم تحديث بيانات حسابك*

👤 الاسم: {user.get('first_name', 'غير محدد')}
🆔 المعرف: @{user.get('username', 'غير محدد')}
💰 الرصيد: *${balance:.2f}*
📦 عدد الطلبات: {orders_count}
📅 تاريخ الانضمام: {join_date_str}

✅ جميع بياناتك محدثة الآن!"""
    else:
        refresh_text = "❌ لا يمكن العثور على بيانات حسابك. يرجى التواصل مع الدعم الفني."
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 عرض المحفظة", callback_data="view_wallet")],
        [InlineKeyboardButton("📦 عرض الطلبات", callback_data="order_history")],
        [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
    ])
    
    await send_user_message(telegram_id, refresh_text, keyboard)

async def handle_spending_details(telegram_id: int):
    """عرض تفاصيل الإنفاق للمستخدم"""
    # الحصول على الطلبات المكتملة للمستخدم
    completed_orders = await db.orders.find({
        "telegram_id": telegram_id,
        "status": "completed"
    }).sort("completion_date", -1).to_list(50)
    
    # حساب الإحصائيات
    total_spent = sum(order.get('price', 0) for order in completed_orders)
    orders_count = len(completed_orders)
    
    if orders_count == 0:
        spending_text = """📊 *تفاصيل الإنفاق*

━━━━━━━━━━━━━━━━━━━━━━━━━

💰 إجمالي الإنفاق: *$0.00*
📦 عدد الطلبات المكتملة: *0*

🎯 ابدأ تسوقك الأول معنا!"""
    else:
        avg_order = total_spent / orders_count if orders_count > 0 else 0
        
        spending_text = f"""📊 *تفاصيل الإنفاق*

━━━━━━━━━━━━━━━━━━━━━━━━━

💰 إجمالي الإنفاق: *${total_spent:.2f}*
📦 عدد الطلبات المكتملة: *{orders_count}*
📈 متوسط قيمة الطلب: *${avg_order:.2f}*

📋 *آخر الطلبات:*"""
        
        # إضافة آخر 5 طلبات
        for i, order in enumerate(completed_orders[:5], 1):
            completion_date = order.get('completion_date')
            date_str = completion_date.strftime('%m-%d') if completion_date else 'غير محدد'
            spending_text += f"\n{i}. {order['product_name']} - ${order['price']:.2f} ({date_str})"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 جميع طلباتي", callback_data="order_history")],
        [InlineKeyboardButton("🛍️ تسوق المزيد", callback_data="browse_products")],
        [InlineKeyboardButton("🔙 عودة للمحفظة", callback_data="view_wallet")]
    ])
    
    await send_user_message(telegram_id, spending_text, keyboard)

async def handle_daily_surprises(telegram_id: int):
    """مفاجآت وعروض اليوم"""
    import random
    from datetime import datetime, timezone
    
    # Get today's date for dynamic content
    today = datetime.now(timezone.utc)
    day_name = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"][today.weekday()]
    
    # استيراد المفاجآت من ملف التكوين
    from offers_config import get_daily_surprise
    daily_surprise = get_daily_surprise()
    
    surprises_text = f"""🎁 *مفاجآت يوم {day_name}* 🎁

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎊 *عرض اليوم الخاص:*
{daily_surprise}

🔥 *عروض محدودة الوقت:*
• خصم إضافي 10% للعملاء الجدد
• مضاعفة النقاط على أول 3 طلبات
• هدية مجانية مع الطلبات فوق $50

⏰ *العرض ينتهي خلال:* 23:59 اليوم

🎯 *طريقة الاستفادة:*
تسوق الآن واستخدم الكود: **DAILY{today.strftime('%d')}**

💡 *نصيحة:* اشترك في الإشعارات للحصول على عروض حصرية يومية!"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ تسوق الآن بالخصم", callback_data="browse_products")],
        [InlineKeyboardButton("💬 اطلب الكود من الدعم", callback_data="support")],
        [InlineKeyboardButton("⭐ المزيد من العروض", callback_data="special_offers")],
        [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
    ])
    
    await send_user_message(telegram_id, surprises_text, keyboard)

async def handle_show_full_menu(telegram_id: int):
    """عرض القائمة الكاملة مع جميع الأوامر"""
    full_menu_text = """📋 **القائمة الكاملة - جميع الأوامر** 📋

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **الأوامر الأساسية:**
• `/start` - العودة للقائمة الرئيسية
• `/menu` - عرض هذه القائمة

🔢 **الأرقام السريعة:**
• `1` - 🛍️ متجر المنتجات
• `2` - 💎 محفظتي الرقمية  
• `3` - 📦 طلباتي وتاريخي
• `4` - 🔥 العروض الحصرية
• `5` - 💬 الدعم المباشر
• `6` - ℹ️ معلومات المتجر
• `7` - 🔄 تحديث الحساب
• `8` - 🎁 مفاجآت اليوم

🎮 **الخدمات المتاحة:**
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🛒 **التسوق:** تصفح وشراء المنتجات الرقمية      ┃
┃ 💳 **المحفظة:** إدارة الرصيد والمدفوعات        ┃
┃ 📊 **التقارير:** متابعة الطلبات والإحصائيات      ┃
┃ 🎁 **العروض:** خصومات وعروض حصرية يومية       ┃
┃ 🛠️ **الدعم:** مساعدة فنية متخصصة 24/7        ┃
┃ 📱 **التحديثات:** آخر الأخبار والمنتجات الجديدة  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

💡 **نصائح الاستخدام:**
• استخدم الأزرار للتنقل السريع
• اكتب الأرقام مباشرة للوصول الفوري
• احفظ هذه القائمة للرجوع إليها لاحقاً

🎊 **نحن هنا لخدمتك على مدار الساعة!** 🎊"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛍️ ابدأ التسوق", callback_data="browse_products"),
            InlineKeyboardButton("💎 عرض المحفظة", callback_data="view_wallet")
        ],
        [
            InlineKeyboardButton("💬 تواصل معنا", callback_data="support"),
            InlineKeyboardButton("🎁 العروض اليومية", callback_data="daily_surprises")
        ],
        [
            InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main_menu")
        ]
    ])
    
    await send_user_message(telegram_id, full_menu_text, keyboard)

async def handle_fast_menu(telegram_id: int):
    """قائمة سريعة ومبسطة"""
    menu_text = """قائمة الأوامر:

الأرقام السريعة:
1 - التسوق     2 - المحفظة
3 - الطلبات    4 - العروض  
5 - الدعم      6 - معلومات
7 - تحديث      8 - مفاجآت

الأوامر:
/start - الرئيسية
/shop - التسوق
/wallet - المحفظة
/orders - الطلبات
/support - الدعم"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛍️ تسوق", callback_data="browse_products"),
            InlineKeyboardButton("💰 محفظة", callback_data="view_wallet")
        ],
        [
            InlineKeyboardButton("📦 طلبات", callback_data="order_history"),
            InlineKeyboardButton("💬 دعم", callback_data="support")
        ],
        [InlineKeyboardButton("🔙 الرئيسية", callback_data="back_to_main_menu")]
    ])
    
    await send_user_message(telegram_id, menu_text, keyboard)

async def handle_full_menu_command(telegram_id: int):
    """معالج أمر /menu - عرض القائمة الكاملة"""
    await handle_fast_menu(telegram_id)

async def handle_quick_access(telegram_id: int):
    """قائمة الوصول السريع للخدمات الأساسية"""
    quick_access_text = """⚡ **الوصول السريع** ⚡

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **الخدمات الأكثر استخداماً:**

🛍️ **التسوق السريع**
• تصفح المنتجات مباشرة
• أحدث العروض والخصومات

💎 **إدارة المحفظة**
• عرض الرصيد الحالي
• شحن المحفظة فوراً

📦 **متابعة الطلبات**
• تاريخ جميع مشترياتك
• حالة الطلبات الحالية

💬 **الدعم الفوري**
• تواصل مباشر مع الفريق
• حل سريع للمشاكل

🎁 **العروض اليومية**
• مفاجآت وخصومات حصرية
• عروض محدودة الوقت

⚡ **نصائح للاستخدام السريع:**
• احفظ هذه القائمة للوصول السريع
• استخدم الأرقام (1-8) للتنقل المباشر
• اضغط على الأزرار للوصول الفوري

🚀 **وفر وقتك مع الوصول السريع!**"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛍️ تسوق سريع", callback_data="browse_products"),
            InlineKeyboardButton("💎 المحفظة", callback_data="view_wallet")
        ],
        [
            InlineKeyboardButton("📦 طلباتي", callback_data="order_history"),
            InlineKeyboardButton("💬 دعم فوري", callback_data="support")
        ],
        [
            InlineKeyboardButton("🎁 عروض اليوم", callback_data="daily_surprises"),
            InlineKeyboardButton("🔥 عروض خاصة", callback_data="special_offers")
        ],
        [
            InlineKeyboardButton("📋 القائمة الكاملة", callback_data="show_full_menu"),
            InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")
        ]
    ])
    
    await send_user_message(telegram_id, quick_access_text, keyboard)

async def handle_enhanced_help_for_unknown_input(telegram_id: int, user_input: str):
    """مساعدة بسيطة وسريعة"""
    help_text = f"""لم أفهم: "{user_input}"

طرق الاستخدام:
• اكتب رقم من 1-8
• استخدم الأوامر: /menu /shop /wallet
• أو اضغط الأزرار أدناه"""
    
    keyboard = await create_main_keyboard()
    await send_user_message(telegram_id, help_text, keyboard)

async def handle_help_command(telegram_id: int):
    """معالج أمر المساعدة"""
    help_text = """❓ *مساعدة - كيفية استخدام البوت* ❓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **الأوامر الأساسية:**
• `/start` - العودة للقائمة الرئيسية
• `/menu` - عرض القائمة الكاملة
• `/help` أو `/مساعدة` - عرض هذه المساعدة

🔢 **الأرقام السريعة:**
• `1` - 🛍️ متجر المنتجات
• `2` - 💎 محفظتي الرقمية  
• `3` - 📦 طلباتي وتاريخي
• `4` - 🔥 العروض الحصرية
• `5` - 💬 الدعم المباشر
• `6` - ℹ️ معلومات المتجر
• `7` - 🔄 تحديث الحساب
• `8` - 🎁 مفاجآت اليوم

💡 **نصائح الاستخدام:**
• استخدم الأزرار للتنقل السريع
• اكتب الأرقام مباشرة للوصول الفوري
• تواصل مع الدعم عند الحاجة

🆔 **معرف حسابك:** `{telegram_id}`

🎊 **نحن هنا لمساعدتك دائماً!** 🎊"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛍️ ابدأ التسوق", callback_data="browse_products"),
            InlineKeyboardButton("💬 تواصل معنا", callback_data="support")
        ],
        [
            InlineKeyboardButton("📋 القائمة الكاملة", callback_data="show_full_menu"),
            InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")
        ]
    ])
    
    await send_user_message(telegram_id, help_text, keyboard)
async def handle_support(telegram_id: int):
    """دعم فني محسن مع خيارات متعددة"""
    support_text = """💬 *الدعم الفني - نحن هنا لمساعدتك* 💬

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 *كيف يمكننا مساعدتك؟*

🔹 مشاكل في الطلبات
🔹 استفسارات عن المنتجات  
🔹 مساعدة في الدفع والشحن
🔹 استرداد أو إلغاء طلب
🔹 اقتراحات وتحسينات

📞 *طرق التواصل معنا:*

💬 **الدردشة المباشرة:** @AbodStoreVIP
📧 **البريد الإلكتروني:** support@abodcard.com
⏰ **ساعات العمل:** 24/7 متواصل

🆔 *معلومات مهمة لتسريع الخدمة:*
• إيدي حسابك: `{telegram_id}`
• نسخ الإيدي أعلاه عند التواصل

⚡ *متوسط وقت الرد:* أقل من 5 دقائق

🏆 *رضاك هدفنا الأول!*"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 دردشة مباشرة", url="https://t.me/AbodStoreVIP")],
        [InlineKeyboardButton("❓ الأسئلة الشائعة", callback_data="faq")],
        [InlineKeyboardButton("📋 تقديم شكوى", callback_data="submit_complaint")],
        [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
    ])
    
    await send_user_message(telegram_id, support_text, keyboard)

async def handle_faq(telegram_id: int):
    """الأسئلة الشائعة"""
    faq_text = """❓ *الأسئلة الشائعة* ❓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔸 **كيف أشحن محفظتي؟**
تواصل مع @AbodStoreVIP مع إيدي حسابك وستتم المساعدة فوراً

🔸 **متى أستلم الكود بعد الطلب؟**
- الأكواد المتوفرة: فوراً
- الطلبات المخصصة: خلال 10-30 دقيقة

🔸 **هل يمكن إلغاء الطلب؟**
نعم، قبل إرسال الكود. تواصل مع الدعم

🔸 **ماذا لو لم يعمل الكود؟**
نستبدله فوراً أو نعيد المبلغ كاملاً

🔸 **هل المتجر آمن؟**
نعم، محمي بأحدث تقنيات الأمان والتشفير

🔸 **طرق الدفع المتاحة؟**
شحن المحفظة عبر الدعم الفني

🔸 **هل توجد رسوم خفية؟**
لا، السعر المعروض هو السعر النهائي"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 سؤال آخر؟", callback_data="support")],
        [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
    ])
    
    await send_user_message(telegram_id, faq_text, keyboard)

async def handle_submit_complaint(telegram_id: int):
    """تقديم شكوى"""
    complaint_text = f"""📋 *تقديم شكوى أو اقتراح* 📋

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

نحن نقدر ملاحظاتك ونسعى لتحسين خدماتنا باستمرار.

📝 *لتقديم شكوى أو اقتراح:*

1️⃣ تواصل معنا على: @AbodStoreVIP
2️⃣ اذكر إيدي حسابك: `{telegram_id}`
3️⃣ اكتب شكواك أو اقتراحك بالتفصيل

⏰ *سنرد عليك خلال:* أقل من ساعة

🎯 *نوع الشكاوى التي نتعامل معها:*
• مشاكل تقنية في الموقع/البوت
• جودة المنتجات أو الخدمة
• مشاكل في عملية الشراء
• اقتراحات للتحسين
• شكاوى من فريق الدعم

🏆 *التزامنا:*
- الرد السريع والاعتذار عند الخطأ
- الحل الفوري أو التعويض المناسب  
- المتابعة حتى رضاك التام

📞 رضاك أولويتنا القصوى!"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 إرسال الشكوى الآن", url="https://t.me/AbodStoreVIP")],
        [InlineKeyboardButton("💬 العودة للدعم", callback_data="support")],
        [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
    ])
    
    await send_user_message(telegram_id, complaint_text, keyboard)

async def create_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📦 إدارة المنتجات", callback_data="manage_products")],
        [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="manage_users")],
        [InlineKeyboardButton("🎫 إدارة الأكواد", callback_data="manage_codes")],
        [InlineKeyboardButton("📊 التقارير", callback_data="reports")],
        [InlineKeyboardButton("📋 الطلبات", callback_data="manage_orders")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_user_start(telegram_id: int, username: str = None, first_name: str = None):
    # Add user to database if not exists
    user_data = await db.users.find_one({"telegram_id": telegram_id})
    if not user_data:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            balance=0.0,
            orders_count=0
        )
        await db.users.insert_one(user.dict())
        user_data = user.dict()
    else:
        # Update user info if needed
        await db.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"username": username, "first_name": first_name}}
        )
    
    # Set up persistent menu button
    await set_persistent_menu(telegram_id)
    
    # Get user balance for personalized message
    user_balance = user_data.get('balance', 0) if user_data else 0
    name = first_name or username or "صديق"
    
    # Simple and fast welcome message
    welcome_text = f"""مرحباً {name}! 

💰 رصيدك: ${user_balance:.2f}
🆔 معرف حسابك: `{telegram_id}`

اختر من الخيارات أدناه أو:
• اكتب رقم من 1-8 للوصول السريع
• اكتب /menu لعرض جميع الأوامر"""
    
    keyboard = await create_main_keyboard()
    await send_user_message(telegram_id, welcome_text, keyboard)

async def handle_admin_start(telegram_id: int):
    welcome_text = """🔧 *لوحة تحكم الإدارة - Abod Card*

مرحباً بك في لوحة تحكم الإدارة. يمكنك إدارة جميع جوانب النظام من هنا.

اختر العملية المطلوبة:"""
    
    keyboard = await create_admin_keyboard()
    await send_admin_message(telegram_id, welcome_text, keyboard)

# API Routes
@api_router.post("/webhook/user/{secret}")
async def user_webhook(secret: str, request: Request):
    if secret != "abod_user_webhook_secret":
        raise HTTPException(status_code=403, detail="Invalid webhook secret")
    
    try:
        update_data = await request.json()
        update = Update.de_json(update_data, user_bot)
        
        if update.message:
            await handle_user_message(update.message)
        elif update.callback_query:
            try:
                await handle_user_callback(update.callback_query)
                # Answer the callback query to remove loading state
                await update.callback_query.answer()
            except Exception as callback_error:
                logging.error(f"User callback error: {callback_error}")
                # Try to answer the callback even if processing failed
                try:
                    await update.callback_query.answer("حدث خطأ، يرجى المحاولة مرة أخرى")
                except:
                    pass
            
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"User webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/webhook/admin/{secret}")
async def admin_webhook(secret: str, request: Request):
    if secret != "abod_admin_webhook_secret":
        raise HTTPException(status_code=403, detail="Invalid webhook secret")
    
    try:
        update_data = await request.json()
        update = Update.de_json(update_data, admin_bot)
        
        if update.message:
            await handle_admin_message(update.message)
        elif update.callback_query:
            try:
                await handle_admin_callback(update.callback_query)
                # Answer the callback query to remove loading state
                await update.callback_query.answer()
            except Exception as callback_error:
                logging.error(f"Admin callback error: {callback_error}")
                # Try to answer the callback even if processing failed
                try:
                    await update.callback_query.answer("حدث خطأ، يرجى المحاولة مرة أخرى")
                except:
                    pass
            
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Admin webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_user_message(message):
    telegram_id = message.chat_id
    text = message.text
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Check if user is banned
    user = await db.users.find_one({"telegram_id": telegram_id})
    if user and user.get('is_banned', False):
        ban_reason = user.get('ban_reason', 'غير محدد')
        ban_message = f"""🚫 *حسابك محظور*

تم حظر حسابك من استخدام الخدمة بسبب:
{ban_reason}

📞 للاستفسار أو الاعتراض: @AbodStoreVIP"""
        await send_user_message(telegram_id, ban_message)
        return
    
    if text == "/start":
        await handle_user_start(telegram_id, username, first_name)
    elif text == "/menu":
        await handle_fast_menu(telegram_id)
    elif text.lower() in ["/help", "/مساعدة", "مساعدة", "help"]:
        await handle_help_command(telegram_id)
    elif text.lower() in ["/shop", "shop"]:
        await handle_browse_products(telegram_id)
    elif text.lower() in ["/wallet", "wallet"]: 
        await handle_view_wallet(telegram_id)
    elif text.lower() in ["/orders", "orders"]:
        await handle_order_history(telegram_id)
    elif text.lower() in ["/support", "support"]:
        await handle_support(telegram_id)
    else:
        # Handle text input based on session state
        session = await get_session(telegram_id)
        if session:
            if session.state == "wallet_topup_amount":
                try:
                    amount = float(text)
                    topup_text = f"""💰 *طلب شحن المحفظة*

المبلغ المطلوب: *{amount} دولار*

للشحن، يرجى التواصل مع الإدارة على:
@AbodStoreVIP

أرسل لهم هذا المبلغ وإيدي حسابك: `{telegram_id}`"""
                    
                    back_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
                    ])
                    await send_user_message(telegram_id, topup_text, back_keyboard)
                    await clear_session(telegram_id)
                except ValueError:
                    await send_user_message(telegram_id, "❌ يرجى إدخال رقم صحيح")
            
            # Handle purchase input from users
            elif session.state == "purchase_input_phone":
                await handle_user_phone_input(telegram_id, text, session)
            
            elif session.state == "purchase_input_email":
                await handle_user_email_input(telegram_id, text, session)
            
            elif session.state == "purchase_input_id":
                await handle_user_id_input(telegram_id, text, session)
        else:
            # Handle direct menu numbers when no session exists
            if text.isdigit() and len(text) == 1:
                menu_number = int(text)
                # Direct response - no loading messages for better speed
                if menu_number == 1:
                    await handle_browse_products(telegram_id)
                elif menu_number == 2:
                    await handle_view_wallet(telegram_id)
                elif menu_number == 3:
                    await handle_order_history(telegram_id)
                elif menu_number == 4:
                    await handle_special_offers(telegram_id)
                elif menu_number == 5:
                    await handle_support(telegram_id)
                elif menu_number == 6:
                    await handle_about_store(telegram_id)
                elif menu_number == 7:
                    await handle_refresh_user_data(telegram_id)
                elif menu_number == 8:
                    await handle_daily_surprises(telegram_id)
                else:
                    await send_user_message(telegram_id, "❌ رقم غير صحيح. يرجى اختيار رقم من 1-8")
            
            # Handle text shortcuts - direct response for speed
            elif text.lower() in ["shop", "متجر", "منتجات", "shopping"]:
                await handle_browse_products(telegram_id)
            elif text.lower() in ["wallet", "محفظة", "رصيد", "balance"]:
                await handle_view_wallet(telegram_id)
            elif text.lower() in ["orders", "طلبات", "طلباتي", "history"]:
                await handle_order_history(telegram_id)
            elif text.lower() in ["support", "دعم"]:
                await handle_support(telegram_id)
            elif text.lower() in ["offers", "عروض", "خصومات", "deals"]:
                await handle_special_offers(telegram_id)
            elif text.lower() in ["about", "معلومات", "عنا", "info"]:
                await handle_about_store(telegram_id)
            elif text.lower() in ["refresh", "تحديث", "update"]:
                await handle_refresh_user_data(telegram_id)
            elif text.lower() in ["daily", "مفاجآت", "اليوم", "surprises"]:
                await handle_daily_surprises(telegram_id)
            else:
                # Enhanced help message for unknown text
                await handle_enhanced_help_for_unknown_input(telegram_id, text)

async def handle_user_callback(callback_query):
    telegram_id = callback_query.message.chat_id
    data = callback_query.data
    
    # Check if user is banned
    user = await db.users.find_one({"telegram_id": telegram_id})
    if user and user.get('is_banned', False):
        ban_reason = user.get('ban_reason', 'غير محدد')
        ban_message = f"""🚫 *حسابك محظور*

تم حظر حسابك من استخدام الخدمة بسبب:
{ban_reason}

📞 للاستفسار أو الاعتراض: @AbodStoreVIP"""
        await send_user_message(telegram_id, ban_message)
        return
    
    # No loading animations - direct response for better performance
    
    if data == "main_menu":
        keyboard = await create_user_keyboard()
        await send_user_message(telegram_id, "🏠 مرحباً بك في القائمة الرئيسية!", keyboard)
        await clear_session(telegram_id)
    
    elif data == "browse_products":
        await handle_browse_products(telegram_id)
    
    elif data == "view_wallet":
        await handle_view_wallet(telegram_id)
    
    elif data == "topup_wallet":
        await handle_topup_wallet(telegram_id)
    
    elif data == "support":
        support_text = """📞 *الدعم الفني*

للحصول على المساعدة، يرجى التواصل مع فريق الدعم:
@AbodStoreVIP

سيقوم فريقنا بالرد عليك في أقرب وقت ممكن."""
        
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ])
        await send_user_message(telegram_id, support_text, back_keyboard)
    
    elif data == "order_history":
        await handle_order_history(telegram_id)
    
    elif data.startswith("product_"):
        product_id = data.replace("product_", "")
        await handle_user_product_selection(telegram_id, product_id)
    
    elif data.startswith("category_"):
        category_id = data.replace("category_", "")
        await handle_user_category_selection(telegram_id, category_id)
    
    elif data.startswith("buy_category_"):
        category_id = data.replace("buy_category_", "")
        await handle_user_purchase(telegram_id, category_id)
    
    elif data.startswith("order_details_"):
        order_id = data.replace("order_details_", "")
        await handle_user_order_details(telegram_id, order_id)
    
    elif data == "back_to_main_menu":
        await handle_back_button(telegram_id, is_admin=False)
    
    elif data == "special_offers":
        await handle_special_offers(telegram_id)
    
    elif data == "about_store":
        await handle_about_store(telegram_id)
    
    elif data == "refresh_data":
        await handle_refresh_user_data(telegram_id)
    
    elif data == "spending_details":
        await handle_spending_details(telegram_id)
    
    elif data == "daily_surprises":
        await handle_daily_surprises(telegram_id)
    
    elif data == "show_full_menu":
        await handle_show_full_menu(telegram_id)
    
    elif data == "quick_access":
        await handle_quick_access(telegram_id)
    
    elif data == "faq":
        await handle_faq(telegram_id)
    
    elif data == "submit_complaint":
        await handle_submit_complaint(telegram_id)

async def handle_browse_products(telegram_id: int):
    products = await db.products.find({"is_active": True}).to_list(100)
    
    if not products:
        no_products_text = """🛍️ *عذراً، المتجر قيد التحديث*

لا توجد منتجات متاحة حالياً. نعمل على إضافة منتجات جديدة ومثيرة!

📞 تواصل مع الدعم للاستفسار عن المنتجات المخصصة."""
        
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 تواصل مع الدعم", callback_data="support")],
            [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
        ])
        await send_user_message(telegram_id, no_products_text, back_keyboard)
        return
    
    # حساب عدد الفئات لكل منتج
    products_with_categories = []
    for product in products:
        categories_count = await db.categories.count_documents({"product_id": product["id"]})
        products_with_categories.append((product, categories_count))
    
    text = f"""🛍️ *متجر Abod Card*

🎯 لديك {len(products)} منتج متاح للاختيار من بينها

━━━━━━━━━━━━━━━━━━━━━━━━━

📦 *اختر المنتج الذي يناسبك:*"""
    
    keyboard = []
    for i, (product, categories_count) in enumerate(products_with_categories, 1):
        button_text = f"{i}. 📦 {product['name']}"
        if categories_count > 0:
            button_text += f" ({categories_count} فئة)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"product_{product['id']}")])
    
    keyboard.extend([
        [InlineKeyboardButton("⭐ عروض خاصة", callback_data="special_offers")],
        [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
    ])
    
    await send_user_message(telegram_id, text, InlineKeyboardMarkup(keyboard))

async def handle_view_wallet(telegram_id: int):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if user:
        balance = user.get("balance", 0.0)
        orders_count = user.get('orders_count', 0)
        join_date = user.get('join_date')
        
        if join_date:
            join_date_str = join_date.strftime('%Y-%m-%d')
        else:
            join_date_str = "غير محدد"
            
        # تحديد حالة المحفظة
        if balance >= 50:
            wallet_status = "🟢 ممتاز"
        elif balance >= 20:
            wallet_status = "🟡 جيد" 
        elif balance > 0:
            wallet_status = "🟠 منخفض"
        else:
            wallet_status = "🔴 فارغ"
            
        wallet_text = f"""💳 *محفظتك الرقمية*

━━━━━━━━━━━━━━━━━━━━━━━━━

💰 الرصيد الحالي: *${balance:.2f}*
📊 حالة المحفظة: {wallet_status}

📈 *إحصائيات حسابك:*
📦 إجمالي الطلبات: *{orders_count}*
📅 عضو منذ: {join_date_str}
🆔 رقم الحساب: `{telegram_id}`

💡 *نصائح:*
• احتفظ برصيد كافٍ لطلباتك
• راقب عروضنا الخاصة لتوفير المال"""
        
        keyboard = [
            [InlineKeyboardButton("💳 شحن المحفظة", callback_data="topup_wallet")],
            [InlineKeyboardButton("📊 تفاصيل الإنفاق", callback_data="spending_details")],
            [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
        ]
        await send_user_message(telegram_id, wallet_text, InlineKeyboardMarkup(keyboard))
    else:
        error_text = "❌ خطأ في الوصول لبيانات المحفظة"
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main_menu")]
        ])
        await send_user_message(telegram_id, error_text, back_keyboard)

async def handle_topup_wallet(telegram_id: int):
    session = TelegramSession(telegram_id=telegram_id, state="wallet_topup_amount")
    await save_session(session)
    
    topup_text = """💳 *شحن المحفظة*

يرجى إدخال المبلغ الذي تريد شحنه (بالدولار):

مثال: 50"""
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="main_menu")]
    ])
    await send_user_message(telegram_id, topup_text, back_keyboard)

async def handle_order_history(telegram_id: int):
    orders = await db.orders.find({"telegram_id": telegram_id}).sort("order_date", -1).to_list(50)
    
    if not orders:
        no_orders_text = "📋 لا توجد طلبات سابقة"
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ])
        await send_user_message(telegram_id, no_orders_text, back_keyboard)
        return
    
    orders_text = "📋 *تاريخ طلباتك:*\n\n"
    keyboard = []
    
    for i, order in enumerate(orders[:10], 1):  # Show first 10 orders
        status_emoji = "✅" if order["status"] == "completed" else "⏳" if order["status"] == "pending" else "❌"
        orders_text += f"{i}. {status_emoji} {order['product_name']} - {order['category_name']}\n"
        orders_text += f"   💰 {order['price']:.2f} دولار - {order['order_date'].strftime('%Y-%m-%d')}\n\n"
        
        keyboard.append([InlineKeyboardButton(f"📋 طلب #{i}", callback_data=f"order_details_{order['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")])
    
    await send_user_message(telegram_id, orders_text, InlineKeyboardMarkup(keyboard))

async def handle_admin_message(message):
    telegram_id = message.chat_id
    text = message.text
    
    # فلترة: فقط الإيدي المحدد يمكنه استخدام بوت الإدارة
    if telegram_id not in ADMIN_IDS:
        unauthorized_message = """❌ *غير مصرح لك باستخدام بوت الإدارة*

هذا البوت مخصص للإدارة فقط.

إذا كنت تريد استخدام الخدمات، يرجى استخدام بوت المستخدمين."""
        await send_admin_message(telegram_id, unauthorized_message)
        return
    
    if text == "/start":
        await handle_admin_start(telegram_id)
    else:
        # Handle admin text input based on session state
        session = await get_session(telegram_id, is_admin=True)
        if session:
            await handle_admin_text_input(telegram_id, text, session)

async def handle_admin_callback(callback_query):
    telegram_id = callback_query.message.chat_id
    data = callback_query.data
    
    # فلترة: فقط الإداريين المحددين يمكنهم استخدام بوت الإدارة
    if telegram_id not in ADMIN_IDS:
        return
    
    if data == "admin_main_menu":
        keyboard = await create_admin_keyboard()
        await send_admin_message(telegram_id, "اختر العملية المطلوبة:", keyboard)
        await clear_session(telegram_id, is_admin=True)
    
    elif data == "manage_products":
        await handle_admin_manage_products(telegram_id)
    
    elif data == "manage_users":
        await handle_admin_manage_users(telegram_id)
    
    elif data == "view_users":
        await handle_admin_view_users(telegram_id)
    
    elif data == "ban_user":
        await handle_admin_ban_user(telegram_id)
    
    elif data == "unban_user":
        await handle_admin_unban_user(telegram_id)
    
    elif data == "edit_product":
        await handle_admin_edit_product(telegram_id)
    
    elif data == "delete_product":
        await handle_admin_delete_product(telegram_id)
    
    elif data == "manage_codes":
        await handle_admin_manage_codes(telegram_id)
    
    elif data.startswith("edit_product_"):
        product_id = data.replace("edit_product_", "")
        await handle_edit_product_selected(telegram_id, product_id)
    
    elif data.startswith("delete_product_"):
        product_id = data.replace("delete_product_", "")
        await handle_delete_product_confirm(telegram_id, product_id)
    
    elif data.startswith("confirm_delete_"):
        product_id = data.replace("confirm_delete_", "")
        await handle_product_delete_confirmed(telegram_id, product_id)
    
    elif data == "skip_product_name":
        await handle_skip_product_name(telegram_id)
    
    elif data == "reports":
        await handle_admin_reports(telegram_id)
    
    elif data == "manage_orders":
        await handle_admin_manage_orders(telegram_id)
    
    elif data == "add_product":
        await handle_admin_add_product(telegram_id)
    
    elif data == "add_user_balance":
        await handle_admin_add_user_balance(telegram_id)
    
    elif data == "add_category":
        await handle_admin_add_category(telegram_id)
    
    elif data.startswith("select_product_for_category_"):
        product_id = data.replace("select_product_for_category_", "")
        await handle_admin_select_product_for_category(telegram_id, product_id)
    
    elif data.startswith("delivery_"):
        delivery_type = data.replace("delivery_", "")
        await handle_admin_delivery_type_selection(telegram_id, delivery_type)
    
    elif data == "add_codes":
        await handle_admin_add_codes(telegram_id)
    
    elif data == "view_codes":
        await handle_admin_view_codes(telegram_id)
    
    elif data == "low_stock_alerts":
        await handle_admin_low_stock_alerts(telegram_id)
    
    elif data.startswith("add_codes_to_category_"):
        category_id = data.replace("add_codes_to_category_", "")
        await handle_admin_select_code_type(telegram_id, category_id)
    
    elif data.startswith("code_type_"):
        # Handle code type selection
        parts = data.split("_")
        code_type = parts[2]  # text, number, or dual
        category_id = parts[3]
        await handle_admin_code_type_selected(telegram_id, code_type, category_id)
    
    elif data.startswith("process_order_"):
        order_id = data.replace("process_order_", "")
        await handle_admin_process_order(telegram_id, order_id)
    
    elif data == "view_all_pending":
        await handle_admin_view_all_pending_orders(telegram_id)
    
    elif data == "orders_report":
        await handle_admin_orders_report(telegram_id)
    
    elif data == "admin_back_to_main":
        await handle_back_button(telegram_id, is_admin=True)

async def handle_admin_manage_products(telegram_id: int):
    keyboard = [
        [InlineKeyboardButton("➕ إضافة منتج جديد", callback_data="add_product")],
        [InlineKeyboardButton("📝 تعديل منتج", callback_data="edit_product")],
        [InlineKeyboardButton("🗑 حذف منتج", callback_data="delete_product")],
        [InlineKeyboardButton("📂 إضافة فئة", callback_data="add_category")],
        [InlineKeyboardButton("🔙 العودة", callback_data="admin_main_menu")]
    ]
    
    text = "📦 *إدارة المنتجات*\n\nاختر العملية المطلوبة:"
    await send_admin_message(telegram_id, text, InlineKeyboardMarkup(keyboard))

async def handle_admin_manage_users(telegram_id: int):
    users_count = await db.users.count_documents({})
    total_balance = await db.users.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]).to_list(1)
    
    total_bal = total_balance[0]["total"] if total_balance else 0
    
    users_text = f"""👥 *إحصائيات المستخدمين*

عدد المستخدمين: *{users_count}*
إجمالي الأرصدة: *{total_bal:.2f} دولار*"""
    
    keyboard = [
        [InlineKeyboardButton("💰 إضافة رصيد لمستخدم", callback_data="add_user_balance")],
        [InlineKeyboardButton("👁 عرض المستخدمين", callback_data="view_users")],
        [InlineKeyboardButton("🔙 العودة", callback_data="admin_main_menu")]
    ]
    
    await send_admin_message(telegram_id, users_text, InlineKeyboardMarkup(keyboard))

async def handle_admin_view_users(telegram_id: int):
    """عرض قائمة المستخدمين للإدارة"""
    try:
        # الحصول على أحدث 20 مستخدم
        users = await db.users.find().sort("join_date", -1).limit(20).to_list(20)
        
        if not users:
            await send_admin_message(telegram_id, "لا يوجد مستخدمون مسجلون بعد.")
            return
        
        users_text = "👥 *قائمة المستخدمين (آخر 20)*\n\n"
        
        for i, user in enumerate(users, 1):
            name = user.get('first_name', 'غير محدد')
            username = user.get('username', 'لا يوجد')
            balance = user.get('balance', 0)
            orders_count = user.get('orders_count', 0)
            telegram_id_user = user.get('telegram_id', 'غير محدد')
            is_banned = user.get('is_banned', False)
            ban_reason = user.get('ban_reason', '')
            
            # تنسيق تاريخ الانضمام
            join_date = user.get('join_date')
            if join_date:
                join_str = join_date.strftime('%Y-%m-%d')
            else:
                join_str = 'غير محدد'
            
            # إضافة حالة الحظر
            ban_status = "🚫 محظور" if is_banned else "✅ نشط"
            ban_info = f"\n🚫 السبب: {ban_reason}" if is_banned and ban_reason else ""
            
            users_text += f"""**{i}.** {name} {ban_status}
🆔 ID: `{telegram_id_user}`
👤 Username: @{username}
💰 الرصيد: ${balance:.2f}
📦 الطلبات: {orders_count}
📅 الانضمام: {join_str}{ban_info}
---
"""
        
        # إضافة ملاحظة عن النسخ
        users_text += "\n💡 اضغط على الإيدي لنسخه"
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث القائمة", callback_data="view_users")],
            [InlineKeyboardButton("💰 إضافة رصيد", callback_data="add_user_balance")],
            [
                InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user"),
                InlineKeyboardButton("✅ إلغاء الحظر", callback_data="unban_user")
            ],
            [InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data="manage_users")]
        ]
        
        await send_admin_message(telegram_id, users_text, InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        await send_admin_message(telegram_id, f"❌ خطأ في عرض المستخدمين: {str(e)}")
        logging.error(f"Error viewing users: {e}")

async def handle_admin_ban_user(telegram_id: int):
    """بدء عملية حظر مستخدم"""
    session = TelegramSession(telegram_id=telegram_id, state="ban_user_id")
    await save_session(session, is_admin=True)
    
    text = """🚫 *حظر مستخدم*

أدخل إيدي المستخدم المراد حظره (Telegram ID):

💡 يمكنك الحصول على الإيدي من قائمة المستخدمين"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="view_users")]
    ])
    
    await send_admin_message(telegram_id, text, keyboard)

async def handle_admin_unban_user(telegram_id: int):
    """بدء عملية إلغاء حظر مستخدم"""
    session = TelegramSession(telegram_id=telegram_id, state="unban_user_id")
    await save_session(session, is_admin=True)
    
    text = """✅ *إلغاء حظر مستخدم*

أدخل إيدي المستخدم المراد إلغاء حظره (Telegram ID):

💡 يمكنك الحصول على الإيدي من قائمة المستخدمين"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="view_users")]
    ])
    
    await send_admin_message(telegram_id, text, keyboard)

async def handle_admin_text_input(telegram_id: int, text: str, session: TelegramSession):
    if session.state == "add_product_name":
        session.data["name"] = text
        session.state = "add_product_description"
        await save_session(session, is_admin=True)
        
        await send_admin_message(telegram_id, "📝 أدخل وصف المنتج:")
    
    elif session.state == "add_product_description":
        session.data["description"] = text
        session.state = "add_product_terms"
        await save_session(session, is_admin=True)
        
        await send_admin_message(telegram_id, "📋 أدخل شروط المنتج:")
    
    elif session.state == "add_product_terms":
        session.data["terms"] = text
        
        # Create the product
        product = Product(
            name=session.data["name"],
            description=session.data["description"],
            terms=session.data["terms"]
        )
        
        await db.products.insert_one(product.dict())
        await clear_session(telegram_id, is_admin=True)
        
        success_text = f"✅ تم إضافة المنتج بنجاح!\n\n*اسم المنتج:* {product.name}"
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 العودة لإدارة المنتجات", callback_data="manage_products")]
        ])
        await send_admin_message(telegram_id, success_text, back_keyboard)
    
    elif session.state == "add_user_balance_id":
        try:
            user_telegram_id = int(text)
            user = await db.users.find_one({"telegram_id": user_telegram_id})
            if user:
                session.data["user_telegram_id"] = user_telegram_id
                session.state = "add_user_balance_amount"
                await save_session(session, is_admin=True)
                
                await send_admin_message(telegram_id, f"💰 أدخل المبلغ المراد إضافته للمستخدم {user.get('first_name', 'غير معروف')}:")
            else:
                await send_admin_message(telegram_id, "❌ المستخدم غير موجود. يرجى إدخال إيدي صحيح:")
        except ValueError:
            await send_admin_message(telegram_id, "❌ يرجى إدخال رقم صحيح:")
    
    # Category creation flow
    elif session.state == "add_category_name":
        session.data["category_name"] = text
        session.state = "add_category_description"
        await save_session(session, is_admin=True)
        
        await send_admin_message(telegram_id, f"2️⃣ أدخل وصف الفئة لـ *{text}*:")
    
    elif session.state == "add_category_description":
        session.data["category_description"] = text
        session.state = "add_category_type"
        await save_session(session, is_admin=True)
        
        await send_admin_message(telegram_id, "3️⃣ أدخل صنف الفئة (مثال: بطاقة هدايا، اشتراك رقمي، إلخ):")
    
    elif session.state == "add_category_type":
        session.data["category_type"] = text
        session.state = "add_category_delivery_type"
        await save_session(session, is_admin=True)
        
        # Show delivery type options
        delivery_keyboard = [
            [InlineKeyboardButton("🎫 كود تلقائي", callback_data="delivery_code")],
            [InlineKeyboardButton("📱 رقم هاتف", callback_data="delivery_phone")],
            [InlineKeyboardButton("📧 بريد إلكتروني", callback_data="delivery_email")],
            [InlineKeyboardButton("🆔 إيدي المستخدم", callback_data="delivery_id")],
            [InlineKeyboardButton("📝 طلب يدوي", callback_data="delivery_manual")]
        ]
        
        await send_admin_message(telegram_id, "4️⃣ اختر نوع التسليم:", InlineKeyboardMarkup(delivery_keyboard))
    
    elif session.state == "add_category_price":
        try:
            price = float(text)
            session.data["category_price"] = price
            session.state = "add_category_redemption"
            await save_session(session, is_admin=True)
            
            await send_admin_message(telegram_id, "6️⃣ أدخل طريقة الاسترداد (مثال: كود رقمي، بريد إلكتروني، إلخ):")
        except ValueError:
            await send_admin_message(telegram_id, "❌ يرجى إدخال رقم صحيح للسعر:")
    
    elif session.state == "add_category_redemption":
        session.data["redemption_method"] = text
        session.state = "add_category_terms"
        await save_session(session, is_admin=True)
        
        await send_admin_message(telegram_id, "7️⃣ أدخل شروط الفئة:")
    
    elif session.state == "add_category_terms":
        session.data["category_terms"] = text
        
        # Create the category
        category = Category(
            name=session.data["category_name"],
            description=session.data["category_description"],
            category_type=session.data["category_type"],
            delivery_type=session.data["delivery_type"],
            price=session.data["category_price"],
            redemption_method=session.data["redemption_method"],
            terms=session.data["category_terms"],
            product_id=session.data["product_id"]
        )
        
        await db.categories.insert_one(category.dict())
        await clear_session(telegram_id, is_admin=True)
        
        delivery_types = {
            "code": "🎫 كود تلقائي",
            "phone": "📱 رقم هاتف", 
            "email": "📧 بريد إلكتروني",
            "id": "🆔 إيدي المستخدم",
            "manual": "📝 طلب يدوي"
        }
        
        success_text = f"""✅ *تم إضافة الفئة بنجاح!*

📦 المنتج: *{session.data['product_name']}*
🏷️ اسم الفئة: *{category.name}*
🚚 نوع التسليم: *{delivery_types[category.delivery_type]}*
💰 السعر: *${category.price:.2f}*
🔄 طريقة الاسترداد: *{category.redemption_method}*

{"يمكنك الآن إضافة أكواد لهذه الفئة." if category.delivery_type == "code" else "هذه الفئة تتطلب تنفيذ يدوي للطلبات."}"""

        keyboard = []
        if category.delivery_type == "code":
            keyboard.append([InlineKeyboardButton("🎫 إضافة أكواد للفئة", callback_data="manage_codes")])
        
        keyboard.extend([
            [InlineKeyboardButton("📂 إضافة فئة أخرى", callback_data="add_category")],
            [InlineKeyboardButton("🔙 العودة لإدارة المنتجات", callback_data="manage_products")]
        ])
        
        await send_admin_message(telegram_id, success_text, InlineKeyboardMarkup(keyboard))
    
    # Handle codes input
    elif session.state == "add_codes_input":
        await handle_admin_codes_input(telegram_id, text, session)
    
    # Handle order processing input
    elif session.state == "process_order_input_code":
        await handle_admin_order_code_input(telegram_id, text, session)
    
    elif session.state == "add_user_balance_amount":
        try:
            amount = float(text)
            user_telegram_id = session.data["user_telegram_id"]
            
            # Update user balance
            await db.users.update_one(
                {"telegram_id": user_telegram_id},
                {"$inc": {"balance": amount}}
            )
            
            # Send notification to user
            await send_user_message(
                user_telegram_id,
                f"💰 تم شحن محفظتك بنجاح!\n\nالمبلغ المضاف: *{amount:.2f} دولار*"
            )
            
            await clear_session(telegram_id, is_admin=True)
            
            success_text = f"✅ تم إضافة {amount:.2f} دولار لحساب المستخدم {user_telegram_id}"
            back_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data="manage_users")]
            ])
            await send_admin_message(telegram_id, success_text, back_keyboard)
            
        except ValueError:
            await send_admin_message(telegram_id, "❌ يرجى إدخال رقم صحيح:")
    
    # Handle ban user flow
    elif session.state == "ban_user_id":
        try:
            user_telegram_id = int(text)
            
            # Check if user exists
            user = await db.users.find_one({"telegram_id": user_telegram_id})
            if not user:
                await send_admin_message(telegram_id, "❌ لا يوجد مستخدم بهذا الإيدي")
                return
            
            if user.get('is_banned', False):
                await send_admin_message(telegram_id, "⚠️ هذا المستخدم محظور بالفعل")
                return
            
            # Store user ID and ask for ban reason
            session.data["ban_user_telegram_id"] = user_telegram_id
            session.data["ban_user_name"] = user.get('first_name', 'غير محدد')
            session.state = "ban_user_reason"
            await save_session(session, is_admin=True)
            
            await send_admin_message(telegram_id, f"🚫 *حظر المستخدم*\n\nالمستخدم: {user.get('first_name', 'غير محدد')}\nالإيدي: `{user_telegram_id}`\n\nأدخل سبب الحظر:")
            
        except ValueError:
            await send_admin_message(telegram_id, "❌ يرجى إدخال إيدي صحيح (أرقام فقط)")
    
    # Handle product editing flow
    elif session.state == "edit_product_name":
        new_name = text.strip()
        if new_name.lower() not in ["تخطي", "skip"]:
            session.data["new_name"] = new_name
        
        session.state = "edit_product_description"
        await save_session(session, is_admin=True)
        
        product = session.data["product"]
        await send_admin_message(telegram_id, f"""📝 *تعديل وصف المنتج*

📄 الوصف الحالي: {product.get('description', 'غير محدد')}

أدخل الوصف الجديد أو اكتب "تخطي" للإبقاء على الوصف الحالي:""")
    
    elif session.state == "edit_product_description":
        new_description = text.strip()
        if new_description.lower() not in ["تخطي", "skip"]:
            session.data["new_description"] = new_description
        
        session.state = "edit_product_terms"
        await save_session(session, is_admin=True)
        
        product = session.data["product"]
        await send_admin_message(telegram_id, f"""📝 *تعديل شروط المنتج*

📋 الشروط الحالية: {product.get('terms', 'غير محدد')}

أدخل الشروط الجديدة أو اكتب "تخطي" للإبقاء على الشروط الحالية:""")
    
    elif session.state == "edit_product_terms":
        new_terms = text.strip()
        if new_terms.lower() not in ["تخطي", "skip"]:
            session.data["new_terms"] = new_terms
        
        # Apply changes
        await apply_product_changes(telegram_id, session)

async def handle_admin_edit_product(telegram_id: int):
    """بدء عملية تعديل منتج"""
    # عرض قائمة المنتجات للاختيار
    products = await db.products.find({"is_active": True}).to_list(20)
    
    if not products:
        await send_admin_message(telegram_id, "❌ لا توجد منتجات متاحة للتعديل")
        return
    
    products_text = "📝 *تعديل منتج*\n\nاختر المنتج المراد تعديله:\n\n"
    keyboard = []
    
    for i, product in enumerate(products, 1):
        products_text += f"{i}. {product['name']}\n"
        keyboard.append([InlineKeyboardButton(f"{i}. {product['name']}", 
                                            callback_data=f"edit_product_{product['id']}")])
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="manage_products")])
    
    await send_admin_message(telegram_id, products_text, InlineKeyboardMarkup(keyboard))

async def handle_admin_delete_product(telegram_id: int):
    """بدء عملية حذف منتج"""
    # عرض قائمة المنتجات للاختيار
    products = await db.products.find({"is_active": True}).to_list(20)
    
    if not products:
        await send_admin_message(telegram_id, "❌ لا توجد منتجات متاحة للحذف")
        return
    
    products_text = "🗑 *حذف منتج*\n\n⚠️ تحذير: حذف المنتج سيؤثر على جميع الفئات المرتبطة به\n\nاختر المنتج المراد حذفه:\n\n"
    keyboard = []
    
    for i, product in enumerate(products, 1):
        products_text += f"{i}. {product['name']}\n"
        keyboard.append([InlineKeyboardButton(f"🗑 {product['name']}", 
                                            callback_data=f"delete_product_{product['id']}")])
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="manage_products")])
    
    await send_admin_message(telegram_id, products_text, InlineKeyboardMarkup(keyboard))

async def handle_edit_product_selected(telegram_id: int, product_id: str):
    """معالجة اختيار منتج للتعديل"""
    # البحث عن المنتج
    product = await db.products.find_one({"id": product_id})
    if not product:
        await send_admin_message(telegram_id, "❌ المنتج غير موجود")
        return
    
    # إنشاء جلسة للتعديل
    session = TelegramSession(
        telegram_id=telegram_id,
        state="edit_product_name",
        data={"product_id": product_id, "product": product}
    )
    await save_session(session, is_admin=True)
    
    edit_text = f"""📝 *تعديل المنتج*

📦 المنتج الحالي: **{product['name']}**
📄 الوصف الحالي: {product.get('description', 'غير محدد')}
📋 الشروط الحالية: {product.get('terms', 'غير محدد')}

أدخل الاسم الجديد للمنتج أو اكتب "تخطي" للإبقاء على الاسم الحالي:"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ تخطي الاسم", callback_data="skip_product_name")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="manage_products")]
    ])
    
    await send_admin_message(telegram_id, edit_text, keyboard)

async def handle_delete_product_confirm(telegram_id: int, product_id: str):
    """تأكيد حذف المنتج"""
    # البحث عن المنتج
    product = await db.products.find_one({"id": product_id})
    if not product:
        await send_admin_message(telegram_id, "❌ المنتج غير موجود")
        return
    
    # البحث عن الفئات المرتبطة
    categories_count = await db.categories.count_documents({"product_id": product_id})
    
    confirm_text = f"""🗑 *تأكيد حذف المنتج*

📦 المنتج: **{product['name']}**
📊 عدد الفئات المرتبطة: {categories_count}

⚠️ **تحذير:** 
• سيتم حذف المنتج نهائياً
• سيتم إخفاء جميع الفئات المرتبطة ({categories_count} فئة)
• لن يتمكن المستخدمون من شراء هذا المنتج

هل أنت متأكد من الحذف؟"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأكيد الحذف", callback_data=f"confirm_delete_{product_id}"),
            InlineKeyboardButton("❌ إلغاء", callback_data="delete_product")
        ]
    ])
    
    await send_admin_message(telegram_id, confirm_text, keyboard)

async def handle_product_delete_confirmed(telegram_id: int, product_id: str):
    """تنفيذ حذف المنتج"""
    try:
        # حذف المنتج (تغيير حالته إلى غير نشط)
        result = await db.products.update_one(
            {"id": product_id},
            {"$set": {"is_active": False}}
        )
        
        if result.modified_count == 0:
            await send_admin_message(telegram_id, "❌ فشل في حذف المنتج")
            return
        
        # إخفاء الفئات المرتبطة (تغيير حالتها إلى غير نشطة)
        categories_result = await db.categories.update_many(
            {"product_id": product_id},
            {"$set": {"is_active": False}}
        )
        
        success_text = f"""✅ *تم حذف المنتج بنجاح*

📦 تم إخفاء المنتج من النظام
📊 تم إخفاء {categories_result.modified_count} فئة مرتبطة

💡 ملاحظة: يمكن استعادة المنتج من قاعدة البيانات لاحقاً إذا لزم الأمر"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 العودة لإدارة المنتجات", callback_data="manage_products")]
        ])
        
        await send_admin_message(telegram_id, success_text, keyboard)
        
    except Exception as e:
        await send_admin_message(telegram_id, f"❌ خطأ في حذف المنتج: {str(e)}")
        logging.error(f"Error deleting product: {e}")

async def handle_skip_product_name(telegram_id: int):
    """تخطي اسم المنتج"""
    session = await get_session(telegram_id, is_admin=True)
    if not session:
        return
    
    session.state = "edit_product_description"
    await save_session(session, is_admin=True)
    
    product = session.data["product"]
    await send_admin_message(telegram_id, f"""📝 *تعديل وصف المنتج*

📄 الوصف الحالي: {product.get('description', 'غير محدد')}

أدخل الوصف الجديد أو اكتب "تخطي" للإبقاء على الوصف الحالي:""")

async def apply_product_changes(telegram_id: int, session):
    """تطبيق التغييرات على المنتج"""
    try:
        product_id = session.data["product_id"]
        product = session.data["product"]
        
        # إعداد التحديثات
        updates = {}
        changes_text = "📝 *تم تحديث المنتج بنجاح*\n\n"
        
        if "new_name" in session.data:
            updates["name"] = session.data["new_name"]
            changes_text += f"📦 الاسم: {product['name']} ← {session.data['new_name']}\n"
        
        if "new_description" in session.data:
            updates["description"] = session.data["new_description"]
            changes_text += f"📄 الوصف: محدث\n"
        
        if "new_terms" in session.data:
            updates["terms"] = session.data["new_terms"]
            changes_text += f"📋 الشروط: محدثة\n"
        
        if updates:
            # تطبيق التحديثات
            await db.products.update_one(
                {"id": product_id},
                {"$set": updates}
            )
            
            changes_text += f"\n✅ تم حفظ جميع التغييرات بنجاح"
        else:
            changes_text = "ℹ️ لم يتم إجراء أي تغييرات على المنتج"
        
        await clear_session(telegram_id, is_admin=True)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 العودة لإدارة المنتجات", callback_data="manage_products")]
        ])
        
        await send_admin_message(telegram_id, changes_text, keyboard)
        
    except Exception as e:
        await send_admin_message(telegram_id, f"❌ خطأ في تحديث المنتج: {str(e)}")
        logging.error(f"Error updating product: {e}")

async def handle_admin_manage_codes(telegram_id: int):
    # Get categories that use codes
    code_categories = await db.categories.find({"delivery_type": "code"}).to_list(100)
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة أكواد", callback_data="add_codes")],
        [InlineKeyboardButton("👁 عرض الأكواد", callback_data="view_codes")],
        [InlineKeyboardButton("🗑 حذف كود", callback_data="delete_code")],
        [InlineKeyboardButton("⚠️ تحذيرات النقص", callback_data="low_stock_alerts")]
    ]
    
    # Show low stock warnings
    warnings = []
    for category in code_categories:
        available_codes = await db.codes.count_documents({
            "category_id": category["id"],
            "is_used": False
        })
        if available_codes <= 5:
            warnings.append(f"⚠️ {category['name']}: {available_codes} أكواد متبقية")
    
    text = "🎫 *إدارة الأكواد*\n\n"
    if warnings:
        text += "🚨 *تحذيرات النقص:*\n" + "\n".join(warnings[:3]) + "\n\n"
    
    text += "اختر العملية المطلوبة:"
    
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="admin_main_menu")])
    await send_admin_message(telegram_id, text, InlineKeyboardMarkup(keyboard))

async def handle_admin_reports(telegram_id: int):
    # Get statistics
    total_users = await db.users.count_documents({})
    total_orders = await db.orders.count_documents({})
    completed_orders = await db.orders.count_documents({"status": "completed"})
    pending_orders = await db.orders.count_documents({"status": "pending"})
    
    # Calculate revenue
    revenue_result = await db.orders.aggregate([
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$price"}}}
    ]).to_list(1)
    
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Get today's orders
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = await db.orders.count_documents({
        "order_date": {"$gte": today}
    })
    
    report_text = f"""📊 *تقرير شامل - Abod Card*

📈 *الإحصائيات العامة:*
• إجمالي المستخدمين: *{total_users}*
• إجمالي الطلبات: *{total_orders}*
• الطلبات المكتملة: *{completed_orders}*
• الطلبات قيد التنفيذ: *{pending_orders}*

💰 *الإحصائيات المالية:*
• إجمالي الإيرادات: *${total_revenue:.2f}*
• متوسط قيمة الطلب: *${total_revenue/completed_orders if completed_orders > 0 else 0:.2f}*

📅 *إحصائيات اليوم:*
• طلبات اليوم: *{today_orders}*

تم إنتاج التقرير في: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"""
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 العودة", callback_data="admin_main_menu")]
    ])
    await send_admin_message(telegram_id, report_text, back_keyboard)

async def handle_admin_manage_orders(telegram_id: int):
    pending_orders = await db.orders.find({"status": "pending"}).to_list(50)
    completed_orders_count = await db.orders.count_documents({"status": "completed"})
    
    orders_text = f"""📋 *إدارة الطلبات*

الطلبات قيد التنفيذ: *{len(pending_orders)}*
الطلبات المكتملة: *{completed_orders_count}*

"""
    
    keyboard = []
    
    if pending_orders:
        orders_text += "*الطلبات قيد التنفيذ:*\n"
        for i, order in enumerate(pending_orders[:5], 1):  # Show first 5 pending orders
            orders_text += f"{i}. {order['product_name']} - ${order['price']:.2f}\n"
            orders_text += f"   👤 المستخدم: {order['telegram_id']}\n"
            keyboard.append([InlineKeyboardButton(f"⚡ تنفيذ طلب #{i}", callback_data=f"process_order_{order['id']}")])
        
        keyboard.append([InlineKeyboardButton("👁 عرض جميع الطلبات المعلقة", callback_data="view_all_pending")])
    else:
        orders_text += "✅ لا توجد طلبات قيد التنفيذ حالياً"
    
    keyboard.append([InlineKeyboardButton("📊 عرض تقرير الطلبات", callback_data="orders_report")])
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="admin_main_menu")])
    
    await send_admin_message(telegram_id, orders_text, InlineKeyboardMarkup(keyboard))

async def handle_admin_add_product(telegram_id: int):
    session = TelegramSession(telegram_id=telegram_id, state="add_product_name")
    await save_session(session, is_admin=True)
    
    text = "📦 *إضافة منتج جديد*\n\nأدخل اسم المنتج:"
    
    cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="manage_products")]
    ])
    await send_admin_message(telegram_id, text, cancel_keyboard)

async def handle_admin_add_user_balance(telegram_id: int):
    session = TelegramSession(telegram_id=telegram_id, state="add_user_balance_id")
    await save_session(session, is_admin=True)
    
    text = "💰 *إضافة رصيد لمستخدم*\n\nأدخل إيدي المستخدم (Telegram ID):"
    
    cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="manage_users")]
    ])
    await send_admin_message(telegram_id, text, cancel_keyboard)

async def handle_admin_add_category(telegram_id: int):
    # Get available products first
    products = await db.products.find({"is_active": True}).to_list(100)
    
    if not products:
        no_products_text = "❌ لا توجد منتجات متاحة. يجب إضافة منتج أولاً قبل إضافة الفئات."
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ إضافة منتج جديد", callback_data="add_product")],
            [InlineKeyboardButton("🔙 العودة", callback_data="manage_products")]
        ])
        await send_admin_message(telegram_id, no_products_text, back_keyboard)
        return
    
    # Show products to select from
    text = "📂 *إضافة فئة جديدة*\n\nاختر المنتج الذي تريد إضافة فئة له:"
    
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(
            product['name'], 
            callback_data=f"select_product_for_category_{product['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="manage_products")])
    
    await send_admin_message(telegram_id, text, InlineKeyboardMarkup(keyboard))

async def handle_user_product_selection(telegram_id: int, product_id: str):
    # Get product details
    product = await db.products.find_one({"id": product_id})
    if not product:
        await send_user_message(telegram_id, "❌ المنتج غير موجود")
        return
    
    # Get categories for this product
    categories = await db.categories.find({"product_id": product_id}).to_list(100)
    
    if not categories:
        no_categories_text = f"❌ لا توجد فئات متاحة للمنتج *{product['name']}*"
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 العودة للمنتجات", callback_data="browse_products")]
        ])
        await send_user_message(telegram_id, no_categories_text, back_keyboard)
        return
    
    product_text = f"""📦 *{product['name']}*

📝 الوصف: {product['description']}

📋 الشروط: {product['terms']}

*الفئات المتاحة:*"""
    
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(
            f"{category['name']} - ${category['price']:.2f}",
            callback_data=f"category_{category['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 العودة للمنتجات", callback_data="browse_products")])
    
    await send_user_message(telegram_id, product_text, InlineKeyboardMarkup(keyboard))

async def handle_user_category_selection(telegram_id: int, category_id: str):
    # Get category details
    category = await db.categories.find_one({"id": category_id})
    if not category:
        await send_user_message(telegram_id, "❌ الفئة غير موجودة")
        return
    
    # Get user balance
    user = await db.users.find_one({"telegram_id": telegram_id})
    if not user:
        await send_user_message(telegram_id, "❌ خطأ في بيانات المستخدم")
        return
    
    category_text = f"""🏷️ *{category['name']}*

📝 الوصف: {category['description']}
🏷️ النوع: {category['category_type']}
💰 السعر: *${category['price']:.2f}*
🔄 طريقة الاسترداد: {category['redemption_method']}

📋 *الشروط:*
{category['terms']}

💳 رصيدك الحالي: *${user['balance']:.2f}*"""
    
    keyboard = []
    
    if user['balance'] >= category['price']:
        keyboard.append([InlineKeyboardButton(
            f"🛒 شراء بـ ${category['price']:.2f}",
            callback_data=f"buy_category_{category_id}"
        )])
    else:
        keyboard.append([InlineKeyboardButton("❌ رصيد غير كافي", callback_data="topup_wallet")])
    
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data=f"product_{category['product_id']}")])
    
    await send_user_message(telegram_id, category_text, InlineKeyboardMarkup(keyboard))

async def handle_user_purchase(telegram_id: int, category_id: str):
    # Get category and user info
    category = await db.categories.find_one({"id": category_id})
    user = await db.users.find_one({"telegram_id": telegram_id})
    product = await db.products.find_one({"id": category["product_id"]})
    
    if not all([category, user, product]):
        await send_user_message(telegram_id, "❌ خطأ في البيانات")
        return
    
    # Check balance
    if user['balance'] < category['price']:
        await send_user_message(telegram_id, "❌ رصيد غير كافي")
        return
    
    delivery_type = category['delivery_type']
    
    # Handle different delivery types
    if delivery_type == "code":
        await handle_code_purchase(telegram_id, category, user, product)
    elif delivery_type in ["phone", "email", "id"]:
        await handle_manual_input_purchase(telegram_id, category, user, product, delivery_type)
    else:  # manual
        await handle_manual_purchase(telegram_id, category, user, product)

async def handle_code_purchase(telegram_id: int, category: dict, user: dict, product: dict):
    # Check for available codes
    available_code = await db.codes.find_one({
        "category_id": category["id"],
        "is_used": False
    })
    
    # Create order
    order = Order(
        user_id=user['id'],
        telegram_id=telegram_id,
        product_name=product['name'],
        category_name=category['name'],
        category_id=category['id'],
        delivery_type=category['delivery_type'],
        price=category['price'],
        status="completed" if available_code else "pending"
    )
    
    # Deduct balance and update user
    await db.users.update_one(
        {"telegram_id": telegram_id},
        {"$inc": {"balance": -category['price'], "orders_count": 1}}
    )
    
    if available_code:
        # Mark code as used
        await db.codes.update_one(
            {"id": available_code['id']},
            {
                "$set": {
                    "is_used": True,
                    "used_by": user['id'],
                    "used_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Add code to order
        order.code_sent = available_code['code']
        order.completion_date = datetime.now(timezone.utc)
        
        # Send code to user
        code_display = available_code['code']
        if available_code.get('serial_number'):
            code_display += f"\nالسيريال: {available_code['serial_number']}"
        
        success_text = f"""✅ *تم الشراء بنجاح!*

📦 المنتج: *{product['name']}*
🏷️ الفئة: *{category['name']}*
💰 السعر: *${category['price']:.2f}*

🎫 *نتيجة الطلب Order Answer:*
`{code_display}`

📋 *الشروط:*
{available_code['terms']}

📝 *الوصف:*
{available_code['description']}

🔄 *طريقة الاسترداد:*
{category['redemption_method']}

شكراً لك لاستخدام خدماتنا! 🎉

للدعم الفني: @AbodStoreVIP"""

        # Notify admin about successful order
        await notify_admin_new_order(
            product['name'],
            category['name'], 
            telegram_id,
            category['price'],
            code_display,
            "completed"
        )
    else:
        # No codes available - manual processing needed
        success_text = f"""⏳ *تم استلام طلبك!*

📦 المنتج: *{product['name']}*
🏷️ الفئة: *{category['name']}*
💰 السعر: *${category['price']:.2f}*

⚠️ الأكواد نفدت مؤقتاً. سيتم تنفيذ طلبك يدوياً خلال 10-30 دقيقة.
سيصلك إشعار فور توفر الكود."""
        
        # Notify admin about stock shortage
        await notify_admin_for_codeless_order(
            product['name'], 
            category['name'], 
            telegram_id, 
            category['price']
        )
    
    # Save order
    await db.orders.insert_one(order.dict())
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 عرض طلباتي", callback_data="order_history")],
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
    ])
    
    await send_user_message(telegram_id, success_text, back_keyboard)

async def handle_manual_input_purchase(telegram_id: int, category: dict, user: dict, product: dict, delivery_type: str):
    # Start session to get user input
    session = TelegramSession(
        telegram_id=telegram_id, 
        state=f"purchase_input_{delivery_type}",
        data={
            "category_id": category["id"],
            "product_name": product["name"],
            "category_name": category["name"],
            "price": category["price"]
        }
    )
    await save_session(session)
    
    if delivery_type == "phone":
        input_text = "📱 أدخل رقم هاتفك:"
    elif delivery_type == "email":
        input_text = "📧 أدخل بريدك الإلكتروني:"
    else:  # id
        input_text = "🆔 أدخل إيدي الحساب المطلوب الشحن إليه:"
    
    await send_user_message(telegram_id, f"""📝 *معلومات إضافية مطلوبة*

📦 المنتج: *{product['name']}*
🏷️ الفئة: *{category['name']}*
💰 السعر: *${category['price']:.2f}*

{input_text}""")

async def handle_manual_purchase(telegram_id: int, category: dict, user: dict, product: dict):
    # Create order directly as pending
    order = Order(
        user_id=user['id'],
        telegram_id=telegram_id,
        product_name=product['name'],
        category_name=category['name'],
        category_id=category['id'],
        delivery_type=category['delivery_type'],
        price=category['price'],
        status="pending"
    )
    
    # Deduct balance and update user
    await db.users.update_one(
        {"telegram_id": telegram_id},
        {"$inc": {"balance": -category['price'], "orders_count": 1}}
    )
    
    # Save order
    await db.orders.insert_one(order.dict())
    
    success_text = f"""⏳ *تم استلام طلبك!*

📦 المنتج: *{product['name']}*
🏷️ الفئة: *{category['name']}*
💰 السعر: *${category['price']:.2f}*

سيتم تنفيذ طلبك يدوياً خلال 10-30 دقيقة.
سيصلك إشعار فور التنفيذ."""
    
    # Notify admin about manual order
    await notify_admin_new_order(
        product['name'],
        category['name'],
        telegram_id,
        category['price'],
        None,
        "pending"
    )
    
    # Notify admin
    admin_message = f"""📋 *طلب يدوي جديد*

📦 المنتج: *{product['name']}*
🏷️ الفئة: *{category['name']}*
👤 المستخدم: {telegram_id}
💰 السعر: ${category['price']:.2f}
📝 النوع: طلب يدوي

للوصول لإدارة الطلبات: /start ثم اختر "📋 الطلبات" """
    
    try:
        await send_admin_message(ADMIN_ID, admin_message)
    except Exception as e:
        logging.error(f"Failed to notify admin: {e}")
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 عرض طلباتي", callback_data="order_history")],
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
    ])
    
    await send_user_message(telegram_id, success_text, back_keyboard)

async def handle_user_order_details(telegram_id: int, order_id: str):
    order = await db.orders.find_one({"id": order_id, "telegram_id": telegram_id})
    if not order:
        await send_user_message(telegram_id, "❌ الطلب غير موجود")
        return
    
    status_text = "✅ مكتمل" if order['status'] == 'completed' else "⏳ قيد التنفيذ" if order['status'] == 'pending' else "❌ فاشل"
    
    order_text = f"""📋 *تفاصيل الطلب*

📦 المنتج: *{order['product_name']}*
🏷️ الفئة: *{order['category_name']}*
💰 السعر: *${order['price']:.2f}*
📅 تاريخ الطلب: {order['order_date'].strftime('%Y-%m-%d %H:%M')}
🔄 الحالة: {status_text}

"""
    
    if order['code_sent']:
        order_text += f"""🎫 *الكود:*
`{order['code_sent']}`

يمكنك نسخ الكود أعلاه واستخدامه."""
    else:
        order_text += "⏳ الكود لم يتم إرساله بعد. سيصلك إشعار فور توفره."
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 العودة لتاريخ الطلبات", callback_data="order_history")]
    ])
    
    await send_user_message(telegram_id, order_text, back_keyboard)

async def handle_user_phone_input(telegram_id: int, text: str, session: TelegramSession):
    """Handle phone number input from user during purchase"""
    # Validate phone number (basic validation)
    phone = text.strip()
    if len(phone) < 8 or not any(char.isdigit() for char in phone):
        await send_user_message(telegram_id, "❌ يرجى إدخال رقم هاتف صحيح")
        return
    
    # Complete the purchase with phone number
    await complete_manual_purchase(telegram_id, session, phone)

async def handle_user_email_input(telegram_id: int, text: str, session: TelegramSession):
    """Handle email input from user during purchase"""
    # Validate email (basic validation)
    email = text.strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        await send_user_message(telegram_id, "❌ يرجى إدخال بريد إلكتروني صحيح")
        return
    
    # Complete the purchase with email
    await complete_manual_purchase(telegram_id, session, email)

async def handle_user_id_input(telegram_id: int, text: str, session: TelegramSession):
    """Handle ID input from user during purchase"""
    # Validate ID (basic validation - should be numeric or alphanumeric)
    user_id = text.strip()
    if len(user_id) < 3:
        await send_user_message(telegram_id, "❌ يرجى إدخال إيدي صحيح (يجب أن يكون أكثر من 3 أحرف/أرقام)")
        return
    
    # Complete the purchase with user ID
    await complete_manual_purchase(telegram_id, session, user_id)

async def complete_manual_purchase(telegram_id: int, session: TelegramSession, user_input: str):
    """Complete purchase that requires manual processing with user input"""
    category_id = session.data["category_id"]
    product_name = session.data["product_name"]
    category_name = session.data["category_name"]
    price = session.data["price"]
    
    # Get user info
    user = await db.users.find_one({"telegram_id": telegram_id})
    if not user:
        await send_user_message(telegram_id, "❌ خطأ في بيانات المستخدم")
        return
    
    # Check balance again
    if user['balance'] < price:
        await send_user_message(telegram_id, "❌ رصيد غير كافي")
        return
    
    # Create order
    order = Order(
        user_id=user['id'],
        telegram_id=telegram_id,
        product_name=product_name,
        category_name=category_name,
        category_id=category_id,
        delivery_type=session.state.replace("purchase_input_", ""),
        price=price,
        status="pending",
        user_input_data=user_input
    )
    
    # Deduct balance and update user
    await db.users.update_one(
        {"telegram_id": telegram_id},
        {"$inc": {"balance": -price, "orders_count": 1}}
    )
    
    # Save order
    await db.orders.insert_one(order.dict())
    
    # Clear session
    await clear_session(telegram_id)
    
    # Send confirmation to user
    if session.state == "purchase_input_phone":
        input_type = "الهاتف"
    elif session.state == "purchase_input_email":
        input_type = "البريد الإلكتروني"
    else:  # purchase_input_id
        input_type = "إيدي الحساب"
        
    success_text = f"""✅ *تم استلام طلبك بنجاح!*

📦 المنتج: *{product_name}*
🏷️ الفئة: *{category_name}*
💰 السعر: *${price:.2f}*
📝 {input_type}: `{user_input}`

⏳ سيتم تنفيذ طلبك خلال 10-30 دقيقة وإرسال التفاصيل إليك.

شكراً لك لاستخدام خدماتنا! 🎉

للدعم الفني: @AbodStoreVIP"""
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 عرض طلباتي", callback_data="order_history")],
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
    ])
    
    await send_user_message(telegram_id, success_text, back_keyboard)
    
    # Notify admin about the new order
    admin_notification = f"""📋 *طلب جديد يتطلب تنفيذ يدوي*

📦 المنتج: {product_name}
🏷️ الفئة: {category_name}
👤 المستخدم: {telegram_id}
💰 السعر: ${price:.2f}
📝 {input_type}: {user_input}

يرجى تنفيذ الطلب وإرسال التفاصيل للمستخدم.

للوصول لإدارة الطلبات: /start ثم اختر "📋 الطلبات" """
    
    # Note: This should be sent to actual admin telegram ID
    # For now, we'll log it or you can replace with actual admin ID
    try:
        # Send to the correct admin ID
        await send_admin_message(ADMIN_ID, admin_notification)
    except Exception as e:
        logging.error(f"Failed to notify admin: {e}")

async def handle_admin_codes_input(telegram_id: int, text: str, session: TelegramSession):
    """Handle codes input from admin"""
    category_id = session.data["category_id"]
    category_name = session.data["category_name"]
    code_type = session.data["code_type"]
    
    # Parse codes from input
    codes_text = text.strip()
    if not codes_text:
        await send_admin_message(telegram_id, "❌ يرجى إدخال الأكواد")
        return
    
    # Split by lines for multiple codes
    code_lines = [line.strip() for line in codes_text.split('\n') if line.strip()]
    
    codes_added = 0
    errors = []
    
    for line in code_lines:
        try:
            if code_type == "dual":
                # Handle dual codes (code|serial)
                if '|' not in line:
                    errors.append(f"خطأ في التنسيق: {line} - يجب استخدام | للفصل")
                    continue
                
                code_part, serial_part = line.split('|', 1)
                code_part = code_part.strip()
                serial_part = serial_part.strip()
                
                if not code_part or not serial_part:
                    errors.append(f"كود أو سيريال فارغ: {line}")
                    continue
                    
            else:
                code_part = line
                serial_part = None
            
            # Check if code already exists
            existing_code = await db.codes.find_one({"code": code_part, "category_id": category_id})
            if existing_code:
                errors.append(f"الكود موجود مسبقاً: {code_part}")
                continue
            
            # Create new code
            new_code = Code(
                code=code_part,
                description=f"كود {code_type}",
                terms="يرجى اتباع شروط الاستخدام",
                category_id=category_id,
                code_type=code_type,
                serial_number=serial_part if code_type == "dual" else None
            )
            
            # Save to database
            await db.codes.insert_one(new_code.dict())
            codes_added += 1
            
        except Exception as e:
            errors.append(f"خطأ في معالجة: {line} - {str(e)}")
    
    # Clear session
    await clear_session(telegram_id, is_admin=True)
    
    # Prepare result message
    result_text = f"✅ *تم إضافة {codes_added} كود للفئة: {category_name}*\n\n"
    
    if errors:
        result_text += f"⚠️ *أخطاء ({len(errors)}):*\n"
        for error in errors[:5]:  # Show first 5 errors
            result_text += f"• {error}\n"
        if len(errors) > 5:
            result_text += f"• ... و {len(errors) - 5} أخطاء أخرى\n"
    
    result_text += f"\n📊 إجمالي الأكواد المضافة: *{codes_added}*"
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة أكواد أخرى", callback_data="add_codes")],
        [InlineKeyboardButton("👁 عرض الأكواد", callback_data="view_codes")],
        [InlineKeyboardButton("🔙 العودة لإدارة الأكواد", callback_data="manage_codes")]
    ]
    
    await send_admin_message(telegram_id, result_text, InlineKeyboardMarkup(keyboard))

async def handle_admin_process_order(telegram_id: int, order_id: str):
    """معالجة طلب معلق من الإدارة"""
    order = await db.orders.find_one({"id": order_id, "status": "pending"})
    if not order:
        await send_admin_message(telegram_id, "❌ الطلب غير موجود أو تم تنفيذه مسبقاً")
        return
    
    # بدء جلسة تنفيذ الطلب
    session = TelegramSession(
        telegram_id=telegram_id,
        state="process_order_input_code",
        data={
            "order_id": order_id,
            "user_telegram_id": order["telegram_id"],
            "product_name": order["product_name"],
            "category_name": order["category_name"],
            "delivery_type": order["delivery_type"]
        }
    )
    await save_session(session, is_admin=True)
    
    # إظهار تفاصيل الطلب وطلب الكود
    delivery_type_names = {
        "code": "🎫 نفدت الأكواد",
        "phone": "📱 رقم هاتف",
        "email": "📧 بريد إلكتروني", 
        "manual": "📝 طلب يدوي"
    }
    
    user_input_info = ""
    if order.get("user_input_data"):
        input_type = "📱 الهاتف" if order["delivery_type"] == "phone" else "📧 البريد الإلكتروني"
        user_input_info = f"\n{input_type}: `{order['user_input_data']}`"
    
    order_details = f"""⚡ *تنفيذ طلب معلق*

📦 المنتج: *{order['product_name']}*
🏷️ الفئة: *{order['category_name']}*
💰 السعر: *${order['price']:.2f}*
🚚 النوع: {delivery_type_names.get(order['delivery_type'], 'غير محدد')}
👤 المستخدم: {order['telegram_id']}{user_input_info}
📅 تاريخ الطلب: {order['order_date'].strftime('%Y-%m-%d %H:%M')}

📝 أدخل الكود أو المعلومات المراد إرسالها للمستخدم:"""
    
    cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="manage_orders")]
    ])
    
    await send_admin_message(telegram_id, order_details, cancel_keyboard)

async def handle_admin_view_all_pending_orders(telegram_id: int):
    """عرض جميع الطلبات المعلقة"""
    pending_orders = await db.orders.find({"status": "pending"}).sort("order_date", 1).to_list(50)
    
    if not pending_orders:
        text = "✅ *لا توجد طلبات معلقة*\n\nجميع الطلبات تم تنفيذها بنجاح!"
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 العودة لإدارة الطلبات", callback_data="manage_orders")]
        ])
        await send_admin_message(telegram_id, text, back_keyboard)
        return
    
    text = f"📋 *جميع الطلبات المعلقة ({len(pending_orders)})*\n\n"
    keyboard = []
    
    delivery_type_icons = {
        "code": "🎫",
        "phone": "📱", 
        "email": "📧",
        "id": "🆔",
        "manual": "📝"
    }
    
    for i, order in enumerate(pending_orders[:10], 1):  # أول 10 طلبات
        time_diff = datetime.now(timezone.utc) - order["order_date"]
        hours_ago = int(time_diff.total_seconds() / 3600)
        
        status_emoji = "🔴" if hours_ago > 24 else "🟡" if hours_ago > 6 else "🟢"
        icon = delivery_type_icons.get(order["delivery_type"], "📄")
        
        text += f"{status_emoji} {i}. {icon} *{order['product_name']}*\n"
        text += f"   💰 ${order['price']:.2f} - {hours_ago}س مضت\n\n"
        
        keyboard.append([InlineKeyboardButton(
            f"⚡ تنفيذ طلب #{i}",
            callback_data=f"process_order_{order['id']}"
        )])
    
    if len(pending_orders) > 10:
        text += f"... و {len(pending_orders) - 10} طلب آخر"
    
    keyboard.append([InlineKeyboardButton("🔙 العودة لإدارة الطلبات", callback_data="manage_orders")])
    
    await send_admin_message(telegram_id, text, InlineKeyboardMarkup(keyboard))

async def handle_admin_orders_report(telegram_id: int):
    """تقرير شامل عن الطلبات"""
    # إحصائيات عامة
    total_orders = await db.orders.count_documents({})
    completed_orders = await db.orders.count_documents({"status": "completed"})
    pending_orders = await db.orders.count_documents({"status": "pending"})
    failed_orders = await db.orders.count_documents({"status": "failed"})
    
    # إيرادات
    revenue_result = await db.orders.aggregate([
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$price"}}}
    ]).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # إحصائيات اليوم
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = await db.orders.count_documents({
        "order_date": {"$gte": today}
    })
    today_revenue_result = await db.orders.aggregate([
        {"$match": {"status": "completed", "order_date": {"$gte": today}}},
        {"$group": {"_id": None, "total": {"$sum": "$price"}}}
    ]).to_list(1)
    today_revenue = today_revenue_result[0]["total"] if today_revenue_result else 0
    
    # طلبات متأخرة (أكثر من 24 ساعة)
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    overdue_orders = await db.orders.count_documents({
        "status": "pending",
        "order_date": {"$lt": yesterday}
    })
    
    report_text = f"""📊 *تقرير شامل عن الطلبات*

📈 *الإحصائيات العامة:*
• إجمالي الطلبات: *{total_orders}*
• الطلبات المكتملة: *{completed_orders}* ✅
• الطلبات المعلقة: *{pending_orders}* ⏳  
• الطلبات الفاشلة: *{failed_orders}* ❌

💰 *الإحصائيات المالية:*
• إجمالي الإيرادات: *${total_revenue:.2f}*
• متوسط قيمة الطلب: *${total_revenue/completed_orders if completed_orders > 0 else 0:.2f}*

📅 *إحصائيات اليوم:*
• طلبات اليوم: *{today_orders}*
• إيرادات اليوم: *${today_revenue:.2f}*

⚠️ *تحذيرات:*
• طلبات متأخرة (+24س): *{overdue_orders}*

تم إنتاج التقرير: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"""
    
    keyboard = []
    if pending_orders > 0:
        keyboard.append([InlineKeyboardButton("📋 عرض الطلبات المعلقة", callback_data="view_all_pending")])
    if overdue_orders > 0:
        keyboard.append([InlineKeyboardButton("⚠️ الطلبات المتأخرة", callback_data="view_overdue_orders")])
    
    keyboard.append([InlineKeyboardButton("🔙 العودة لإدارة الطلبات", callback_data="manage_orders")])
    
    await send_admin_message(telegram_id, report_text, InlineKeyboardMarkup(keyboard))

async def handle_admin_order_code_input(telegram_id: int, text: str, session: TelegramSession):
    """معالجة إدخال الكود من الإدارة لتنفيذ الطلب"""
    order_id = session.data["order_id"]
    user_telegram_id = session.data["user_telegram_id"]
    product_name = session.data["product_name"]
    category_name = session.data["category_name"]
    delivery_type = session.data["delivery_type"]
    
    code_to_send = text.strip()
    if not code_to_send:
        await send_admin_message(telegram_id, "❌ يرجى إدخال الكود أو المعلومات")
        return
    
    try:
        # تحديث حالة الطلب
        await db.orders.update_one(
            {"id": order_id},
            {
                "$set": {
                    "status": "completed",
                    "code_sent": code_to_send,
                    "completion_date": datetime.now(timezone.utc),
                    "admin_notes": f"تم التنفيذ يدوياً بواسطة الإدارة"
                }
            }
        )
        
        # الحصول على تفاصيل الطلب
        order = await db.orders.find_one({"id": order_id})
        
        # إرسال الكود للمستخدم
        user_message = f"""✅ *تم تنفيذ طلبك بنجاح!*

📦 المنتج: *{product_name}*
🏷️ الفئة: *{category_name}*
💰 السعر: *${order['price']:.2f}*

🎫 *نتيجة الطلب Order Answer:*
`{code_to_send}`

شكراً لك لاستخدام خدماتنا! 🎉

للدعم الفني: @AbodStoreVIP"""
        
        user_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 عرض طلباتي", callback_data="order_history")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main_menu")]
        ])
        
        await send_user_message(user_telegram_id, user_message, user_keyboard)
        
        # رسالة تأكيد للإدارة
        admin_confirmation = f"""✅ *تم تنفيذ الطلب بنجاح!*

📦 المنتج: {product_name}
👤 المستخدم: {user_telegram_id}
🎫 الكود المرسل: `{code_to_send}`

تم إرسال إشعار للمستخدم بالكود."""
        
        admin_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 إدارة الطلبات", callback_data="manage_orders")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="admin_main_menu")]
        ])
        
        await send_admin_message(telegram_id, admin_confirmation, admin_keyboard)
        
        # مسح الجلسة
        await clear_session(telegram_id, is_admin=True)
        
    except Exception as e:
        logging.error(f"Error processing order: {e}")
        await send_admin_message(telegram_id, f"❌ حدث خطأ أثناء تنفيذ الطلب: {str(e)}")

async def notify_admin_new_order(product_name: str, category_name: str, user_telegram_id: int, price: float, code: str = None, status: str = "completed"):
    """إشعار الإدارة بكل طلب جديد"""
    if status == "completed" and code:
        admin_message = f"""✅ *طلب جديد مكتمل*

📦 المنتج: *{product_name}*
🏷️ الفئة: *{category_name}*
👤 المستخدم: {user_telegram_id}
💰 السعر: ${price:.2f}
🎫 الكود: `{code[:20]}...` (مرسل للعميل)

✅ تم تنفيذ الطلب تلقائياً وإرسال الكود للعميل."""
    else:
        admin_message = f"""⏳ *طلب جديد في انتظار التنفيذ*

📦 المنتج: *{product_name}*
🏷️ الفئة: *{category_name}*
👤 المستخدم: {user_telegram_id}
💰 السعر: ${price:.2f}

⚠️ يحتاج تنفيذ يدوي - يرجى المتابعة من لوحة الإدارة."""
    
    try:
        await send_admin_message(ADMIN_ID, admin_message)
    except Exception as e:
        logging.error(f"Failed to notify admin about new order: {e}")

async def notify_admin_for_codeless_order(product_name: str, category_name: str, user_telegram_id: int, price: float):
    """إشعار الإدارة في حالة عدم وجود أكواد"""
    admin_message = f"""🔔 *طلب جديد يحتاج إلى معالجة يدوية*

⚠️ *السبب: نفدت الأكواد من المخزون*

📦 المنتج: *{product_name}*
🏷️ الفئة: *{category_name}*
👤 المستخدم: {user_telegram_id}
💰 السعر: ${price:.2f}

يرجى إضافة أكواد جديدة لهذه الفئة أو التواصل مع المستخدم لتنفيذ الطلب يدوياً.

📋 للوصول لإدارة الطلبات: /start ثم اختر "📋 الطلبات" """
    
    try:
        await send_admin_message(ADMIN_ID, admin_message)
    except Exception as e:
        logging.error(f"Failed to notify admin: {e}")

async def check_for_pending_orders():
    """فحص الطلبات المتأخرة وإرسال تنبيه للإدارة"""
    try:
        # البحث عن طلبات معلقة أكثر من 30 دقيقة
        thirty_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
        overdue_orders = await db.orders.find({
            "status": "pending",
            "order_date": {"$lt": thirty_minutes_ago}
        }).to_list(10)
        
        if overdue_orders:
            admin_message = f"""⚠️ *تنبيه: طلبات متأخرة ({len(overdue_orders)})*

الطلبات التالية قيد التنفيذ منذ أكثر من 30 دقيقة:

"""
            
            for i, order in enumerate(overdue_orders[:5], 1):
                hours_ago = int((datetime.now(timezone.utc) - order["order_date"]).total_seconds() / 3600)
                admin_message += f"{i}. *{order['product_name']}* - ${order['price']:.2f}\n"
                admin_message += f"   👤 {order['telegram_id']} - {hours_ago}س مضت\n\n"
            
            if len(overdue_orders) > 5:
                admin_message += f"... و {len(overdue_orders) - 5} طلبات أخرى\n\n"
            
            admin_message += "يرجى متابعة الطلبات المعلقة بأسرع وقت ممكن."
            
            await send_admin_message(ADMIN_ID, admin_message)
            
    except Exception as e:
        logging.error(f"Error checking pending orders: {e}")

async def handle_admin_select_product_for_category(telegram_id: int, product_id: str):
    # Get product details
    product = await db.products.find_one({"id": product_id})
    if not product:
        await send_admin_message(telegram_id, "❌ المنتج غير موجود")
        return
    
    # Start category creation session
    session = TelegramSession(
        telegram_id=telegram_id, 
        state="add_category_name",
        data={"product_id": product_id, "product_name": product['name']}
    )
    await save_session(session, is_admin=True)
    
    text = f"📂 *إضافة فئة للمنتج: {product['name']}*\n\n1️⃣ أدخل اسم الفئة:"
    
    cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="add_category")]
    ])
    await send_admin_message(telegram_id, text, cancel_keyboard)

async def handle_admin_delivery_type_selection(telegram_id: int, delivery_type: str):
    session = await get_session(telegram_id, is_admin=True)
    if not session:
        await send_admin_message(telegram_id, "❌ انتهت الجلسة. يرجى البدء مرة أخرى.")
        return
    
    delivery_types = {
        "code": "🎫 كود تلقائي",
        "phone": "📱 رقم هاتف", 
        "email": "📧 بريد إلكتروني",
        "id": "🆔 إيدي المستخدم",
        "manual": "📝 طلب يدوي"
    }
    
    session.data["delivery_type"] = delivery_type
    session.state = "add_category_price"
    await save_session(session, is_admin=True)
    
    await send_admin_message(telegram_id, f"✅ تم اختيار: {delivery_types[delivery_type]}\n\n5️⃣ أدخل سعر الفئة (بالدولار):")

async def handle_admin_add_codes(telegram_id: int):
    # Get categories that support codes
    categories = await db.categories.find({"delivery_type": "code"}).to_list(100)
    
    if not categories:
        no_categories_text = "❌ لا توجد فئات تدعم الأكواد. يجب إضافة فئة بنوع 'كود تلقائي' أولاً."
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📂 إضافة فئة جديدة", callback_data="add_category")],
            [InlineKeyboardButton("🔙 العودة", callback_data="manage_codes")]
        ])
        await send_admin_message(telegram_id, no_categories_text, back_keyboard)
        return
    
    text = "🎫 *إضافة أكواد*\n\nاختر الفئة التي تريد إضافة أكواد لها:"
    keyboard = []
    
    for category in categories:
        # Get current stock
        available_codes = await db.codes.count_documents({
            "category_id": category["id"],
            "is_used": False
        })
        
        keyboard.append([InlineKeyboardButton(
            f"{category['name']} ({available_codes} متاح)",
            callback_data=f"add_codes_to_category_{category['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="manage_codes")])
    await send_admin_message(telegram_id, text, InlineKeyboardMarkup(keyboard))

async def handle_admin_select_code_type(telegram_id: int, category_id: str):
    category = await db.categories.find_one({"id": category_id})
    if not category:
        await send_admin_message(telegram_id, "❌ الفئة غير موجودة")
        return
    
    text = f"🎫 *إضافة أكواد للفئة: {category['name']}*\n\nاختر نوع الكود:"
    
    keyboard = [
        [InlineKeyboardButton("📝 نصي (ABC123)", callback_data=f"code_type_text_{category_id}")],
        [InlineKeyboardButton("🔢 رقمي (123456)", callback_data=f"code_type_number_{category_id}")],
        [InlineKeyboardButton("🔗 مزدوج (كود + سيريال)", callback_data=f"code_type_dual_{category_id}")],
        [InlineKeyboardButton("🔙 العودة", callback_data="add_codes")]
    ]
    
    await send_admin_message(telegram_id, text, InlineKeyboardMarkup(keyboard))

async def handle_admin_code_type_selected(telegram_id: int, code_type: str, category_id: str):
    category = await db.categories.find_one({"id": category_id})
    if not category:
        await send_admin_message(telegram_id, "❌ الفئة غير موجودة")
        return
    
    # Start code addition session
    session = TelegramSession(
        telegram_id=telegram_id,
        state="add_codes_input",
        data={
            "category_id": category_id,
            "category_name": category["name"],
            "code_type": code_type
        }
    )
    await save_session(session, is_admin=True)
    
    code_type_names = {
        "text": "نصي (مثل: ABC123DEF)",
        "number": "رقمي (مثل: 123456789)", 
        "dual": "مزدوج (كود + سيريال)"
    }
    
    if code_type == "dual":
        text = f"""🎫 *إضافة أكواد مزدوجة للفئة: {category['name']}*

📝 أدخل الأكواد بالتنسيق التالي:
كود واحد: `ABC123|SERIAL456`
عدة أكواد (كل كود في سطر منفصل):
```
ABC123|SERIAL456
DEF789|SERIAL123  
GHI456|SERIAL789
```

⚠️ استخدم الرمز | للفصل بين الكود والسيريال"""
    else:
        text = f"""🎫 *إضافة أكواد {code_type_names[code_type]} للفئة: {category['name']}*

📝 أدخل الأكواد:
• كود واحد: `ABC123`
• عدة أكواد (كل كود في سطر منفصل):
```
ABC123
DEF456
GHI789
```"""
    
    cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="manage_codes")]
    ])
    
    await send_admin_message(telegram_id, text, cancel_keyboard)

async def handle_admin_view_codes(telegram_id: int):
    categories = await db.categories.find({"delivery_type": "code"}).to_list(100)
    
    if not categories:
        text = "❌ لا توجد فئات تدعم الأكواد"
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 العودة", callback_data="manage_codes")]
        ])
        await send_admin_message(telegram_id, text, back_keyboard)
        return
    
    text = "👁 *عرض الأكواد*\n\n"
    
    for category in categories:
        total_codes = await db.codes.count_documents({"category_id": category["id"]})
        used_codes = await db.codes.count_documents({"category_id": category["id"], "is_used": True})
        available_codes = total_codes - used_codes
        
        status_emoji = "🟢" if available_codes > 10 else "🟡" if available_codes > 5 else "🔴"
        text += f"{status_emoji} *{category['name']}*\n"
        text += f"   المجموع: {total_codes} | المتاح: {available_codes} | المستخدم: {used_codes}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة أكواد", callback_data="add_codes")],
        [InlineKeyboardButton("🔙 العودة", callback_data="manage_codes")]
    ]
    
    await send_admin_message(telegram_id, text, InlineKeyboardMarkup(keyboard))

async def handle_admin_low_stock_alerts(telegram_id: int):
    categories = await db.categories.find({"delivery_type": "code"}).to_list(100)
    
    low_stock = []
    for category in categories:
        available_codes = await db.codes.count_documents({
            "category_id": category["id"],
            "is_used": False
        })
        if available_codes <= 5:
            low_stock.append({
                "name": category["name"],
                "count": available_codes,
                "id": category["id"]
            })
    
    if not low_stock:
        text = "✅ *جميع الأكواد متوفرة بكميات جيدة*\n\nلا توجد تحذيرات حالياً."
    else:
        text = "🚨 *تحذيرات نقص الأكواد*\n\n"
        for item in low_stock:
            status = "🔴 نفدت" if item["count"] == 0 else f"⚠️ {item['count']} متبقية"
            text += f"{status} - {item['name']}\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة أكواد", callback_data="add_codes")],
        [InlineKeyboardButton("🔙 العودة", callback_data="manage_codes")]
    ]
    
    await send_admin_message(telegram_id, text, InlineKeyboardMarkup(keyboard))

# API endpoints for web interface
@api_router.get("/products", response_model=List[Product])
async def get_products():
    products = await db.products.find().to_list(100)
    return [Product(**product) for product in products]

@api_router.get("/categories")
async def get_categories():
    categories = await db.categories.find().to_list(1000)
    return [Category(**category) for category in categories]

@api_router.get("/codes-stats")
async def get_codes_stats():
    categories = await db.categories.find({"delivery_type": "code"}).to_list(100)
    stats = []
    
    for category in categories:
        total_codes = await db.codes.count_documents({"category_id": category["id"]})
        used_codes = await db.codes.count_documents({"category_id": category["id"], "is_used": True})
        available_codes = total_codes - used_codes
        
        stats.append({
            "category_name": category["name"],
            "category_id": category["id"],
            "total_codes": total_codes,
            "used_codes": used_codes,
            "available_codes": available_codes,
            "status": "low" if available_codes <= 5 else "medium" if available_codes <= 10 else "good"
        })
    
    return stats

@api_router.get("/users", response_model=List[User])
async def get_users():
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.get("/orders", response_model=List[Order])
async def get_orders():
    orders = await db.orders.find().sort("order_date", -1).to_list(1000)
    return [Order(**order) for order in orders]

@api_router.get("/pending-orders")
async def get_pending_orders():
    orders = await db.orders.find({"status": "pending"}).sort("order_date", -1).to_list(100)
    return orders

@api_router.post("/set-webhooks")
async def set_webhooks():
    try:
        # Set user bot webhook
        await user_bot.set_webhook(
            url="https://telecard-manager.preview.emergentagent.com/api/webhook/user/abod_user_webhook_secret"
        )
        
        # Set admin bot webhook
        await admin_bot.set_webhook(
            url="https://telecard-manager.preview.emergentagent.com/api/webhook/admin/abod_admin_webhook_secret"
        )
        
        return {"status": "success", "message": "Webhooks set successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background task to check for overdue orders
import asyncio
from contextlib import asynccontextmanager
import threading
from datetime import timedelta

async def send_system_heartbeat():
    """إرسال إشعار دوري للتأكد من عمل النظام"""
    try:
        # إحصائيات سريعة
        users_count = await db.users.count_documents({})
        orders_today = await db.orders.count_documents({
            "order_date": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)}
        })
        pending_orders = await db.orders.count_documents({"status": "pending"})
        
        # إحصائية الأكواد المتاحة
        available_codes = await db.codes.count_documents({"is_used": False})
        
        heartbeat_text = f"""💗 *نبضة النظام* - {datetime.now(timezone.utc).strftime('%H:%M')}

✅ النظام يعمل بشكل طبيعي

📊 الإحصائيات:
👥 المستخدمين: {users_count}
📦 طلبات اليوم: {orders_today}
⏳ طلبات معلقة: {pending_orders}
🎫 أكواد متاحة: {available_codes}

🕐 آخر فحص: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"""
        
        # إضافة تحذيرات إن وجدت
        warnings = []
        if pending_orders > 5:
            warnings.append(f"⚠️ يوجد {pending_orders} طلب معلق")
        if available_codes < 50:
            warnings.append(f"⚠️ الأكواد قليلة: {available_codes} فقط")
        
        if warnings:
            heartbeat_text += "\n\n🚨 تحذيرات:\n" + "\n".join(warnings)
        
        # إرسال نبض النظام للإداري المسؤول عن النظام
        await send_admin_message(SYSTEM_ADMIN_ID, heartbeat_text)
        
    except Exception as e:
        # إرسال تحذير في حالة الخطأ
        error_text = f"""🚨 *خطأ في النظام*

❌ فشل في إرسال نبضة النظام
🕐 الوقت: {datetime.now(timezone.utc).strftime('%H:%M:%S')}
📝 الخطأ: {str(e)}

يرجى التحقق من النظام فوراً!"""
        
        try:
            # إرسال إشعار الخطأ للإداري المسؤول عن النظام
            await send_admin_message(SYSTEM_ADMIN_ID, error_text)
        except:
            logging.error(f"Failed to send error notification: {e}")

async def background_tasks():
    """مهام الخلفية"""
    heartbeat_counter = 0
    
    while True:
        try:
            # فحص الطلبات المعلقة كل ساعة
            if heartbeat_counter % 6 == 0:  # كل ساعة (6 * 10 دقائق)
                await check_for_pending_orders()
            
            # إرسال نبضة النظام كل 10 دقائق
            await send_system_heartbeat()
            
            heartbeat_counter += 1
            await asyncio.sleep(600)  # 10 دقائق
            
        except Exception as e:
            logging.error(f"Background task error: {e}")
            
            # إرسال إشعار طارئ في حالة تعطل المهام الخلفية
            emergency_text = f"""🆘 *تحذير طارئ*

❌ تعطل في المهام الخلفية
🕐 الوقت: {datetime.now(timezone.utc).strftime('%H:%M:%S')}
📝 الخطأ: {str(e)}

سيتم إعادة المحاولة خلال 5 دقائق"""
            
            try:
                # إرسال إشعار الطوارئ للإداري المسؤول عن النظام
                await send_admin_message(SYSTEM_ADMIN_ID, emergency_text)
            except:
                pass
            
            await asyncio.sleep(300)  # انتظار 5 دقائق في حالة الخطأ

@app.on_event("startup")
async def startup_background_tasks():
    """بدء المهام الخلفية"""
    asyncio.create_task(background_tasks())

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()