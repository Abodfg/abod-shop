        // Global Variables
        let tgWebApp = null;
        let userTelegramId = null;
        let userData = {};
        let products = [];
        let categories = [];
        let userOrders = [];

        // API Base URL - Backend Server
        const API_BASE = 'https://telegr-shop-bot.preview.emergentagent.com/api';

        // Initialize App
        function initApp() {
            // Initialize Telegram Web App
            if (window.Telegram && window.Telegram.WebApp) {
                tgWebApp = window.Telegram.WebApp;
                tgWebApp.ready();
                tgWebApp.expand();
                
                // Set colors
                tgWebApp.setHeaderColor('#1A1F2E');
                tgWebApp.setBackgroundColor('#1A1F2E');
                
                // Get user data
                if (tgWebApp.initDataUnsafe && tgWebApp.initDataUnsafe.user) {
                    userTelegramId = tgWebApp.initDataUnsafe.user.id;
                    userData = tgWebApp.initDataUnsafe.user;
                    
                    // Update user name in header
                    const userNameEl = document.getElementById('user-name');
                    if (userNameEl && userData.first_name) {
                        userNameEl.textContent = `مرحباً ${userData.first_name}`;
                    }
                }
            }

            // Fallback: Get user ID from URL
            if (!userTelegramId) {
                const urlParams = new URLSearchParams(window.location.search);
                userTelegramId = urlParams.get('user_id');
                
                // If no user_id, check localStorage for guest user
                if (!userTelegramId) {
                    const guestUser = localStorage.getItem('guestUser');
                    if (guestUser) {
                        const guest = JSON.parse(guestUser);
                        userData = guest;
                        userTelegramId = guest.guest_id;
                    } else {
                        // Show guest registration modal
                        showGuestRegistrationModal();
                    }
                }
            }
                const urlParams = new URLSearchParams(window.location.search);
                userTelegramId = urlParams.get('user_id');
            }

            // Load initial data
            loadData();
        }

        // Load Data
        async function loadData() {
            showLoading();
            
            try {
                // Load all data in parallel
                const [productsRes, categoriesRes, usersRes, ordersRes] = await Promise.all([
                    fetch(`${API_BASE}/products`),
                    fetch(`${API_BASE}/categories`),
                    userTelegramId ? fetch(`${API_BASE}/users`) : null,
                    userTelegramId ? fetch(`${API_BASE}/orders`) : null
                ]);

                // Parse responses
                products = await productsRes.json();
                categories = await categoriesRes.json();
                
                if (usersRes) {
                    const users = await usersRes.json();
                    const currentUser = users.find(u => u.telegram_id == userTelegramId);
                    if (currentUser) {
                        userData = { ...userData, ...currentUser };
                        updateUserBalance();
                        updateUserStats();
                    }
                }

                if (ordersRes) {
                    const allOrders = await ordersRes.json();
                    userOrders = allOrders.filter(order => order.telegram_id == userTelegramId);
                }

                // Setup UI
                setupProducts();
                setupOrders();
                
            } catch (error) {
                console.error('Error loading data:', error);
                showNotification('حدث خطأ في تحميل البيانات', 'error');
            } finally {
                hideLoading();
            }
        }

        // Update User Balance (USD only)
        function updateUserBalance() {
            const balanceElements = document.querySelectorAll('#user-balance, #wallet-balance');
            balanceElements.forEach(el => {
                if (userData.balance !== undefined) {
                    el.textContent = `$${parseFloat(userData.balance).toFixed(2)}`;
                } else {
                    el.textContent = '$0.00';
                }
            });
        }

        // Update User Stats
        function updateUserStats() {
            if (userData.orders_count !== undefined) {
                const ordersElement = document.getElementById('orders-count');
                if (ordersElement) ordersElement.textContent = userData.orders_count;
            }
            
            if (userData.join_date) {
                const joinDate = new Date(userData.join_date).toLocaleDateString('ar');
                const joinDateElement = document.getElementById('join-date');
                if (joinDateElement) joinDateElement.textContent = joinDate;
            }
        }

        // Setup Products
        function setupProducts() {
            // Featured products (first 6)
            const featuredContainer = document.getElementById('featured-products');
            if (featuredContainer) {
                featuredContainer.innerHTML = renderProducts(products.slice(0, 6));
            }

            // All products
            const allContainer = document.getElementById('all-products');
            if (allContainer) {
                allContainer.innerHTML = renderProducts(products);
            }

            // Category-specific products
            setupCategoryProducts();
        }

        // Setup Category Products
        function setupCategoryProducts() {
            // استخدام category_type مباشرة بدلاً من الكلمات المفاتيح
            const categoryTypes = ['games', 'gift_cards', 'ecommerce', 'subscriptions'];

            categoryTypes.forEach(categoryType => {
                const container = document.getElementById(`${categoryType}-products`);
                if (container) {
                    // البحث عن المنتجات حسب category_type
                    const categoryProducts = products.filter(product => 
                        product.category_type === categoryType
                    );
                    
                    // إذا لم توجد منتجات بـ category_type، استخدم الكلمات المفاتيح كاحتياطي
                    if (categoryProducts.length === 0) {
                        const fallbackMappings = {
                            'games': ['game', 'gaming', 'play', 'steam', 'xbox', 'playstation'],
                            'gift_cards': ['gift', 'card', 'amazon', 'apple', 'google', 'itunes'],
                            'ecommerce': ['shop', 'store', 'market', 'ecommerce', 'commerce'],
                            'subscriptions': ['netflix', 'spotify', 'subscription', 'premium', 'plus', 'pro']
                        };
                        
                        const keywords = fallbackMappings[categoryType] || [];
                        const fallbackProducts = products.filter(product => 
                            keywords.some(keyword => 
                                product.name.toLowerCase().includes(keyword)
                            )
                        );
                        container.innerHTML = renderProducts(fallbackProducts);
                    } else {
                        container.innerHTML = renderProducts(categoryProducts);
                    }
                }
            });
        }

        // Render Products
        function renderProducts(productList) {
            if (!productList || productList.length === 0) {
                return `
                    <div class="empty-state">
                        <div class="empty-icon">📦</div>
                        <h3 class="empty-title">لا توجد منتجات</h3>
                        <p class="empty-text">لم يتم العثور على منتجات في هذه الفئة</p>
                    </div>
                `;
            }

            return productList.map((product, index) => {
                let badge = '';
                if (index === 0) badge = '<span class="product-badge hot">الأكثر طلباً</span>';
                else if (index === 1) badge = '<span class="product-badge new">جديد</span>';
                else if (Math.random() > 0.7) badge = '<span class="product-badge discount">خصم</span>';

                return `
                    <div class="product-card" onclick="viewProduct('${product.id}', '${product.name}')">
                        ${badge}
                        <div class="product-image">🎮</div>
                        <div class="product-info">
                            <h3 class="product-title">${product.name}</h3>
                            <p class="product-description">${product.description || 'منتج رقمي عالي الجودة'}</p>
                            <div class="product-price">
                                <span class="price-current">ابدأ من $5.00</span>
                            </div>
                            <button class="product-button">عرض الباقات</button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // View Product
        async function viewProduct(productId, productName) {
            showLoading();
            
            try {
                // Ensure categories are loaded first
                if (!categories || categories.length === 0) {
                    const categoriesRes = await fetch(`${API_BASE}/categories`);
                    categories = await categoriesRes.json();
                }
                
                // Get categories for this product
                const productCategories = categories.filter(cat => cat.product_id === productId);
                
                if (productCategories.length === 0) {
                    showNotification('لا توجد باقات متاحة لهذا المنتج', 'warning');
                    hideLoading();
                    return;
                }

                // Switch to products section first
                showSection('products');
                
                // Create products grid with categories
                const productsGrid = document.getElementById('all-products') || 
                                   document.getElementById('featured-products');
                
                if (productsGrid) {
                    productsGrid.innerHTML = `
                        <div class="category-header" style="grid-column: 1 / -1; text-align: center; padding: 2rem; background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%); border-radius: var(--radius-lg); margin-bottom: 2rem; color: white;">
                            <h2 style="margin: 0 0 0.5rem 0; font-size: 1.5rem;">${productName}</h2>
                            <p style="margin: 0 0 1rem 0; opacity: 0.9;">اختر الباقة المناسبة لك</p>
                            <button class="btn-secondary" onclick="loadData(); showSection('home');" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 0.5rem 1rem; border-radius: var(--radius); cursor: pointer;">العودة للرئيسية</button>
                        </div>
                        ${renderCategories(productCategories)}
                    `;
                }
                
            } catch (error) {
                console.error('Error viewing product:', error);
                showNotification('حدث خطأ في عرض المنتج', 'error');
            } finally {
                hideLoading();
            }
        }

        // Render Categories
        function renderCategories(categoryList) {
            return categoryList.map((category, index) => {
                let badge = '';
                if (index === 0 && categoryList.length > 1) {
                    badge = '<span class="product-badge hot">الأكثر طلباً</span>';
                } else if (index === categoryList.length - 1 && categoryList.length > 2) {
                    badge = '<span class="product-badge new">أفضل قيمة</span>';
                }

                return `
                    <div class="product-card">
                        ${badge}
                        <div class="product-image">💎</div>
                        <div class="product-info">
                            <h3 class="product-title">${category.name}</h3>
                            <p class="product-description">${category.description || 'باقة رقمية مميزة'}</p>
                            <div class="product-price">
                                <span class="price-current">$${category.price?.toFixed(2) || '0.00'}</span>
                            </div>
                            <button class="product-button" onclick="purchaseCategory('${category.id}', '${category.name}', ${category.price}, '${category.delivery_type}')">
                                شراء
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Input Modal Functions
        let inputModalCallback = null;
        
        function showInputModal(title, label, placeholder, helpText, inputType, callback) {
            document.getElementById('modal-title').textContent = title;
            document.getElementById('input-label').textContent = label;
            document.getElementById('user-input').placeholder = placeholder;
            document.getElementById('input-help').textContent = helpText;
            document.getElementById('user-input').type = inputType;
            document.getElementById('user-input').value = '';
            
            inputModalCallback = callback;
            
            const modal = document.getElementById('input-modal');
            modal.style.display = 'flex';
            
            // Focus on input
            setTimeout(() => {
                document.getElementById('user-input').focus();
            }, 100);
            
            // Telegram haptic feedback
            if (tgWebApp && tgWebApp.HapticFeedback) {
                tgWebApp.HapticFeedback.impactOccurred('light');
            }
        }
        
        function closeInputModal() {
            const modal = document.getElementById('input-modal');
            modal.style.display = 'none';
            inputModalCallback = null;
            
            // Telegram haptic feedback
            if (tgWebApp && tgWebApp.HapticFeedback) {
                tgWebApp.HapticFeedback.impactOccurred('light');
            }
        }
        
        function confirmInput() {
            const inputValue = document.getElementById('user-input').value.trim();
            const inputType = document.getElementById('user-input').type;
            
            // Validation
            if (!inputValue) {
                showNotification('يرجى إدخال البيانات المطلوبة', 'error');
                return;
            }
            
            // Email validation
            if (inputType === 'email' && !inputValue.includes('@')) {
                showNotification('يرجى إدخال بريد إلكتروني صحيح', 'error');
                return;
            }
            
            // Phone validation (basic)
            if (inputType === 'tel' && inputValue.length < 8) {
                showNotification('يرجى إدخال رقم هاتف صحيح', 'error');
                return;
            }
            
            if (inputModalCallback) {
                inputModalCallback(inputValue);
                closeInputModal();
            }
            
            // Telegram haptic feedback
            if (tgWebApp && tgWebApp.HapticFeedback) {
                tgWebApp.HapticFeedback.notificationOccurred('success');
            }
        }
        
        // Keyboard events for modal
        document.addEventListener('keydown', function(event) {
            const modal = document.getElementById('input-modal');
            if (modal.style.display === 'flex') {
                if (event.key === 'Enter') {
                    confirmInput();
                } else if (event.key === 'Escape') {
                    closeInputModal();
                }
            }
        });

        // Continue Purchase (helper function)
        async function continuePurchase(categoryId, categoryName, price, deliveryType, additionalData) {
            // Show confirmation with delivery method (USD)
            let deliveryInfo = getDeliveryTypeName(deliveryType);
            if (additionalData) {
                const dataValue = additionalData.user_id || additionalData.email || additionalData.phone;
                deliveryInfo += `\nالمعلومات المطلوبة: ${dataValue}`;
            }
            
            if (!confirm(`تأكيد الشراء\n\nالمنتج: ${categoryName}\nالسعر: $${price.toFixed(2)}\nطريقة التسليم: ${deliveryInfo}\n\nهل تريد المتابعة؟`)) {
                return;
            }

            showLoading();

            try {
                const purchaseData = {
                    user_telegram_id: parseInt(userTelegramId),
                    category_id: categoryId,
                    delivery_type: deliveryType || 'code'
                };

                // Add additional data for specific delivery types
                if (additionalData) {
                    purchaseData.additional_info = additionalData;
                }

                const response = await fetch(`${API_BASE}/purchase`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(purchaseData)
                });

                const result = await response.json();
                
                if (response.ok && result.success) {
                    let message = 'تم الشراء بنجاح!';
                    
                    if (result.order_type === 'instant') {
                        message = `تم الشراء بنجاح!\n${categoryName}\nتم إرسال الكود إلى البوت`;
                    } else {
                        message = `تم إنشاء الطلب بنجاح!\n${categoryName}\nسيتم التنفيذ خلال ${result.estimated_time || '10-30 دقيقة'}`;
                    }
                    
                    showNotification(message, 'success');
                    
                    // Update local balance
                    if (userData.balance !== undefined) {
                        userData.balance -= price;
                        updateUserBalance();
                    }

                    // Navigate to orders after 3 seconds
                    setTimeout(() => {
                        showSection('orders');
                        loadData(); // Refresh orders
                    }, 3000);
                    
                } else {
                    const errorMessage = result.detail || result.message || 'فشل في إتمام الشراء';
                    showNotification(errorMessage, 'error');
                }

            } catch (error) {
                console.error('Purchase error:', error);
                showNotification('حدث خطأ أثناء الشراء', 'error');
            } finally {
                hideLoading();
            }
        }

        // Purchase Category
        async function purchaseCategory(categoryId, categoryName, price, deliveryType) {
            if (!userTelegramId) {
                showNotification('يرجى فتح التطبيق من خلال البوت', 'error');
                return;
            }

            // Check balance (USD)
            const userBalance = parseFloat(userData.balance || 0);
            
            if (userBalance < price) {
                showNotification(
                    `رصيد غير كافي\nرصيدك: $${userBalance.toFixed(2)}\nالمطلوب: $${price.toFixed(2)}\n\n💳 يمكنك شحن محفظتك من الطرق المتاحة في البوت`, 
                    'error'
                );
                
                // توجيه للمحفظة بعد 3 ثوانِ
                setTimeout(() => {
                    showSection('wallet');
                }, 3000);
                
                return;
            }

            // Handle delivery types that require input
            if (deliveryType === 'id') {
                showInputModal(
                    'إدخال معرف المستخدم',
                    'يرجى إدخال الـ ID المطلوب:',
                    'مثال: 123456789',
                    'تأكد من صحة المعرف المدخل',
                    'text',
                    (userId) => {
                        const additionalData = { user_id: userId };
                        console.log('ID entered successfully:', userId);
                        continuePurchase(categoryId, categoryName, price, deliveryType, additionalData);
                    }
                );
                return;
                
            } else if (deliveryType === 'email') {
                showInputModal(
                    'إدخال البريد الإلكتروني',
                    'يرجى إدخال البريد الإلكتروني:',
                    'example@domain.com',
                    'سيتم إرسال المنتج إلى هذا البريد',
                    'email',
                    (email) => {
                        const additionalData = { email: email };
                        console.log('Email entered successfully:', email);
                        continuePurchase(categoryId, categoryName, price, deliveryType, additionalData);
                    }
                );
                return;
                
            } else if (deliveryType === 'phone') {
                showInputModal(
                    'إدخال رقم الهاتف',
                    'يرجى إدخال رقم الهاتف:',
                    '+966xxxxxxxxx',
                    'تأكد من صحة رقم الهاتف',
                    'phone',
                    (phone) => {
                        const additionalData = { phone: phone };
                        console.log('Phone entered successfully:', phone);
                        continuePurchase(categoryId, categoryName, price, deliveryType, additionalData);
                    }
                );
                return;
            }

            // If no input required, continue directly
            continuePurchase(categoryId, categoryName, price, deliveryType, null);
        }

        // Continue Purchase (separated for modal callback)
        async function continuePurchase(categoryId, categoryName, price, deliveryType, additionalData) {
            // Check if guest user
            if (isGuestUser()) {
                // Guest users: Send order via WhatsApp
                const phone = userData.phone;
                const name = userData.first_name || 'ضيف';
                
                let orderDetails = `طلب جديد من ${name}\n\n`;
                orderDetails += `📦 المنتج: ${categoryName}\n`;
                orderDetails += `💰 السعر: $${price.toFixed(2)}\n`;
                orderDetails += `📱 رقم الهاتف: ${phone}\n`;
                
                if (additionalData) {
                    const dataValue = additionalData.user_id || additionalData.email || additionalData.phone;
                    orderDetails += `📝 معلومات إضافية: ${dataValue}\n`;
                }
                
                // Create WhatsApp link to support
                const supportPhone = '967783380906'; // رقم Abod Shop Support
                const whatsappMessage = encodeURIComponent(orderDetails);
                const whatsappUrl = `https://wa.me/${supportPhone}?text=${whatsappMessage}`;
                
                if (confirm(`تأكيد الطلب\n\n${categoryName}\nالسعر: $${price.toFixed(2)}\n\nسيتم فتح WhatsApp للتواصل مع الدعم وإتمام الطلب. هل تريد المتابعة؟`)) {
                    window.open(whatsappUrl, '_blank');
                    showNotification('يرجى إكمال الطلب عبر WhatsApp. سيتم الرد عليك خلال دقائق', 'success');
                }
                return;
            }
            
            // Regular Telegram users
            let deliveryInfo = getDeliveryTypeName(deliveryType);
            if (additionalData) {
                const dataValue = additionalData.user_id || additionalData.email || additionalData.phone;
                deliveryInfo += `\nالمعلومات المطلوبة: ${dataValue}`;
            }
            if (!confirm(`تأكيد الشراء\n\nالمنتج: ${categoryName}\nالسعر: $${price.toFixed(2)}\nطريقة التسليم: ${deliveryInfo}\n\nهل تريد المتابعة؟`)) {
                return;
            }

            showLoading();

            try {
                const purchaseData = {
                    user_telegram_id: parseInt(userTelegramId),
                    category_id: categoryId,
                    delivery_type: deliveryType || 'code'
                };

                // Add additional data for specific delivery types
                if (additionalData) {
                    purchaseData.additional_info = additionalData;
                }

                const response = await fetch(`${API_BASE}/purchase`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(purchaseData)
                });

                const result = await response.json();
                
                if (response.ok && result.success) {
                    let message = 'تم الشراء بنجاح!';
                    
                    if (result.order_type === 'instant') {
                        message = `تم الشراء بنجاح!\n${categoryName}\nتم إرسال الكود إلى البوت`;
                    } else {
                        message = `تم إنشاء الطلب بنجاح!\n${categoryName}\nسيتم التنفيذ خلال ${result.estimated_time || '10-30 دقيقة'}`;
                    }
                    
                    showNotification(message, 'success');
                    
                    // Update local balance
                    if (userData.balance !== undefined) {
                        userData.balance -= price;
                        updateUserBalance();
                    }

                    // Navigate to orders after 3 seconds
                    setTimeout(() => {
                        showSection('orders');
                        loadData(); // Refresh orders
                    }, 3000);
                    
                } else {
                    const errorMessage = result.detail || result.message || 'فشل في إتمام الشراء';
                    showNotification(errorMessage, 'error');
                }

            } catch (error) {
                console.error('Purchase error:', error);
                showNotification('حدث خطأ أثناء الشراء', 'error');
            } finally {
                hideLoading();
            }
        }

        // Setup Orders
        function setupOrders() {
            const ordersContainer = document.getElementById('orders-container');
            if (!ordersContainer) return;

            if (!userOrders || userOrders.length === 0) {
                ordersContainer.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📦</div>
                        <h3 class="empty-title">لا توجد طلبات</h3>
                        <p class="empty-text">لم تقم بأي طلبات حتى الآن</p>
                        <button class="btn-primary" onclick="showSection('products')">
                            تصفح المنتجات
                        </button>
                    </div>
                `;
                return;
            }

            // Sort orders by date (newest first)
            userOrders.sort((a, b) => new Date(b.order_date) - new Date(a.order_date));

            ordersContainer.innerHTML = userOrders.map(order => {
                const orderDate = new Date(order.order_date);
                const dateStr = orderDate.toLocaleDateString('ar');
                const timeStr = orderDate.toLocaleTimeString('ar');
                
                let codeSection = '';
                if (order.status === 'completed' && order.code_sent) {
                    codeSection = `
                        <div class="order-code">
                            <div class="code-text">${order.code_sent}</div>
                            <button class="copy-button" onclick="copyCode('${order.code_sent}', this)">
                                نسخ الكود
                            </button>
                        </div>
                    `;
                }

                return `
                    <div class="order-card">
                        <div class="order-header">
                            <div class="order-id">طلب #${order.id?.substring(0, 8) || 'غير محدد'}</div>
                            <div class="order-status ${order.status}">
                                ${order.status === 'completed' ? '✅ مكتمل' : '⏳ قيد التنفيذ'}
                            </div>
                        </div>
                        <div class="order-details">
                            <div class="order-product">${order.product_name} - ${order.category_name}</div>
                            <div class="order-meta">السعر: $${order.price?.toFixed(2) || '0.00'}</div>
                            <div class="order-meta">التاريخ: ${dateStr} - ${timeStr}</div>
                        </div>
                        ${codeSection}
                    </div>
                `;
            }).join('');
        }

        // Copy Code
        function copyCode(code, button) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(code).then(() => {
                    const originalText = button.textContent;
                    button.textContent = '✅ تم النسخ!';
                    button.style.background = '#28a745';
                    
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.style.background = '';
                    }, 2000);
                    
                    showNotification('تم نسخ الكود بنجاح', 'success');
                }).catch(() => {
                    showNotification('فشل في نسخ الكود', 'error');
                });
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = code;
                document.body.appendChild(textArea);
                textArea.select();
                try {
                    document.execCommand('copy');
                    showNotification('تم نسخ الكود بنجاح', 'success');
                } catch (err) {
                    showNotification('فشل في نسخ الكود', 'error');
                }
                document.body.removeChild(textArea);
            }
        }

        // Recharge Wallet
        function rechargeWallet() {
            if (tgWebApp && tgWebApp.sendData) {
                // إرسال بيانات واضحة للبوت لمعالجة شحن المحفظة
                tgWebApp.sendData(JSON.stringify({ 
                    type: 'wallet_action',
                    action: 'charge_wallet',
                    user_id: userTelegramId 
                }));
                showNotification('تم إرسال طلب شحن المحفظة إلى البوت', 'success');
                
                // إغلاق الـ WebApp والعودة للبوت بعد إرسال البيانات
                setTimeout(() => {
                    if (tgWebApp && tgWebApp.close) {
                        tgWebApp.close();
                    }
                }, 1000);
            } else {
                // تحويل للبوت مباشرة إذا لم تعمل sendData
                showNotification('سيتم تحويلك للبوت لشحن المحفظة', 'info');
                
                if (tgWebApp && tgWebApp.close) {
                    tgWebApp.close();
                } else {
                    // كنسخ احتياطية - فتح البوت في نافذة جديدة
                    window.open(`https://t.me/AbodCard_bot`, '_blank');
                }
            }
        }

        // Start Chat
        function startChat() {
            if (tgWebApp && tgWebApp.sendData) {
                tgWebApp.sendData(JSON.stringify({ 
                    action: 'start_support',
                    user_id: userTelegramId 
                }));
                showNotification('تم إرسال طلب الدعم إلى البوت', 'success');
            } else if (tgWebApp && tgWebApp.close) {
                // إغلاق الويب أب والعودة للبوت للدعم
                tgWebApp.close();
            } else {
                showNotification('يرجى استخدام البوت للتواصل مع الدعم', 'warning');
            }
        }

        // Search Function
        async function performSearch() {
            const searchInput = document.getElementById('search-input');
            const query = searchInput.value.trim();
            
            if (!query) {
                showNotification('يرجى إدخال كلمة بحث', 'warning');
                return;
            }
            
            showSection('search');
            const resultsContainer = document.getElementById('search-results');
            resultsContainer.innerHTML = '<div style="text-align: center; padding: 2rem;"><div class="spinner"></div><p>جاري البحث...</p></div>';
            
            try {
                // Search in products
                const searchedProducts = products.filter(product => 
                    product.name.toLowerCase().includes(query.toLowerCase()) ||
                    (product.description && product.description.toLowerCase().includes(query.toLowerCase()))
                );
                
                // Search in categories
                const searchedCategories = categories.filter(category =>
                    category.name.toLowerCase().includes(query.toLowerCase()) ||
                    (category.description && category.description.toLowerCase().includes(query.toLowerCase()))
                );
                
                if (searchedProducts.length === 0 && searchedCategories.length === 0) {
                    resultsContainer.innerHTML = `
                        <div style="text-align: center; padding: 3rem;">
                            <h3 style="color: var(--secondary); margin-bottom: 1rem;">❌ لم يتم العثور على نتائج</h3>
                            <p>لم يتم العثور على منتجات أو فئات تطابق "<strong>${query}</strong>"</p>
                            <br>
                            <p style="color: var(--text-muted);">💡 اقتراحات:</p>
                            <p style="color: var(--text-muted);">• تأكد من كتابة الاسم بشكل صحيح</p>
                            <p style="color: var(--text-muted);">• جرب كلمات مفتاحية أخرى</p>
                            <br>
                            <button onclick="showSection('home')" class="action-btn">🏠 العودة للرئيسية</button>
                        </div>
                    `;
                    return;
                }
                
                let resultsHTML = '';
                
                // Display products results
                if (searchedProducts.length > 0) {
                    resultsHTML += `<h2 style="margin-bottom: 1rem;">🎮 المنتجات (${searchedProducts.length})</h2>`;
                    resultsHTML += '<div class="product-grid">';
                    
                    searchedProducts.forEach(product => {
                        const productCategories = categories.filter(cat => cat.product_id === product.id);
                        const priceRange = productCategories.length > 0 
                            ? `$${Math.min(...productCategories.map(c => c.price)).toFixed(2)} - $${Math.max(...productCategories.map(c => c.price)).toFixed(2)}`
                            : 'السعر حسب الفئة';
                        
                        resultsHTML += `
                            <div class="product-card" onclick="viewProduct('${product.id}', '${product.name.replace(/'/g, "\\'")}')">
                                <div class="product-info">
                                    <h3 class="product-title">${product.name}</h3>
                                    <p class="product-description">${product.description || ''}</p>
                                    <div class="product-price">${priceRange}</div>
                                </div>
                                <button class="action-btn">عرض الفئات</button>
                            </div>
                        `;
                    });
                    
                    resultsHTML += '</div>';
                }
                
                // Display categories results
                if (searchedCategories.length > 0) {
                    resultsHTML += `<h2 style="margin: 2rem 0 1rem;">🏷️ الفئات (${searchedCategories.length})</h2>`;
                    resultsHTML += '<div class="product-grid">';
                    
                    searchedCategories.forEach(category => {
                        const deliveryIcon = {
                            'code': '🎫',
                            'phone': '📱',
                            'email': '📧',
                            'id': '🆔',
                            'manual': '✋'
                        }[category.delivery_type] || '🎫';
                        
                        resultsHTML += `
                            <div class="product-card" onclick="purchaseCategory('${category.id}', '${category.name.replace(/'/g, "\\'")}', ${category.price}, '${category.delivery_type}')">
                                <div class="product-info">
                                    <h3 class="product-title">${deliveryIcon} ${category.name}</h3>
                                    <p class="product-description">${category.description || ''}</p>
                                    <div class="product-price">$${category.price.toFixed(2)}</div>
                                </div>
                                <button class="action-btn">شراء الآن</button>
                            </div>
                        `;
                    });
                    
                    resultsHTML += '</div>';
                }
                
                resultsContainer.innerHTML = resultsHTML;
                
            } catch (error) {
                console.error('Search error:', error);
                resultsContainer.innerHTML = `
                    <div style="text-align: center; padding: 3rem;">
                        <h3 style="color: var(--danger-color);">❌ حدث خطأ أثناء البحث</h3>
                        <p>الخطأ: ${error.message}</p>
                        <button onclick="showSection('home')" class="action-btn">🏠 العودة للرئيسية</button>
                    </div>
                `;
            }
        }

        // Show Section
        function showSection(sectionName) {
            // Hide all sections
            document.querySelectorAll('.section').forEach(section => {
                section.classList.remove('active');
            });
            
            // Show target section
            const targetSection = document.getElementById(`${sectionName}-section`);
            if (targetSection) {
                targetSection.classList.add('active');
            }
            
            // Update navigation
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            
            document.querySelectorAll('.bottom-nav-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Find and activate corresponding nav items
            const navLink = document.querySelector(`.nav-link[onclick*="'${sectionName}'"]`);
            if (navLink) navLink.classList.add('active');
            
            const bottomNavItem = document.querySelector(`.bottom-nav-item[onclick*="'${sectionName}'"]`);
            if (bottomNavItem) bottomNavItem.classList.add('active');

            // Haptic feedback
            if (tgWebApp && tgWebApp.HapticFeedback) {
                tgWebApp.HapticFeedback.impactOccurred('light');
            }
        }

        // Show Loading
        function showLoading() {
            document.getElementById('loading').style.display = 'flex';
        }

        // Hide Loading
        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }

        // Show Notification
        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            const content = document.getElementById('notification-content');
            
            content.textContent = message;
            notification.className = `notification ${type}`;
            
            // Show notification
            requestAnimationFrame(() => {
                notification.classList.add('show');
            });
            
            // Hide after 4 seconds
            setTimeout(() => {
                notification.classList.remove('show');
            }, 4000);

            // Haptic feedback
            if (tgWebApp && tgWebApp.HapticFeedback) {
                if (type === 'success') {
                    tgWebApp.HapticFeedback.notificationOccurred('success');
                } else if (type === 'error') {
                    tgWebApp.HapticFeedback.notificationOccurred('error');
                } else {
                    tgWebApp.HapticFeedback.impactOccurred('medium');
                }
            }
        }

        // Get Delivery Type Name
        function getDeliveryTypeName(deliveryType) {
            switch (deliveryType) {
                case 'id':
                    return 'إرسال إلى معرف المستخدم';
                case 'email':
                    return 'إرسال إلى البريد الإلكتروني';
                case 'phone':
                    return 'إرسال إلى رقم الهاتف';
                case 'code':
                default:
                    return 'كود فوري';
            }
        }

        // Modal Functions (TokenStore Style)
        let currentInputCallback = null;
        let currentInputType = null;

        function showInputModal(title, label, placeholder, helpText, inputType = 'text', callback) {
            const modal = document.getElementById('input-modal');
            const modalTitle = document.getElementById('modal-title');
            const inputLabel = document.getElementById('input-label');
            const userInput = document.getElementById('user-input');
            const inputHelp = document.getElementById('input-help');
            
            // Set modal content
            modalTitle.textContent = title;
            inputLabel.textContent = label;
            userInput.placeholder = placeholder;
            userInput.type = inputType;
            inputHelp.textContent = helpText;
            
            // Clear previous input
            userInput.value = '';
            
            // Store callback and type
            currentInputCallback = callback;
            currentInputType = inputType;
            
            // Show modal
            modal.style.display = 'flex';
            
            // Focus input after animation
            setTimeout(() => {
                userInput.focus();
            }, 300);
            
            // Haptic feedback
            if (tgWebApp && tgWebApp.HapticFeedback) {
                tgWebApp.HapticFeedback.impactOccurred('medium');
            }
        }

        function closeInputModal() {
            const modal = document.getElementById('input-modal');
            const userInput = document.getElementById('user-input');
            
            modal.style.display = 'none';
            userInput.value = '';
            currentInputCallback = null;
            currentInputType = null;
            
            // Haptic feedback
            if (tgWebApp && tgWebApp.HapticFeedback) {
                tgWebApp.HapticFeedback.impactOccurred('light');

        // Guest User Functions
        function showGuestRegistrationModal() {
            const modal = document.getElementById('guest-modal');
            modal.style.display = 'flex';
        }

        function closeGuestModal() {
            const modal = document.getElementById('guest-modal');
            modal.style.display = 'none';
        }

        function registerGuest() {
            const phone = document.getElementById('guest-phone').value.trim();
            const name = document.getElementById('guest-name').value.trim() || 'ضيف';
            
            if (!phone) {
                alert('يرجى إدخال رقم الهاتف');
                return;
            }
            
            // Validate phone number (basic)
            const phoneRegex = /^[0-9+\s-]{8,20}$/;
            if (!phoneRegex.test(phone)) {
                alert('يرجى إدخال رقم هاتف صحيح');
                return;
            }
            
            // Create guest user ID
            const guestId = 'guest_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            
            // Save guest user
            const guestUser = {
                guest_id: guestId,
                first_name: name,
                phone: phone,
                is_guest: true,
                created_at: new Date().toISOString()
            };
            
            localStorage.setItem('guestUser', JSON.stringify(guestUser));
            
            // Set global variables
            userData = guestUser;
            userTelegramId = guestId;
            
            // Update UI
            const userNameEl = document.getElementById('user-name');
            if (userNameEl) {
                userNameEl.textContent = `مرحباً ${name}`;
            }
            
            closeGuestModal();
            
            // Load data
            loadData();
            
            // Show welcome message
            showNotification('✅ مرحباً بك! يمكنك الآن تصفح المتجر والشراء', 'success');
        }

        function isGuestUser() {
            return userData && userData.is_guest === true;
        }

            }
        }

        function confirmInput() {
            const userInput = document.getElementById('user-input');
            const value = userInput.value.trim();
            
            if (!value) {
                showNotification('يرجى إدخال البيانات المطلوبة', 'error');
                userInput.focus();
                return;
            }
            
            // Validate based on input type
            if (currentInputType === 'email' && !value.includes('@')) {
                showNotification('يرجى إدخال بريد إلكتروني صحيح', 'error');
                userInput.focus();
                return;
            }
            
            if (currentInputType === 'phone' && value.length < 8) {
                showNotification('يرجى إدخال رقم هاتف صحيح', 'error');
                userInput.focus();
                return;
            }
            
            // Call the callback with the value
            if (currentInputCallback) {
                currentInputCallback(value);
            }
            
            closeInputModal();
            
            // Haptic feedback
            if (tgWebApp && tgWebApp.HapticFeedback) {
                tgWebApp.HapticFeedback.notificationOccurred('success');
            }
        }

        // Handle Enter key in modal
        document.addEventListener('keydown', function(event) {
            const modal = document.getElementById('input-modal');
            if (modal.style.display === 'flex') {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    confirmInput();
                } else if (event.key === 'Escape') {
                    event.preventDefault();
                    closeInputModal();
                }
            }
        });

        // Initialize app when DOM is loaded
        document.addEventListener('DOMContentLoaded', initApp);

        // Prevent unwanted gestures
        document.addEventListener('touchstart', function(e) {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        });

        let lastTouchEnd = 0;
        document.addEventListener('touchend', function(event) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
