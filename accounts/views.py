from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import CustomUser, Details, Items, Summary
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import User as AuthUser  
import base64
import requests
import json
import io
from django.shortcuts import render, get_object_or_404
import pytesseract
from PIL import Image
import os
import google.generativeai as genai
from django.contrib import messages
from django.views.decorators.http import require_POST
import re
from django.shortcuts import render
import requests
import xml.etree.ElementTree as ET
from .forms import UploadImageForm
from PIL import Image
from datetime import datetime
import pytesseract
    
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def say_hello(request):
    return HttpResponse("You are my night, and dayy~")

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        userpass = request.POST['password']
        
        try:
            user = CustomUser.objects.get(username=username, userpass=userpass)
            request.session['user_id'] = user.id  
            return redirect('dashboard')
        except CustomUser.DoesNotExist:
            pass

        try:
            auth_user = AuthUser.objects.get(username=username)
            if auth_user.check_password(userpass):  
                request.session['user_id'] = auth_user.id  
                return redirect('dashboard')
        except AuthUser.DoesNotExist:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

@never_cache
def dashboard(request):
    if 'user_id' not in request.session:
        return redirect('login')

    latest_documents = Details.objects.all().order_by('-id')[:4]

    document_count = Details.objects.count()

    for document in latest_documents:
        if document.image:
            document.image_base64 = base64.b64encode(document.image).decode('utf-8')
        else:
            document.image_base64 = None

    return render(request, 'dashboard.html', {
        'latest_documents': latest_documents,
        'document_count': document_count,
    })

@never_cache
def uploaddocument(request):
    if 'user_id' not in request.session:
        return redirect('login')  

    extracted_data = None
    raw_text = None
    xml_data = None
    image_name = None
    image_data_base64 = None

    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            image_name = request.POST.get('name')
            image = request.FILES['image']
            image_data = image.read()
            image_data_base64 = base64.b64encode(image_data).decode('utf-8')

            img = Image.open(image)
            text = pytesseract.image_to_string(img)
            raw_text = text

            response = chat_session.send_message(
                f"Please convert the following text into XML format. The XML should have the following structure exactly as shown below:\n"
                f"- Use lowercase for all tag names with no spaces.\n"
                f"- The content inside each tag should be formatted exactly as in the text.\n"
                f"- Replace problematic characters in xml_string with their XML escape equivalents using xml_string.replace(&, &amp;).replace(<, &lt;).replace(>, &gt;).replace("", &quot;).replace('', &apos;).\n"
                f"- Remove any unwanted characters.\n"
                f"- Ensure that tags and values are exactly as shown, with no additional tags or modifications.\n"
                f"\n"
                f"Example XML format:\n"
                f"<invoice>\n"
                f"  <invoicenumber>16662010</invoicenumber>\n"
                f"  <invoicedate>08/28/2016</invoicedate>\n"
                f"  <seller>\n"
                f"    <companyname>Smith-Cook</companyname>\n"
                f"  </seller>\n"
                f"  <buyer>\n"
                f"    <companyname>Snyder-Johnson</companyname>\n"
                f"  </buyer>\n"
                f"  <items>\n"
                f"    <item>\n"
                f"      <description>Nintendo Gameboy Pocket Console Green with Box MGB-001 Japan Tested Working</description>\n"
                f"      <quantity>1,00</quantity>\n"
                f"      <unitprice>65,00</unitprice>\n"
                f"      <netprice>65,00</netprice>\n"
                f"    </item>\n"
                f"    <!-- More items as needed -->\n"
                f"  </items>\n"
                f"  <total>2 053,73</total>\n"
                f"</invoice>\n"
                f"\n"
                f"Text: {text}"
            )
                
            print(response.text)
            if response:
                xml_data = response.text.strip()  
                try:
                    extracted_data = parse_xml(xml_data)
                    print("Annyeong!")
                except ET.ParseError as e:
                    print(f"XML ParseError: {e}")  
                    extracted_data = "Error parsing XML response"
            else:
                extracted_data = "No response from Gemini API"

    else:
        form = UploadImageForm()

    return render(request, 'uploaddocument.html', {
        'form': form,
        'image_name': image_name,
        'image_data': image_data_base64,
        'raw_text': raw_text,
        'extracted_data': extracted_data,
        'xml_data': xml_data
    })

@never_cache
@require_POST
def save_extracted_data(request):
    if 'user_id' not in request.session:
        return redirect('login')  

    image_name = request.POST.get('image_name')
    image_data_base64 = request.POST.get('image_data')
    image_data = base64.b64decode(image_data_base64) if image_data_base64 else None
    seller_name = request.POST.get('seller_name')
    client_name = request.POST.get('client_name')
    invoice_number = request.POST.get('invoice_number')
    invoice_date = request.POST.get('invoice_date')
    total = request.POST.get('total')

    details_instance = Details(
        image_name=image_name,
        image=image_data,
        seller_name=seller_name,
        client_name=client_name,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
    )
    details_instance.save()

    descriptions = request.POST.getlist('items_description[]')
    quantities = request.POST.getlist('items_quantity[]')
    unit_prices = request.POST.getlist('items_unit_price[]')
    net_prices = request.POST.getlist('items_net_price[]')

    for description, quantity, unit_price, net_price in zip(descriptions, quantities, unit_prices, net_prices):
        Items.objects.create(
            invoice=details_instance,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            net_price=net_price
        )

    Summary.objects.create(
        invoice=details_instance,
        total=total
    )

    return redirect('uploaddocument')  

@never_cache
def proccessedimages(request):
    if 'user_id' not in request.session:
        return redirect('login')

    details_list = Details.objects.all()
    
    for details in details_list:
        if details.image:
            details.image_base64 = base64.b64encode(details.image).decode('utf-8')
        else:
            details.image_base64 = None

    return render(request, 'proccessedimages.html', {'details_list': details_list})

@never_cache
def view_details(request, pk):
    details = get_object_or_404(Details, pk=pk)
    items = details.items.all()
    summary = details.summary if hasattr(details, 'summary') else None

    image_data_base64 = None
    if details.image:
        image_data_base64 = base64.b64encode(details.image).decode('utf-8')

    context = {
        'pk': details.pk, 
        'image_name': details.image_name,
        'image_data': image_data_base64,
        'extracted_data': {
            'seller': {'name': details.seller_name},
            'buyer': {'name': details.client_name},
            'invoice_number': details.invoice_number,
            'invoice_date': details.invoice_date,
            'items': list(items.values('description', 'quantity', 'unit_price', 'net_price')),
            'total': summary.total if summary else '',
        } if summary else None,
    }
    return render(request, 'view_details.html', context)


@never_cache
@require_POST
def save_extracted_data2(request, pk=None):
    if 'user_id' not in request.session:
        return redirect('login') 

    image_name = request.POST.get('image_name')
    image_data_base64 = request.POST.get('image_data')
    image_data = base64.b64decode(image_data_base64) if image_data_base64 else None
    seller_name = request.POST.get('seller_name')
    client_name = request.POST.get('client_name')
    invoice_number = request.POST.get('invoice_number')
    invoice_date = request.POST.get('invoice_date')
    total = request.POST.get('total')

    if pk:
        details_instance = get_object_or_404(Details, pk=pk)
        details_instance.image_name = image_name
        details_instance.image = image_data
        details_instance.seller_name = seller_name
        details_instance.client_name = client_name
        details_instance.invoice_number = invoice_number
        details_instance.invoice_date = invoice_date
        details_instance.save()
    else:
        details_instance = Details(
            image_name=image_name,
            image=image_data,
            seller_name=seller_name,
            client_name=client_name,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
        )
        details_instance.save()

    descriptions = request.POST.getlist('items_description[]')
    quantities = request.POST.getlist('items_quantity[]')
    unit_prices = request.POST.getlist('items_unit_price[]')
    net_prices = request.POST.getlist('items_net_price[]')

    Items.objects.filter(invoice=details_instance).delete()

    for description, quantity, unit_price, net_price in zip(descriptions, quantities, unit_prices, net_prices):
        Items.objects.create(
            invoice=details_instance,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            net_price=net_price
        )

    if details_instance.summary:
        summary = details_instance.summary
        summary.total = total
        summary.save()
    else:
        Summary.objects.create(
            invoice=details_instance,
            total=total
        )
    return redirect('proccessedimages')  

@require_POST
def delete_details(request, pk):
    if 'user_id' not in request.session:
        return redirect('login')  

    details = get_object_or_404(Details, pk=pk)

    details.summary.delete() if details.summary else None
    details.items.all().delete()

    details.delete()

    return redirect('proccessedimages')  

def logout(request):
    request.session.flush()  
    return redirect('login')  

def clean_value(value):
    return float(value.replace(" ", "").replace(",", "."))


os.environ["GEMINI_API_KEY"] = "AIzaSyBiQn-MDin7cAXcNX1eFOVUGGDb5c5U8HQ"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
generation_config = {
    "temperature": 2,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)
chat_session = model.start_chat(history=[])

def parse_xml(xml_data):
    root = ET.fromstring(xml_data)
    
    parsed_data = {
        "seller": {
            "name": root.findtext("seller/companyname"),
        },
        "buyer": {
            "name": root.findtext("buyer/companyname"),
            
        },
        "invoice_number": root.findtext("invoicenumber"),
        "invoice_date": root.findtext("invoicedate"),
        "items": [],
        "total": root.findtext("total"),
    }
    for item in root.findall("items/item"):
        parsed_data["items"].append({
            "description": item.findtext("description"),
            "quantity": item.findtext("quantity"),
            "unit_price": item.findtext("unitprice"),
            "net_price": item.findtext("netprice")
        })

    return parsed_data
