from django.shortcuts import render,redirect,get_object_or_404
from django.http import JsonResponse
from .forms import ProductForm
from .models import Customer_Profile,Product, Wishlist, Address, CartItem, Order, ShippingAddress, CustomerReview, Growbag, Notification, Season, SellerRevenue, AdminSettings, DeliveryAgentProfile, UserAgentDistance, AssignedDeliveryAgent
from userapp.models import CustomUser,SellerDetails
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.core.paginator import Paginator

# Create your views here.

#admin
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def generate_bar_plot(data, title):
    plt.figure(figsize=(8, 6))
    plt.bar(data.keys(), data.values())
    plt.title(title)
    plt.xlabel('Category')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    return base64.b64encode(buffer.getvalue()).decode()

@never_cache
@login_required(login_url='user_login')
def admin_dashboard(request):
    total_users = CustomUser.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(payment_status=Order.PaymentStatusChoices.SUCCESSFUL) \
                                  .aggregate(revenue=Sum('total_price'))['revenue'] or Decimal('0.00')  

    counts_plot = generate_bar_plot({'Users': total_users, 'Products': total_products, 'Orders': total_orders}, 'Counts')
  
    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'counts_plot': counts_plot,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required(login_url='user_login')
def admin_products(request):
    products = Product.objects.all()
    paginator = Paginator(products, 5)  # Show 8 products per page

    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    return render(request, 'admin_products.html', {'products': products})

@login_required(login_url='user_login')
def admin_users(request):
    customers = CustomUser.objects.filter(is_customer=True)
    sellers = CustomUser.objects.filter(is_seller=True)
    return render(request, 'admin_users.html', {'customers': customers, 'sellers': sellers})

@login_required(login_url='user_login')
def admin_orders(request):
    orders_list = Order.objects.all()
    paginator = Paginator(orders_list, 10)  # Show 10 orders per page

    page = request.GET.get('page')
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        orders = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        orders = paginator.page(paginator.num_pages)

    context = {'orders': orders}
    return render(request, 'admin_orders.html', context)


def admin_settings(request):
    admin_settings_obj, created = AdminSettings.objects.get_or_create(pk=1)
    if request.method == 'POST':
        selected_season = request.POST.get('selected_season')
        admin_settings_obj.selected_season = selected_season
        admin_settings_obj.save()
    
    return render(request, 'admin_settings.html', {'admin_settings_obj': admin_settings_obj})


from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # Add this import
from reportlab.lib import colors
from .models import CustomUser, Product
from reportlab.lib.pagesizes import landscape 


def admin_report(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Get current user email
        current_user_email = request.user.email

        # Prepare header content with line breaks
        header_content = [
            f'Report Type: {report_type}',
            f'Date Range: {start_date} to {end_date}',
            f'Current User Email: {current_user_email}'
        ]

        # Create a PDF document
        response = HttpResponse(content_type='application/pdf')
        if report_type == 'user':
            filename = "user_report.pdf"
        elif report_type == 'products':
            filename = "product_report.pdf"
        elif report_type == 'orders':
            filename = "order_report.pdf"
        else:
            filename = "report.pdf"  # Default filename if report type is not recognized
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []

        # Add header to the document
        header_style = getSampleStyleSheet()["Normal"]
        header_style.leading = 18  # Line spacing
        for line in header_content:
            header_paragraph = Paragraph(line, header_style)
            elements.append(header_paragraph)
            elements.append(Spacer(1, 12))  # Add some space between lines

        if report_type == 'user':
            # Generate user report
            users = CustomUser.objects.filter(date_joined__range=[start_date, end_date], hub_status=False)

            # Set up the PDF content
            data = [['Sl No.','Email', 'First Name', 'Last Name', 'User Type']]
            for idx, user in enumerate(users, start=1):
                user_type = 'Customer' if user.is_customer else 'Seller' if user.is_seller else 'Delivery Agent'
                data.append([idx,user.email, user.first_name, user.last_name, user_type])

            # Create a table
            table = Table(data)
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                       ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                       ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                       ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                       ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

            elements.append(table)

        elif report_type == 'products':
            # Generate product report
            products = Product.objects.filter(created_at__range=[start_date, end_date])
            wrap_style = ParagraphStyle(name='WrapStyle', wordWrap='CJK')

            # Set up the PDF content
            data = [['Sl No.','Product Name', 'Stock', 'Price', 'Category', 'Subcategory', 'Seller']]  # Update table header
            for idx, product in enumerate(products, start=1):
                data.append([idx,
                            Paragraph(product.product_name, wrap_style),  # Wrap Product Name
                            product.stock,
                            product.price,
                            product.product_category,
                            product.product_subcategory,
                            Paragraph(product.seller.email, wrap_style)])  # Wrap Seller Email

            col_widths = [doc.width * 0.05]  # Adjust width of the serial number column
            col_widths += [doc.width * 0.2]  # Increase width of "Product Name"
            col_widths += [doc.width * 0.1] * 2  # Adjust width of other columns
            col_widths += [doc.width * 0.10] * 2  # Increase width of "Category" and "Subcategory"
            col_widths[-1] = doc.width * 0.25

            # Create a table with adjusted column widths
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

            elements.append(table)


        elif report_type == 'orders':
            # Generate order report
            orders = Order.objects.filter(order_date__range=[start_date, end_date])

            wrap_style = ParagraphStyle(name='WrapStyle', wordWrap='CJK')

            # Set up the PDF content
            data = [['Sl No.','Order Date', 'User Email', 'Product Name', 'Seller Email', 'Total Price', 'Status', 'Order Status']]  # Update table header
            for idx, order in enumerate(orders, start=1):
                data.append([
                    idx,
                    Paragraph(order.order_date.strftime('%Y-%m-%d %H:%M:%S'), wrap_style),  # Wrap Order Date
                    Paragraph(order.user.email, wrap_style),  # Wrap User Email
                    Paragraph('<font size=10>' + ', '.join([item.product.product_name for item in order.cart_items.all()]) + '</font>', wrap_style),  # Wrap product name
                    Paragraph(order.cart_items.first().product.seller.email, wrap_style),  # Wrap Seller Email
                    order.total_price,
                    order.get_payment_status_display(),
                    order.get_order_status_display()
                ])

            col_widths = [doc.width * 0.05]  # Adjust width of the serial number column
            col_widths += [doc.width * 0.10]  # Increase width of "Order Date"
            col_widths += [doc.width * 0.15] * 2  # Increase width of "User Email" and "Seller Email"
            col_widths += [doc.width * 0.2] * 5  # Increase width of other columns

            # Create a table with adjusted column widths
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                       ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                       ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                       ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                       ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

            elements.append(table)

        # Build the document
        doc.build(elements)
        return response

    return render(request, 'admin_report.html')

def admin_agent_assign(request):
    delivery_agent = DeliveryAgentProfile.objects.all()
    return render(request, 'admin_agent_assign.html', {'delivery_agents': delivery_agent})

def admin_hubs(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        place = request.POST.get('place')
        confirm_password = request.POST.get('confirm-password')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif CustomUser.objects.filter(first_name=place, hub_status=True).exists():
            messages.error(request, 'A hub already exists for the selected place.')
        else:
            user = CustomUser.objects.create(
                email=email,
                first_name=place,
                hub_status=True,
                is_customer=False
            )
            user.set_password(password) 
            user.save()
        return redirect('admin_hubs')
    
    hubs = CustomUser.objects.filter(hub_status=True)

    return render(request, 'admin_hubs.html',{'hubs': hubs})

def delete_hub(request, hub_id):
    hub = CustomUser.objects.get(id=hub_id)
    hub.delete()
    return redirect('admin_hubs')


def hub_agent_assign(request):
    user=request.user
    
    distinct_order_ids = Order.objects.filter(
        accepted_by_store=True
    ).values('id').distinct()
    
    # Retrieve orders using the distinct order IDs
    show_orders = Order.objects.filter(id__in=distinct_order_ids)

    return render(request, 'hub_agent_assign.html', {'show_orders': show_orders})


from django.core.mail import send_mail
from django.template.loader import render_to_string

def admin_delivery_agents(request):
    if request.method == 'POST':
        # Check if the form is submitted
        user_id = request.POST.get('user_id')  # Get the user_id from the form
        # Retrieve the User object
        user = CustomUser.objects.get(id=user_id)
        # Update the is_active field to True
        user.is_active = True
        user.save()  # Save the user object

        subject = 'Congratulations! Your Profile Has Been Approved!'
        message = 'Welcome to AgriSelect. Your request to become a delivery agent has been approved. You can now login to your account and start using our platform. Best Regards - AgriSelect'
        html_message = render_to_string('approve_notification.html')
        recipient_list = [user.email]
        send_mail(subject, message, from_email=None, recipient_list=recipient_list, html_message=html_message)
        return redirect('admin_delivery_agents')
    
    delivery_agents = DeliveryAgentProfile.objects.select_related('delivery_agent').all()
    paginator = Paginator(delivery_agents, 10)  # Show 10 delivery agents per page

    page = request.GET.get('page')
    try:
        delivery_agents = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        delivery_agents = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        delivery_agents = paginator.page(paginator.num_pages)
    return render(request, 'admin_delivery_agents.html',{'delivery_agents':delivery_agents})

def get_agent_details(request, agent_id):
    agent = get_object_or_404(DeliveryAgentProfile, id=agent_id)
    return render(request, 'agent_details.html', {'agent': agent})

#Hub
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.urls import reverse

def hub_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.hub_status:
                login(request, user)
                return HttpResponseRedirect(reverse('hub_dashboard'))
            else:
                error_message = "Invalid credentials. Please make sure you are logging in as a hub user."
                return render(request, 'hub_login.html', {'error_message': error_message})
        else:
            error_message = "Invalid email or password."
            return render(request, 'hub_login.html', {'error_message': error_message})
    else:
        return render(request, 'hub_login.html')

@never_cache
def hub_dashboard(request):
    return render(request, 'hub_dashboard.html')

def hub_orders(request): 
    orders = Order.objects.filter(cart_items__dispatched=True, payment_status=Order.PaymentStatusChoices.SUCCESSFUL).distinct()
    if request.method == 'POST':  
        cart_item_id = request.POST.get('cart_item_id')  
        cart_item = CartItem.objects.get(pk=cart_item_id)  
        cart_item.accepted_by_store = True
        cart_item.save()
        for order in Order.objects.filter(cart_items=cart_item):
            if not all(item.dispatched for item in order.cart_items.all()):
                break
        else:
            order.accepted_by_store = True
            order.save()

        return redirect('hub_orders')
    context = {'orders': orders}
    return render(request, 'hub_orders.html', context)


def hub_report(request):
    return render(request, 'hub_report.html')



#Customer

@never_cache
def index(request):
    user = request.user
    products_with_sentiment_sum = Product.objects.annotate(sentiment_sum=Sum('customerreview__sentiment_score')).order_by('-sentiment_sum')[:3]
    for product in products_with_sentiment_sum:
        print (product.product_name)
    if user.is_anonymous:
        return render(request, 'index.html', {'products_with_sentiment_sum' : products_with_sentiment_sum})
    elif user.is_seller:
        return render(request, 'seller_dashboard.html')
    else:
        return render(request,'index.html', {'products_with_sentiment_sum': products_with_sentiment_sum })
    

# def search_products(request):
#     query = request.GET.get('q', '')
#     results = [] 

#     if query:
#         # Perform your search query here, for example, by filtering products based on the search query
#         results = Product.objects.filter(product_name__icontains=query)

#     # Prepare the search results as JSON data
#     search_results = [{'id':product.id,'product_name': product.product_name, 'product_category': product.product_category} for product in results]

#     response_data = {'results': search_results}
#     return JsonResponse(response_data)

def search_product(request, product_name):
    print(product_name)
    
    # Perform the search using a Q object to filter the Product model
    results = Product.objects.filter(product_name__icontains=product_name)
    
    # Serialize the results to JSON
    serialized_results = []
    
    if results.exists():  # Check if there are any results
        for result in results:
            serialized_results.append({
                'id': result.id,
                'product_name': result.product_name,
                'product_image': result.product_image.url,
            })
            print(result.id)
    else:
        print("No results found.")

    return JsonResponse({'results': serialized_results})


def customer_allProducts(request, category='All'):
    if category == 'All':
        products = Product.objects.filter(status__in=['in_stock', 'out_of_stock']).exclude(status='deactivated')
    else:
        products = Product.objects.filter(product_category=category, status__in=['instock', 'out_of_stock']).exclude(status='deactivated')
    categories = Product.objects.values_list('product_category', flat=True).distinct()
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'customer_allProducts.html', {'page': page,'products': products, 'selected_category': category, 'categories': categories})

import random
from twilio.rest import Client
from django.utils import timezone


def send_otp_via_sms(mobile_number, otp):
    # Your Twilio credentials
    account_sid = 'ACa2fcaf87e061fb6edd80385a76c502f1'
    auth_token = 'a7574566c793cbadaa642b43e0301903'
    twilio_number = '+12136744510'
    
    # Initialize Twilio client
    client = Client(account_sid, auth_token)
    
    # Compose the message
    message_body = f"Your OTP for verification is: {otp}"
    
    # Send the SMS
    client.messages.create(from_=twilio_number, body=message_body, to=mobile_number)

# def is_otp_expired(otp_timestamp):
#     # Check if the OTP timestamp is within the last 10 minutes
#     ten_minutes_ago = timezone.now() - timezone.timedelta(minutes=10)
#     return otp_timestamp < ten_minutes_ago

def customer_Profile(request):
    user_profile, created = Customer_Profile.objects.get_or_create(customer=request.user)
    addresses = Address.objects.filter(user_id=request.user.id)
    district_choices = Address.DISTRICT_CHOICES 
    
    if request.method == 'POST':
        # Check which form was submitted based on the button clicked
        if 'profile_save_button' in request.POST:
            # Handle profile form submission
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            mobile_number = request.POST.get('mobile_number')

            # Update the user profile fields
            user_profile.first_name = first_name
            user_profile.last_name = last_name
            user_profile.mobile_number = mobile_number
            user_profile.save()

            messages.success(request, 'Profile added successfully', extra_tags='profile_tag') 
            return redirect('customer_Profile')  # Display a success message
        
        elif 'verify_button' in request.POST:
            # Generate OTP
            otp = ''.join(random.choices('0123456789', k=6))
            otp_timestamp = timezone.now()
            user_profile.otp = otp
            # user_profile.otp_timestamp = otp_timestamp
            user_profile.save()

            # Send OTP via SMS
            send_otp_via_sms(user_profile.mobile_number, otp)

            # Store the OTP in the session to validate later
            request.session['otp'] = otp
            # request.session['otp_timestamp'] = otp_timestamp.isoformat()

            return redirect('customer_Profile') 
        
        elif 'submit_otp' in request.POST:
            # Get the entered OTP from the form
            entered_otp = request.POST.get('otp')

            # Get the OTP stored in the database for the user
            stored_otp = user_profile.otp
            # otp_timestamp = user_profile.otp_timestamp

            # Check if the OTP is expired
            # if is_otp_expired(otp_timestamp):
            #     messages.error(request, 'OTP has expired. Please request a new OTP.')
            #     return redirect('customer_Profile')

            # Check if the entered OTP matches the stored OTP
            if entered_otp == stored_otp:
                # Update the verified field to True
                user_profile.verified = True
                user_profile.save()
                messages.success(request, 'Mobile number verified successfully')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')

            return redirect('customer_Profile')


        elif 'address_save_button' in request.POST:
            
            # Handle address form submission
            building_name = request.POST.get('building_name')
            address_type = request.POST.get('address_type')
            street = request.POST.get('street')
            city = request.POST.get('city')
            state = request.POST.get('state')
            zip_code = request.POST.get('zip_code') 

            latitude_zip, longitude_zip = get_lat_long(zip_code)
            user_profile.latitude_zip = latitude_zip
            user_profile.longitude_zip = longitude_zip
            district = request.POST.get('district')
            if district in ['Ernakulam', 'Thrissur', 'Idukki', 'Alappuzha', 'Kottayam', 'Thiruvananthapuram', 'Pathanamthitta', 'Kollam']:
                location = 'Ernakulam'
            elif district in ['Kannur', 'Kasaragod', 'Kozhikode']:
                location = 'Kannur'
            elif district in ['Malappuram', 'Palakkad', 'Wayanad']:
                location = 'Malappuram'
            else:
                # Handle other districts
                location = ''
            address = Address(
                user=request.user,
                building_name=building_name,
                address_type=address_type,
                street=street,
                city=city,
                state=state,
                zip_code=zip_code,
                district=district,
                location=location
            )
            address.save()
            messages.success(request, 'Address added successfully', extra_tags='add_address_tag')
            return redirect('customer_Profile') 
    
    context = {
        'user_profile': user_profile,
        'addresses': addresses, 
        'district_choices': district_choices,
        'form_submitted': request.method == 'POST',
    }
    return render(request, 'customer_Profile.html', context)
    

def update_address(request):
    if request.method == 'POST':
        # Extract the data sent via AJAX
        address_id = request.POST.get('address_id')
        building_name = request.POST.get('building_name')
        address_type = request.POST.get('address_type')
        street = request.POST.get('street')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        district = request.POST.get('district')
        if district in ['Ernakulam', 'Thrissur', 'Idukki', 'Alappuzha', 'Kottayam', 'Thiruvananthapuram', 'Pathanamthitta', 'Kollam']:
            location = 'Ernakulam'
        elif district in ['Kannur', 'Kasaragod', 'Kozhikode']:
            location = 'Kannur'
        elif district in ['Malappuram', 'Palakkad', 'Wayanad']:
            location = 'Malappuram'
        else:
            # Handle other districts
            location = ''
        # Update the address
        address = get_object_or_404(Address, id=address_id)
        address.building_name = building_name
        address.address_type = address_type
        address.street = street
        address.city = city
        address.state = state
        address.zip_code = zip_code
        address.district = district
        address.location = location
        address.save()

        # You can return a JSON response to indicate a successful update
        return JsonResponse({'success': True})

    # If the request is not a POST request or not an AJAX request, return an error response
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def delete_address(request, address_id):
    try:
        details = Address.objects.get(id=address_id)
        details.delete()
        return JsonResponse({'success': True})
    except Address.DoesNotExist:
        # Handle the case where the address does not exist
        return JsonResponse({'success': False})
    
@login_required(login_url='user_login')
def customer_Wishlist(request):
    if request.user.is_authenticated:
        user_wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        products = user_wishlist.products.all()
        paginator = Paginator(products, 6)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)
        return render(request, 'customer_Wishlist.html', {'user': request.user, 'wishlist': user_wishlist, 'page': page})
    else:
        return render(request, 'customer_Wishlist.html', {'user': None, 'wishlist': None})

@login_required(login_url='user_login')
def add_to_wishlist(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, pk=product_id)
        user_wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        user_wishlist.products.add(product)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})
    

def remove_from_wishlist(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, pk=product_id)
        user_wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        user_wishlist.products.remove(product)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})


companion_crops_data = {
    'Cherry Tomato': [9,11,12,13],
    'Carrot': [1,11],
    'Tulsi': [1,11],
    'Green Chilli': [9,1,12],
    'Eggplant': [9,11,14,15,16],
    'Apple': [11,12],
    'Tulsi': [1,11],
    'Mango': [17,18],
    'Jasmine': [19,20,21],
    'Lotus': [],
    'Marigold': [1,12,9,13,5],
    'Cucumber': [12,11,1],
    # Add more products and their companion crops as needed
}

@login_required(login_url='user_login')
def customer_ProductView(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product_category = product.product_category
    product_subcategory = product.product_subcategory

    # Fetch related products and reviews
    related_products = Product.objects.filter(
        product_category=product_category,
        status__in=['in_stock', 'out_of_stock']
    ).exclude(pk=product_id)[:4]

    reviews = CustomerReview.objects.filter(product=product)
    if request.user.is_authenticated:
            user_has_purchased_product = Order.objects.filter(
            user=request.user,
            cart_items__product=product,
            payment_status=Order.PaymentStatusChoices.SUCCESSFUL
        ).exists()
            
    # Get companion crops for the selected product
    companion_crops_ids = companion_crops_data.get(product.product_name, [])
    
    # Retrieve details of recommended products from the Product model
    recommended_products = Product.objects.filter(pk__in=companion_crops_ids)
    
    context = {
        'product': product,
        'product_category': product_category,
        'product_subcategory': product_subcategory,
        'related_products': related_products,
        'reviews': reviews,
        'user_has_purchased_product': user_has_purchased_product,
        'recommended_products': recommended_products 
    }

    return render(request, 'customer_ProductView.html', context)

import nltk
nltk.download('vader_lexicon')
from nltk.sentiment import SentimentIntensityAnalyzer
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment')
        sentiment_analyzer = SentimentIntensityAnalyzer()
        sentiment_score = sentiment_analyzer.polarity_scores(comment)['compound']
        
        # Check if the user has already reviewed the product
        existing_review = CustomerReview.objects.filter(product=product, user=request.user).exists()
        

        if not existing_review:
            # Create a new review
            review = CustomerReview.objects.create(product=product, user=request.user, rating=rating, comment=comment, sentiment_score=sentiment_score)
            return redirect('customer_ProductView', product_id=product_id)
        else:
            return JsonResponse({'success': False, 'message': 'You have already reviewed this product.'})   

    return redirect('customer_ProductView', product_id=product_id)


@login_required(login_url='user_login')
def customer_OrderView(request):
    user = request.user
    # Fetch the user's orders and related products
    orders = Order.objects.filter(user=user, payment_status=Order.PaymentStatusChoices.SUCCESSFUL).prefetch_related('cart_items').order_by('-order_date')

    # Set the number of orders to display per page
    orders_per_page = 5

    # Paginate the orders
    paginator = Paginator(orders, orders_per_page)
    page = request.GET.get('page', 1)

    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        orders_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver the last page of results.
        orders_page = paginator.page(paginator.num_pages)

    context = {
        'orders': orders_page,
    }
    print(orders)  # Add this line to print the orders in the console

    return render(request, 'customer_OrderView.html', context)

from django.utils.decorators import method_decorator
from django.views import View
from datetime import datetime

from django.db.models import DateTimeField
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@method_decorator(login_required, name='dispatch')
class CustomerOrderView(View):
    template_name = 'customer_OrderView.html'
    items_per_page = 10  # Adjust the number of items per page as needed

    def get(self, request, *args, **kwargs):
        user = request.user
        date_filter = request.GET.get('date_filter')

        orders = Order.objects.filter(user=user, payment_status=Order.PaymentStatusChoices.SUCCESSFUL)
    
        if date_filter:
            # Check if date_filter is not None or empty
            if date_filter.strip():
                # Parse the date from the input field
                parsed_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                print(parsed_date)
                print(date_filter)
                # Filter orders based on the chosen date
                orders = orders.filter(order_date__date=parsed_date)

        orders = orders.annotate(truncated_date=TruncDate('order_date')).prefetch_related('cart_items')

        # Paginate the orders
        paginator = Paginator(orders, self.items_per_page)
        page = request.GET.get('page')

        try:
            orders = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            orders = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            orders = paginator.page(paginator.num_pages)

        context = {
            'orders': orders,
        }
        return render(request, self.template_name, context)


def verify_order_otp(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        otp_entered = request.POST.get('otp')
        
        # Retrieve the order object
        order = Order.objects.get(id=order_id)
        assign = AssignedDeliveryAgent.objects.get(order=order) 
        # Check if the entered OTP matches the OTP stored in the order and it's not null
        if order.otp == otp_entered and order.otp != 'Null':
            # Update the order to mark it as verified
            order.verified = True
            order.order_status = order.OrderStatusChoices.DELIVERED
            order.save()
            assign.delivered = True
            assign.save()
            # Redirect to a success page or display a success message
            messages.success(request, 'Order verified successfully.')
            return redirect('customer_order_view')  # Change 'success_page' to the name of your success page URL
        else:
            # Display an error message if the OTP is incorrect or null
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('customer_order_view')










#cart
@login_required(login_url='user_login')
# def add_to_Cart(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
    
#     if request.method == 'POST':
#         quantity = int(request.POST.get('quantity', 1))
        
#         # Check if a similar product with status cleared or ordered exists in the cart
#         existing_cart_item = CartItem.objects.filter(user=request.user, product=product, status__in=[CartItem.StatusChoices.CLEARED, CartItem.StatusChoices.ORDERED]).first()

#         if existing_cart_item:
#             # If an existing item is found, create a new cart item
#             new_cart_item = CartItem.objects.create(user=request.user, product=product, quantity=quantity, status=CartItem.StatusChoices.ACTIVE)
#         else:
#             # If no existing item is found, update the existing one with status active
#             cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
#             cart_item.quantity = quantity
#             cart_item.status = CartItem.StatusChoices.ACTIVE
#             cart_item.save()
#             new_cart_item = cart_item
#         return redirect('cart')
#         # return redirect('http://127.0.0.1:8000/customer_ProductView/' + str(product_id) + '/')

def add_to_cart(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)

        # Check if a similar product with status active exists in the cart
        existing_cart_item = CartItem.objects.filter(user=request.user, product=product, status=CartItem.StatusChoices.ACTIVE).first()

        if existing_cart_item:
            # If an existing item is found, update the existing cart item with status active
            if existing_cart_item.quantity < product.stock:
                existing_cart_item.quantity += 1
                existing_cart_item.save()
            else:
                messages.error(request, "Cannot add more than available stock.")
        else:
            # If no existing item is found, create a new cart item
            if product.stock > 0:
                new_quantity = min(1, product.stock)  # Ensure the quantity does not exceed available stock
                new_cart_item = CartItem.objects.create(user=request.user, product=product, quantity=new_quantity, status=CartItem.StatusChoices.ACTIVE)

    return redirect('cart')

def cart(request): 
    cart_items = CartItem.objects.filter(user=request.user, status=CartItem.StatusChoices.ACTIVE) 
    total_items = sum(cart_item.quantity for cart_item in cart_items)
    total_price = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)
    context = {
        'cart_items': cart_items,
        'total_items': total_items,
        'total_price': total_price,
            # ... other context variables ... 
    } 
    return render(request, 'customer_Cart.html',context) 
 
def remove_from_cart(request, product_id): 
    cart_item = get_object_or_404(CartItem, user=request.user, id=product_id) 
    print(f"Received product_id: {product_id}")  #Fixed the typo here 
    # cart_item.status = CartItem.StatusChoices.CLEARED  # Set status to cleared
    cart_item.delete()  # Save the changes to the object
    return redirect('cart')

def decrease_item(request, item_id): 
    try: 
        cart_item = CartItem.objects.get(id=item_id) 
        if cart_item.quantity > 1: 
            cart_item.quantity -= 1 
            cart_item.save() 
    except CartItem.DoesNotExist: 
        pass  # Handle the case when the item does not exist in the cart 
    return redirect('cart')  # Redirect back to the cart page after decreasing the item quantity 
 
def increase_item(request, item_id): 
    try: 
        cart_item = CartItem.objects.get(id=item_id) 
        if cart_item.quantity + 1 <= cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
    except CartItem.DoesNotExist: 
        pass  # Handle the case when the item does not exist in the cart 
    return redirect('cart')

def customer_Checkout(request):
    user = request.user
    # Fetch the user's addresses from the database
    user_addresses = Address.objects.filter(user=user)
    cart_items = CartItem.objects.filter(user=request.user,  status=CartItem.StatusChoices.ACTIVE) 
    total_items = sum(cart_item.quantity for cart_item in cart_items)
    total_price = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total_items': total_items,
        'total_price': total_price,
        'user_addresses': user_addresses,
            # ... other context variables ... 
    } 
    return render(request,'customer_Checkout.html',context)

from django.http import HttpResponse
from django.template.loader import get_template
from django.views import View
from xhtml2pdf import pisa

class GeneratePDF(View):
    template_name = 'invoice_template.html'

    def get(self, request, *args, **kwargs):
        # Fetch order details from the database based on the order_id
        order_id = kwargs['order_id']
        order = Order.objects.get(id=order_id)

        # Render the template
        template = get_template(self.template_name)
        context = {'order': order}
        html = template.render(context)

        # Create a PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'filename=invoice_{order_id}.pdf'

        # Generate PDF using ReportLab
        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')

        return response














#Seller
@never_cache
def seller_home(request):
    return render(request,'seller_home.html')

@login_required(login_url='user_login')
def seller_addProducts(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)  # Create a new Product instance but don't save it yet
            product.seller = request.user 
            # Manually assign the selected category and subcategory values to the model fields
            product.product_category = form.cleaned_data['category']
            product.product_subcategory = form.cleaned_data['subcategory']
            
            product.save()  # Save the complete Product instance
            messages.success(request, "Product added successfully.", extra_tags='seller_product_add')
            return redirect('seller_addProducts')  # Redirect back to the add products page
    else:
        form = ProductForm()
    context = {'form': form}
    return render(request, 'seller_addProducts.html', context)

@login_required(login_url='user_login')
def seller_Products(request):
    products = Product.objects.filter(
        seller=request.user,
        status__in=[Product.StatusChoices.IN_STOCK, Product.StatusChoices.OUT_OF_STOCK]
    )  # Fetch products associated with the currently logged-in seller
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page,'products': products}
    return render(request, 'seller_Products.html', context)

def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product.status = Product.StatusChoices.DEACTIVATED
        product.save()
        # Optionally, you can add a success message here
    except Product.DoesNotExist:
        # Handle the case where the product does not exist
        pass
    return redirect('seller_Products')

def seller_updateProduct(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            # Add a success message if needed
            return redirect('seller_Products')  # Redirect back to the products list
    else:
        form = ProductForm(instance=product)

    return render(request, 'seller_updateProduct.html', {'form': form, 'product': product})


def seller_Profile(request):
    user = request.user  # Get the current logged-in user
    try:
        seller_details = SellerDetails.objects.get(user=user)  # Retrieve the seller's details
    except SellerDetails.DoesNotExist:
        seller_details = None

    if request.method == "POST":
        # Update the CustomUser fields
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        # You can update other CustomUser fields here if needed

        # Update the SellerDetails fields
        if seller_details is None:
            # Create a new SellerDetails instance if it doesn't exist
            seller_details = SellerDetails(user=user)

        seller_details.store_name = request.POST.get("store-name")
        seller_details.phone_number = request.POST.get("phone-number")
        seller_details.pincode = request.POST.get("pincode")
        seller_details.building_name = request.POST.get("pickup-building")
        seller_details.pickup_address = request.POST.get("pickup-address")
        seller_details.city = request.POST.get("city")
        seller_details.state = request.POST.get("state")
        seller_details.account_holder_name = request.POST.get("account-holder-name")
        seller_details.account_number = request.POST.get("account-number")
        seller_details.bank_name = request.POST.get("bank-name")
        seller_details.branch = request.POST.get("branch")
        seller_details.ifsc_code = request.POST.get("ifsc-code")

        # Save both the CustomUser and SellerDetails instances
        user.save()
        seller_details.save()

        messages.success(request, "Profile updated successfully!") 
        return redirect('seller_Profile')  # Redirect back to the profile page after successful update

    context = {
        'seller_details': seller_details,  # Pass the seller details to the template
    }
    return render(request, 'seller_Profile.html', context)


from django.db.models import Sum
from django.db.models import Count

@never_cache
def seller_dashboard(request):
    if request.user.is_authenticated:
        # Get the count of products for the logged-in seller
        current_seller = request.user
        product_count = Product.objects.filter(seller=current_seller).count()
        seller_products = Product.objects.filter(seller=current_seller)
        notification = Notification.objects.filter(seller_id=request.user.id,read=False).count()
        order_count = Order.objects.filter(cart_items__product__in=seller_products).count()
        products_sold_quantity = CartItem.objects.filter(
            product__seller=current_seller,
            status=CartItem.StatusChoices.ORDERED,
            order__payment_status=Order.PaymentStatusChoices.SUCCESSFUL
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0

        total_revenue = SellerRevenue.objects.filter(seller=current_seller).aggregate(Sum('revenue'))['revenue__sum'] or 0

        # Pass the counts to the template
        context = {
            'product_count': product_count,
            'order_count': order_count,
            'products_sold_quantity': products_sold_quantity,
            'notification':notification,
            'total_revenue': total_revenue,
            # Add other counts to the context if needed
        }

        return render(request, 'seller_dashboard.html', context)
    else:
        return render(request, 'error.html', {'error_message': 'User not authenticated'})

# def get_sales_data(request):
#     # Assuming your Order model has a date field named 'order_date'
#     sales_data = Order.objects.filter(
#         user=request.user,
#         payment_status=Order.PaymentStatusChoices.SUCCESSFUL
#     ).values('order_date__month').annotate(total_sales=Sum('total_price'))

#     # Convert the QuerySet to a list of dictionaries
#     sales_data_list = list(sales_data)

#     return JsonResponse({'sales_data': sales_data_list})

def get_product_statistics(request):
    # Assuming your Product model has 'product_category' and 'product_subcategory' fields
    category_statistics = Product.objects.filter(
        seller=request.user
    ).values('product_category').annotate(product_count=Count('id'))

    subcategory_statistics = Product.objects.filter(
        seller=request.user
    ).values('product_subcategory').annotate(product_count=Count('id'))

    return JsonResponse({
        'category_statistics': list(category_statistics),
        'subcategory_statistics': list(subcategory_statistics),
    })

from django.db.models import Count

def sales_statistics(request):
    # Calculate product sales data
    product_sales_data = Product.objects.annotate(
        total_sales=Count('order__id')
    ).values('product_name', 'total_sales')

    # Convert the queryset into a dictionary suitable for the chart
    product_data = {
        'labels': [entry['product_name'] for entry in product_sales_data],
        'datasets': [{
            'data': [entry['total_sales'] for entry in product_sales_data],
            'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56']  # Adjust colors as needed
        }]
    }

    # Pass data to the template context
    context = {
        'product_data': product_data,
    }

    return render(request, 'seller_dashboard.html', context)


from datetime import datetime
@login_required
def seller_orders(request):
    if request.method == 'POST':  
        cart_item_id = request.POST.get('cart_item_id')  
        cart_item = CartItem.objects.get(pk=cart_item_id)  
        cart_item.dispatched = True
        cart_item.save()
        # Check if all products of the order are dispatched
        for order in Order.objects.filter(cart_items=cart_item):
            if not all(item.dispatched for item in order.cart_items.all()):
                break
        else:
            order.order_status = Order.OrderStatusChoices.DISPATCHED
            order.save()

        return redirect('seller_orders')
    
    seller_id = request.user.id
    date_filter = request.GET.get('date_filter')

    # Step 1: Query orders for a specific seller with successful payment status
    seller_orders = Order.objects.filter(cart_items__product__seller_id=seller_id, payment_status=Order.PaymentStatusChoices.SUCCESSFUL)

    # Step 2: Filter orders based on the provided date
    if date_filter:
        date_filter = datetime.strptime(date_filter, '%Y-%m-%d').date()
        seller_orders = seller_orders.filter(order_date__date=date_filter)

    seller_orders = seller_orders.distinct()

    # Step 3: Extract relevant information from orders
    orders_data = []
    for order in seller_orders:
        order_info = {
            'order_id': order.id,
            'order_date': order.order_date,
            'total_price': order.total_price,
            'order_status': order.order_status,
            'items': []
        }

        # Extract information about each bought item in the order
        for cart_item in order.cart_items.all():
            if cart_item.product.seller_id == seller_id:
                item_info = {
                    'product_image': cart_item.product.product_image.url,
                    'product_name': cart_item.product.product_name,
                    'quantity': cart_item.quantity,
                    'total_item_price': cart_item.total_price,
                    'cart_item_id': cart_item.id,
                    'dispatched': cart_item.dispatched
                }
                order_info['items'].append(item_info)

        orders_data.append(order_info)

    # Paginate the orders_data
    paginator = Paginator(orders_data, 6)  # Show 10 orders per page

    page_number = request.GET.get('page')
    try:
        orders_data = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        orders_data = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        orders_data = paginator.page(paginator.num_pages)

    # Step 4: Pass the data to the template
    context = {'orders_data': orders_data}
    
    return render(request, 'seller_orders.html', context)


def seller_report(request):
    return render(request, 'seller_report.html')

from django.http import HttpResponse, HttpResponseNotAllowed

def generate_sales_report(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        seller_id = request.user.id
        
        seller_products = Product.objects.filter(seller_id=seller_id)
        
        # Filter orders based on the selected date range and seller's products
        orders = Order.objects.filter(
            Q(order_date_only__gte=start_date) & Q(order_date_only__lte=end_date),
            cart_items__product__in=seller_products
        ).distinct()
        print(orders)
        print(start_date)
        print(end_date)
        # Generate PDF
        template_path = 'seller_sales_report.html'  # HTML template for the PDF
        context = {'orders': orders}
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'filename="sales_report.pdf"'
        
        template = get_template(template_path)
        html = template.render(context)
        
        # Create PDF
        pisa.CreatePDF(html, dest=response)
        return response
    else:
        # Handle GET request or other methods if needed
        return HttpResponseNotAllowed(['POST'])

def seller_sales_report(request):
    return render(request, 'seller_sales_report.html')

from django.db.models import Q

@login_required
def low_stock_notification(request, seller_id):
    products=Product.objects.filter(seller_id=seller_id)
    for i in products:
        if i.stock<5:
            existing_notification = Notification.objects.filter(
                Q(seller_id=seller_id) & Q(message__icontains=i.product_name)
            ).exists()
            if not existing_notification:
                # Create a new notification only if a similar one does not exist
                stock = Notification.objects.create(
                    seller_id=seller_id,
                    message=f"The product {i.product_name} is on low stock with {i.stock}",
                )
            print("stock")
    return redirect("seller_dashboard")

@login_required
def showNotification(request,seller_id):
    notifications=Notification.objects.filter(seller_id=seller_id)
    return render(request,"notification_list.html",{'notifications':notifications})

@login_required
def mark_notifications_as_read(request):
    noti=Notification.objects.filter(seller_id=request.user.id,read=False)
    noti.delete()
    return redirect('seller_dashboard')


def order_notification(seller_id, product_id):
    # Retrieve the order
    print("function")
    
    # Assuming you have a list of products in the order
    

    product=Product.objects.get(id=product_id)
    print(product_id)
        # Create a notification for the seller if the product is associated with the seller
    if product.seller_id == seller_id:
        print("if")
        notification = Notification(
            seller_id=seller_id,
            message=f"An order for the product {product.product_name} has been placed."
        )
        notification.save()

#payment
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from decimal import Decimal
from django.db import transaction



# authorize razorpay client with API Keys.
razorpay_client = razorpay.Client(
	auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))


def homepage(request):
    if request.method == 'POST':
        selected_address_id = request.POST.get('selected_address')
        if selected_address_id:
            user = request.user
            cart_items = CartItem.objects.filter(user=user, status=CartItem.StatusChoices.ACTIVE)
            total_price = Decimal(sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items))
            currency = 'INR'
            amount = int(total_price * 100)
            razorpay_order = razorpay_client.order.create(dict(
                amount=amount,
                currency=currency,
                payment_capture='0'
            ))
            razorpay_order_id = razorpay_order['id']
            callback_url = '/paymenthandler/'
            order = Order.objects.create(
                user=user,
                total_price=total_price,
                razorpay_order_id=razorpay_order_id,
                shipping_address_id=selected_address_id,
                payment_status=Order.PaymentStatusChoices.PENDING,
            )
            for cart_item in cart_items:
                order.cart_items.add(cart_item)
            order.save()

    # Create a context dictionary with all the variables you want to pass to the template
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_merchant_key': settings.RAZOR_KEY_ID,
        'razorpay_amount': amount,  # Set to 'total_price'
        'currency': currency,
        'callback_url': callback_url,
    }

    return render(request, 'homepage.html', context=context)

from twilio.rest import Client
# we need to csrf_exempt this url as
# POST request will be made by Razorpay
# and it won't have the csrf token.
@csrf_exempt
def paymenthandler(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        # Verify the payment signature.
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        result = razorpay_client.utility.verify_payment_signature(
            params_dict)
        if result is False:
            # Signature verification failed.    
            return render(request, 'payment/paymentfail.html')
        else:
            # Signature verification succeeded.
            # Retrieve the order from the database
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            

            # Capture the payment with the amount from the order
            amount = int(order.total_price * 100)  # Convert Decimal to paise
            razorpay_client.payment.capture(payment_id, amount)

            # Update the order with payment ID and change status to "Successful"
            order.payment_id = payment_id
            order.payment_status = Order.PaymentStatusChoices.SUCCESSFUL
            order.save()
           
            # Update the stock of products
            for cart_item in order.cart_items.all():
                product = cart_item.product
                if product.status == Product.StatusChoices.IN_STOCK:
                    product.stock -= cart_item.quantity
                    if product.stock == 0:
                        product.status = Product.StatusChoices.OUT_OF_STOCK
                    product.save()

                    
                    order_notification(product.seller.id, product.id)
                
                revenue_amount = cart_item.total_price * Decimal('0.70')  # Calculate revenue (70% of total price)
                SellerRevenue.objects.create(order=order, seller=product.seller, revenue=revenue_amount)

            cart_items = CartItem.objects.filter(user=request.user)
            for cart_item in cart_items:
                cart_item.status = CartItem.StatusChoices.ORDERED
                cart_item.save()
            
            if order.payment_status == Order.PaymentStatusChoices.SUCCESSFUL:
                message_body = f"✅ Your order has been placed for order ID #{order.id} on  📅{order.order_date_only}. We look forward for further orders from you. Thank for choosing AgriSelect🌱 for your need."

                client = Client("AC784edca2d4dc48edab5e0eb39519d949", "b4f393289f7f588341d23277806cdaa3")
                message = client.messages.create(
                    from_='whatsapp:+14155238886',
                    body=message_body,
                    to='whatsapp:+917306053696'  # Replace with the user's WhatsApp number
                )

            # Redirect to a success page or return a success response
            return redirect('/')



@login_required(login_url='user_login')
def product_crops(request):
    crop_products = Product.objects.filter(product_category='crops',status__in=['in_stock', 'out_of_stock'])
    products_per_page = 6  # You can adjust this number as needed

    # Get the page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Create a Paginator instance for the crop products
    paginator = Paginator(crop_products, products_per_page)

    # Get the products for the current page
    crop_products_page = paginator.get_page(page_number)
    return render(request, 'product_crops.html', {'crop_products_page': crop_products_page})

@login_required(login_url='user_login')
def product_seeds(request):
    seeds_products = Product.objects.filter(product_category='seeds',status__in=['in_stock', 'out_of_stock'])
    products_per_page = 6  # You can adjust this number as needed

    # Get the page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Create a Paginator instance for the crop products
    paginator = Paginator(seeds_products, products_per_page)

    # Get the products for the current page
    seeds_products_page = paginator.get_page(page_number)
    return render(request, 'product_seeds.html', {'seeds_products_page': seeds_products_page})

@login_required(login_url='user_login')
def customer_growbag(request):
    if request.method == 'POST':
        customer = request.user
        color_chosen = request.POST.get('color')  # Get the chosen color from the form data
        size_chosen = request.POST.get('size')  # Get the chosen size from the form data
        drainage_holes = request.POST.get('drainage') == 'on'  # Check if drainage holes are selected
        icon_chosen = request.POST.get('icons')  # Get the chosen icon from the form data
        current_price = Decimal(request.POST.get('price'))  # Convert to Decimal
        qty = int(request.POST.get('quantity')) 
        image = request.FILES.get('growbag-img')

        # Create a new instance of the Growbag model with the form data
        growbag = Growbag(
            customer = customer,
            color_chosen=color_chosen,
            size_chosen=size_chosen,
            drainage_holes=drainage_holes,
            icon_chosen=icon_chosen,
            current_price=current_price,
            qty=qty,
            image=image
        )

        # Save the instance to the database
        growbag.save()
        total_price = current_price * qty
        request.session['total_price'] = str(total_price)
        return redirect('growbag_checkout')

    return render(request, 'customer_growbag.html')

def growbag_checkout(request):
    total_price = request.session.get('total_price')
    total_price = Decimal(total_price)
    request.session['total_price'] = str(total_price)

    return render(request, 'growbag_checkout.html', {'total_price': total_price})

import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from decimal import Decimal
from django.db import transaction

razorpay_client = razorpay.Client(
	auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))


def growbag_payment(request):
    if request.method == 'POST':
            user = request.user
            total_price = request.session.get('total_price')
            total_price = Decimal(total_price)
            currency = 'INR'
            amount = int(total_price * 100)
            razorpay_order = razorpay_client.order.create(dict(
                amount=amount,
                currency=currency,
                payment_capture='0'
            ))
            razorpay_order_id = razorpay_order['id']
            callback_url = '/growbagpaymenthandler/'             

    # Create a context dictionary with all the variables you want to pass to the template
            context = {
                'total_price': total_price,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_merchant_key': settings.RAZOR_KEY_ID,
                'razorpay_amount': amount,  # Set to 'total_price'
                'currency': currency,
                'callback_url': callback_url,
            }

    return render(request, 'growbag_payment.html', context=context)

from twilio.rest import Client
@csrf_exempt
def growbagpaymenthandler(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        # Verify the payment signature.
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        result = razorpay_client.utility.verify_payment_signature(
            params_dict)
        if result is False:
            # Signature verification failed.    
            return render(request, 'payment/paymentfail.html')
        else:
            total_price = request.session.get('total_price')
            total_price = Decimal(total_price)
            # Capture the payment with the amount from the order
            amount = int(total_price * 100)  # Convert Decimal to paise
            razorpay_client.payment.capture(payment_id, amount)

            # Update the order with payment ID and change status to "Successful"
            # order.payment_id = payment_id
            # order.payment_status = Growbag.PaymentStatusChoices.SUCCESSFUL
            # order.save()
           
            # Update the stock of products
            # for cart_item in order.cart_items.all():
            #     product = cart_item.product
            #     if product.status == Product.StatusChoices.IN_STOCK:
            #         product.stock -= cart_item.quantity
            #         if product.stock == 0:
            #             product.status = Product.StatusChoices.OUT_OF_STOCK
            #         product.save()

                    
            #         order_notification(product.seller.id, product.id)
                
            #     revenue_amount = cart_item.total_price * Decimal('0.70')  # Calculate revenue (70% of total price)
            #     SellerRevenue.objects.create(order=order, seller=product.seller, revenue=revenue_amount)

            # cart_items = CartItem.objects.filter(user=request.user)
            # for cart_item in cart_items:
            #     cart_item.status = CartItem.StatusChoices.ORDERED
            #     cart_item.save()

            # Redirect to a success page or return a success response
            return redirect('/')
        


def seasonal_sale(request):
    admin_settings_obj, created = AdminSettings.objects.get_or_create(pk=1)
    selected_season = admin_settings_obj.selected_season
    
    current_season = Season.objects.get(name=selected_season)
    seasonal_products = Product.objects.filter(season=current_season)

    paginator = Paginator(seasonal_products, 6)
    page_number = request.GET.get('page')
    try:
        seasonal_products = paginator.page(page_number)
    except PageNotAnInteger:
        seasonal_products = paginator.page(1)
    except EmptyPage:
        seasonal_products = paginator.page(paginator.num_pages)

    context = {
        'seasonal_products': seasonal_products,
        'selected_season': selected_season  # Pass selected season to template
    }
    return render(request, 'seasonal_sale.html', context)



from math import sin, cos, sqrt, atan2, radians

def haversine(lat1, lon1, lat2, lon2):
    # Helper function to convert latitude and longitude strings to floats
    def convert_coord(coord):
        return float(coord) if coord is not None else 0.0
    
    # Convert latitude and longitude strings to floats
    lat1, lon1, lat2, lon2 = map(convert_coord, [lat1, lon1, lat2, lon2])

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula (rest of the function remains the same)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) * 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) * 2
    print(a)
    c = 2 * atan2(sqrt(abs(a)), sqrt(1 - abs(a)))
    distance = 6371.0 * c  # Radius of Earth in kilometers

    return distance

def allot_del_boy(request, order_id):
    agents = DeliveryAgentProfile.objects.all()
    order_instance = Order.objects.filter(id=order_id).first()
    if order_instance:
            user_order=order_instance.user
            profile= Address.objects.filter(user=user_order).first()
            latitude=profile.latitude_zip
            longitude=profile.longitude_zip
            for agent in agents:
                if latitude is not None and longitude is not None:
                    # Calculate distance for each seller using haversine
                    distance = haversine(agent.latitude_zip, agent.longitude_zip, latitude, longitude)
                    UserAgentDistance.objects.update_or_create(
                        user=request.user,
                        agent=agent.delivery_agent,
                        defaults={'distance': distance}
                    )
            useragent = UserAgentDistance.objects.filter(user=request.user)
            nearby_agent = useragent.filter(
                distance__isnull=False,
                user=request.user,
            ).order_by('distance')[:1]

            nearest_user_agent_distance = nearby_agent.first()
            if nearest_user_agent_distance:
                nearest_delivery_agent = nearest_user_agent_distance.agent
            
            AssignedDeliveryAgent.objects.create(
            user=request.user, order=order_instance, deliveryagent=nearest_delivery_agent)
            return redirect('hub_agent_assign')

        
    else:
        # Handle the case where no order with the given ID is found
        return HttpResponse("Order not found")
    
from geopy.geocoders import Nominatim

def get_lat_long(location):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(location)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

#delivery agent
@never_cache
def delivery_agent_home(request):
    return render(request, 'delivery_agent_home.html')

from django.contrib.auth.hashers import make_password

def delivery_agent_reg(request):
    alert_message = None
    if request.method == 'POST':
        # Extract data from the form
        email = request.POST.get('email')
        password = make_password(request.POST.get('password'))
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        pincode=request.POST.get('pincode'),
        latitude_zip, longitude_zip = get_lat_long(pincode)

        
        # Create a CustomUser instance
        user = CustomUser(email=email, password=password, first_name=first_name, last_name=last_name, is_delivery_agent=True, is_active=False)
        user.save()
        
        delivery_agent_profile = DeliveryAgentProfile(
            delivery_agent=user,
            profile_photo=request.FILES.get('profilePhoto'),
            gender=request.POST.get('gender'),
            date_of_birth=request.POST.get('date_of_birth'),
            address=request.POST.get('address'),
            phone=request.POST.get('phone'),
            location=request.POST.get('location'),
            aadhaar_number=request.POST.get('id_number'),
            pincode=pincode,
            latitude_zip=latitude_zip,
            longitude_zip=longitude_zip,
            driver_license_number=request.POST.get('driver_license_number'),
            vehicle_type=request.POST.get('vehicle_type'),
            vehicle_number=request.POST.get('vehicle_number'),
            bank_name=request.POST.get('bank_name'),
            branch=request.POST.get('branch'),
            account_number=request.POST.get('account_number'),
            ifsc_code=request.POST.get('ifsc_code'),
            id_document=request.FILES.get('id_document')
        )
        
        # Save the DeliveryAgentProfile instance
        delivery_agent_profile.save()
        alert_message = "Successfully registered!"
    return render(request, 'delivery_agent_reg.html',  {'alert_message': alert_message})

def delivery_agent_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        # Check if the email and password match
        if email and password:
            user = CustomUser.objects.filter(email=email).first()
            if user and user.check_password(password):
                # If the email and password match, attempt to authenticate the user
                user = authenticate(request, email=email, password=password)
                if user:
                    if user.is_active and user.is_delivery_agent:
                        login(request, user)
                        return redirect(reverse('delivery_agent'))  # Redirect to the delivery agent's home page
                    elif not user.is_active:
                        messages.error(request, "Your account is not active.")
                    else:
                        messages.error(request, "You are not authorized to access this page.")
                else:
                    messages.error(request, "Invalid email or password.")
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Email and password are required.")
    return render(request, 'delivery_agent_login.html')

@never_cache
@login_required(login_url='delivery_agent_login')
def delivery_agent(request):
    if request.method == 'POST':
        user = request.user
        if user.is_authenticated:
            delivery_agent_profile = DeliveryAgentProfile.objects.get(delivery_agent=user)
            if 'availableBtn' in request.POST:
                delivery_agent_profile.availability = True
            elif 'notAvailableBtn' in request.POST:
                delivery_agent_profile.availability = False
            delivery_agent_profile.save()
            return redirect('delivery_agent')  # Redirect after POST to avoid resubmission on refresh
    
    # Fetch the delivery agent profile
    user = request.user
    if user.is_authenticated:
        delivery_agent_profile = DeliveryAgentProfile.objects.get(delivery_agent=user)
    else:
        delivery_agent_profile = None

    context = {
        'delivery_agent_profile': delivery_agent_profile,
    }
    return render(request, 'delivery_agent.html', context)

@login_required(login_url='delivery_agent_login')
def delivery_agent_profile(request):
    delivery_agent_profile = DeliveryAgentProfile.objects.get(delivery_agent=request.user)
    context = {'delivery_agent_profile': delivery_agent_profile}
    return render(request, 'delivery_agent_profile.html', context)
   

@login_required(login_url='delivery_agent_login')
# def delivery_agent_orders(request):
#     orders_list = Order.objects.filter(cart_items__accepted_by_store=True).distinct()
#     paginator = Paginator(orders_list, 10)  # Number of orders per page
#     if request.method == 'POST':  
#         cart_item_id = request.POST.get('cart_item_id')  
#         cart_item = CartItem.objects.get(pk=cart_item_id)  
#         cart_item.ready_for_pickup = True
#         cart_item.save()
#         for order in Order.objects.filter(cart_items=cart_item):
#             if all(item.ready_for_pickup for item in order.cart_items.all()):
#                 order.ready_for_pickup = True
#                 order.save()

#         return redirect('delivery_agent_orders')
#     page_number = request.GET.get('page')
#     try:
#         orders = paginator.page(page_number)
#     except PageNotAnInteger:
#         orders = paginator.page(1)
#     except EmptyPage:
#         orders = paginator.page(paginator.num_pages)

#     context = {'orders': orders}
#     return render(request, 'delivery_agent_orders.html', context)

def delivery_agent_orders(request):
    del_req= AssignedDeliveryAgent.objects.filter(deliveryagent=request.user)
    return render(request, 'delivery_agent_orders.html', {'del_req':del_req})

def send_otp_to_customer(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    user_profile = get_object_or_404(Customer_Profile, customer=order.user)
    
    # Generate OTP
    otp = ''.join(random.choices('0123456789', k=6))
    order.otp = otp
    order.save()
    
    # Send OTP via SMS
    send_otp_via_sms(user_profile.mobile_number, otp)
    
    return redirect('delivery_agent_orders')


def customer_addresses(request):
    user_profile, created = Customer_Profile.objects.get_or_create(customer=request.user)
    addresses = Address.objects.filter(user_id=request.user.id)
    district_choices = Address.DISTRICT_CHOICES 
    
    if request.method == 'POST':        
        
        if 'address_save_button' in request.POST:
            
            # Handle address form submission
            building_name = request.POST.get('building_name')
            address_type = request.POST.get('address_type')
            street = request.POST.get('street')
            city = request.POST.get('city')
            state = request.POST.get('state')
            zip_code = request.POST.get('zip_code') 

            latitude_zip, longitude_zip = get_lat_long(zip_code)
            
            district = request.POST.get('district')
            if district in ['Ernakulam', 'Thrissur', 'Idukki', 'Alappuzha', 'Kottayam', 'Thiruvananthapuram', 'Pathanamthitta', 'Kollam']:
                location = 'Ernakulam'
            elif district in ['Kannur', 'Kasaragod', 'Kozhikode']:
                location = 'Kannur'
            elif district in ['Malappuram', 'Palakkad', 'Wayanad']:
                location = 'Malappuram'
            else:
                # Handle other districts
                location = ''
            address = Address(
                user=request.user,
                building_name=building_name,
                address_type=address_type,
                street=street,
                city=city,
                state=state,
                zip_code=zip_code,
                district=district,
                location=location,
                latitude_zip = latitude_zip,
                longitude_zip = longitude_zip
            )
            address.save()
            messages.success(request, 'Address added successfully', extra_tags='add_address_tag')
            return redirect('customer_addresses') 
    
    context = {
        'addresses': addresses, 
        'district_choices': district_choices,
        'form_submitted': request.method == 'POST',
    }
    return render(request, 'customer_addresses.html', context)


def update_picked(request):
    if request.method == 'POST':
        # Get the order ID from the form
        order_id = request.POST.get('order_id')
        
        # Retrieve the AssignedDeliveryAgent object for the given order ID
        assigned_delivery_agent = AssignedDeliveryAgent.objects.get(order_id=order_id)
        
        # Update the status to 'PICKED'
        assigned_delivery_agent.status = 'PI'
        assigned_delivery_agent.save()
        order = Order.objects.get(id=order_id)
        # Update the ready_for_pickup field of the Order object to True
        order.picked_by_agent = True
        order.save()
        # Redirect to the same page or any other page as needed
        return redirect('delivery_agent_orders')  # Redirect to the delivery agent orders page
    
    # Handle GET requests or any other scenarios if needed
    return redirect('delivery_agent_orders')
    
def update_ready_picked(request):
    if request.method == 'POST':
        # Get the order ID from the form
        order_id = request.POST.get('order_id')
        assigned_delivery_agent = AssignedDeliveryAgent.objects.get(order_id=order_id)
        assigned_delivery_agent.ready_for_pickup = True
        assigned_delivery_agent.save()
        order = Order.objects.get(id=order_id)
        # Update the ready_for_pickup field of the Order object to True
        order.ready_for_pickup = True
        order.save()
        return redirect('delivery_agent_orders')
    


