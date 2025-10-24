#!/bin/bash

# 🌐 Abod Card - إعداد الدومين المخصص
# هذا السكريبت يساعد في إعداد ملفات ربط الدومين

echo "🌐 مرحباً بك في معالج إعداد دومين Abod Card"
echo "================================================"

# التحقق من الدليل الحالي
if [ ! -f "backend/server.py" ]; then
    echo "❌ يرجى تشغيل السكريبت من المجلد الرئيسي للمشروع"
    exit 1
fi

echo ""
echo "🎯 أدخل معلومات دومينك:"
read -p "اسم الدومين (مثل: abodcard.42web.io): " domain_name
read -p "URL الـ Emergent الحالي (اتركه فارغ للافتراضي): " emergent_url

# استخدام القيم الافتراضية
if [ -z "$domain_name" ]; then
    domain_name="abodcard.42web.io"
fi

if [ -z "$emergent_url" ]; then
    emergent_url="https://telegr-shop-bot.preview.emergentagent.com"
fi

echo ""
echo "📋 معلومات الدومين:"
echo "الدومين: $domain_name"
echo "مصدر Emergent: $emergent_url"
echo ""

# اختيار نوع الإعداد
echo "🔧 اختر نوع الإعداد:"
echo "1) إعادة توجيه بسيطة (الأسهل)"
echo "2) عرض مدمج بـ iframe (مُوصى)"
echo "3) PHP Proxy (متقدم)" 
echo "4) إعداد .htaccess"
echo "5) إنشاء جميع الأنواع"

read -p "أدخل اختيارك (1-5): " setup_type

# إنشاء مجلد للملفات
output_dir="domain_files_${domain_name//./_}"
mkdir -p "$output_dir"

case $setup_type in
    1)
        echo "📝 إنشاء ملف إعادة التوجيه البسيط..."
        
        cat > "$output_dir/index.html" << EOF
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abod Card - متجر البطاقات الرقمية</title>
    <meta name="description" content="أفضل متجر للبطاقات الرقمية والخدمات الإلكترونية">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; padding: 0;
            background: linear-gradient(135deg, #0080FF, #0066CC);
            color: white; display: flex; justify-content: center;
            align-items: center; min-height: 100vh; text-align: center;
        }
        .container {
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px);
            padding: 3rem; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.2);
            max-width: 500px; width: 90%; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .logo { font-size: 3rem; font-weight: 800; margin-bottom: 1rem;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .countdown { font-size: 1.2rem; font-weight: 600; color: #FFD700; }
        .btn { display: inline-block; background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #333; text-decoration: none; padding: 12px 24px; border-radius: 10px;
            font-weight: 600; transition: transform 0.3s ease; margin-top: 1rem;
        }
        .btn:hover { transform: translateY(-2px); }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">⚡ Abod Card</div>
        <h2>متجر البطاقات الرقمية</h2>
        <p>جاري التحويل إلى المتجر...</p>
        <div class="countdown">خلال <span id="counter">3</span> ثوانِ</div>
        <br>
        <a href="${emergent_url}/api/app?user_id=123" class="btn">دخول المتجر الآن</a>
    </div>
    <script>
        let countdown = 3;
        const timer = setInterval(() => {
            countdown--;
            document.getElementById('counter').textContent = countdown;
            if (countdown <= 0) {
                clearInterval(timer);
                const userId = new URLSearchParams(window.location.search).get('user_id') || '123';
                window.location.href = '${emergent_url}/api/app?user_id=' + userId;
            }
        }, 1000);
    </script>
</body>
</html>
EOF
        ;;
    
    2)
        echo "📝 إنشاء ملف العرض المدمج..."
        cp "proxy_setup/index.html" "$output_dir/index.html"
        
        # تحديث URL في الملف
        sed -i "s|https://telegr-shop-bot.preview.emergentagent.com|$emergent_url|g" "$output_dir/index.html"
        sed -i "s|abodcard.42web.io|$domain_name|g" "$output_dir/index.html"
        ;;
    
    3)
        echo "📝 إنشاء ملف PHP Proxy..."
        cp "php_proxy/index.php" "$output_dir/index.php"
        
        # تحديث URL في الملف
        sed -i "s|https://telegr-shop-bot.preview.emergentagent.com|$emergent_url|g" "$output_dir/index.php"
        ;;
    
    4)
        echo "📝 إنشاء ملف .htaccess..."
        cat > "$output_dir/.htaccess" << EOF
RewriteEngine On
RewriteCond %{REQUEST_URI} ^/$
RewriteRule ^(.*)$ ${emergent_url}/api/app?user_id=123 [R=302,L]
RewriteCond %{REQUEST_URI} ^/api/(.*)$
RewriteRule ^api/(.*)$ ${emergent_url}/api/\$1 [R=302,L]
EOF
        ;;
    
    5)
        echo "📝 إنشاء جميع أنواع الملفات..."
        
        # إعادة توجيه بسيط
        mkdir -p "$output_dir/redirect"
        cp "redirect_setup/index.html" "$output_dir/redirect/"
        
        # عرض مدمج  
        mkdir -p "$output_dir/iframe"
        cp "proxy_setup/index.html" "$output_dir/iframe/"
        
        # PHP Proxy
        mkdir -p "$output_dir/php"
        cp "php_proxy/index.php" "$output_dir/php/"
        
        # .htaccess
        mkdir -p "$output_dir/htaccess"
        cp "htaccess_setup/.htaccess" "$output_dir/htaccess/"
        
        # تحديث جميع الـ URLs
        find "$output_dir" -type f \( -name "*.html" -o -name "*.php" -o -name ".htaccess" \) -exec sed -i "s|https://telegr-shop-bot.preview.emergentagent.com|$emergent_url|g" {} \;
        find "$output_dir" -type f \( -name "*.html" -o -name "*.php" \) -exec sed -i "s|abodcard.42web.io|$domain_name|g" {} \;
        ;;
    
    *)
        echo "❌ اختيار غير صحيح"
        exit 1
        ;;
esac

# إنشاء ملف README
cat > "$output_dir/README.md" << EOF
# 📁 ملفات ربط الدومين - $domain_name

## 📋 المحتويات
EOF

case $setup_type in
    1) echo "- index.html: ملف إعادة التوجيه البسيط" >> "$output_dir/README.md" ;;
    2) echo "- index.html: ملف العرض المدمج بـ iframe" >> "$output_dir/README.md" ;;
    3) echo "- index.php: ملف PHP Proxy" >> "$output_dir/README.md" ;;
    4) echo "- .htaccess: ملف إعدادات Apache" >> "$output_dir/README.md" ;;
    5) 
        cat >> "$output_dir/README.md" << EOF
- redirect/: ملفات إعادة التوجيه البسيط
- iframe/: ملفات العرض المدمج
- php/: ملفات PHP Proxy  
- htaccess/: ملفات إعدادات Apache
EOF
        ;;
esac

cat >> "$output_dir/README.md" << EOF

## 🚀 خطوات التثبيت

1. ادخل إلى cPanel أو File Manager للدومين $domain_name
2. ارفع الملفات المطلوبة إلى المجلد الرئيسي (public_html)
3. تأكد من صحة الصلاحيات (644 للملفات، 755 للمجلدات)
4. اختبر الموقع: https://$domain_name

## 🔧 الإعدادات
- الدومين المستهدف: $domain_name
- مصدر Emergent: $emergent_url
- تاريخ الإنشاء: $(date)

## 💡 نصائح
- استخدم HTTPS دائماً
- اختبر على أجهزة مختلفة
- راقب سجلات الخطأ إذا واجهت مشاكل

EOF

echo ""
echo "✅ تم إنشاء ملفات الربط بنجاح!"
echo "📁 مكان الملفات: $output_dir"
echo ""
echo "📋 الخطوات التالية:"
echo "1. ادخل إلى استضافة $domain_name"
echo "2. ارفع الملفات من المجلد: $output_dir"
echo "3. اختبر الموقع: https://$domain_name"
echo ""
echo "📖 للمزيد من التفاصيل، راجع: DOMAIN_SETUP_GUIDE.md"

# عرض محتويات المجلد
echo ""
echo "📂 الملفات المُنشأة:"
ls -la "$output_dir"