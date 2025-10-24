# 🔐 دليل حماية وإعدادات بوت Abod Shop

## 📋 جدول المحتويات
1. [إعدادات البوت الأساسية](#bot-settings)
2. [طبقات الحماية المطبقة](#security-layers)
3. [كيفية تحديث إعدادات البوت](#update-settings)
4. [توصيات الأمان الإضافية](#security-recommendations)

---

## 🤖 إعدادات البوت الأساسية {#bot-settings}

### بوت المستخدم (User Bot)
- **Bot Token:** `8270585864:AAHcUrFnCX7nYcnAKXdlymtzZXHXghDGW-o`
- **Username:** يجب تحديده عبر @BotFather
- **Webhook URL:** `https://telegr-shop-bot.preview.emergentagent.com/api/webhook/user/abod_user_webhook_secret`

### بوت الإدارة (Admin Bot)  
- **Bot Token:** `7835622090:AAGLTeEv-zUdNNkUrkS_L_FCd3zSUOosVeU`
- **Username:** يجب تحديده عبر @BotFather
- **Webhook URL:** `https://telegr-shop-bot.preview.emergentagent.com/api/webhook/admin/abod_admin_webhook_secret`

---

## 🔒 طبقات الحماية المطبقة {#security-layers}

### 1. حماية Webhook
```python
# السر الخاص بكل webhook لمنع الوصول غير المصرح
USER_WEBHOOK_SECRET = "abod_user_webhook_secret"
ADMIN_WEBHOOK_SECRET = "abod_admin_webhook_secret"
```

### 2. نظام التحقق من الصلاحيات
```python
# قائمة الإداريين المصرح لهم
ADMIN_ID = 7040570081
SYSTEM_ADMIN_ID = 1573526135
```

### 3. حماية قاعدة البيانات
- استخدام MongoDB مع اتصال محلي آمن
- عدم تخزين معلومات حساسة بشكل مباشر
- تشفير البيانات الحساسة

### 4. Rate Limiting (منع الإساءة)
- الحد الأقصى من الطلبات لكل مستخدم
- منع الـ spam والهجمات

### 5. Input Validation
- التحقق من جميع المدخلات
- منع SQL/NoSQL Injection
- تنظيف البيانات قبل التخزين

### 6. Session Management
```python
class TelegramSession:
    telegram_id: int
    state: str
    data: dict
    created_at: datetime
    expires_at: datetime
```

---

## 🛠️ كيفية تحديث إعدادات البوت {#update-settings}

### عبر BotFather (@BotFather)

#### 1. تغيير اسم البوت
```
/setname - أرسل لـ @BotFather
اختر البوت
أدخل الاسم الجديد: Abod Shop
```

#### 2. تغيير وصف البوت (Description)
```
/setdescription - أرسل لـ @BotFather
اختر البوت
أدخل الوصف:

🛍️ متجر Abod Shop - متجرك الرقمي الأول

🎮 شحن الألعاب
🎁 بطاقات الهدايا الرقمية  
🛒 التجارة الإلكترونية
📱 الاشتراكات الرقمية

💰 دفع آمن وسريع
⚡ خدمة 24/7
🔒 موثوق وآمن

📞 للدعم: @AbodStoreVIP
```

#### 3. تغيير الوصف القصير (About)
```
/setabouttext - أرسل لـ @BotFather
اختر البوت
أدخل:

⚡ Abod Shop - متجرك الرقمي المتكامل
🎮 شحن ألعاب | 🎁 بطاقات هدايا | 💳 خدمات رقمية
```

#### 4. إضافة صورة للبوت
```
/setuserpic - أرسل لـ @BotFather
اختر البوت
أرسل صورة الشعار
```

#### 5. إضافة أوامر البوت
```
/setcommands - أرسل لـ @BotFather
اختر البوت (User Bot)
أدخل:

start - بدء البوت وعرض القائمة الرئيسية
menu - عرض القائمة الرئيسية
search - البحث عن منتج
help - المساعدة والدعم
```

#### 6. تفعيل Inline Mode (اختياري)
```
/setinline - أرسل لـ @BotFather
اختر البوت
Enable
```

#### 7. تفعيل الدفع (Payments)
```
/setpayments - قد لا يكون ضرورياً لأننا نستخدم نظام دفع محلي
```

---

## 🔐 توصيات الأمان الإضافية {#security-recommendations}

### 1. حماية Token البوت
✅ **ما تم تطبيقه:**
- Tokens محفوظة في server.py (آمنة على السيرفر)
- لا يتم عرض Tokens للمستخدمين

⚠️ **توصيات إضافية:**
```bash
# انقل الـ Tokens إلى .env (أكثر أماناً)
# في /app/backend/.env أضف:
USER_BOT_TOKEN=8270585864:AAHcUrFnCX7nYcnAKXdlymtzZXHXghDGW-o
ADMIN_BOT_TOKEN=7835622090:AAGLTeEv-zUdNNkUrkS_L_FCd3zSUOosVeU

# ثم في server.py استخدم:
USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
```

### 2. حماية حساب Telegram الشخصي

#### أ. تفعيل المصادقة الثنائية (2FA)
1. افتح Telegram
2. Settings > Privacy and Security > Two-Step Verification
3. Set Additional Password
4. احفظ كلمة المرور في مكان آمن

#### ب. Sessions Management
1. Settings > Devices > Active Sessions
2. راجع جميع الأجهزة المتصلة
3. احذف أي جهاز مشبوه

#### ج. Privacy Settings
```
Settings > Privacy and Security:
- Phone Number: Nobody
- Profile Photo: My Contacts
- Last Seen: Nobody
- Forwards: Nobody
- Calls: My Contacts
- Groups & Channels: My Contacts
```

### 3. مراقبة النشاط المشبوه

#### نظام التنبيهات (مطبق)
```python
# يتم إرسال إشعار للإدارة عند:
- محاولات تسجيل دخول مشبوهة
- طلبات غير عادية
- نشاط spam
```

### 4. Backup منتظم
```bash
# احفظ نسخة من قاعدة البيانات يومياً
mongodump --db test_database --out /backup/$(date +%Y%m%d)

# احفظ الملفات المهمة
cp -r /app/backend /backup/code_$(date +%Y%m%d)
```

### 5. تحديث دوري
- راقب تحديثات Telegram Bot API
- حدّث المكتبات بانتظام
- راجع logs الأمان يومياً

### 6. Webhook Security
```python
# تحقق من IP Address
ALLOWED_IPS = [
    "149.154.160.0/20",  # Telegram IP range
    "91.108.4.0/22",
]

# تحقق من SSL Certificate
# استخدم HTTPS فقط
```

---

## 🚨 في حالة الاختراق

### خطوات الطوارئ:
1. **غيّر Token البوت فوراً**
   ```
   /revoke - عبر @BotFather
   /newbot - إنشاء بوت جديد
   ```

2. **غيّر webhook secrets**
   ```python
   # في server.py غير:
   USER_WEBHOOK_SECRET = "new_secret_here_123"
   ADMIN_WEBHOOK_SECRET = "new_admin_secret_456"
   ```

3. **راجع قاعدة البيانات**
   ```bash
   # ابحث عن تغييرات غير معتادة
   mongo test_database --eval "db.users.find().pretty()"
   mongo test_database --eval "db.orders.find().pretty()"
   ```

4. **غير كلمات المرور**
   - MongoDB password
   - Server access passwords
   - Telegram 2FA

5. **راجع Logs**
   ```bash
   tail -n 1000 /var/log/supervisor/backend.err.log
   ```

---

## 📞 الدعم الفني

لأي استفسارات أمنية:
- Telegram: @AbodStoreVIP
- تحقق من السجلات بانتظام
- راقب النشاط غير الطبيعي

---

## ✅ Checklist الأمان

- [x] Webhook secrets محددة
- [x] Admin authorization مطبقة
- [x] Input validation فعالة
- [x] Session management آمنة
- [x] Database queries محمية
- [ ] 2FA مفعلة على Telegram الشخصي
- [ ] Backup منتظم
- [ ] Monitoring system
- [ ] Rate limiting مفصل أكثر
- [ ] IP whitelisting

---

*آخر تحديث: 2025-10-24*
*النسخة: 1.0*
