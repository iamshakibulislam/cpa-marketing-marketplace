from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from .models import Offer, UserOfferRequest, ClickTracking
from user.models import User
import requests
import json

@login_required
def offers(request):
    # Get all active offers
    offers_list = Offer.objects.filter(is_active=True).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(offers_list, 10)  # 10 offers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user's request status for each offer
    user_requests = {}
    if request.user.is_authenticated:
        user_requests = {
            req.offer_id: req.status 
            for req in UserOfferRequest.objects.filter(user=request.user)
        }
    
    # Prepare offers with user status
    offers_with_status = []
    for offer in page_obj:
        # Determine user's status for this offer
        if offer.id in user_requests:
            user_status = user_requests[offer.id]
            if user_status == 'approved':
                status_display = 'Approved'
                status_class = 'bg-success'
            elif user_status == 'pending':
                status_display = 'Pending'
                status_class = 'bg-warning'
            else:  # rejected
                status_display = 'Rejected'
                status_class = 'bg-danger'
        else:
            if offer.need_approval:
                status_display = 'Need Approval'
                status_class = 'bg-info'
            else:
                status_display = 'Active'
                status_class = 'bg-success'
        
        offers_with_status.append({
            'offer': offer,
            'status_display': status_display,
            'status_class': status_class,
            'user_has_requested': offer.id in user_requests
        })
    
    context = {
        'offers': offers_with_status,
        'page_obj': page_obj,
        'total_offers': paginator.count,
    }
    
    return render(request, 'dashboard/offers.html', context)


@login_required
@require_POST
@csrf_exempt
def request_offer_access(request):
    """Handle AJAX request for offer access"""
    try:
        offer_id = request.POST.get('offer_id')
        promotional_method = request.POST.get('promotional_method')
        
        if not offer_id or not promotional_method:
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields'
            })
        
        # Get the offer
        offer = Offer.objects.get(id=offer_id, is_active=True)
        
        # Check if user already has a request for this offer
        existing_request, created = UserOfferRequest.objects.get_or_create(
            user=request.user,
            offer=offer,
            defaults={
                'status': 'pending',
                'admin_note': f'Promotional Method: {promotional_method}'
            }
        )
        
        if not created:
            # Update existing request
            existing_request.admin_note = f'Promotional Method: {promotional_method}'
            existing_request.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Request submitted successfully!',
            'status': 'pending'
        })
        
    except Offer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Offer not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        })


def track_click(request):
    """Track offer clicks and redirect to original URL"""
    userid = request.GET.get('userid')
    offerid = request.GET.get('offerid')
    
    if not userid or not offerid:
        return HttpResponse("Invalid tracking link", status=400)
    
    try:
        # Get user and offer
        user = get_object_or_404(User, id=userid)
        offer = get_object_or_404(Offer, id=offerid, is_active=True)
        
        # Check if user is approved for this offer
        try:
            user_request = UserOfferRequest.objects.get(user=user, offer=offer)
            if user_request.status != 'approved':
                return HttpResponse("Access denied", status=403)
        except UserOfferRequest.DoesNotExist:
            return HttpResponse("Access denied", status=403)
        
        # Get visitor information
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')
        
        # Get location information (optional - you can use a service like ipapi.co)
        country = None
        city = None
        try:
            # You can integrate with IP geolocation services here
            # For now, we'll leave it as None
            pass
        except:
            pass
        
        # Create click tracking record
        ClickTracking.objects.create(
            user=user,
            offer=offer,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            city=city
        )
        
        # Redirect to original offer URL
        return redirect(offer.offer_url)
        
    except (User.DoesNotExist, Offer.DoesNotExist):
        return HttpResponse("Invalid tracking link", status=404)
    except Exception as e:
        return HttpResponse("An error occurred", status=500)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def get_tracking_domains(request):
    """Get available tracking domains for the user"""
    from django.conf import settings
    domains = getattr(settings, 'TRACKING_DOMAINS', ['http://localhost:8000'])
    
    # Format domains for display (remove protocol for cleaner display)
    domain_options = []
    for domain in domains:
        display_name = domain.replace('https://', '').replace('http://', '')
        domain_options.append({
            'value': domain,
            'display': display_name
        })
    
    return JsonResponse({
        'success': True,
        'domains': domain_options
    })
