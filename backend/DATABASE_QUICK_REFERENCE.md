# مرجع سريع - قاعدة بيانات Abod Card

## 🔌 الاتصال بقاعدة البيانات
```bash
mongo mongodb://localhost:27017/abod_card_db
```

---

## 📊 المجموعات الأساسية

### 1. users (المستخدمين)
```javascript
// هيكل البيانات
{
    "id": "uuid",
    "telegram_id": 123456789,
    "username": "user123",
    "first_name": "أحمد",
    "balance": 25.50,
    "join_date": ISODate(),
    "orders_count": 5,
    "is_banned": false,
    "ban_reason": null,
    "banned_at": null
}

// أمثلة للاستعلامات
db.users.find().limit(10)                          // عرض 10 مستخدمين
db.users.find({"telegram_id": 123456789})          // البحث عن مستخدم
db.users.find({"is_banned": true})                 // المستخدمين المحظورين
db.users.find({"balance": {$gt: 50}})              // الرصيد أكبر من 50
db.users.countDocuments()                          // عدد المستخدمين الكلي
```

### 2. products (المنتجات)
```javascript
// هيكل البيانات
{
    "id": "uuid",
    "name": "PUBG Mobile",
    "description": "بطاقات شحن لعبة PUBG Mobile",
    "terms": "صالحة لمدة سنة من تاريخ الشراء",
    "is_active": true,
    "created_at": ISODate()
}

// أمثلة للاستعلامات
db.products.find({"is_active": true})              // المنتجات النشطة
db.products.updateOne(                             // تعديل منتج
    {"name": "PUBG Mobile"},
    {"$set": {"description": "وصف جديد"}}
)
db.products.deleteOne({"name": "منتج قديم"})        // حذف منتج
```

### 3. categories (الفئات)
```javascript
// هيكل البيانات
{
    "id": "uuid",
    "name": "325 شدة",
    "description": "325 شدة PUBG Mobile",
    "category_type": "gaming",
    "price": 5.00,
    "delivery_type": "code",      // code, phone, email, id, manual
    "redemption_method": "أدخل الكود في اللعبة",
    "terms": "الشروط والأحكام",
    "image_url": "https://example.com/image.jpg",
    "product_id": "معرف المنتج",
    "created_at": ISODate()
}

// أمثلة للاستعلامات
db.categories.find({"delivery_type": "code"})      // فئات الأكواد فقط
db.categories.find({"price": {$lte: 10}})          // السعر أقل من أو يساوي 10
db.categories.updateOne(                           // تحديث السعر
    {"name": "325 شدة"},
    {"$set": {"price": 6.00}}
)
```

### 4. codes (الأكواد)
```javascript
// هيكل البيانات
{
    "id": "uuid",
    "code": "ABC123DEF456",
    "description": "كود 325 شدة",
    "terms": "صالح لمدة سنة",
    "category_id": "معرف الفئة",
    "code_type": "text",          // text, number, dual
    "serial_number": "1234567890", // للنوع dual فقط
    "is_used": false,
    "used_by": null,
    "used_at": null,
    "created_at": ISODate()
}

// أمثلة للاستعلامات
db.codes.find({"is_used": false})                  // الأكواد المتاحة
db.codes.find({"category_id": "معرف_الفئة", "is_used": false})  // أكواد فئة معينة
db.codes.countDocuments({"is_used": false})        // عدد الأكواد المتاحة
db.codes.aggregate([                               // إحصائيات الأكواد لكل فئة
    {$match: {"is_used": false}},
    {$group: {_id: "$category_id", count: {$sum: 1}}}
])
```

### 5. orders (الطلبات)
```javascript
// هيكل البيانات
{
    "id": "uuid",
    "user_telegram_id": 123456789,
    "product_name": "PUBG Mobile",
    "category_name": "325 شدة",
    "price": 5.00,
    "delivery_type": "code",
    "status": "completed",        // pending, completed, failed
    "code_sent": "ABC123DEF456",
    "completion_date": ISODate(),
    "order_date": ISODate(),
    "admin_response": "تم التنفيذ"
}

// أمثلة للاستعلامات
db.orders.find({"status": "pending"})              // الطلبات المعلقة
db.orders.find({"user_telegram_id": 123456789})    // طلبات مستخدم معين
db.orders.find({                                   // الطلبات اليوم
    "order_date": {
        $gte: new Date(new Date().setHours(0,0,0,0))
    }
})
db.orders.aggregate([                              // إجمالي المبيعات اليوم
    {$match: {"order_date": {$gte: new Date(new Date().setHours(0,0,0,0))}}},
    {$group: {_id: null, total: {$sum: "$price"}}}
])
```

---

## 🔧 عمليات شائعة

### إضافة رصيد لمستخدم:
```javascript
db.users.updateOne(
    {"telegram_id": 123456789},
    {"$inc": {"balance": 50.00}}
)
```

### البحث عن المستخدمين الأكثر شراءً:
```javascript
db.users.find().sort({"orders_count": -1}).limit(10)
```

### حذف الطلبات القديمة (أكثر من 3 شهور):
```javascript
var threeMonthsAgo = new Date();
threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
db.orders.deleteMany({
    "order_date": {"$lt": threeMonthsAgo},
    "status": "completed"
})
```

### إحصائيات شاملة:
```javascript
// عدد المستخدمين النشطين (لديهم طلبات)
db.users.countDocuments({"orders_count": {$gt: 0}})

// إجمالي المبيعات هذا الشهر
var startOfMonth = new Date();
startOfMonth.setDate(1);
startOfMonth.setHours(0,0,0,0);

db.orders.aggregate([
    {$match: {"order_date": {$gte: startOfMonth}, "status": "completed"}},
    {$group: {_id: null, total: {$sum: "$price"}, count: {$sum: 1}}}
])

// أكثر المنتجات مبيعاً
db.orders.aggregate([
    {$match: {"status": "completed"}},
    {$group: {_id: "$product_name", count: {$sum: 1}}},
    {$sort: {"count": -1}},
    {$limit: 10}
])
```

---

## 🛠️ صيانة قاعدة البيانات

### نسخة احتياطية:
```bash
# نسخة كاملة
mongodump --db abod_card_db --out /backup/$(date +%Y%m%d)/

# نسخة مجموعة واحدة فقط
mongodump --db abod_card_db --collection users --out /backup/users_$(date +%Y%m%d)/
```

### استعادة النسخة الاحتياطية:
```bash
mongorestore /backup/20250926/abod_card_db/
```

### فهرسة البيانات (لتحسين الأداء):
```javascript
// فهرسة حقل telegram_id في جدول المستخدمين
db.users.createIndex({"telegram_id": 1})

// فهرسة حقل category_id في جدول الأكواد
db.codes.createIndex({"category_id": 1, "is_used": 1})

// فهرسة تاريخ الطلبات
db.orders.createIndex({"order_date": -1})
```

### تنظيف البيانات:
```javascript
// حذف المستخدمين الذين لم يقوموا بأي طلب لأكثر من 6 شهور
var sixMonthsAgo = new Date();
sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

db.users.deleteMany({
    "orders_count": 0,
    "join_date": {"$lt": sixMonthsAgo}
})

// حذف الأكواد المستخدمة القديمة (أكثر من سنة)
var oneYearAgo = new Date();
oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);

db.codes.deleteMany({
    "is_used": true,
    "used_at": {"$lt": oneYearAgo}
})
```

---

## 📈 تقارير مفيدة

### تقرير يومي:
```javascript
var today = new Date();
today.setHours(0,0,0,0);
var tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);

print("=== تقرير اليوم ===");
print("المستخدمين الجدد: " + db.users.countDocuments({"join_date": {$gte: today, $lt: tomorrow}}));
print("الطلبات الجديدة: " + db.orders.countDocuments({"order_date": {$gte: today, $lt: tomorrow}}));

var todaySales = db.orders.aggregate([
    {$match: {"order_date": {$gte: today, $lt: tomorrow}, "status": "completed"}},
    {$group: {_id: null, total: {$sum: "$price"}}}
]).toArray();

print("مبيعات اليوم: $" + (todaySales.length > 0 ? todaySales[0].total : 0));
```

### تقرير أسبوعي:
```javascript
var weekAgo = new Date();
weekAgo.setDate(weekAgo.getDate() - 7);

print("=== تقرير الأسبوع ===");
print("المستخدمين الجدد: " + db.users.countDocuments({"join_date": {$gte: weekAgo}}));
print("إجمالي الطلبات: " + db.orders.countDocuments({"order_date": {$gte: weekAgo}}));

var weekSales = db.orders.aggregate([
    {$match: {"order_date": {$gte: weekAgo}, "status": "completed"}},
    {$group: {_id: null, total: {$sum: "$price"}}}
]).toArray();

print("مبيعات الأسبوع: $" + (weekSales.length > 0 ? weekSales[0].total : 0));
```

---

## 🚨 تحذيرات مهمة

⚠️ **قبل حذف أي بيانات:**
1. تأكد من عمل نسخة احتياطية
2. اختبر الاستعلام باستخدام `find()` قبل `deleteMany()`
3. استخدم `limit()` عند التجريب

⚠️ **لا تعدل في:**
- حقول `_id` (إيدي قاعدة البيانات الداخلي)
- حقول `id` (إيدي التطبيق) إلا إذا كنت متأكداً
- الطلبات المكتملة إلا في حالات استثنائية

⚠️ **احرص على:**
- استخدام المرشحات المناسبة في الاستعلامات
- مراقبة حجم قاعدة البيانات بانتظام
- عمل فهرسة للحقول كثيرة الاستعلام

---

**💡 نصيحة:** احفظ هذا الملف كمرجع سريع واستخدم `Ctrl+F` للبحث عن ما تحتاجه!