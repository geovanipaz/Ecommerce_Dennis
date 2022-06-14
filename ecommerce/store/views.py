from multiprocessing import context
from django.shortcuts import render
from .models import Order, OrderItem, Product, ShippingAddress
from django.http import JsonResponse
import json
import datetime

def store(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        #pega ou cria um pedido
        order, created = Order.objects.get_or_create(
            customer=customer, complete=False
        )
        #coloca numa lista todos item do pedido do pedido
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_total':0, 'get_total_items':0,'shipping':False}
        cartItems = order['get_total_items']
    
    products = Product.objects.all()
    context = {'products':products, 'cartItems':cartItems}
    return render(request, 'store/store.html', context)

def cart(request):
    #se autenticado o cliente é o atual usuario
    if request.user.is_authenticated:
        customer = request.user.customer
        #pega ou cria um pedido
        order, created = Order.objects.get_or_create(
            customer=customer, complete=False
        )
        #coloca numa lista todos item do pedido do pedido
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        try:
            cart = json.loads(request.COOKIES['cart'])
        except:
            cart = {}
        print('Cart:', cart)
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0, 'shipping':False}
        cartItems = order['get_cart_items']
        
        for i in cart:
            cartItems += cart[i]['quantity']
            
            product = Product.objects.get(id=i)
            total = (product.price * cart[i]['quantity'])
            
            order['get_cart_total'] += total
            order['get_cart_items'] += cart[i]['quantity']
            
            item = {
                'product':{
                  'id':product.id,
                  'name':product.name,
                  'price':product.price,
                  'imageURL':product.image.url 
                },
                'quantity':cart[i]['quantity'],
                'get_total': total
            }
            items.append(item)
        
    context = {'items':items, 'order':order, 'cartItems':cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(
            customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_total':0, 'get_total_items':0, 'shipping':False}
        cartItems = order['get_total_items']
        
    context = {'items':items, 'order':order,'cartItems':cartItems}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    
    print('action:', action)
    print('productId:', productId)
    
    customer = request.user.customer
    product = Product.objects.get(pk=productId)
    order, created = Order.objects.get_or_create(
            customer=customer, complete=False)
    
    orderitem, created = OrderItem.objects.get_or_create(
        order=order, product=product)
    
    if action == 'add':
        orderitem.quantity = (orderitem.quantity + 1)
    elif action == 'remove':
        orderitem.quantity = (orderitem.quantity - 1)
        
    orderitem.save()
    if orderitem.quantity <= 0:
        orderitem.delete()
        
    return JsonResponse('Item was Added', safe=False)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(
            customer=customer, complete=False)
        total = float(data['form']['total'])
        order.transaction_id = transaction_id
        
        if total == order.get_cart_total:
            order.complete = True
        order.save()
        
        if order.shipping == True:
            ShippingAddress.objects.create(
			customer=customer,
			order=order,
			address=data['shipping']['address'],
			city=data['shipping']['city'],
			state=data['shipping']['state'],
			zipcode=data['shipping']['zipcode'],
			)
    else:
        print('User is not logged in..')
    return JsonResponse('Payment Completed', safe=False)