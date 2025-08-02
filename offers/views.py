from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Offer, UserOfferRequest

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
