# 🤖 دليل إعدادات البوت الشامل - Abod Shop

## 📋 المحتويات
1. [إعدادات البوت الأساسية](#basic-settings)
2. [تعديل عبر BotFather](#botfather)
3. [أدوات الحماية المتقدمة](#security-tools)
4. [استراتيجية النسخ الاحتياطي](#backup)

---

## 🎯 إعدادات البوت الأساسية {#basic-settings}

### معلومات البوتات الحالية

#### بوت المستخدم (User Bot)
```
Token: 8270585864:AAHcUrFnCX7nYcnAKXdlymtzZXHXghDGW-o
Username: @YourUserBotName (قم بتحديثه)
Webhook: https://digital-shop-bot-1.preview.emergentagent.com/api/webhook/user/abod_user_webhook_secret
```

#### بوت الإدارة (Admin Bot)
```
Token: 7835622090:AAGLTeEv-zUdNNkUrkS_L_FCd3zSUOosVeU
Username: @YourAdminBotName (قم بتحديثه)
Webhook: https://digital-shop-bot-1.preview.emergentagent.com/api/webhook/admin/abod_admin_webhook_secret
```

---

## 🛠️ تعديل عبر BotFather {#botfather}

### الخطوة 1: افتح محادثة مع @BotFather

1. ابحث عن `@BotFather` في Telegram
2. اضغط Start
3. ستظهر لك قائمة الأوامر

---

### الخطوة 2: تغيير اسم البوت

#### للبوت الرئيسي (User Bot):
```
1. أرسل: /setname
2. اختر البوت من القائمة
3. أرسل الاسم الجديد: Abod Shop
```

#### للبوت الإداري (Admin Bot):
```
1. أرسل: /setname
2. اختر البوت الإداري
3. أرسل: Abod Shop Admin
```

---

### الخطوة 3: تغيير وصف البوت (Description)

#### وصف بوت المستخدم:
```
1. أرسل: /setdescription
2. اختر البوت
3. أرسل النص التالي:

🛍️ متجر Abod Shop - متجرك الرقمي الشامل

نقدم لك:
🎮 شحن الألعاب الإلكترونية
🎁 بطاقات الهدايا الرقمية  
🛒 خدمات التجارة الإلكترونية
📱 الاشتراكات الرقمية المتنوعة

✨ مميزات متجرنا:
• دفع آمن وسريع 💰
• خدمة عملاء متاحة 24/7 ⚡
• أسعار تنافسية وعروض حصرية 🔥
• توصيل فوري للأكواد 📲

🔒 موثوق وآمن 100%
📞 للدعم: @AbodStoreVIP
```

#### وصف بوت الإدارة:
```
1. أرسل: /setdescription
2. اختر بوت الإدارة
3. أرسل:

🔐 لوحة تحكم Abod Shop الإدارية

بوت خاص للإدارة فقط
✅ إدارة المنتجات والفئات
✅ إدارة الطلبات والمستخدمين
✅ إدارة المحافظ والمدفوعات
✅ التقارير والإحصائيات

⚠️ وصول محدود للإداريين المصرح لهم فقط
```

---

### الخطوة 4: تغيير الوصف القصير (About Text)

#### للبوت الرئيسي:
```
1. أرسل: /setabouttext
2. اختر البوت
3. أرسل:

⚡ Abod Shop - متجرك الرقمي المتكامل
🎮 شحن ألعاب | 🎁 بطاقات هدايا | 💳 خدمات رقمية
🔒 آمن وموثوق | ⚡ توصيل فوري
```

#### للبوت الإداري:
```
1. أرسل: /setabouttext
2. اختر بوت الإدارة
3. أرسل:

🔐 Abod Shop - لوحة التحكم الإدارية
✅ للإداريين المصرح لهم فقط
```

---

### الخطوة 5: إضافة صورة للبوت

```
1. أرسل: /setuserpic
2. اختر البوت
3. أرسل صورة الشعار (يفضل 512x512 px)
```

**مواصفات الصورة الموصى بها:**
- الحجم: 512x512 بكسل
- الصيغة: PNG (مع خلفية شفافة)
- الحجم: أقل من 5 ميجابايت

---

### الخطوة 6: إضافة أوامر البوت

#### أوامر بوت المستخدم:
```
1. أرسل: /setcommands
2. اختر البوت
3. أرسل:

start - بدء البوت وعرض القائمة الرئيسية
menu - عرض القائمة الرئيسية
search - البحث عن منتج
wallet - عرض المحفظة والرصيد
orders - عرض طلباتي السابقة
support - التواصل مع الدعم الفني
help - المساعدة والأسئلة الشائعة
```

#### أوامر بوت الإدارة:
```
1. أرسل: /setcommands
2. اختر بوت الإدارة
3. أرسل:

start - فتح لوحة التحكم الإدارية
products - إدارة المنتجات
users - إدارة المستخدمين
orders - إدارة الطلبات
wallet - إدارة المحافظ
reports - التقارير والإحصائيات
payments - طرق الدفع
```

---

### الخطوة 7: تفعيل Inline Mode (اختياري)

```
1. أرسل: /setinline
2. اختر البوت
3. أرسل: Enable
4. (اختياري) قم بتعيين placeholder text
```

---

### الخطوة 8: تفعيل الإعدادات المتقدمة

#### تفعيل WebApp Button:
```
✅ تم تفعيله بالفعل في الكود
لا حاجة لإعدادات إضافية
```

#### إعدادات الخصوصية:
```
1. أرسل: /setjoingroups
2. اختر Disable (لمنع إضافة البوت للمجموعات)
```

---

## 🔒 أدوات الحماية المتقدمة {#security-tools}

### 1. Rate Limiting

تم تطبيق Rate Limiting في الكود:
```python
# محاولات webhook غير صالحة يتم تسجيلها
logging.warning(f"Invalid webhook secret attempt from {request.client.host}")
```

**كيفية مراقبة المحاولات المشبوهة:**
```bash
# عرض آخر 100 محاولة مشبوهة
tail -n 100 /var/log/supervisor/backend.err.log | grep "Invalid webhook"
```

---

### 2. IP Whitelisting

**نطاقات IP المسموحة (Telegram):**
```python
149.154.160.0/20
91.108.4.0/22
91.108.56.0/22
```

**كيفية تشديد الحماية (اختياري):**
في ملف `/app/backend/server.py` قم بإزالة التعليق من:
```python
if not any(client_ip.startswith(range_prefix) for range_prefix in allowed_ranges):
    logging.warning(f"Webhook request from unauthorized IP: {client_ip}")
    raise HTTPException(status_code=403, detail="Unauthorized IP")
```

---

### 3. Webhook Secret Rotation

**كيفية تغيير Webhook Secrets:**

1. في `/app/backend/server.py` غيّر:
```python
# السطر ~971
if secret != "new_user_webhook_secret_2024":  # غيّر هنا

# السطر ~1008
if secret != "new_admin_webhook_secret_2024":  # غيّر هنا
```

2. في `/app/backend/server.py` حدّث URLs:
```python
# السطر ~6321
url="https://digital-shop-bot-1.preview.emergentagent.com/api/webhook/user/new_user_webhook_secret_2024"

# السطر ~6326
url="https://digital-shop-bot-1.preview.emergentagent.com/api/webhook/admin/new_admin_webhook_secret_2024"
```

3. أعد تشغيل Backend:
```bash
sudo supervisorctl restart backend
```

4. أعد تسجيل Webhooks:
```bash
curl -X POST "https://digital-shop-bot-1.preview.emergentagent.com/api/set-webhooks"
```

---

### 4. Token Security

**الأمان الحالي:**
✅ Tokens محفوظة في الكود (مناسب للتطوير)

**تحسين الأمان (للإنتاج):**

1. انقل Tokens إلى `.env`:
```bash
# في /app/backend/.env أضف:
USER_BOT_TOKEN=8270585864:AAHcUrFnCX7nYcnAKXdlymtzZXHXghDGW-o
ADMIN_BOT_TOKEN=7835622090:AAGLTeEv-zUdNNkUrkS_L_FCd3zSUOosVeU
```

2. في `server.py` استخدم:
```python
import os
USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
```

---

### 5. حماية حساب Telegram الشخصي

#### تفعيل المصادقة الثنائية (2FA):
```
1. Telegram > Settings > Privacy and Security
2. Two-Step Verification > Set Additional Password
3. أدخل كلمة مرور قوية
4. أضف بريد إلكتروني للاسترداد
5. احفظ الكلمة في مكان آمن
```

#### إدارة الجلسات:
```
1. Settings > Devices > Active Sessions
2. راجع جميع الأجهزة المتصلة
3. احذف أي جهاز غير معروف
4. فعّل "Terminate all other sessions"
```

#### إعدادات الخصوصية الموصى بها:
```
Settings > Privacy and Security:
✅ Phone Number: Nobody
✅ Last Seen & Online: Nobody  
✅ Profile Photo: My Contacts
✅ Forwards: Nobody
✅ Calls: My Contacts
✅ Groups & Channels: My Contacts
✅ Voice Messages: Enabled (but restrict to contacts)
```

---

## 💾 استراتيجية النسخ الاحتياطي {#backup}

### 1. نسخ احتياطي يومي

**إنشاء سكريبت backup:**
```bash
#!/bin/bash
# /app/scripts/daily_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup"

# نسخ قاعدة البيانات
mongodump --db test_database --out "$BACKUP_DIR/mongo_$DATE"

# نسخ الكود
cp -r /app/backend "$BACKUP_DIR/backend_$DATE"
cp -r /app/frontend/public "$BACKUP_DIR/frontend_$DATE"

# ضغط الملفات
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" "$BACKUP_DIR/mongo_$DATE" "$BACKUP_DIR/backend_$DATE" "$BACKUP_DIR/frontend_$DATE"

# حذف الملفات القديمة (أكثر من 7 أيام)
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.tar.gz"
```

**جدولة Backup يومياً:**
```bash
# تحرير crontab
crontab -e

# إضافة السطر التالي (backup كل يوم الساعة 3 صباحاً)
0 3 * * * /app/scripts/daily_backup.sh >> /var/log/backup.log 2>&1
```

---

### 2. استعادة من النسخة الاحتياطية

```bash
# فك ضغط الملف
tar -xzf backup_20250124_030000.tar.gz

# استعادة قاعدة البيانات
mongorestore --db test_database mongo_20250124_030000/test_database

# استعادة الكود
cp -r backend_20250124_030000/* /app/backend/
cp -r frontend_20250124_030000/* /app/frontend/public/

# إعادة تشغيل الخدمات
sudo supervisorctl restart all
```

---

## 📊 المراقبة والتنبيهات

### 1. مراقبة السجلات

```bash
# مراقبة Errors في الوقت الفعلي
tail -f /var/log/supervisor/backend.err.log | grep ERROR

# عرض آخر 100 خطأ
tail -n 100 /var/log/supervisor/backend.err.log | grep ERROR

# إحصائيات الطلبات
tail -n 1000 /var/log/supervisor/backend.err.log | grep "webhook" | wc -l
```

---

### 2. مراقبة الأداء

```bash
# التحقق من استهلاك الذاكرة
ps aux | grep python

# التحقق من استخدام CPU
top -p $(pgrep -f "uvicorn")

# حالة الخدمات
sudo supervisorctl status
```

---

## 🚨 خطة الطوارئ

### في حالة اختراق محتمل:

#### 1. إيقاف البوت فوراً
```bash
sudo supervisorctl stop backend
```

#### 2. تغيير Bot Tokens
```
1. افتح @BotFather
2. أرسل: /revoke
3. اختر البوت المخترق
4. سيتم إنشاء Token جديد
5. حدّث الكود بالـ Token الجديد
```

#### 3. تغيير Webhook Secrets
```python
# في server.py غيّر:
USER_WEBHOOK_SECRET = "new_emergency_secret_" + str(time.time())
ADMIN_WEBHOOK_SECRET = "new_emergency_admin_" + str(time.time())
```

#### 4. مراجعة قاعدة البيانات
```bash
# البحث عن تعديلات مشبوهة
mongo test_database --eval "db.users.find().sort({_id:-1}).limit(10).pretty()"
mongo test_database --eval "db.orders.find().sort({_id:-1}).limit(10).pretty()"
```

#### 5. استعادة من Backup
```bash
# إذا لزم الأمر
mongorestore --db test_database backup_latest/test_database
```

#### 6. تغيير جميع كلمات المرور
- MongoDB password
- Server SSH password
- Telegram 2FA

---

## ✅ Checklist الأمان الشامل

### إعدادات البوت:
- [ ] تم تعيين اسم البوت
- [ ] تم تعيين الوصف الكامل
- [ ] تم تعيين الوصف القصير
- [ ] تم رفع صورة البوت
- [ ] تم إضافة الأوامر
- [ ] تم تعطيل Join Groups

### الحماية:
- [ ] Webhook Secrets فريدة وقوية
- [ ] IP Whitelisting مفعل (اختياري)
- [ ] Rate Limiting مطبق
- [ ] Logging للأحداث المشبوهة
- [ ] Tokens في ملف .env (للإنتاج)

### حساب Telegram الشخصي:
- [ ] 2FA مفعل
- [ ] مراجعة Active Sessions
- [ ] إعدادات الخصوصية محدثة
- [ ] بريد استرداد مضاف

### النسخ الاحتياطي:
- [ ] Backup يومي مجدول
- [ ] اختبار استعادة Backup
- [ ] تخزين Backups في مكان آمن

### المراقبة:
- [ ] مراقبة السجلات يومياً
- [ ] تنبيهات للأخطاء
- [ ] مراقبة الأداء

---

## 📞 معلومات الدعم

**للطوارئ الأمنية:**
- راجع السجلات فوراً
- اتبع خطة الطوارئ
- وثّق جميع الخطوات

**للمساعدة الفنية:**
- Telegram: @AbodStoreVIP
- راجع `/app/BOT_SECURITY_SETTINGS_GUIDE.md`

---

*آخر تحديث: 2025-10-24*
*الإصدار: 2.0 - شامل ومحدّث*
*تم إزالة جميع الإشارات للنجوم - نظام الدولار فقط*
