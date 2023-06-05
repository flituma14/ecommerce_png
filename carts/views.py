import http
import http.client
import json

from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from carts.models import Cart, CartItem
from store.models import Product
    



@csrf_exempt
def charge(request, total = 0, sub_total = 0, iva = 0):    
    conn = http.client.HTTPSConnection("api-uat.kushkipagos.com")
    token = request.POST['kushkiToken']
    
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active = True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart = cart, is_active = True)
       
        for cart_item in cart_items:
            sub_total += (cart_item.product.price * cart_item.quantity)
            
        iva = (12*sub_total)/100
        
    except ObjectDoesNotExist:
        pass
    
    
    payload = {
        'token' : token,
        'amount': {
            'currency' : 'USD',
            'subtotalIva' : sub_total,
            'subtotalIva0': 0,
            'iva' : iva,
            'ice' : 0,
            'extraTaxes':{
                'iac': 0,
                'tasaAeroportuaria' : 0,
                'agenciaDeViaje': 0,    
            } 
        },
        'metadata' : {
            'key0' : 'value0',
            'key1' : 'value1',
            'key2' : 'value2',
        },
        'fullResponse': 'v2',
        'ignoreWarnings': True,
        'contactDetails': {
            'firstName': 'Freddy',
            'lastName' : 'Lituma',
            'email': 'fflituma14@gmail.com',
            'documentType': 'CI',
            'documentNumber': '0922869623',
            'phoneNumber': '+5930984762551',
        },
        'orderDetails':{
            'siteDomain' : 'www.example.com',
            'shippingDetails': {
                'name' : 'Freddy Lituma',
                'phone': '+5934364265472',
                'address1': 'Guayaquil',
                'city': 'Guayaquil',
                'region': 'Costa',
                'country': 'Ecuador',
            },
            'billingDetails':{
                'name' : 'Freddy Lituma',
                'phone': '+59334532654',
                'address1': 'Centro 123',
                'city': 'Guayaquil',
                'region': 'Costa',
                'country': 'Ecuador',
            }
        },
        'productDetails' : {
            'product': [
                {
                    'id': '1234',
                    'title': 'xyz',
                    'price' : 1.1,
                    'sku': '121313',
                    'quantity': 1,
                }
            ]
        }
    }
    
    
    headers = {
        'Private-Merchant-Id': "be47550cb6d0483ca3f2b150eb04e96f",
        'Content-Type': "application/json",
        'Accept': "application/json"
    }
    
    
    conn.request("POST", "/card/v1/charges", json.dumps(payload), headers)

    res = conn.getresponse()
    data = res.read()

    print(token)
    print(data.decode("utf-8"))
    
    
    #print(json.dumps(payload))
    #print(token)
    
    return redirect('cart')


@login_required(login_url='login')
def cajita(request, sub_total = 0, iva =0, total =0, cart_items = None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active = True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart = cart, is_active = True)
       
        for cart_item in cart_items:
            sub_total += (cart_item.product.price * cart_item.quantity)
            
        iva = (12*sub_total)/100
        total = sub_total + iva
        
    except ObjectDoesNotExist:
        pass
    
    context = {
        'sub_total' : sub_total, 
        'iva' : iva,
        'total': total,
    }
    
    return render(request, 'store/cajita.html', context)

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


@login_required(login_url='login')
def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)

    current_user = request.user

    print(current_user)

    if current_user.is_authenticated:
        #aqui en este bloque agregaremos la logica del carrito de compras cuando
        #el usuario esta autenticado
        
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.get(product = product, user = current_user)
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                user = current_user,
            )
            cart_item.save()

        return redirect('cart')

    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = _cart_id(request)
            )
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.get(product=product, cart=cart)
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                cart = cart,
            )
            
        return redirect('cart')



@login_required(login_url='login')
def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

@login_required(login_url='login')
def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

    cart_item.delete()
    return redirect('cart')


@login_required(login_url='login')
def cart(request, total = 0, sub_total = 0, iva = 0, quantity = 0, cart_items = None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active = True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart = cart, is_active = True)

        for cart_item in cart_items:
            sub_total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    
        iva = (12 * sub_total)/100
        total = sub_total + iva
        
    except ObjectDoesNotExist:
        pass
    
    context = {
        'quantity': quantity,
        'cart_items': cart_items,
        'sub_total' : sub_total,
        'iva' : iva,
        'total': total,
    }
    
    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request, sub_total = 0):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active = True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart = cart, is_active = True)
       
        for cart_item in cart_items:
            sub_total += (cart_item.product.price * cart_item.quantity)
            
        iva = (12*sub_total)/100
        total = sub_total + iva
        
    except ObjectDoesNotExist:
        pass
    
    context = {
        'cart_items' : cart_items,
        'sub_total' : sub_total, 
        'iva' : iva,
        'total': total,
    }
    
    return render(request, 'store/checkout.html', context)