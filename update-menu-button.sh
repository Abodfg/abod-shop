#!/bin/bash
# 🤖 تحديث Telegram Bot Menu Button
# بعد نشر الموقع على GitHub Pages

echo "🔄 جاري تحديث Menu Button..."

response=$(curl -s -X POST "https://api.telegram.org/bot8270585864:AAHcUrFnCX7nYcnAKXdlymtzZXHXghDGW-o/setChatMenuButton" \
-H "Content-Type: application/json" \
-d '{
  "menu_button": {
    "type": "web_app",
    "text": "🛍️ افتح المتجر",
    "web_app": {
      "url": "https://abodfg.github.io/abod-shop"
    }
  }
}')

echo ""
echo "📊 النتيجة:"
echo "$response" | python3 -m json.tool

if echo "$response" | grep -q '"ok":true'; then
    echo ""
    echo "✅ تم التحديث بنجاح!"
    echo "🎉 الرابط الجديد: https://abodfg.github.io/abod-shop"
    echo ""
    echo "📱 الآن:"
    echo "  1. افتح البوت في Telegram"
    echo "  2. أغلق المحادثة وافتحها من جديد"
    echo "  3. اضغط Menu Button (☰)"
    echo "  4. اضغط '🛍️ افتح المتجر'"
    echo "  5. سيفتح من رابطك الخاص!"
else
    echo ""
    echo "❌ حدث خطأ! راجع الرسالة أعلاه"
fi
