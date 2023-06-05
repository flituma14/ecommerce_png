from django.shortcuts import render
from .models import Product
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required(login_url='login')
def store(request):
    products = Product.objects.all().filter(is_avaible = True)
    product_count = products.count()
    context = {
        'products' : products,
        'product_count' : product_count
    }
    return render(request, 'store/store.html', context)

