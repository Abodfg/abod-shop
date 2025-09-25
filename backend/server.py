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
import asyncio
import httpx
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
import json

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
    redemption_method: str
    terms: str
    image_url: Optional[str] = None
    product_id: str

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
    price: float
    status: str  # "pending", "completed", "failed"
    code_sent: Optional[str] = None
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

# More admin handlers would be implemented here...

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
    allow_methods=["*"],
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