import pathlib
from wsgiref.util import FileWrapper
from mimetypes import guess_type

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from products.models import Product
from .forms import OrderForm
from .models import Order

@login_required
def order_checkout_view(request):
    product_id = request.session.get("product_id") or None
    if product_id == None:
        return redirect("/")
    # qs = Product.objects.filter(id=product_id)
    # if not qs.exists():
    #     return redirect("/")
    # product = qs.first()
    product = None
    try:
        product = Product.objects.get(id=product_id)
    except:
        return redirect("/")    
    # if not product.has_inventory:
    #     return redirect("/no-inventory")
    user = request.user
    order_id = request.session.get("order_id") # cart
    order_obj = None
    new_creation = False
    try:
        order_obj = Order.objects.get(id=order_id)
    except:
        order_id = None    
    if order_id == None:
        new_creation = True
        order_obj = Order.objects.create(product=product, user=user)
    if order_obj != None and new_creation == False:    
        if order_obj.product.id != product.id:
            order_obj = Order.objects.create(product=product, user=user)
    request.session['order_id'] = order_obj.id  
    form = OrderForm(request.POST or None, product=product, instance=order_obj)
    if form.is_valid():
        order_obj.shipping_address = form.cleaned_data.get("shipping_address")
        order_obj.billing_address = form.cleaned_data.get("billing_address")
        order_obj.mark_paid(save=False)
        # order_obj.status = 'paid'
        order_obj.save()
        del request.session['order_id']
        return redirect("/success")    
    return render(request, 'orders/checkout.html', {"form": 
    form, "objects": order_obj, "is_digital": product.is_digital})

def download_order(request, *args, **Kwargs):
    '''
     Download our order product media,
     if it exists
    '''    
    order_id = 'abc'
    qs = Product.objects.filter(media__isnull=False)
    product_obj = qs.first()
    if not product_obj.media:
        raise Http404
    media = product_obj.media
    product_path = media.path 
    path = pathlib.Path(product_path)
    pk = product_obj.pk
    ext = path.suffix # .png, .csv, .mov
    fname = f"my-cool-product-{order_id}-{pk}{ext}"
    # if not path.exists():
    #     raise Http404
    
    with open(path, 'rb') as f:
        wrapper = FileWrapper(f)
        content_type = 'application/force-download'
        guessed_ = guess_type(path)[0]
        if guessed_:
            content_type = guessed_        
        response = HttpResponse(wrapper, content_type=content_type)
        response['content-Disposition'] = f"attachment;filename={fname}"
        response['X-SendFile'] = f"{fname}"
    return response




