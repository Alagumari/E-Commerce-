from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from cart.models import Cart
from .models import Order, OrderItem
import json

def get_razorpay_client():
    """Get razorpay client — returns None if keys not configured"""
    try:
        import razorpay
        key = getattr(settings, 'RAZORPAY_KEY_ID', '')
        secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        if key and secret and not key.startswith('rzp_test_YourKey'):
            return razorpay.Client(auth=(key, secret))
    except Exception:
        pass
    return None

@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        messages.warning(request, '🛒 Your cart is empty!')
        return redirect('cart:cart')

    profile = getattr(request.user, 'profile', None)

    if request.method == 'POST':
        # Validate form fields
        required = ['full_name', 'email', 'phone', 'address', 'city', 'state', 'pincode']
        for field in required:
            if not request.POST.get(field, '').strip():
                messages.error(request, f'❌ Please fill in {field.replace("_", " ").title()}!')
                return redirect('orders:checkout')

        total_amount = cart.get_total()
        discount_amount = cart.get_discount()

        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            discount_amount=discount_amount,
            coupon_code=cart.coupon.code if cart.coupon else '',
            full_name=request.POST['full_name'].strip(),
            email=request.POST['email'].strip(),
            phone=request.POST['phone'].strip(),
            address=request.POST['address'].strip(),
            city=request.POST['city'].strip(),
            state=request.POST['state'].strip(),
            pincode=request.POST['pincode'].strip(),
        )

        # Create order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                price=item.product.get_discounted_price(),
                quantity=item.quantity,
            )

        # Try real Razorpay order creation
        razorpay_order_id = ''
        rzp_client = get_razorpay_client()
        if rzp_client:
            try:
                amount_paise = int(float(total_amount) * 100)
                rzp_order = rzp_client.order.create({
                    'amount': amount_paise,
                    'currency': 'INR',
                    'receipt': f'order_{order.id}',
                    'notes': {
                        'order_id': str(order.id),
                        'customer': request.user.username,
                    }
                })
                razorpay_order_id = rzp_order['id']
                order.razorpay_order_id = razorpay_order_id
                order.save()
                messages.info(request, '💳 Razorpay order created successfully!')
            except Exception as e:
                messages.warning(request, f'⚠️ Razorpay: {str(e)} — use demo payment.')
        else:
            # Demo mode
            order.razorpay_order_id = f'demo_order_{order.id}'
            order.save()

        amount_paise = int(float(total_amount) * 100)
        return render(request, 'orders/payment.html', {
            'order': order,
            'razorpay_key': getattr(settings, 'RAZORPAY_KEY_ID', ''),
            'razorpay_order_id': order.razorpay_order_id,
            'amount': amount_paise,
            'total_display': total_amount,
            'is_demo': not bool(rzp_client),
        })

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'profile': profile,
    })


@login_required
def payment_success(request):
    """Handle payment success from Razorpay callback or demo button"""
    order_id = request.POST.get('order_id') or request.GET.get('order_id')

    if not order_id:
        messages.error(request, '❌ Invalid payment request.')
        return redirect('products:home')

    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Verify real Razorpay payment signature
    rzp_client = get_razorpay_client()
    payment_id = request.POST.get('razorpay_payment_id', '')
    signature = request.POST.get('razorpay_signature', '')

    if rzp_client and payment_id and signature:
        try:
            params = {
                'razorpay_order_id': request.POST.get('razorpay_order_id', ''),
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            }
            rzp_client.utility.verify_payment_signature(params)
            order.razorpay_payment_id = payment_id
            messages.success(request, f'✅ Payment verified successfully!')
        except Exception as e:
            order.payment_status = 'failed'
            order.save()
            messages.error(request, f'❌ Payment verification failed: {e}')
            return redirect('orders:detail', order_id=order.id)
    else:
        # Demo mode — simulate success
        order.razorpay_payment_id = payment_id or f'demo_pay_{order.id}'

    order.payment_status = 'paid'
    order.status = 'confirmed'
    order.save()

    # Clear cart
    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        cart.items.all().delete()
        cart.coupon = None
        cart.save()

    messages.success(request, f'🎉 Order #{order.id} placed successfully! Thank you for shopping at ShopKart!')
    return redirect('orders:detail', order_id=order.id)


@login_required
def payment_failed(request):
    order_id = request.GET.get('order_id') or request.POST.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order.payment_status = 'failed'
        order.save()
        messages.error(request, '❌ Payment failed. Please try again.')
        return redirect('orders:detail', order_id=order.id)
    return redirect('products:home')


@login_required
def order_list_view(request):
    orders = request.user.orders.all()
    return render(request, 'orders/list.html', {'orders': orders})


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status in ['pending', 'confirmed']:
        order.status = 'cancelled'
        order.save()
        messages.info(request, f'🚫 Order #{order.id} cancelled.')
    else:
        messages.error(request, '❌ This order cannot be cancelled.')
    return redirect('orders:detail', order_id=order.id)
