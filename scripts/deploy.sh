#!/bin/bash

# 🚀 Abod Card Deployment Script
# هذا السكريبت يساعد في نشر البوت على منصات مختلفة

echo "🚀 بدء نشر Abod Card..."

# التحقق من وجود Git
if ! command -v git &> /dev/null; then
    echo "❌ Git غير مثبت. يرجى تثبيت Git أولاً."
    exit 1
fi

# إنشاء repository إذا لم يكن موجوداً
if [ ! -d ".git" ]; then
    echo "📦 إنشاء Git repository..."
    git init
    git add .
    git commit -m "Initial Abod Card deployment setup"
fi

# التحقق من ملفات النشر
echo "📋 التحقق من ملفات النشر..."

if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ ملف requirements.txt غير موجود في مجلد backend"
    exit 1
fi

if [ ! -f "Procfile" ]; then
    echo "✅ إنشاء Procfile..."
    echo "web: cd backend && python -m uvicorn server:app --host 0.0.0.0 --port \$PORT" > Procfile
fi

if [ ! -f "runtime.txt" ]; then
    echo "✅ إنشاء runtime.txt..."
    echo "python-3.11" > runtime.txt
fi

echo "📋 ملفات النشر جاهزة!"

# عرض خيارات النشر
echo ""
echo "🌟 اختر منصة النشر:"
echo "1) Render.com (مُوصى به)"
echo "2) Railway.app"
echo "3) Heroku"
echo "4) إنشاء ملفات النشر فقط"

read -p "أدخل اختيارك (1-4): " choice

case $choice in
    1)
        echo "🎯 تحضير النشر لـ Render.com..."
        echo ""
        echo "📋 الخطوات التالية:"
        echo "1. اذهب إلى https://render.com"
        echo "2. سجل دخول بحساب GitHub"
        echo "3. اضغط 'New' → 'Web Service'"
        echo "4. اختر هذا المشروع من GitHub"
        echo "5. استخدم هذه الإعدادات:"
        echo "   Build Command: pip install -r backend/requirements.txt"
        echo "   Start Command: cd backend && python -m uvicorn server:app --host 0.0.0.0 --port \$PORT"
        echo ""
        echo "6. أضف متغيرات البيئة:"
        echo "   MONGO_URL = mongodb+srv://username:password@cluster.mongodb.net/abod_card_db"
        echo "   DB_NAME = abod_card_db"
        echo "   CORS_ORIGINS = *"
        echo "   USER_BOT_TOKEN = 7933553585:AAHNAAxp2ZCVV_KqohmF2Mx5WL66__HYnno"
        echo "   ADMIN_BOT_TOKEN = 7835622090:AAGLTeEv-zUdNNkUrkS_L_FCd3zSUOosVeU"
        ;;
    2)
        echo "🚆 تحضير النشر لـ Railway..."
        echo ""
        echo "📋 الخطوات التالية:"
        echo "1. اذهب إلى https://railway.app"
        echo "2. سجل دخول بحساب GitHub"
        echo "3. اضغط 'New Project'"
        echo "4. اختر 'Deploy from GitHub repo'"
        echo "5. أضف متغيرات البيئة نفسها كما في Render"
        ;;
    3)
        echo "🟣 تحضير النشر لـ Heroku..."
        echo ""
        echo "📋 الخطوات التالية:"
        echo "1. ثبت Heroku CLI"
        echo "2. heroku login"
        echo "3. heroku create abod-card-bot"
        echo "4. heroku config:set MONGO_URL='mongodb+srv://...'"
        echo "5. git push heroku main"
        ;;
    4)
        echo "✅ تم إنشاء ملفات النشر فقط."
        ;;
    *)
        echo "❌ اختيار غير صحيح"
        exit 1
        ;;
esac

echo ""
echo "✅ جاهز للنشر!"
echo ""
echo "🔗 روابط مفيدة:"
echo "- Render.com: https://render.com"
echo "- Railway.app: https://railway.app"
echo "- MongoDB Atlas: https://www.mongodb.com/atlas"
echo "- دليل النشر الكامل: DEPLOYMENT_GUIDE.md"
echo ""
echo "💡 نصيحة: لا تنس تحديث Webhooks بعد النشر!"
echo "   curl -X POST 'https://your-app-url.com/api/set-webhooks'"