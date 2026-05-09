from django.urls import path
from . import views

app_name = 'orders'
urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('', views.order_list_view, name='list'),
    path('<int:order_id>/', views.order_detail_view, name='detail'),
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel'),
]
