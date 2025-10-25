#!/usr/bin/env python3
"""
سكريبت حذف الفئات من قاعدة البيانات مباشرة
Delete Categories Script - Direct Database Access
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv('/app/backend/.env')

async def list_categories():
    """عرض جميع الفئات"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 70)
    print("📋 قائمة جميع الفئات")
    print("=" * 70)
    
    categories = await db.categories.find({}).to_list(length=None)
    
    if not categories:
        print("❌ لا توجد فئات في قاعدة البيانات")
        client.close()
        return
    
    print(f"\n📊 إجمالي الفئات: {len(categories)}")
    active_count = len([c for c in categories if c.get('is_active', True)])
    print(f"🟢 فئات نشطة: {active_count}")
    print(f"🔴 فئات معطلة: {len(categories) - active_count}\n")
    
    # عرض الفئات مع المنتجات
    products = await db.products.find({}).to_list(length=None)
    products_dict = {p['id']: p['name'] for p in products}
    
    for i, cat in enumerate(categories, 1):
        status = "🟢 نشط" if cat.get('is_active', True) else "🔴 معطل"
        product_name = products_dict.get(cat.get('product_id'), 'غير معروف')
        print(f"{i}. {status} | {cat['name']}")
        print(f"   ID: {cat['id']}")
        print(f"   المنتج: {product_name}")
        print(f"   السعر: ${cat.get('price', 0):.2f}")
        print()
    
    client.close()

async def delete_category_by_id(category_id: str):
    """حذف فئة بواسطة ID"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"\n🔍 البحث عن الفئة: {category_id}")
    
    # البحث عن الفئة
    category = await db.categories.find_one({"id": category_id})
    
    if not category:
        print("❌ الفئة غير موجودة!")
        client.close()
        return False
    
    print(f"✅ تم العثور على الفئة: {category['name']}")
    print(f"   المنتج ID: {category.get('product_id')}")
    print(f"   السعر: ${category.get('price', 0):.2f}")
    print(f"   الحالة الحالية: {'نشط' if category.get('is_active', True) else 'معطل'}")
    
    # تأكيد الحذف
    print(f"\n⚠️  هل أنت متأكد من حذف الفئة '{category['name']}'؟")
    confirm = input("اكتب 'نعم' للتأكيد: ")
    
    if confirm.lower() not in ['نعم', 'yes', 'y']:
        print("❌ تم إلغاء العملية")
        client.close()
        return False
    
    # حذف الفئة (تعطيلها)
    result = await db.categories.update_one(
        {"id": category_id},
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count > 0:
        print(f"\n✅ تم حذف الفئة '{category['name']}' بنجاح!")
        print(f"   Matched: {result.matched_count}")
        print(f"   Modified: {result.modified_count}")
    else:
        print("❌ فشل في حذف الفئة")
    
    client.close()
    return True

async def delete_category_by_name(category_name: str, product_name: str = None):
    """حذف فئة بواسطة الاسم"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"\n🔍 البحث عن الفئة: {category_name}")
    
    # البحث عن الفئة
    query = {"name": {"$regex": category_name, "$options": "i"}}
    categories = await db.categories.find(query).to_list(length=None)
    
    if not categories:
        print("❌ لم يتم العثور على فئات بهذا الاسم!")
        client.close()
        return False
    
    # إذا كان هناك أكثر من فئة، اعرضها
    if len(categories) > 1:
        print(f"\n📋 تم العثور على {len(categories)} فئة:")
        for i, cat in enumerate(categories, 1):
            product = await db.products.find_one({"id": cat.get('product_id')})
            product_name_found = product['name'] if product else 'غير معروف'
            print(f"{i}. {cat['name']} - {product_name_found} (${cat.get('price', 0):.2f})")
        
        choice = input("\nاختر رقم الفئة للحذف (أو اضغط Enter للإلغاء): ")
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(categories):
            print("❌ تم إلغاء العملية")
            client.close()
            return False
        
        category = categories[int(choice) - 1]
    else:
        category = categories[0]
    
    # عرض تفاصيل الفئة
    product = await db.products.find_one({"id": category.get('product_id')})
    product_name_found = product['name'] if product else 'غير معروف'
    
    print(f"\n✅ الفئة المختارة:")
    print(f"   الاسم: {category['name']}")
    print(f"   المنتج: {product_name_found}")
    print(f"   السعر: ${category.get('price', 0):.2f}")
    print(f"   ID: {category['id']}")
    
    # تأكيد الحذف
    confirm = input("\n⚠️  اكتب 'نعم' للتأكيد: ")
    
    if confirm.lower() not in ['نعم', 'yes', 'y']:
        print("❌ تم إلغاء العملية")
        client.close()
        return False
    
    # حذف الفئة
    result = await db.categories.update_one(
        {"id": category['id']},
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count > 0:
        print(f"\n✅ تم حذف الفئة '{category['name']}' بنجاح!")
        print(f"   Matched: {result.matched_count}")
        print(f"   Modified: {result.modified_count}")
    else:
        print("❌ فشل في حذف الفئة")
    
    client.close()
    return True

async def delete_multiple_categories(product_name: str):
    """حذف جميع فئات منتج معين"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"\n🔍 البحث عن منتج: {product_name}")
    
    # البحث عن المنتج
    product = await db.products.find_one({"name": {"$regex": product_name, "$options": "i"}})
    
    if not product:
        print("❌ المنتج غير موجود!")
        client.close()
        return False
    
    print(f"✅ تم العثور على المنتج: {product['name']}")
    print(f"   ID: {product['id']}")
    
    # البحث عن جميع فئات المنتج
    categories = await db.categories.find({"product_id": product['id']}).to_list(length=None)
    
    if not categories:
        print(f"❌ لا توجد فئات لهذا المنتج")
        client.close()
        return False
    
    print(f"\n📋 تم العثور على {len(categories)} فئة:")
    for i, cat in enumerate(categories, 1):
        status = "🟢" if cat.get('is_active', True) else "🔴"
        print(f"{i}. {status} {cat['name']} (${cat.get('price', 0):.2f})")
    
    # تأكيد الحذف
    confirm = input(f"\n⚠️  هل تريد حذف جميع الـ {len(categories)} فئة؟ اكتب 'نعم' للتأكيد: ")
    
    if confirm.lower() not in ['نعم', 'yes', 'y']:
        print("❌ تم إلغاء العملية")
        client.close()
        return False
    
    # حذف جميع الفئات
    result = await db.categories.update_many(
        {"product_id": product['id']},
        {"$set": {"is_active": False}}
    )
    
    print(f"\n✅ تم حذف {result.modified_count} فئة من {len(categories)} بنجاح!")
    
    client.close()
    return True

async def main():
    """القائمة الرئيسية"""
    print("\n" + "=" * 70)
    print("🗑️  سكريبت حذف الفئات - قاعدة البيانات المباشرة")
    print("=" * 70)
    
    while True:
        print("\n📋 الخيارات:")
        print("1. عرض جميع الفئات")
        print("2. حذف فئة بواسطة ID")
        print("3. حذف فئة بواسطة الاسم")
        print("4. حذف جميع فئات منتج معين")
        print("5. خروج")
        
        choice = input("\nاختر رقم (1-5): ")
        
        if choice == "1":
            await list_categories()
        
        elif choice == "2":
            category_id = input("\nأدخل ID الفئة: ")
            await delete_category_by_id(category_id)
        
        elif choice == "3":
            category_name = input("\nأدخل اسم الفئة (أو جزء منه): ")
            await delete_category_by_name(category_name)
        
        elif choice == "4":
            product_name = input("\nأدخل اسم المنتج (أو جزء منه): ")
            await delete_multiple_categories(product_name)
        
        elif choice == "5":
            print("\n👋 مع السلامة!")
            break
        
        else:
            print("❌ خيار غير صحيح!")

if __name__ == "__main__":
    asyncio.run(main())
