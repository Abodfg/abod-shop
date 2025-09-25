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

async def create_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📦 إدارة المنتجات", callback_data="manage_products")],
        [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="manage_users")],
        [InlineKeyboardButton("🎫 إدارة الأكواد", callback_data="manage_codes")],
        [InlineKeyboardButton("📊 التقارير", callback_data="reports")],
        [InlineKeyboardButton("📋 الطلبات", callback_data="manage_orders")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_user_start(telegram_id: int, username: str, first_name: str):
    # Check if user exists, create if not
    user_data = await db.users.find_one({"telegram_id": telegram_id})
    if not user_data:
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name
        )
        await db.users.insert_one(new_user.dict())
    
    welcome_text = """🎉 مرحبًا بك في بوت "Abod Card"! 🎉

أنت الآن في المكان الصحيح لشراء المنتجات الرقمية والاشتراكات الرقمية والبطاقات!

*خدماتنا الرئيسية:*
• منتجات رقمية: أكواد للألعاب وبطاقات الهدايا
• اشتراكات رقمية: ChatGPT Plus، Telegram Premium وأكثر
• بطاقات هدايا: Google Play، iTunes، PlayStation، Steam
• إدارة محفظتك الرقمية بسهولة
• دعم فني متواصل

✨ اختر من الخيارات أدناه للبدء! ✨"""
    
    keyboard = await create_user_keyboard()
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
            await handle_user_callback(update.callback_query)
            
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
            await handle_admin_callback(update.callback_query)
            
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Admin webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_user_message(message):
    telegram_id = message.chat_id
    text = message.text
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    if text == "/start":
        await handle_user_start(telegram_id, username, first_name)
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

async def handle_user_callback(callback_query):
    telegram_id = callback_query.message.chat_id
    data = callback_query.data
    
    await callback_query.answer()
    
    if data == "main_menu":
        keyboard = await create_user_keyboard()
        await send_user_message(telegram_id, "اختر من الخيارات التالية:", keyboard)
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

async def handle_browse_products(telegram_id: int):
    products = await db.products.find({"is_active": True}).to_list(100)
    
    if not products:
        no_products_text = "❌ لا توجد منتجات متاحة حالياً"
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ])
        await send_user_message(telegram_id, no_products_text, back_keyboard)
        return
    
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(product["name"], callback_data=f"product_{product['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")])
    
    text = "🛒 *المنتجات المتاحة:*\n\nاختر المنتج الذي تريده:"
    await send_user_message(telegram_id, text, InlineKeyboardMarkup(keyboard))

async def handle_view_wallet(telegram_id: int):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if user:
        balance = user.get("balance", 0.0)
        wallet_text = f"""💰 *محفظتك الرقمية*

الرصيد الحالي: *{balance:.2f} دولار*
عدد الطلبات: *{user.get('orders_count', 0)}*

تاريخ الانضمام: {user.get('join_date', 'غير محدد')}"""
        
        keyboard = [
            [InlineKeyboardButton("💳 شحن المحفظة", callback_data="topup_wallet")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        await send_user_message(telegram_id, wallet_text, InlineKeyboardMarkup(keyboard))

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
    
    await callback_query.answer()
    
    if data == "admin_main_menu":
        keyboard = await create_admin_keyboard()
        await send_admin_message(telegram_id, "اختر العملية المطلوبة:", keyboard)
        await clear_session(telegram_id, is_admin=True)
    
    elif data == "manage_products":
        await handle_admin_manage_products(telegram_id)
    
    elif data == "manage_users":
        await handle_admin_manage_users(telegram_id)
    
    elif data == "manage_codes":
        await handle_admin_manage_codes(telegram_id)
    
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
    elif delivery_type in ["phone", "email"]:
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

🎫 *الكود الخاص بك:*
`{code_display}`

📋 *الشروط:*
{available_code['terms']}

📝 *الوصف:*
{available_code['description']}

🔄 *طريقة الاسترداد:*
{category['redemption_method']}

شكراً لك لاستخدام خدماتنا! 🎉"""
    else:
        # No codes available - manual processing needed
        success_text = f"""⏳ *تم استلام طلبك!*

📦 المنتج: *{product['name']}*
🏷️ الفئة: *{category['name']}*
💰 السعر: *${category['price']:.2f}*

⚠️ الأكواد نفدت مؤقتاً. سيتم تنفيذ طلبك يدوياً خلال 24 ساعة.
سيصلك إشعار فور توفر الكود."""
        
        # Notify admin about stock shortage
        await send_admin_message(
            telegram_id,  # This should be admin's telegram ID
            f"🚨 *نفدت أكواد الفئة!*\n\n📦 المنتج: {product['name']}\n🏷️ الفئة: {category['name']}\n👤 المستخدم: {telegram_id}\n💰 السعر: ${category['price']:.2f}\n\n⚠️ يرجى إضافة أكواد جديدة وتنفيذ الطلب يدوياً."
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
    
    input_text = "📱 أدخل رقم هاتفك:" if delivery_type == "phone" else "📧 أدخل بريدك الإلكتروني:"
    
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

سيتم تنفيذ طلبك يدوياً خلال 24 ساعة.
سيصلك إشعار فور التنفيذ."""
    
    # Notify admin
    await send_admin_message(
        telegram_id,  # This should be admin's telegram ID  
        f"📋 *طلب يدوي جديد*\n\n📦 المنتج: {product['name']}\n🏷️ الفئة: {category['name']}\n👤 المستخدم: {telegram_id}\n💰 السعر: ${category['price']:.2f}\n📝 النوع: طلب يدوي"
    )
    
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
    input_type = "الهاتف" if session.state == "purchase_input_phone" else "البريد الإلكتروني"
    success_text = f"""✅ *تم استلام طلبك بنجاح!*

📦 المنتج: *{product_name}*
🏷️ الفئة: *{category_name}*
💰 السعر: *${price:.2f}*
📝 {input_type}: `{user_input}`

⏳ سيتم تنفيذ طلبك خلال 24 ساعة وإرسال التفاصيل إليك.

شكراً لك لاستخدام خدماتنا! 🎉"""
    
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

يرجى تنفيذ الطلب وإرسال التفاصيل للمستخدم."""
    
    # Note: This should be sent to actual admin telegram ID
    # For now, we'll log it or you can replace with actual admin ID
    try:
        # Replace with actual admin telegram ID
        admin_telegram_id = 123456789  # Replace with real admin ID
        await send_admin_message(admin_telegram_id, admin_notification)
    except Exception as e:
        logging.error(f"Failed to notify admin: {e}")
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
    input_type = "الهاتف" if session.state == "purchase_input_phone" else "البريد الإلكتروني"
    success_text = f"""✅ *تم استلام طلبك بنجاح!*

📦 المنتج: *{product_name}*
🏷️ الفئة: *{category_name}*
💰 السعر: *${price:.2f}*
📝 {input_type}: `{user_input}`

⏳ سيتم تنفيذ طلبك خلال 24 ساعة وإرسال التفاصيل إليك.

شكراً لك لاستخدام خدماتنا! 🎉"""
    
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

يرجى تنفيذ الطلب وإرسال التفاصيل للمستخدم."""
    
    # Note: This should be sent to actual admin telegram ID
    # For now, we'll log it or you can replace with actual admin ID
    try:
        # Replace with actual admin telegram ID
        admin_telegram_id = 123456789  # Replace with real admin ID
        await send_admin_message(admin_telegram_id, admin_notification)
    except Exception as e:
        logging.error(f"Failed to notify admin: {e}")

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

@api_router.get("/users", response_model=List[User])
async def get_users():
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.get("/orders", response_model=List[Order])
async def get_orders():
    orders = await db.orders.find().sort("order_date", -1).to_list(1000)
    return [Order(**order) for order in orders]

@api_router.post("/set-webhooks")
async def set_webhooks():
    try:
        # Set user bot webhook
        await user_bot.set_webhook(
            url="https://cardmartbot.preview.emergentagent.com/api/webhook/user/abod_user_webhook_secret"
        )
        
        # Set admin bot webhook
        await admin_bot.set_webhook(
            url="https://cardmartbot.preview.emergentagent.com/api/webhook/admin/abod_admin_webhook_secret"
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()