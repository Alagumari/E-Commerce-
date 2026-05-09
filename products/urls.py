from django.urls import path
from . import views

app_name = 'products'
urlpatterns = [
    path('', views.home_view, name='home'),
    path('products/', views.product_list_view, name='list'),
    path('products/<slug:slug>/', views.product_detail_view, name='detail'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
]
