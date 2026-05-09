from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from .models import Product, Category, Review, Wishlist

def home_view(request):
    featured = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    # Only top-level categories for home page
    categories = Category.objects.filter(parent=None)
    best_sellers = Product.objects.filter(is_active=True, discount_percent__gt=0).order_by('-discount_percent')[:4]
    # Fashion subcategories for home section
    fashion_subs = Category.objects.filter(parent__slug='fashion')
    return render(request, 'products/home.html', {
        'featured': featured,
        'categories': categories,
        'best_sellers': best_sellers,
        'fashion_subs': fashion_subs,
    })

def product_list_view(request):
    products = Product.objects.filter(is_active=True)
    # Top-level for sidebar (show subcategories under Fashion)
    top_categories = Category.objects.filter(parent=None)
    all_categories = Category.objects.all()

    query = request.GET.get('q', '')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    cat_slug = request.GET.get('category', '')
    selected_category = None
    if cat_slug:
        selected_category = get_object_or_404(Category, slug=cat_slug)
        # If top-level: include its subcategories too
        # If subcategory: just that subcategory
        if selected_category.parent is None:
            sub_ids = list(selected_category.subcategories.values_list('id', flat=True))
            products = products.filter(
                Q(category=selected_category) | Q(category__id__in=sub_ids)
            )
        else:
            products = products.filter(category=selected_category)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    sort = request.GET.get('sort', 'newest')
    sort_map = {
        'newest': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'name': 'name',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))

    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)

    return render(request, 'products/list.html', {
        'products': products,
        'top_categories': top_categories,
        'selected_category': selected_category,
        'query': query,
        'cat_slug': cat_slug,
        'sort': sort,
    })

def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.select_related('user').order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    user_review = None
    in_wishlist = False
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating and comment:
            Review.objects.update_or_create(
                product=product, user=request.user,
                defaults={'rating': int(rating), 'comment': comment}
            )
            messages.success(request, '⭐ Review submitted!')
            return redirect('products:detail', slug=slug)

    return render(request, 'products/detail.html', {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'related': related,
        'user_review': user_review,
        'in_wishlist': in_wishlist,
        'range_5': range(1, 6),
    })

@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        messages.info(request, f'💔 Removed from wishlist')
    else:
        messages.success(request, f'❤️ Added to wishlist!')
    return redirect(request.META.get('HTTP_REFERER', 'products:home'))

@login_required
def wishlist_view(request):
    wishlist = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'products/wishlist.html', {'wishlist': wishlist})
