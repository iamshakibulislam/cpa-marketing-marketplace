from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db import models
from .models import Offer, UserOfferRequest, ClickTracking, Conversion, SiteSettings, CPANetwork
from user.models import User
import json

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def offers_list(request):
    """Display list of offers with search and pagination"""
    offers_list = Offer.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        offers_list = offers_list.filter(
            models.Q(offer_name__icontains=search_query) |
            models.Q(cpa_network__name__icontains=search_query)
        )
    
    # Get user's offer requests
    user_requests = {}
    if request.user.is_authenticated:
        requests = UserOfferRequest.objects.filter(user=request.user)
        user_requests = {req.offer.id: req.status for req in requests}
    
    # Prepare offers data with status information
    offers_data = []
    for offer in offers_list:
        # Determine status for this offer and user
        if offer.id in user_requests:
            status = user_requests[offer.id]
            if status == 'approved':
                status_display = 'Approved'
                status_class = 'bg-success'
            elif status == 'rejected':
                status_display = 'Rejected'
                status_class = 'bg-danger'
            else:  # pending
                status_display = 'Pending'
                status_class = 'bg-warning'
        else:
            status_display = 'Need Approval'
            status_class = 'bg-secondary'
        
        offers_data.append({
            'offer': offer,
            'status_display': status_display,
            'status_class': status_class
        })
    
    # Pagination
    paginator = Paginator(offers_data, 10)  # Show 10 offers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'offers': page_obj,
        'user_requests': user_requests,
        'search_query': search_query,
        'total_offers': len(offers_data),
    }
    
    return render(request, 'dashboard/offers.html', context)

@require_POST
@login_required
def request_offer_access(request):
    """Handle offer access request"""
    try:
        data = json.loads(request.body)
        offer_id = data.get('offer_id')
        promotion_method = data.get('promotion_method', '')
        
        if not offer_id:
            return JsonResponse({'success': False, 'message': 'Offer ID is required'})
        
        offer = get_object_or_404(Offer, id=offer_id, is_active=True)
        
        # Check if user already has a request for this offer
        existing_request, created = UserOfferRequest.objects.get_or_create(
            user=request.user,
            offer=offer,
            defaults={
                'status': 'pending',
                'admin_note': f'Promotion method: {promotion_method}'
            }
        )
        
        if not created:
            # Update existing request
            existing_request.status = 'pending'
            existing_request.admin_note = f'Promotion method: {promotion_method}'
            existing_request.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Request submitted successfully',
            'status': 'pending'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def track_click(request):
    """Track offer clicks and redirect to original URL with click ID"""
    userid = request.GET.get('userid')
    offerid = request.GET.get('offerid')

    if not userid or not offerid:
        return HttpResponse("Invalid tracking link", status=400)

    try:
        user = get_object_or_404(User, id=userid)
        offer = get_object_or_404(Offer, id=offerid, is_active=True)

        try:
            user_request = UserOfferRequest.objects.get(user=user, offer=offer)
            if user_request.status != 'approved':
                return HttpResponse("Access denied", status=403)
        except UserOfferRequest.DoesNotExist:
            return HttpResponse("Access denied", status=403)

        # Generate click ID
        from .models import generate_click_id
        click_id = generate_click_id(user.id, offer.id)

        # Get visitor information
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')

        country = None # Placeholder for IP geolocation
        city = None    # Placeholder for IP geolocation

        # Create click tracking record
        click_tracking = ClickTracking.objects.create(
            user=user,
            offer=offer,
            click_id=click_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            city=city
        )

        # Build redirect URL with click ID for the specific CPA network
        redirect_url = offer.build_redirect_url(click_id)

        # Redirect to original offer URL with click ID
        return redirect(redirect_url)

    except (User.DoesNotExist, Offer.DoesNotExist):
        return HttpResponse("Invalid tracking link", status=404)
    except Exception as e:
        return HttpResponse("An error occurred", status=500)

def get_tracking_domains(request):
    """Get available tracking domains"""
    domains = getattr(settings, 'TRACKING_DOMAINS', ['http://localhost:8000'])
    
    domain_choices = []
    for domain in domains:
        domain_choices.append({
            'value': domain,
            'display': domain.replace('http://', '').replace('https://', '')
        })
    
    return JsonResponse({
        'success': True,
        'domains': domain_choices
    })

@csrf_exempt
def handle_postback(request):
    """Handle postback from CPA networks"""
    try:
        # Get the CPA network from the request
        network_key = request.GET.get('network') or request.POST.get('network')
        if not network_key:
            return HttpResponse("Network parameter required", status=400)

        # Get the CPA network
        try:
            cpa_network = CPANetwork.objects.get(network_key=network_key, is_active=True)
        except CPANetwork.DoesNotExist:
            return HttpResponse(f"Unknown network: {network_key}", status=400)

        # Get click ID and payout from the postback
        click_id_param = cpa_network.postback_click_id_parameter
        payout_param = cpa_network.postback_payout_parameter

        # Try to get values from both GET and POST
        network_click_id = request.GET.get(click_id_param) or request.POST.get(click_id_param)
        network_payout = request.GET.get(payout_param) or request.POST.get(payout_param)

        if not network_click_id:
            return HttpResponse(f"Missing {click_id_param} parameter", status=400)

        # Find the click tracking record
        try:
            click_tracking = ClickTracking.objects.get(click_id=network_click_id)
        except ClickTracking.DoesNotExist:
            return HttpResponse("Click tracking record not found", status=404)

        # Convert payout to decimal
        try:
            payout = float(network_payout) if network_payout else 0.0
        except (ValueError, TypeError):
            payout = 0.0

        # Create or update conversion record
        conversion, created = Conversion.objects.get_or_create(
            click_tracking=click_tracking,
            defaults={
                'payout': payout,
                'status': 'approved', # Default status for new conversions
                'network_click_id': network_click_id,
                'network_payout': network_payout
            }
        )

        if not created:
            # Update existing conversion
            conversion.payout = payout
            conversion.network_click_id = network_click_id
            conversion.network_payout = network_payout
            conversion.save()

        return HttpResponse("OK", status=200)

    except Exception as e:
        return HttpResponse(f"Error processing postback: {str(e)}", status=500)
