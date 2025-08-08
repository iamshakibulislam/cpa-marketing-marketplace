from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db import models
from django.db.models import Q
from .models import Offer, UserOfferRequest, ClickTracking, Conversion, SiteSettings, CPANetwork
from user.models import User
import json
import requests
from datetime import datetime

def get_client_ip(request):
    """Get client IP address - improved version based on Stack Overflow best practices"""
    # Try different headers in order of preference
    ip = None
    
    # 1. Try X-Forwarded-For (most common for proxies)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    
    # 2. Try X-Real-IP
    if not ip or ip == '127.0.0.1':
        ip = request.META.get('HTTP_X_REAL_IP')
    
    # 3. Try X-Forwarded
    if not ip or ip == '127.0.0.1':
        ip = request.META.get('HTTP_X_FORWARDED')
    
    # 4. Try X-Cluster-Client-IP
    if not ip or ip == '127.0.0.1':
        ip = request.META.get('HTTP_X_CLUSTER_CLIENT_IP')
    
    # 5. Fallback to REMOTE_ADDR
    if not ip or ip == '127.0.0.1':
        ip = request.META.get('REMOTE_ADDR')
    
    # 6. If still no valid IP, try HTTP_CLIENT_IP
    if not ip or ip == '127.0.0.1':
        ip = request.META.get('HTTP_CLIENT_IP')
    
    # 7. Last resort - if we're in development, use a default
    if not ip:
        ip = '127.0.0.1'  # Localhost for development
    
    return ip

@login_required
def view_offer(request, offer_id):
    """Display detailed view of a specific offer"""
    offer = get_object_or_404(Offer, id=offer_id, is_active=True)
    
    # Get user's request status for this offer
    try:
        user_request = UserOfferRequest.objects.get(user=request.user, offer=offer)
        status = user_request.status
        if status == 'approved':
            status_display = 'Approved'
            status_class = 'bg-success'
            can_access = True
        elif status == 'rejected':
            status_display = 'Rejected'
            status_class = 'bg-danger'
            can_access = False
        else:  # pending
            status_display = 'Pending'
            status_class = 'bg-warning'
            can_access = False
    except UserOfferRequest.DoesNotExist:
        status_display = 'Need Approval'
        status_class = 'bg-secondary'
        can_access = False
        user_request = None
    
    # Get tracking domains
    tracking_domains = getattr(settings, 'TRACKING_DOMAINS', ['http://localhost:8000'])
    domain_options = []
    for domain in tracking_domains:
        domain_options.append({
            'value': domain,
            'display': domain.replace('http://', '').replace('https://', '')
        })
    
    context = {
        'offer': offer,
        'status_display': status_display,
        'status_class': status_class,
        'can_access': can_access,
        'user_request': user_request,
        'tracking_domains': domain_options,
        'default_domain': getattr(settings, 'DEFAULT_TRACKING_DOMAIN', 'http://localhost:8000')
    }
    
    return render(request, 'dashboard/view_offer.html', context)

@login_required
def approved_offers(request):
    """Display list of approved offers for the user"""
    # Get user's approved offers
    user_requests = UserOfferRequest.objects.filter(
        user=request.user, 
        status='approved'
    ).values_list('offer_id', flat=True)
    
    offers_list = Offer.objects.filter(
        id__in=user_requests,
        is_active=True
    )
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        offers_list = offers_list.filter(
            models.Q(offer_name__icontains=search_query) |
            models.Q(cpa_network__name__icontains=search_query)
        )
    
    # Prepare offers data with status information (all will be approved)
    offers_data = []
    for offer in offers_list:
        offers_data.append({
            'offer': offer,
            'status_display': 'Approved',
            'status_class': 'bg-success'
        })
    
    # Pagination
    paginator = Paginator(offers_data, 10)  # Show 10 offers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'offers': page_obj,
        'search_query': search_query,
        'total_offers': len(offers_data),
    }
    
    return render(request, 'dashboard/approved_offers.html', context)

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
    
    # Get subid parameters
    subid1 = request.GET.get('subid1', '')
    subid2 = request.GET.get('subid2', '')
    subid3 = request.GET.get('subid3', '')

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

        # Create click tracking record with subid parameters
        click_tracking = ClickTracking.objects.create(
            user=user,
            offer=offer,
            click_id=click_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            subid1=subid1 if subid1 else None,
            subid2=subid2 if subid2 else None,
            subid3=subid3 if subid3 else None
        )
        
        # Fetch IP information from ipinfo.io and save it
        if ip_address:
            if ip_address == '127.0.0.1':
                # For development environment, set some default values
                click_tracking.country = 'Development'
                click_tracking.city = 'Localhost'
                click_tracking.region = 'Development Environment'
                click_tracking.timezone = 'UTC'
                click_tracking.organization = 'Development Server'
                click_tracking.save()
                print(f"Development environment detected, using default values for {ip_address}")
            else:
                try:
                    # Fetch IP info from ipinfo.io
                    response = requests.get(f'https://ipinfo.io/{ip_address}/json', timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Update click tracking with IP info
                        click_tracking.country = data.get('country', '')
                        click_tracking.city = data.get('city', '')
                        click_tracking.region = data.get('region', '')
                        click_tracking.timezone = data.get('timezone', '')
                        click_tracking.postal_code = data.get('postal', '')
                        click_tracking.organization = data.get('org', '')
                        
                        # Parse location coordinates
                        if 'loc' in data and data['loc']:
                            try:
                                lat, lon = data['loc'].split(',')
                                click_tracking.latitude = float(lat.strip())
                                click_tracking.longitude = float(lon.strip())
                            except (ValueError, AttributeError):
                                pass
                        
                        click_tracking.save()
                        print(f"IP info fetched for {ip_address}: {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}")
                    else:
                        print(f"Failed to fetch IP info for {ip_address}: HTTP {response.status_code}")
                except Exception as e:
                    print(f"Error fetching IP info for {ip_address}: {str(e)}")
        else:
            print(f"No IP address captured")

        # Build redirect URL with click ID for the specific CPA network
        redirect_url = offer.build_redirect_url(click_id)
        
        # Enhanced debug logging (remove in production)
        print("=" * 50)
        print("CLICK TRACKING DEBUG INFO:")
        print(f"User ID: {user.id}")
        print(f"Offer ID: {offer.id}")
        print(f"Offer Name: {offer.offer_name}")
        print(f"Click ID: {click_id}")
        print(f"CPA Network: {offer.cpa_network.name}")
        print(f"CPA Network Key: {offer.cpa_network.network_key}")
        print(f"Click ID Parameter: '{offer.cpa_network.click_id_parameter}'")
        print(f"Original Offer URL: {offer.offer_url}")
        print(f"Final Redirect URL: {redirect_url}")
        print(f"Redirect URL type: {type(redirect_url)}")
        print(f"Redirect URL length: {len(redirect_url)}")
        print("=" * 50)

        # Use HttpResponseRedirect instead of redirect() for better control
        print(f"About to redirect to: {redirect_url}")
        return HttpResponseRedirect(redirect_url)

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

        # Use the offer's payout amount (set in admin panel) instead of network payout
        offer_payout = click_tracking.offer.payout

        # Create or update conversion record
        conversion, created = Conversion.objects.get_or_create(
            click_tracking=click_tracking,
            defaults={
                'payout': offer_payout,  # Use offer payout instead of network payout
                'status': 'approved', # Default status for new conversions
                'network_click_id': network_click_id,
                'network_payout': network_payout  # Store network payout for reference
            }
        )

        if not created:
            # Update existing conversion
            conversion.payout = offer_payout  # Use offer payout instead of network payout
            conversion.network_click_id = network_click_id
            conversion.network_payout = network_payout
            conversion.save()  # This will automatically handle balance updates

        return HttpResponse("OK", status=200)

    except Exception as e:
        return HttpResponse(f"Error processing postback: {str(e)}", status=500)

def test_cpa_networks(request):
    """Test view to check CPA network configurations"""
    networks = CPANetwork.objects.all()
    offers = Offer.objects.all()
    
    debug_info = []
    debug_info.append("=== CPA NETWORKS ===")
    for network in networks:
        debug_info.append(f"Network: {network.name}")
        debug_info.append(f"  Key: {network.network_key}")
        debug_info.append(f"  Click ID Parameter: {network.click_id_parameter}")
        debug_info.append("")
    
    debug_info.append("=== OFFERS ===")
    for offer in offers:
        debug_info.append(f"Offer: {offer.offer_name}")
        debug_info.append(f"  URL: {offer.offer_url}")
        debug_info.append(f"  CPA Network: {offer.cpa_network.name if offer.cpa_network else 'None'}")
        if offer.cpa_network:
            debug_info.append(f"  Click ID Parameter: {offer.cpa_network.click_id_parameter}")
            # Test the build_redirect_url method
            test_url = offer.build_redirect_url("TEST-CLICK-ID")
            debug_info.append(f"  Test Redirect URL: {test_url}")
        debug_info.append("")
    
    return HttpResponse("<br>".join(debug_info))

def test_redirect_url(request):
    """Test view to verify redirect URL building"""
    offer_id = request.GET.get('offer_id', 1)
    click_id = request.GET.get('click_id', 'TEST-CLICK-ID')
    
    try:
        offer = Offer.objects.get(id=offer_id)
        redirect_url = offer.build_redirect_url(click_id)
        
        result = f"""
        <h3>Redirect URL Test</h3>
        <p><strong>Offer:</strong> {offer.offer_name}</p>
        <p><strong>CPA Network:</strong> {offer.cpa_network.name}</p>
        <p><strong>Click ID Parameter:</strong> {offer.cpa_network.click_id_parameter}</p>
        <p><strong>Original URL:</strong> {offer.offer_url}</p>
        <p><strong>Click ID:</strong> {click_id}</p>
        <p><strong>Final Redirect URL:</strong> <a href="{redirect_url}" target="_blank">{redirect_url}</a></p>
        <p><strong>URL Length:</strong> {len(redirect_url)}</p>
        <p><strong>Contains Parameter:</strong> {offer.cpa_network.click_id_parameter in redirect_url}</p>
        """
        
        return HttpResponse(result)
    except Offer.DoesNotExist:
        return HttpResponse("Offer not found")

@login_required
def daily_reports(request):
    """
    Daily Reports View - Shows daily performance summary with filtering and pagination
    """
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    offer_id = request.GET.get('offer_id')
    subid = request.GET.get('subid')
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 15)
    
    # Get user's click tracking data
    user_click_data = ClickTracking.objects.filter(user=request.user)
    
    # Apply date filters if provided
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            user_click_data = user_click_data.filter(
                click_date__date__range=[start_date, end_date]
            )
        except ValueError:
            pass
    
    # Apply offer filter if provided
    if offer_id:
        user_click_data = user_click_data.filter(offer_id=offer_id)
    
    # Apply subid filter if provided
    if subid:
        user_click_data = user_click_data.filter(
            Q(subid1=subid) | Q(subid2=subid) | Q(subid3=subid)
        )
    
    # Group by date and calculate daily metrics
    daily_stats = {}
    
    for click in user_click_data:
        date_key = click.click_date.date()
        if date_key not in daily_stats:
            daily_stats[date_key] = {
                'clicks': 0,
                'conversions': 0,
                'earnings': 0,
                'conversion_rate': 0.0,
                'epc': 0.0
            }
        
        daily_stats[date_key]['clicks'] += 1
        
        # Check if this click led to a conversion
        conversion = Conversion.objects.filter(click_tracking=click).first()
        if conversion:
            daily_stats[date_key]['conversions'] += 1
            # Earnings = offer payout × number of conversions
            daily_stats[date_key]['earnings'] += float(click.offer.payout)
    
    # Calculate conversion rates and EPC
    for date, stats in daily_stats.items():
        if stats['clicks'] > 0:
            stats['conversion_rate'] = (stats['conversions'] / stats['clicks']) * 100
            # EPC = total earnings / total clicks
            stats['epc'] = stats['earnings'] / stats['clicks']
    
    # Sort by date (most recent first)
    sorted_dates = sorted(daily_stats.keys(), reverse=True)
    
    # Prepare data for template
    daily_reports_data = []
    for date in sorted_dates:
        stats = daily_stats[date]
        daily_reports_data.append({
            'date': date,
            'total_clicks': stats['clicks'],
            'total_conversions': stats['conversions'],
            'conversion_rate': round(stats['conversion_rate'], 2),
            'earnings': round(stats['earnings'], 2),
            'epc': round(stats['epc'], 2)
        })
    
    # Pagination
    paginator = Paginator(daily_reports_data, page_size)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    # Calculate summary statistics
    total_clicks = sum(stats['clicks'] for stats in daily_stats.values())
    total_conversions = sum(stats['conversions'] for stats in daily_stats.values())
    total_earnings = sum(stats['earnings'] for stats in daily_stats.values())
    avg_conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
    
    # Get available offers for filter (offers the user has access to)
    user_approved_requests = UserOfferRequest.objects.filter(
        user=request.user, 
        status='approved'
    ).values_list('offer_id', flat=True)
    user_offers = Offer.objects.filter(
        id__in=user_approved_requests,
        is_active=True
    )
    
    # Get available subids for filter
    subids = set()
    for click in user_click_data:
        if click.subid1:
            subids.add(click.subid1)
        if click.subid2:
            subids.add(click.subid2)
        if click.subid3:
            subids.add(click.subid3)
    
    context = {
        'daily_data': page_obj,
        'offers': user_offers,
        'subids': sorted(list(subids)),
        'current_filters': {
            'start_date': start_date,
            'end_date': end_date,
            'offer_id': offer_id,
            'subid': subid,
            'page_size': page_size
        }
    }
    
    return render(request, 'dashboard/daily_reports.html', context)

@login_required
def get_daily_details(request):
    """Get detailed performance data for a specific date"""
    print(f"DEBUG: get_daily_details called with params: {request.GET}")
    
    date_str = request.GET.get('date')
    offer_id = request.GET.get('offer_id')
    subid = request.GET.get('subid')
    
    print(f"DEBUG: date_str={date_str}, offer_id={offer_id}, subid={subid}")
    
    if not date_str:
        return JsonResponse({'success': False, 'message': 'Date parameter required'})
    
    try:
        # Parse the date
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get user's click tracking data for the specific date
        user_click_data = ClickTracking.objects.filter(
            user=request.user,
            click_date__date=selected_date
        )
        
        # Apply filters if provided
        if offer_id:
            user_click_data = user_click_data.filter(offer_id=offer_id)
        
        if subid:
            user_click_data = user_click_data.filter(
                Q(subid1=subid) | Q(subid2=subid) | Q(subid3=subid)
            )
        
        # Calculate daily metrics
        total_clicks = user_click_data.count()
        conversions = Conversion.objects.filter(click_tracking__in=user_click_data)
        total_conversions = conversions.count()
        
        # Calculate earnings (offer payout × conversions)
        total_earnings = 0
        for conversion in conversions:
            total_earnings += float(conversion.click_tracking.offer.payout)
        
        # Calculate conversion rate and EPC
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        epc = (total_earnings / total_clicks) if total_clicks > 0 else 0
        
        # Get top performing offers for this date
        offer_stats = {}
        for click in user_click_data:
            offer_name = click.offer.offer_name
            if offer_name not in offer_stats:
                offer_stats[offer_name] = {
                    'clicks': 0,
                    'conversions': 0,
                    'earnings': 0
                }
            
            offer_stats[offer_name]['clicks'] += 1
            
            # Check if this click led to a conversion
            conversion = Conversion.objects.filter(click_tracking=click).first()
            if conversion:
                offer_stats[offer_name]['conversions'] += 1
                offer_stats[offer_name]['earnings'] += float(click.offer.payout)
        
        # Sort offers by earnings (descending)
        top_offers = sorted(offer_stats.items(), key=lambda x: x[1]['earnings'], reverse=True)
        
        # Prepare response data
        response_data = {
            'success': True,
            'date': selected_date.strftime('%B %d, %Y'),
            'summary': {
                'total_clicks': total_clicks,
                'total_conversions': total_conversions,
                'conversion_rate': round(conversion_rate, 2),
                'earnings': round(total_earnings, 2),
                'epc': round(epc, 2)
            },
            'top_offers': []
        }
        
        # Add top performing offers (limit to 5)
        for offer_name, stats in top_offers[:5]:
            response_data['top_offers'].append({
                'name': offer_name,
                'clicks': stats['clicks'],
                'conversions': stats['conversions'],
                'earnings': round(stats['earnings'], 2)
            })
        
        return JsonResponse(response_data)
        
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid date format'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def click_reports(request):
    """Display click tracking reports with filtering and pagination"""
    from datetime import datetime, timedelta
    from django.db.models import Q
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    offer_id = request.GET.get('offer_id')
    subid = request.GET.get('subid')
    
    # Set default date range (last 7 days)
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=6)
    
    # Get user's click tracking data
    click_data = ClickTracking.objects.filter(
        user=request.user,
        click_date__date__range=[start_date, end_date]
    ).select_related('offer').order_by('-click_date')
    
    # Apply filters
    if offer_id:
        click_data = click_data.filter(offer_id=offer_id)
    
    if subid:
        click_data = click_data.filter(
            Q(subid1=subid) | Q(subid2=subid) | Q(subid3=subid)
        )
    
    # Get unique offers and subids for filter dropdowns
    offers = Offer.objects.filter(is_active=True).order_by('offer_name')
    subids = ClickTracking.objects.filter(user=request.user).values_list(
        'subid1', 'subid2', 'subid3'
    ).distinct()
    
    # Flatten and filter subids
    unique_subids = set()
    for subid_tuple in subids:
        for subid_val in subid_tuple:
            if subid_val:
                unique_subids.add(subid_val)
    
    # Pagination
    paginator = Paginator(click_data, 20)  # Show 20 clicks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Prepare current filters for template
    current_filters = {
        'start_date': start_date,
        'end_date': end_date,
        'offer_id': offer_id,
        'subid': subid
    }
    
    context = {
        'click_data': page_obj,
        'offers': offers,
        'subids': sorted(unique_subids),
        'current_filters': current_filters,
        'total_clicks': click_data.count(),
    }
    
    return render(request, 'dashboard/click_report.html', context)

@login_required
def offer_reports(request):
    """Display offer performance reports with filtering and pagination"""
    from datetime import datetime, timedelta
    from django.db.models import Count, Sum, Q
    from decimal import Decimal
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Set default date range (last 7 days)
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=6)
    
    # Get user's approved offers
    user_offers = Offer.objects.filter(
        userofferrequest__user=request.user,
        userofferrequest__status='approved',
        is_active=True
    ).distinct()
    
    # Get offer performance data
    offer_data = []
    total_clicks = 0
    total_conversions = 0
    total_earnings = Decimal('0.00')
    
    for offer in user_offers:
        # Get clicks for this offer in date range
        clicks = ClickTracking.objects.filter(
            user=request.user,
            offer=offer,
            click_date__date__range=[start_date, end_date]
        ).count()
        
        # Get conversions for this offer in date range
        conversions = Conversion.objects.filter(
            click_tracking__user=request.user,
            click_tracking__offer=offer,
            conversion_date__date__range=[start_date, end_date]
        )
        
        conversion_count = conversions.count()
        
        # Calculate earnings (conversions * offer payout)
        earnings = conversion_count * offer.payout
        
        # Calculate EPC (Earnings Per Click)
        epc = earnings / clicks if clicks > 0 else Decimal('0.00')
        
        # Add to totals
        total_clicks += clicks
        total_conversions += conversion_count
        total_earnings += earnings
        
        offer_data.append({
            'offer': offer,
            'clicks': clicks,
            'conversions': conversion_count,
            'epc': epc,
            'payout': offer.payout,
            'earnings': earnings
        })
    
    # Sort by clicks (descending)
    offer_data.sort(key=lambda x: x['clicks'], reverse=True)
    
    # Pagination
    paginator = Paginator(offer_data, 15)  # Show 15 offers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate overall stats
    overall_epc = total_earnings / total_clicks if total_clicks > 0 else Decimal('0.00')
    
    # Prepare current filters for template
    current_filters = {
        'start_date': start_date,
        'end_date': end_date
    }
    
    context = {
        'offer_data': page_obj,
        'current_filters': current_filters,
        'total_offers': len(offer_data),
        'total_clicks': total_clicks,
        'total_conversions': total_conversions,
        'total_earnings': total_earnings,
        'overall_epc': overall_epc
    }
    
    return render(request, 'dashboard/offer_report.html', context)

@login_required
def conversion_reports(request):
    """Display conversion tracking reports with filtering and pagination"""
    from datetime import datetime, timedelta
    from django.db.models import Count, Sum, Q
    from decimal import Decimal
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    offer_id = request.GET.get('offer_id')
    subid = request.GET.get('subid')
    
    # Set default date range (last 7 days)
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=6)
    
    # Get conversion data with related click tracking info
    conversion_data = Conversion.objects.filter(
        click_tracking__user=request.user,
        conversion_date__date__range=[start_date, end_date]
    ).select_related('click_tracking', 'click_tracking__offer')
    
    # Apply filters
    if offer_id:
        conversion_data = conversion_data.filter(click_tracking__offer_id=offer_id)
    
    if subid:
        conversion_data = conversion_data.filter(
            Q(click_tracking__subid1=subid) | 
            Q(click_tracking__subid2=subid) | 
            Q(click_tracking__subid3=subid)
        )
    
    # Get unique offers for filter dropdown
    offers = Offer.objects.filter(
        userofferrequest__user=request.user,
        userofferrequest__status='approved',
        is_active=True
    ).distinct()
    
    # Get unique subids for filter dropdown
    subids = ClickTracking.objects.filter(
        user=request.user,
        click_date__date__range=[start_date, end_date]
    ).values_list('subid1', flat=True).distinct().exclude(subid1__isnull=True).exclude(subid1='')
    
    subids = list(subids) + list(ClickTracking.objects.filter(
        user=request.user,
        click_date__date__range=[start_date, end_date]
    ).values_list('subid2', flat=True).distinct().exclude(subid2__isnull=True).exclude(subid2=''))
    
    subids = list(subids) + list(ClickTracking.objects.filter(
        user=request.user,
        click_date__date__range=[start_date, end_date]
    ).values_list('subid3', flat=True).distinct().exclude(subid3__isnull=True).exclude(subid3=''))
    
    subids = list(set(subids))  # Remove duplicates
    
    # Pagination
    paginator = Paginator(conversion_data, 20)  # Show 20 conversions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals
    total_conversions = conversion_data.count()
    
    # Calculate total earnings - handle case where no conversions exist
    if total_conversions > 0:
        # First try to sum the payout field directly
        total_earnings = conversion_data.aggregate(
            total_earnings=Sum('payout')
        )['total_earnings'] or Decimal('0.00')
        
            # If payout sum is 0, calculate based on offer payouts
        if total_earnings == Decimal('0.00'):
            # Debug: Print conversion data to see what's happening
            print(f"Debug: Found {total_conversions} conversions but payout sum is 0")
            for conv in conversion_data[:3]:  # Print first 3 conversions
                print(f"Conversion ID: {conv.id}, Payout: {conv.payout}, Offer Payout: {conv.click_tracking.offer.payout}")
            
            # Calculate earnings based on offer payouts
            total_earnings = sum(
                conversion.click_tracking.offer.payout 
                for conversion in conversion_data
                if conversion.click_tracking.offer.payout
            )
    else:
        total_earnings = Decimal('0.00')
    
    # Prepare current filters for template
    current_filters = {
        'start_date': start_date,
        'end_date': end_date,
        'offer_id': offer_id,
        'subid': subid
    }
    
    context = {
        'conversion_data': page_obj,
        'current_filters': current_filters,
        'offers': offers,
        'subids': subids,
        'total_conversions': total_conversions,
        'total_earnings': total_earnings
    }
    
    return render(request, 'dashboard/conversion_report.html', context)

@login_required
def subid_reports(request):
    """Display subid conversion tracking reports with filtering and pagination"""
    from datetime import datetime, timedelta
    from django.db.models import Count, Sum, Q, Avg
    from decimal import Decimal
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    subid = request.GET.get('subid')
    
    # Set default date range (last 7 days)
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=6)
    
    # Get conversion data with subids only
    conversion_data = Conversion.objects.filter(
        click_tracking__user=request.user,
        conversion_date__date__range=[start_date, end_date]
    ).select_related('click_tracking', 'click_tracking__offer').filter(
        Q(click_tracking__subid1__isnull=False) & ~Q(click_tracking__subid1='') |
        Q(click_tracking__subid2__isnull=False) & ~Q(click_tracking__subid2='') |
        Q(click_tracking__subid3__isnull=False) & ~Q(click_tracking__subid3='')
    )
    
    # Apply subid filter if specified
    if subid:
        conversion_data = conversion_data.filter(
            Q(click_tracking__subid1=subid) | 
            Q(click_tracking__subid2=subid) | 
            Q(click_tracking__subid3=subid)
        )
    
    # Get unique subids for filter dropdown
    subids = ClickTracking.objects.filter(
        user=request.user,
        click_date__date__range=[start_date, end_date]
    ).values_list('subid1', flat=True).distinct().exclude(subid1__isnull=True).exclude(subid1='')
    
    subids = list(subids) + list(ClickTracking.objects.filter(
        user=request.user,
        click_date__date__range=[start_date, end_date]
    ).values_list('subid2', flat=True).distinct().exclude(subid2__isnull=True).exclude(subid2=''))
    
    subids = list(subids) + list(ClickTracking.objects.filter(
        user=request.user,
        click_date__date__range=[start_date, end_date]
    ).values_list('subid3', flat=True).distinct().exclude(subid3__isnull=True).exclude(subid3=''))
    
    subids = list(set(subids))  # Remove duplicates
    
    # Pagination
    paginator = Paginator(conversion_data, 20)  # Show 20 conversions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals
    total_conversions = conversion_data.count()
    
    # Calculate total earnings - handle case where no conversions exist
    if total_conversions > 0:
        # Force evaluation of queryset to ensure data is loaded
        conversion_list = list(conversion_data)
        
        # First try to sum the payout field directly
        total_earnings = conversion_data.aggregate(
            total_earnings=Sum('payout')
        )['total_earnings'] or Decimal('0.00')
        
        # If payout sum is 0, calculate based on offer payouts
        if total_earnings == Decimal('0.00'):
            # Calculate earnings based on offer payouts using the list
            total_earnings = sum(
                float(conversion.click_tracking.offer.payout) 
                for conversion in conversion_list
                if conversion.click_tracking.offer.payout
            )
            # Convert to Decimal to ensure proper type
            total_earnings = Decimal(str(total_earnings))
    else:
        total_earnings = Decimal('0.00')
    
    # Calculate EPC (Earnings Per Click)
    total_clicks = ClickTracking.objects.filter(
        user=request.user,
        click_date__date__range=[start_date, end_date]
    ).filter(
        Q(subid1__isnull=False) & ~Q(subid1='') |
        Q(subid2__isnull=False) & ~Q(subid2='') |
        Q(subid3__isnull=False) & ~Q(subid3='')
    ).count()
    
    if subid:
        total_clicks = ClickTracking.objects.filter(
            user=request.user,
            click_date__date__range=[start_date, end_date]
        ).filter(
            Q(subid1=subid) | Q(subid2=subid) | Q(subid3=subid)
        ).count()
    
    epc = total_earnings / total_clicks if total_clicks > 0 else Decimal('0.00')
    
    # Prepare current filters for template
    current_filters = {
        'start_date': start_date,
        'end_date': end_date,
        'subid': subid
    }
    
    context = {
        'conversion_data': page_obj,
        'current_filters': current_filters,
        'subids': subids,
        'total_conversions': total_conversions,
        'total_earnings': total_earnings,
        'total_clicks': total_clicks,
        'epc': epc
    }
    
    return render(request, 'dashboard/subid_report.html', context)

@login_required
def payment_methods(request):
    """Handle payment method submission and display"""
    from .models import PaymentMethod
    
    # Get user's payment methods
    approved_payment = PaymentMethod.objects.filter(user=request.user, status='approved').first()
    pending_payment = PaymentMethod.objects.filter(user=request.user, status='pending').first()
    rejected_payment = PaymentMethod.objects.filter(user=request.user, status='rejected').first()
    
    # Determine if user can add a new payment method
    can_add_payment = not (approved_payment or pending_payment)
    
    if request.method == 'POST':
        binance_email = request.POST.get('binance_email')
        id_front = request.FILES.get('id_front')
        id_back = request.FILES.get('id_back')
        
        if binance_email and id_front and id_back:
            # Create new payment method
            payment_method = PaymentMethod.objects.create(
                user=request.user,
                binance_email=binance_email,
                id_front=id_front,
                id_back=id_back,
                status='pending'
            )
            messages.success(request, 'Payment method submitted successfully! It will be reviewed by our admin team.')
            return redirect('payment_methods')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'approved_payment': approved_payment,
        'pending_payment': pending_payment,
        'rejected_payment': rejected_payment,
        'can_add_payment': can_add_payment,
    }
    
    return render(request, 'dashboard/payment.html', context)

@login_required
def invoice_list(request):
    """Display user's invoices"""
    from .models import Invoice
    
    # Get user's invoices
    invoices = Invoice.objects.filter(user=request.user).order_by('-created_at')
    
    # Get summary statistics
    total_invoices = invoices.count()
    total_pending = invoices.filter(status='pending').count()
    total_paid = invoices.filter(status='paid').count()
    total_rejected = invoices.filter(status='rejected').count()
    total_amount = sum(invoice.amount for invoice in invoices.filter(status='paid'))
    
    context = {
        'invoices': invoices,
        'total_invoices': total_invoices,
        'total_pending': total_pending,
        'total_paid': total_paid,
        'total_rejected': total_rejected,
        'total_amount': total_amount,
    }
    
    return render(request, 'dashboard/invoice.html', context)
