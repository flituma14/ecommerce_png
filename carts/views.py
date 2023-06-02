import http
from django.shortcuts import get_object_or_404, redirect, render
from django.template import RequestContext
from carts.models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
#import requests
from store.models import Product
import json

def _request_token_payment(card_holder_name = "", card_number = "", expiry_month = "", expiry_year = "", cvc = ""):
    import http.client
    conn = http.client.HTTPSConnection("api-uat.kushkipagos.com")
    payload = {
        'card' : {
            'name' : card_holder_name,
            'number': card_number,
            'expiryMonth': expiry_month,
            'expiryYear': expiry_year,
            'cvv': cvc,
        },
        'totalAmount': 1.1,
        'currency' : 'USD'
    }

    headers = {
        'Public-Merchant-Id': "b8099f6006c740089b4ed0100ec5f536",
        'Content-Type': "application/json",
        'Accept': "application/json"
    }

    conn.request("POST", "/card/v1/tokens", json.dumps(payload), headers)
    res = conn.getresponse()
    data = json.loads(res.read())
    token = data['token']
    return token

#@csrf_exempt
def charge(request):    
    import http.client
    conn = http.client.HTTPSConnection("api-uat.kushkipagos.com")
    
    card_holder_name = request.POST['card_holder_name']
    card_number = request.POST['card_number']
    expiry_month = request.POST['expiry_month']
    expiry_year = request.POST['expiry_year']
    cvc = request.POST['cvc']
    
    token = _request_token_payment(card_holder_name, card_number, expiry_month, expiry_year, cvc)
    
    payload = {
        'token' : token,
        'amount': {
            'currency' : 'USD',
            'subtotalIva' : 0,
            'subtotalIva0': 8,
            'iva' : 0,
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
            'documentType': 'DNI',
            'documentNumber': 'ABCD123456EF',
            'phoneNumber': '+5931111111',
        },
        'orderDetails':{
            'siteDomain' : 'www.example.com',
            'shippingDetails': {
                'name' : 'Freddy Lituma',
                'phone': '+5934364265472',
                'addres': 'Guayaquil',
                'city': 'Guayaquil',
                'region': 'Costa',
                'country': 'Ecuador',
            },
            'billingDetails':{
                'name' : 'Freddy Lituma',
                'phone': '+59334532654',
                'addres': 'Centro 123',
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
                    'price' : '1400',
                    'sku': '121313',
                    'quantity': 1,
                }
            ]
        },
        'threeDomainSecure':{
            'cavv' :'AAABBoVBaZKAR3BkdkFpELpWIiE=',
            'eci': '07',
            'xid': 'NEpab1F1MEdtaWJ2bEY3ckYxQzE=',
            'specificationVersion': '2.2.0',
            'acceptRisk': True
        }
    }
    
    
    headers = {
        'Public-Merchant-Id': "b8099f6006c740089b4ed0100ec5f536",
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



def cajita(request, total = 0, tax =0, grand_total =0, cart_items = None):
    try:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_items = CartItem.objects.filter(cart = cart, is_active = True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            
        tax = (2*total)/100
        grand_total = total + tax
        
    except ObjectDoesNotExist:
        pass
    
    context = {
        'sub_total' : total, 
        'tax' : tax,
        'grand_total': grand_total,
    }
    
    return render(request, 'store/cajita.html', context)

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
        
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
    cart.save()

    try:
        cart_item = CartItem.objects.get(product= product, cart = cart)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart,
        )
    
    cart_item.save()  
    return redirect('cart')

def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id = _cart_id(request))
    product = get_object_or_404(Product, id = product_id)
    cart_item = CartItem.objects.get(product = product, cart = cart)

    if cart_item.quantity>1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart')


def remove_cart_item(request, product_id):
    cart = Cart.objects.get(cart_id = _cart_id(request))
    product = get_object_or_404(Product, id = product_id)
    cart_item = CartItem.objects.get(product = product, cart = cart)
    cart_item.delete()
    return

def cart(request, grand_total = 0, total = 0, tax = 0, quantity = 0, cart_items = None):
    try:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_items = CartItem.objects.filter(cart = cart, is_active = True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    
        tax = (2*total)/100
        grand_total = total + tax
        
    except ObjectDoesNotExist:
        pass
    
    context = {
        'total' : total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax' : tax,
        'grand_total': grand_total,
    }
    
    return render(request, 'store/cart.html', context)
