"""
نظام اختبار الأداء - Performance Testing System
يقوم بإنشاء آلاف الطلبات الوهمية لاختبار النظام
"""

import asyncio
import random
import time
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid

# الاتصال بقاعدة البيانات
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'abod_card')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# أسماء وهمية
FIRST_NAMES = ["أحمد", "محمد", "علي", "عمر", "خالد", "سعد", "عبدالله", "يوسف", "إبراهيم", "فهد"]
USERNAMES = ["test_user", "demo_user", "fake_user", "test", "demo", "performance", "load_test"]

# حالات الطلبات
ORDER_STATUSES = ["completed", "pending", "failed", "cancelled"]

async def generate_test_users(count: int):
    """إنشاء مستخدمين وهميين"""
    users = []
    print(f"🔄 إنشاء {count} مستخدم وهمي...")
    
    for i in range(count):
        user_id = 9000000000 + i  # IDs تبدأ من 9 billion (وهمية)
        user = {
            "id": str(uuid.uuid4()),
            "telegram_id": user_id,
            "username": f"{random.choice(USERNAMES)}_{i}",
            "first_name": f"{random.choice(FIRST_NAMES)}_{i}",
            "balance": round(random.uniform(0, 1000), 2),
            "join_date": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365)),
            "is_test_data": True  # علامة البيانات الوهمية
        }
        users.append(user)
    
    if users:
        result = await db.users.insert_many(users)
        print(f"✅ تم إنشاء {len(result.inserted_ids)} مستخدم")
    
    return users

async def generate_test_orders(users, orders_per_user: int):
    """إنشاء طلبات وهمية"""
    orders = []
    
    # الحصول على المنتجات والفئات الحقيقية
    categories = await db.categories.find({"is_active": True}).to_list(100)
    
    if not categories:
        print("❌ لا توجد فئات في النظام!")
        return []
    
    print(f"🔄 إنشاء {len(users) * orders_per_user} طلب وهمي...")
    
    for user in users:
        for _ in range(orders_per_user):
            category = random.choice(categories)
            status = random.choices(
                ORDER_STATUSES,
                weights=[60, 20, 15, 5],  # 60% completed, 20% pending, etc.
                k=1
            )[0]
            
            order_date = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            order = {
                "id": str(uuid.uuid4()),
                "order_number": f"AC{order_date.strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}",
                "telegram_id": user['telegram_id'],
                "product_name": category.get('product_name', 'Test Product'),
                "category_name": category['name'],
                "category_id": category['id'],
                "price": category['price'],
                "delivery_type": category.get('delivery_type', 'code'),
                "delivery_info": f"test_info_{random.randint(1000, 9999)}",
                "status": status,
                "order_date": order_date,
                "is_test_data": True  # علامة البيانات الوهمية
            }
            
            if status == "completed":
                order["completed_at"] = order_date + timedelta(minutes=random.randint(5, 60))
            elif status == "cancelled":
                order["cancelled_at"] = order_date + timedelta(minutes=random.randint(1, 30))
            
            orders.append(order)
    
    return orders

async def bulk_insert_orders(orders, batch_size=1000):
    """إدخال الطلبات دفعة واحدة"""
    total = len(orders)
    inserted = 0
    
    print(f"🔄 إدخال {total} طلب إلى قاعدة البيانات...")
    start_time = time.time()
    
    for i in range(0, total, batch_size):
        batch = orders[i:i + batch_size]
        await db.orders.insert_many(batch)
        inserted += len(batch)
        print(f"   ✓ تم إدخال {inserted}/{total} طلب...")
    
    elapsed = time.time() - start_time
    print(f"✅ تم إدخال {total} طلب في {elapsed:.2f} ثانية")
    print(f"📊 السرعة: {total/elapsed:.2f} طلب/ثانية")
    
    return elapsed

async def run_performance_test(num_users: int = 100, orders_per_user: int = 10):
    """تشغيل اختبار الأداء الكامل"""
    print("="*50)
    print("🚀 بدء اختبار الأداء")
    print(f"👥 عدد المستخدمين: {num_users}")
    print(f"📦 طلبات لكل مستخدم: {orders_per_user}")
    print(f"📊 إجمالي الطلبات: {num_users * orders_per_user}")
    print("="*50)
    
    overall_start = time.time()
    
    # 1. إنشاء المستخدمين
    users_start = time.time()
    users = await generate_test_users(num_users)
    users_time = time.time() - users_start
    
    # 2. إنشاء الطلبات
    orders_gen_start = time.time()
    orders = await generate_test_orders(users, orders_per_user)
    orders_gen_time = time.time() - orders_gen_start
    
    # 3. إدخال الطلبات
    orders_insert_time = await bulk_insert_orders(orders)
    
    # 4. حساب الإحصائيات
    overall_time = time.time() - overall_start
    
    # التحليل
    print("\n" + "="*50)
    print("📊 نتائج اختبار الأداء:")
    print("="*50)
    print(f"⏱️  وقت إنشاء المستخدمين: {users_time:.2f}s")
    print(f"⏱️  وقت إنشاء الطلبات: {orders_gen_time:.2f}s")
    print(f"⏱️  وقت إدخال الطلبات: {orders_insert_time:.2f}s")
    print(f"⏱️  الوقت الإجمالي: {overall_time:.2f}s")
    print()
    print(f"📈 الأداء:")
    print(f"   • {num_users/overall_time:.2f} مستخدم/ثانية")
    print(f"   • {len(orders)/overall_time:.2f} طلب/ثانية")
    print()
    
    # إحصائيات قاعدة البيانات
    total_users = await db.users.count_documents({})
    test_users = await db.users.count_documents({"is_test_data": True})
    total_orders = await db.orders.count_documents({})
    test_orders = await db.orders.count_documents({"is_test_data": True})
    
    print(f"💾 قاعدة البيانات:")
    print(f"   • إجمالي المستخدمين: {total_users} ({test_users} وهمي)")
    print(f"   • إجمالي الطلبات: {total_orders} ({test_orders} وهمي)")
    print("="*50)
    
    return {
        "users_created": num_users,
        "orders_created": len(orders),
        "total_time": overall_time,
        "users_per_second": num_users/overall_time,
        "orders_per_second": len(orders)/overall_time,
        "db_total_users": total_users,
        "db_test_users": test_users,
        "db_total_orders": total_orders,
        "db_test_orders": test_orders
    }

async def delete_test_data():
    """حذف جميع البيانات الوهمية"""
    print("🗑️  حذف البيانات الوهمية...")
    
    # حذف المستخدمين الوهميين
    users_result = await db.users.delete_many({"is_test_data": True})
    print(f"   ✓ تم حذف {users_result.deleted_count} مستخدم وهمي")
    
    # حذف الطلبات الوهمية
    orders_result = await db.orders.delete_many({"is_test_data": True})
    print(f"   ✓ تم حذف {orders_result.deleted_count} طلب وهمي")
    
    print(f"✅ تم حذف جميع البيانات الوهمية")
    
    return {
        "users_deleted": users_result.deleted_count,
        "orders_deleted": orders_result.deleted_count
    }

async def get_test_data_stats():
    """الحصول على إحصائيات البيانات الوهمية"""
    test_users = await db.users.count_documents({"is_test_data": True})
    test_orders = await db.orders.count_documents({"is_test_data": True})
    
    return {
        "test_users": test_users,
        "test_orders": test_orders
    }

if __name__ == "__main__":
    # للاختبار المباشر
    async def main():
        # اختبار بـ 100 مستخدم و 10 طلبات لكل مستخدم = 1000 طلب
        await run_performance_test(num_users=100, orders_per_user=10)
    
    asyncio.run(main())
