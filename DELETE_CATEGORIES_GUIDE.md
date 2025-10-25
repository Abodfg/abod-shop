# 🗑️ دليل حذف الفئات من قاعدة البيانات

## 📥 تحميل ملف الموقع (GitHub Pages)

**الملف الجاهز للرفع:**
```
/app/github-deploy/index-download-20251025-200931.html
```

**خطوات الرفع:**
1. قم بتحميل الملف من المسار أعلاه
2. أعد تسميته إلى `index.html`
3. ارفعه على GitHub Pages (استبدل الملف القديم)
4. انتظر دقيقة واحدة حتى يتم النشر
5. امسح الكاش: `Ctrl + Shift + R` (أو `Cmd + Shift + R` على Mac)

---

## 🛠️ حذف الفئات من قاعدة البيانات مباشرة

### الطريقة 1: استخدام السكريبت التفاعلي (موصى به) ⭐

```bash
cd /app
python3 delete_categories_script.py
```

**الخيارات المتاحة:**

1. **عرض جميع الفئات** - يعرض قائمة كاملة بجميع الفئات مع حالتها
2. **حذف فئة بواسطة ID** - حذف فئة محددة بدقة
3. **حذف فئة بواسطة الاسم** - البحث والحذف بالاسم
4. **حذف جميع فئات منتج** - حذف كل الفئات لمنتج معين دفعة واحدة

---

### الطريقة 2: حذف يدوي من Python Console

#### أ) حذف فئة واحدة بالاسم

```python
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def delete_category():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # مثال: حذف فئة "10 شدات"
    category_name = "10 شدات"
    
    # البحث عن الفئة
    category = await db.categories.find_one({"name": category_name})
    
    if category:
        print(f"تم العثور على: {category['name']}")
        
        # حذف (تعطيل) الفئة
        result = await db.categories.update_one(
            {"id": category['id']},
            {"$set": {"is_active": False}}
        )
        
        print(f"✅ تم الحذف - Matched: {result.matched_count}, Modified: {result.modified_count}")
    else:
        print("❌ الفئة غير موجودة")
    
    client.close()

asyncio.run(delete_category())
```

**تنفيذ:**
```bash
python3 -c "$(cat << 'EOF'
# ضع الكود أعلاه هنا
EOF
)"
```

---

#### ب) حذف عدة فئات من منتج معين

```python
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def delete_product_categories():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # مثال: حذف جميع فئات "شدات ببجي"
    product_name = "شدات ببجي"
    
    # البحث عن المنتج
    product = await db.products.find_one({"name": {"$regex": product_name, "$options": "i"}})
    
    if product:
        print(f"المنتج: {product['name']}")
        
        # حذف جميع فئات المنتج
        result = await db.categories.update_many(
            {"product_id": product['id']},
            {"$set": {"is_active": False}}
        )
        
        print(f"✅ تم حذف {result.modified_count} فئة")
    else:
        print("❌ المنتج غير موجود")
    
    client.close()

asyncio.run(delete_product_categories())
```

---

#### ج) حذف فئة بواسطة ID

```python
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def delete_by_id():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # ID الفئة المراد حذفها
    category_id = "5e50b2c9-3beb-429c-b06c-d6ee729eadb2"
    
    result = await db.categories.update_one(
        {"id": category_id},
        {"$set": {"is_active": False}}
    )
    
    print(f"✅ Matched: {result.matched_count}, Modified: {result.modified_count}")
    
    client.close()

asyncio.run(delete_by_id())
```

---

### الطريقة 3: استخدام MongoDB CLI (إذا كان متاح)

```bash
mongo mongodb://localhost:27017/test_database

# حذف فئة بالاسم
db.categories.updateOne(
  {name: "10 شدات"},
  {$set: {is_active: false}}
)

# حذف جميع فئات منتج
db.categories.updateMany(
  {product_id: "907b1bae-4daf-4ee1-859c-390bed923d47"},
  {$set: {is_active: false}}
)
```

---

## 🔍 عرض الفئات قبل الحذف

### طريقة سريعة:

```bash
curl -s "https://digital-cards-bot.preview.emergentagent.com/api/categories" | python3 -m json.tool | grep -A 3 "name"
```

### أو:

```python
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def list_categories():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    categories = await db.categories.find({}).to_list(length=None)
    
    print(f"إجمالي الفئات: {len(categories)}\n")
    
    for i, cat in enumerate(categories, 1):
        status = "🟢" if cat.get('is_active', True) else "🔴"
        print(f"{i}. {status} {cat['name']} (${cat.get('price', 0):.2f}) - ID: {cat['id']}")
    
    client.close()

asyncio.run(list_categories())
```

---

## 📋 أمثلة عملية شائعة

### مثال 1: حذف فئة "10 شدات" من ببجي

```bash
cd /app
cat > /tmp/delete_10_shdat.py << 'EOF'
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def delete():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    result = await db.categories.update_one(
        {"name": "10 شدات", "product_id": "907b1bae-4daf-4ee1-859c-390bed923d47"},
        {"$set": {"is_active": False}}
    )
    
    print(f"✅ تم حذف '10 شدات' - Matched: {result.matched_count}")
    client.close()

asyncio.run(delete())
EOF

python3 /tmp/delete_10_shdat.py
```

### مثال 2: حذف جميع فئات منتج "بطاقات قوقل بلاي"

```bash
cd /app
cat > /tmp/delete_google_play.py << 'EOF'
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def delete():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # البحث عن المنتج
    product = await db.products.find_one({"name": {"$regex": "قوقل بلاي", "$options": "i"}})
    
    if product:
        result = await db.categories.update_many(
            {"product_id": product['id']},
            {"$set": {"is_active": False}}
        )
        print(f"✅ تم حذف {result.modified_count} فئة من '{product['name']}'")
    else:
        print("❌ المنتج غير موجود")
    
    client.close()

asyncio.run(delete())
EOF

python3 /tmp/delete_google_play.py
```

---

## ⚠️ ملاحظات مهمة

1. **الحذف هو Soft Delete**: الفئة تبقى في قاعدة البيانات لكن `is_active = False`
2. **لا يمكن التراجع**: بعد الحذف، يجب استعادة الفئة يدوياً إذا أردت
3. **التأثير فوري**: الفئة ستختفي من البوت والموقع فوراً
4. **الفئات المعطلة**: لا تظهر في `/api/categories` API

---

## 🔄 استعادة فئة محذوفة

```python
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def restore():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # استعادة فئة بالـ ID
    category_id = "5e50b2c9-3beb-429c-b06c-d6ee729eadb2"
    
    result = await db.categories.update_one(
        {"id": category_id},
        {"$set": {"is_active": True}}
    )
    
    print(f"✅ تم استعادة الفئة - Modified: {result.modified_count}")
    client.close()

asyncio.run(restore())
```

---

## 📞 المساعدة

إذا واجهت أي مشكلة:
1. تحقق من الأخطاء في `/var/log/supervisor/backend.err.log`
2. تأكد من وجود الفئة: `python3 delete_categories_script.py` → خيار 1
3. استخدم السكريبت التفاعلي للحذف الآمن

---

**✅ تم إنشاء الدليل بتاريخ: 2025-10-25**
