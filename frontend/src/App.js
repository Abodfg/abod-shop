import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Alert, AlertDescription } from './components/ui/alert';
import { Toaster } from './components/ui/sonner';
import { toast } from 'sonner';
import { ShoppingCart, Users, Package, BarChart3, MessageSquare, Settings, Bot, DollarSign, Star, Zap } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [users, setUsers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [pendingOrders, setPendingOrders] = useState([]);
  const [codesStats, setCodesStats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [webhooksSet, setWebhooksSet] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [productsRes, categoriesRes, usersRes, ordersRes, pendingOrdersRes, codesStatsRes] = await Promise.all([
        axios.get(`${API}/products`),
        axios.get(`${API}/categories`),
        axios.get(`${API}/users`),
        axios.get(`${API}/orders`),
        axios.get(`${API}/pending-orders`),
        axios.get(`${API}/codes-stats`)
      ]);
      
      setProducts(productsRes.data);
      setCategories(categoriesRes.data);
      setUsers(usersRes.data);
      setOrders(ordersRes.data);
      setPendingOrders(pendingOrdersRes.data);
      setCodesStats(codesStatsRes.data);
    } catch (error) {
      console.error('خطأ في جلب البيانات:', error);
      toast.error('فشل في تحميل البيانات');
    }
  };

  const setupWebhooks = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/set-webhooks`);
      setWebhooksSet(true);
      toast.success('تم تفعيل البوتات بنجاح!');
    } catch (error) {
      console.error('خطأ في إعداد الويب هوك:', error);
      toast.error('فشل في تفعيل البوتات');
    }
    setLoading(false);
  };

  return (
    <div className="App min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      <Toaster />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard 
            products={products}
            categories={categories}
            users={users}
            orders={orders}
            pendingOrders={pendingOrders}
            codesStats={codesStats}
            setupWebhooks={setupWebhooks}
            loading={loading}
            webhooksSet={webhooksSet}
            refreshData={fetchData}
          />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

const Dashboard = ({ products, categories, users, orders, pendingOrders, codesStats, setupWebhooks, loading, webhooksSet, refreshData }) => {
  const totalRevenue = orders
    .filter(order => order.status === 'completed')
    .reduce((sum, order) => sum + order.price, 0);
    
  const totalBalance = users.reduce((sum, user) => sum + user.balance, 0);
  
  const lowStockAlerts = codesStats.filter(stat => stat.status === 'low').length;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-xl">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Abod Card</h1>
                <p className="text-blue-200 text-sm">إدارة بوت البطاقات الرقمية</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <Badge variant={webhooksSet ? "default" : "destructive"} className="px-3 py-1">
                {webhooksSet ? "البوت نشط" : "البوت متوقف"}
              </Badge>
              
              <Button 
                onClick={setupWebhooks} 
                disabled={loading}
                className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white border-0"
                data-testid="setup-webhooks-btn"
              >
                {loading ? "جاري التفعيل..." : "تفعيل البوتات"}
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-white/80">إجمالي المستخدمين</CardTitle>
              <Users className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{users.length}</div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-white/80">إجمالي المنتجات</CardTitle>
              <Package className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{products.length}</div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-white/80">إجمالي الطلبات</CardTitle>
              <ShoppingCart className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{orders.length}</div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-white/80">الطلبات المعلقة</CardTitle>
              <ShoppingCart className="h-4 w-4 text-orange-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{pendingOrders.length}</div>
              <p className="text-xs text-orange-400 mt-1">
                {lowStockAlerts > 0 && `${lowStockAlerts} أكواد منخفضة`}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="bg-white/5 border-white/10">
            <TabsTrigger value="overview" className="data-[state=active]:bg-white/10 text-white">نظرة عامة</TabsTrigger>
            <TabsTrigger value="products" className="data-[state=active]:bg-white/10 text-white">المنتجات</TabsTrigger>
            <TabsTrigger value="codes" className="data-[state=active]:bg-white/10 text-white">الأكواد</TabsTrigger>
            <TabsTrigger value="pending" className="data-[state=active]:bg-white/10 text-white">الطلبات المعلقة</TabsTrigger>
            <TabsTrigger value="users" className="data-[state=active]:bg-white/10 text-white">المستخدمون</TabsTrigger>
            <TabsTrigger value="orders" className="data-[state=active]:bg-white/10 text-white">الطلبات</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Bot className="w-5 h-5" />
                    معلومات البوت
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-white/70">بوت المستخدمين:</span>
                      <Badge variant="outline" className="text-blue-300 border-blue-300">
                        @AbodCardBot
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/70">بوت الإدارة:</span>
                      <Badge variant="outline" className="text-green-300 border-green-300">
                        @AbodCardAdminBot
                      </Badge>
                    </div>
                    <Separator className="bg-white/10" />
                    <div className="flex justify-between">
                      <span className="text-white/70">حالة النظام:</span>
                      <Badge variant={webhooksSet ? "default" : "destructive"}>
                        {webhooksSet ? "نشط" : "متوقف"}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    الإحصائيات المالية
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-white/70">إجمالي الأرصدة:</span>
                      <span className="text-white font-semibold">${totalBalance.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/70">الإيرادات المحققة:</span>
                      <span className="text-green-400 font-semibold">${totalRevenue.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/70">الطلبات المعلقة:</span>
                      <span className="text-orange-400 font-semibold">{pendingOrders.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/70">تحذيرات نقص الأكواد:</span>
                      <span className={`font-semibold ${lowStockAlerts > 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {lowStockAlerts > 0 ? `${lowStockAlerts} فئات` : 'لا توجد'}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Bot Setup Instructions */}
            <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  تعليمات الإعداد
                </CardTitle>
                <CardDescription className="text-white/70">
                  خطوات تشغيل النظام وإعداد البوتات
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Alert className="bg-blue-500/10 border-blue-500/20">
                  <Zap className="h-4 w-4 text-blue-400" />
                  <AlertDescription className="text-white/80">
                    <strong>الخطوة 1:</strong> انقر على زر "تفعيل البوتات" أعلاه لتشغيل النظام
                  </AlertDescription>
                </Alert>
                
                <Alert className="bg-green-500/10 border-green-500/20">
                  <MessageSquare className="h-4 w-4 text-green-400" />
                  <AlertDescription className="text-white/80">
                    <strong>الخطوة 2:</strong> ابحث عن البوتات في تليجرام وابدأ المحادثة معهما
                  </AlertDescription>
                </Alert>

                <Alert className="bg-purple-500/10 border-purple-500/20">
                  <Star className="h-4 w-4 text-purple-400" />
                  <AlertDescription className="text-white/80">
                    <strong>الخطوة 3:</strong> استخدم لوحة التحكم هذه لإدارة المنتجات والأكواد والمستخدمين
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="products" className="space-y-6">
            <Card className="bg-white/5 border-white/10 backdrop-blur-xl" data-testid="products-card">
              <CardHeader>
                <CardTitle className="text-white">إدارة المنتجات والفئات</CardTitle>
                <CardDescription className="text-white/70">
                  عرض وإدارة جميع المنتجات والفئات المتاحة في النظام
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {products.length === 0 ? (
                    <div className="text-center py-8">
                      <Package className="w-12 h-12 text-white/30 mx-auto mb-4" />
                      <p className="text-white/70">لا توجد منتجات مضافة بعد</p>
                      <p className="text-white/50 text-sm">استخدم بوت الإدارة لإضافة منتجات جديدة</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {products.map((product) => {
                        const productCategories = categories.filter(cat => cat.product_id === product.id);
                        return (
                          <div key={product.id} className="p-4 border border-white/10 rounded-lg bg-white/5">
                            <div className="flex items-center justify-between mb-4">
                              <div>
                                <h3 className="text-white font-semibold text-lg">{product.name}</h3>
                                <p className="text-white/70 text-sm">{product.description}</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="text-blue-300 border-blue-300">
                                  {productCategories.length} فئة
                                </Badge>
                                <Badge variant={product.is_active ? "default" : "secondary"}>
                                  {product.is_active ? "نشط" : "متوقف"}
                                </Badge>
                              </div>
                            </div>
                            
                            {productCategories.length > 0 && (
                              <div className="mt-4 grid gap-2">
                                <h4 className="text-white/80 text-sm font-medium">الفئات:</h4>
                                {productCategories.map((category) => {
                                  const deliveryTypeIcons = {
                                    'code': '🎫',
                                    'phone': '📱',
                                    'email': '📧',
                                    'id': '🆔',
                                    'manual': '📝'
                                  };
                                  
                                  return (
                                    <div key={category.id} className="p-3 bg-white/5 rounded-lg border border-white/5">
                                      <div className="flex items-center justify-between">
                                        <div>
                                          <span className="text-white text-sm font-medium">
                                            {deliveryTypeIcons[category.delivery_type]} {category.name}
                                          </span>
                                          <p className="text-white/60 text-xs">{category.description}</p>
                                        </div>
                                        <div className="text-right">
                                          <span className="text-green-400 font-semibold">${category.price}</span>
                                          <p className="text-white/50 text-xs">{category.category_type}</p>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="codes" className="space-y-6">
            <Card className="bg-white/5 border-white/10 backdrop-blur-xl" data-testid="codes-card">
              <CardHeader>
                <CardTitle className="text-white">إدارة الأكواد</CardTitle>
                <CardDescription className="text-white/70">
                  حالة المخزون للفئات التي تدعم الأكواد التلقائية
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {codesStats.length === 0 ? (
                    <div className="text-center py-8">
                      <Star className="w-12 h-12 text-white/30 mx-auto mb-4" />
                      <p className="text-white/70">لا توجد فئات تدعم الأكواد</p>
                      <p className="text-white/50 text-sm">أضف فئات بنوع "كود تلقائي" لإدارة الأكواد</p>
                    </div>
                  ) : (
                    <div className="grid gap-4">
                      {codesStats.map((stat) => {
                        const statusColors = {
                          'good': 'text-green-400',
                          'medium': 'text-yellow-400', 
                          'low': 'text-red-400'
                        };
                        
                        const statusIcons = {
                          'good': '🟢',
                          'medium': '🟡',
                          'low': '🔴'
                        };
                        
                        return (
                          <div key={stat.category_id} className="p-4 border border-white/10 rounded-lg bg-white/5">
                            <div className="flex items-center justify-between">
                              <div>
                                <h3 className="text-white font-semibold flex items-center gap-2">
                                  {statusIcons[stat.status]} {stat.category_name}
                                </h3>
                                <div className="flex gap-4 text-sm mt-2">
                                  <span className="text-white/70">المجموع: <span className="text-white">{stat.total_codes}</span></span>
                                  <span className="text-green-400">متاح: {stat.available_codes}</span>
                                  <span className="text-gray-400">مستخدم: {stat.used_codes}</span>
                                </div>
                              </div>
                              <div className="text-right">
                                <div className={`text-lg font-bold ${statusColors[stat.status]}`}>
                                  {stat.available_codes}
                                </div>
                                <p className="text-white/50 text-xs">متاح</p>
                              </div>
                            </div>
                            
                            {stat.status === 'low' && (
                              <div className="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                                <p className="text-red-400 text-sm">⚠️ مخزون منخفض - يرجى إضافة أكواد جديدة</p>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pending" className="space-y-6">
            <Card className="bg-white/5 border-white/10 backdrop-blur-xl" data-testid="pending-orders-card">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <ShoppingCart className="w-5 h-5" />
                  الطلبات المعلقة
                </CardTitle>
                <CardDescription className="text-white/70">
                  الطلبات التي تحتاج تنفيذ يدوي من الإدارة
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {pendingOrders.length === 0 ? (
                    <div className="text-center py-8">
                      <ShoppingCart className="w-12 h-12 text-green-400/30 mx-auto mb-4" />
                      <p className="text-green-400/70">✅ لا توجد طلبات معلقة</p>
                      <p className="text-white/50 text-sm">جميع الطلبات تم تنفيذها</p>
                    </div>
                  ) : (
                    <div className="grid gap-4">
                      {pendingOrders.map((order) => {
                        const deliveryTypeIcons = {
                          'code': '🎫 نفدت الأكواد',
                          'phone': '📱 رقم هاتف',
                          'email': '📧 بريد إلكتروني',
                          'id': '🆔 إيدي حساب',
                          'manual': '📝 طلب يدوي'
                        };
                        
                        return (
                          <div key={order.id} className="p-4 border border-orange-500/20 rounded-lg bg-orange-500/5">
                            <div className="flex items-center justify-between">
                              <div>
                                <h3 className="text-white font-semibold">{order.product_name}</h3>
                                <p className="text-white/70 text-sm">{order.category_name}</p>
                                <p className="text-orange-400 text-xs mt-1">
                                  {deliveryTypeIcons[order.delivery_type]}
                                </p>
                                {order.user_input_data && (
                                  <p className="text-blue-300 text-xs mt-1">
                                    📝 {order.user_input_data}
                                  </p>
                                )}
                              </div>
                              <div className="text-right">
                                <p className="text-green-400 font-semibold">${order.price.toFixed(2)}</p>
                                <p className="text-white/70 text-sm">👤 {order.telegram_id}</p>
                                <p className="text-white/50 text-xs">
                                  {new Date(order.order_date).toLocaleDateString('ar-SA')}
                                </p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users" className="space-y-6">
            <Card className="bg-white/5 border-white/10 backdrop-blur-xl" data-testid="users-card">
              <CardHeader>
                <CardTitle className="text-white">إدارة المستخدمين</CardTitle>
                <CardDescription className="text-white/70">
                  عرض جميع المستخدمين المسجلين في النظام
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {users.length === 0 ? (
                    <div className="text-center py-8">
                      <Users className="w-12 h-12 text-white/30 mx-auto mb-4" />
                      <p className="text-white/70">لا يوجد مستخدمون مسجلون بعد</p>
                      <p className="text-white/50 text-sm">سيظهر المستخدمون هنا عند بدء استخدامهم للبوت</p>
                    </div>
                  ) : (
                    <div className="grid gap-4">
                      {users.map((user) => (
                        <div key={user.id} className="p-4 border border-white/10 rounded-lg bg-white/5">
                          <div className="flex items-center justify-between">
                            <div>
                              <h3 className="text-white font-semibold">{user.first_name || 'مستخدم'}</h3>
                              <p className="text-white/70 text-sm">@{user.username || 'غير محدد'}</p>
                              <p className="text-white/50 text-xs">ID: {user.telegram_id}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-green-400 font-semibold">${user.balance.toFixed(2)}</p>
                              <p className="text-white/70 text-sm">{user.orders_count} طلب</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="orders" className="space-y-6">
            <Card className="bg-white/5 border-white/10 backdrop-blur-xl" data-testid="orders-card">
              <CardHeader>
                <CardTitle className="text-white">إدارة الطلبات</CardTitle>
                <CardDescription className="text-white/70">
                  عرض جميع الطلبات في النظام
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {orders.length === 0 ? (
                    <div className="text-center py-8">
                      <ShoppingCart className="w-12 h-12 text-white/30 mx-auto mb-4" />
                      <p className="text-white/70">لا توجد طلبات بعد</p>
                      <p className="text-white/50 text-sm">ستظهر الطلبات هنا عند بدء المستخدمين بالشراء</p>
                    </div>
                  ) : (
                    <div className="grid gap-4">
                      {orders.slice(0, 10).map((order) => (
                        <div key={order.id} className="p-4 border border-white/10 rounded-lg bg-white/5">
                          <div className="flex items-center justify-between">
                            <div>
                              <h3 className="text-white font-semibold">{order.product_name}</h3>
                              <p className="text-white/70 text-sm">{order.category_name}</p>
                              <p className="text-white/50 text-xs">ID: {order.telegram_id}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-green-400 font-semibold">${order.price.toFixed(2)}</p>
                              <Badge variant={
                                order.status === 'completed' ? 'default' : 
                                order.status === 'pending' ? 'secondary' : 'destructive'
                              }>
                                {order.status === 'completed' ? 'مكتمل' : 
                                 order.status === 'pending' ? 'قيد التنفيذ' : 'فاشل'}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default App;