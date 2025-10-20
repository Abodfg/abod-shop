<?php
// Abod Card - PHP Proxy للربط مع Emergent
header('Content-Type: text/html; charset=UTF-8');
header('X-Powered-By: Abod Card');

// إعدادات الـ proxy
$emergent_base_url = 'https://abod-digital.preview.emergentagent.com';
$default_user_id = isset($_GET['user_id']) ? $_GET['user_id'] : rand(100000, 999999);

// تحديد المسار المطلوب
$request_path = isset($_GET['path']) ? $_GET['path'] : '/api/app';
$query_params = http_build_query(['user_id' => $default_user_id]);

// URL كامل للـ Emergent
$target_url = $emergent_base_url . $request_path . '?' . $query_params;

// إعدادات cURL
$curl = curl_init();
curl_setopt_array($curl, [
    CURLOPT_URL => $target_url,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_USERAGENT => 'Abod Card Proxy/1.0',
    CURLOPT_HTTPHEADER => [
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language: ar,en;q=0.5',
        'Cache-Control: no-cache',
    ],
]);

// تنفيذ الطلب
$response = curl_exec($curl);
$http_code = curl_getinfo($curl, CURLINFO_HTTP_CODE);
curl_close($curl);

// معالجة النتيجة
if ($response && $http_code == 200) {
    // تحديث الروابط في المحتوى لتشير للدومين المحلي
    $response = str_replace(
        $emergent_base_url,
        'https://' . $_SERVER['HTTP_HOST'],
        $response
    );
    
    // إضافة معلومات إضافية للتتبع
    $response = str_replace(
        '</head>',
        '<meta name="proxy-source" content="Abod Card PHP Proxy">
        <meta name="original-url" content="' . htmlspecialchars($target_url) . '">
        <script>
            console.log("تم تحميل الصفحة عبر Abod Card Proxy");
            console.log("المصدر الأصلي: ' . $target_url . '");
        </script>
        </head>',
        $response
    );
    
    echo $response;
} else {
    // في حالة فشل التحميل، عرض صفحة خطأ جميلة
    ?>
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>خطأ في التحميل - Abod Card</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0080FF, #0066CC);
                color: white;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                text-align: center;
            }
            .error-container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 3rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                max-width: 500px;
                width: 90%;
            }
            .error-icon {
                font-size: 4rem;
                margin-bottom: 1rem;
            }
            .error-title {
                font-size: 1.8rem;
                margin-bottom: 1rem;
                font-weight: 600;
            }
            .error-message {
                font-size: 1rem;
                margin-bottom: 2rem;
                opacity: 0.9;
                line-height: 1.6;
            }
            .retry-btn {
                background: linear-gradient(135deg, #FFD700, #FFA500);
                color: #333;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 10px;
                font-weight: 600;
                transition: transform 0.3s ease;
                border: none;
                cursor: pointer;
                display: inline-block;
            }
            .retry-btn:hover {
                transform: translateY(-2px);
            }
            .debug-info {
                margin-top: 2rem;
                padding-top: 2rem;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                font-size: 0.8rem;
                opacity: 0.7;
            }
        </style>
    </head>
    <body>
        <div class="error-container">
            <div class="error-icon">⚠️</div>
            <div class="error-title">خطأ في تحميل المتجر</div>
            <div class="error-message">
                عذراً، حدث خطأ أثناء محاولة الاتصال بخادم المتجر.<br>
                يرجى المحاولة مرة أخرى خلال بضع دقائق.
            </div>
            <button class="retry-btn" onclick="window.location.reload()">
                🔄 إعادة المحاولة
            </button>
            
            <div class="debug-info">
                رمز الخطأ: <?php echo $http_code; ?><br>
                الوقت: <?php echo date('Y-m-d H:i:s'); ?><br>
                المحاولة: <?php echo $target_url; ?>
            </div>
        </div>
        
        <script>
            // إعادة المحاولة التلقائية بعد 30 ثانية
            setTimeout(() => {
                console.log('إعادة المحاولة التلقائية...');
                window.location.reload();
            }, 30000);
        </script>
    </body>
    </html>
    <?php
}

// تسجيل الزيارة (اختياري)
$log_entry = date('Y-m-d H:i:s') . " - IP: " . $_SERVER['REMOTE_ADDR'] . " - User ID: " . $default_user_id . " - URL: " . $target_url . " - Status: " . $http_code . "\n";
file_put_contents('access.log', $log_entry, FILE_APPEND | LOCK_EX);
?>