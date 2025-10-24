"""
Order Report Generator - توليد تقارير الطلبات كصور
"""
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime

def create_order_report_image(order_data: dict) -> io.BytesIO:
    """
    إنشاء صورة تقرير طلب
    
    Args:
        order_data: بيانات الطلب
        
    Returns:
        BytesIO: الصورة كملف بايتات
    """
    
    # إعدادات الصورة
    width = 800
    height = 1000
    bg_color = (26, 26, 46)  # خلفية داكنة
    primary_color = (0, 174, 255)  # الأزرق الكهربائي
    text_color = (255, 255, 255)
    secondary_color = (150, 150, 150)
    
    # إنشاء الصورة
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # الخطوط (استخدام خط افتراضي)
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        normal_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    y_position = 40
    
    # الشعار والعنوان
    draw.text((width//2, y_position), "Abod CARD", font=title_font, fill=primary_color, anchor="mm")
    y_position += 50
    draw.text((width//2, y_position), "Order Report", font=header_font, fill=text_color, anchor="mm")
    y_position += 60
    
    # خط فاصل
    draw.line([(50, y_position), (width-50, y_position)], fill=primary_color, width=3)
    y_position += 30
    
    # رقم الطلب
    draw.text((50, y_position), "Order Number:", font=header_font, fill=secondary_color)
    y_position += 35
    draw.text((50, y_position), order_data.get('order_number', 'N/A'), font=normal_font, fill=primary_color)
    y_position += 50
    
    # الحالة
    status_emoji = {
        'completed': '✓ Completed',
        'pending': '⏳ Pending',
        'failed': '✗ Failed',
        'cancelled': '⊘ Cancelled'
    }.get(order_data.get('status', 'pending'), 'Unknown')
    
    draw.text((50, y_position), "Status:", font=header_font, fill=secondary_color)
    y_position += 35
    status_color = (0, 255, 100) if order_data.get('status') == 'completed' else (255, 100, 0)
    draw.text((50, y_position), status_emoji, font=normal_font, fill=status_color)
    y_position += 50
    
    # خط فاصل
    draw.line([(50, y_position), (width-50, y_position)], fill=(60, 60, 80), width=2)
    y_position += 30
    
    # تفاصيل المنتج
    draw.text((50, y_position), "Product Details:", font=header_font, fill=secondary_color)
    y_position += 40
    
    draw.text((50, y_position), f"Product: {order_data.get('product_name', 'N/A')}", font=normal_font, fill=text_color)
    y_position += 30
    draw.text((50, y_position), f"Category: {order_data.get('category_name', 'N/A')}", font=normal_font, fill=text_color)
    y_position += 30
    draw.text((50, y_position), f"Price: ${order_data.get('price', 0):.2f}", font=normal_font, fill=primary_color)
    y_position += 50
    
    # خط فاصل
    draw.line([(50, y_position), (width-50, y_position)], fill=(60, 60, 80), width=2)
    y_position += 30
    
    # معلومات التاريخ
    draw.text((50, y_position), "Date & Time:", font=header_font, fill=secondary_color)
    y_position += 40
    
    order_date = order_data.get('order_date')
    if isinstance(order_date, datetime):
        draw.text((50, y_position), f"Order Date: {order_date.strftime('%Y-%m-%d %H:%M:%S')}", font=normal_font, fill=text_color)
        y_position += 30
    
    completed_at = order_data.get('completed_at')
    if completed_at and isinstance(completed_at, datetime):
        draw.text((50, y_position), f"Completed: {completed_at.strftime('%Y-%m-%d %H:%M:%S')}", font=normal_font, fill=(0, 255, 100))
        y_position += 50
    else:
        y_position += 20
    
    # خط فاصل
    draw.line([(50, y_position), (width-50, y_position)], fill=(60, 60, 80), width=2)
    y_position += 30
    
    # معلومات التوصيل
    draw.text((50, y_position), "Delivery Info:", font=header_font, fill=secondary_color)
    y_position += 40
    
    delivery_info = order_data.get('delivery_info', 'No information')
    # تقسيم النص الطويل
    max_chars = 50
    if len(delivery_info) > max_chars:
        lines = [delivery_info[i:i+max_chars] for i in range(0, len(delivery_info), max_chars)]
        for line in lines[:3]:  # أول 3 أسطر فقط
            draw.text((50, y_position), line, font=small_font, fill=text_color)
            y_position += 25
    else:
        draw.text((50, y_position), delivery_info, font=normal_font, fill=text_color)
        y_position += 40
    
    y_position += 30
    
    # خط فاصل نهائي
    draw.line([(50, y_position), (width-50, y_position)], fill=primary_color, width=3)
    y_position += 30
    
    # Footer
    draw.text((width//2, height-50), "Thank you for using Abod Card!", font=small_font, fill=secondary_color, anchor="mm")
    draw.text((width//2, height-25), "@AbodStoreVIP", font=small_font, fill=primary_color, anchor="mm")
    
    # حفظ الصورة في BytesIO
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG', optimize=True)
    img_byte_arr.seek(0)
    
    return img_byte_arr
