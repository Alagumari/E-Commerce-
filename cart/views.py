from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from products.models import Product
from .models import Cart, CartItem, Coupon

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart/cart.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if item.quantity < product.stock:
            item.quantity += 1
            item.save()
            messages.success(request, f'🛒 {product.name} quantity updated!')
        else:
            messages.warning(request, '⚠️ Max stock reached!')
    else:
        messages.success(request, f'✅ {product.name} added to cart!')
    return redirect(request.META.get('HTTP_REFERER', 'cart:cart'))

@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    if action == 'increase':
        if item.quantity < item.product.stock:
            item.quantity += 1
            item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
            messages.info(request, '🗑️ Item removed from cart')
            return redirect('cart:cart')
    return redirect('cart:cart')

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, '🗑️ Item removed from cart')
    return redirect('cart:cart')

@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        cart = get_object_or_404(Cart, user=request.user)
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
            subtotal = cart.get_subtotal()
            if subtotal >= coupon.min_amount:
                cart.coupon = coupon
                cart.save()
                messages.success(request, f'🎉 Coupon "{code}" applied! {coupon.discount_percent}% off!')
            else:
                messages.error(request, f'❌ Minimum order ₹{coupon.min_amount} required.')
        except Coupon.DoesNotExist:
            messages.error(request, '❌ Invalid coupon code.')
    return redirect('cart:cart')

@login_required
def remove_coupon(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.coupon = None
    cart.save()
    messages.info(request, 'Coupon removed.')
    return redirect('cart:cart')
