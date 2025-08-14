from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib import messages
from .models import ReferralLink
from django.http import HttpResponseForbidden
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class ReferralTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to handle referral tracking across all pages.
    This ensures referral links work even if users navigate to different pages.
    """
    
    def process_request(self, request):
        """
        Process referral tracking on each request.
        Check for referral parameters in URL and set cookies if found.
        """
        # Check if this is a referral link visit (either /ref/CODE/ or ?ref=CODE)
        referral_code = None
        
        # Check for /ref/CODE/ pattern in URL
        if request.path.startswith('/ref/') and len(request.path.split('/')) >= 3:
            referral_code = request.path.split('/')[2]
        
        # Check for ?ref=CODE parameter
        if not referral_code:
            referral_code = request.GET.get('ref')
        
        if referral_code:
            try:
                # Validate the referral code
                referral_link = ReferralLink.objects.get(
                    referral_code=referral_code,
                    is_active=True
                )
                
                # Store in session for immediate use
                request.session['referral_code'] = referral_code
                request.session['referrer_id'] = referral_link.user.id
                
                # Set cookies for persistent tracking (30 days)
                request.referral_code = referral_code
                request.referrer_id = referral_link.user.id
                
                # Add success message if not already present
                if not any('referred by' in str(msg) for msg in messages.get_messages(request)):
                    messages.success(request, f"You've been referred by {referral_link.user.full_name}!")
                
            except ReferralLink.DoesNotExist:
                # Invalid referral code, continue normally
                pass
        
        return None  # Continue with the request
    
    def process_response(self, request, response):
        """
        Process response to ensure referral cookies are set if needed.
        """
        # If we have referral data from the request, set cookies
        if hasattr(request, 'referral_code') and hasattr(request, 'referrer_id'):
            response.set_cookie(
                'referral_code', 
                request.referral_code, 
                max_age=30*24*60*60,  # 30 days
                httponly=True,
                samesite='Lax'
            )
            response.set_cookie(
                'referrer_id', 
                str(request.referrer_id), 
                max_age=30*24*60*60,  # 30 days
                httponly=True,
                samesite='Lax'
            )
        
        return response 


class TrackingDomainAccessMiddleware(MiddlewareMixin):
    """
    Middleware to control access to tracking domains
    
    This middleware prevents users from accessing the main homepage
    when they visit tracking domains, and ensures proper access control.
    """
    
    def process_request(self, request):
        """Process request to check domain access restrictions"""
        # Get tracking domains from settings
        tracking_domains = getattr(settings, 'TRACKING_DOMAINS', [])
        default_tracking_domain = getattr(settings, 'DEFAULT_TRACKING_DOMAIN', '')
        
        # Get the current host
        current_host = request.get_host()
        
        # Check if current host is a tracking domain
        is_tracking_domain = self._is_tracking_domain(current_host, tracking_domains, default_tracking_domain)
        
        if is_tracking_domain:
            # User is on a tracking domain
            response = self._handle_tracking_domain_access(request, current_host)
            if response:
                return response
        
        # Continue with normal request processing
        return None
    
    def _is_tracking_domain(self, host, tracking_domains, default_tracking_domain):
        """Check if the given host is a tracking domain"""
        # Remove port if present
        host = host.split(':')[0]
        
        # Check against tracking domains
        for domain in tracking_domains:
            # Extract domain from URL
            if domain.startswith('http'):
                domain_host = domain.split('://')[1].split('/')[0]
            else:
                domain_host = domain
            
            # Remove port if present in domain
            domain_host = domain_host.split(':')[0]
            
            if host == domain_host:
                return True
        
        # Check against default tracking domain
        if default_tracking_domain:
            default_host = default_tracking_domain.split('://')[1].split('/')[0]
            default_host = default_host.split(':')[0]
            if host == default_host:
                return True
        
        return False
    
    def _handle_tracking_domain_access(self, request, host):
        """
        Handle access control for tracking domains
        
        Returns:
            - HttpResponse if access should be denied/redirected
            - None if access should continue normally
        """
        current_path = request.path
        
        # Define allowed paths for tracking domains
        allowed_tracking_paths = [
            '/offers/postback/',  # Postback endpoint
            '/offer/',             # Offer tracking
            '/ref/',              # Referral tracking
            '/static/',           # Static files
            '/media/',            # Media files
            '/admin/',            # Admin access (if needed)
            '/api/',              # API endpoints
        ]
        
        # Check if current path is allowed on tracking domains
        is_allowed_path = any(current_path.startswith(allowed_path) for allowed_path in allowed_tracking_paths)
        
        if not is_allowed_path:
            # User is trying to access restricted content on tracking domain
            logger.warning(f"Access denied to {current_path} on tracking domain {host}")
            
            # Return HTTP 404 Not Found instead of redirecting
            from django.http import Http404
            raise Http404(f"Page not found on tracking domain {host}")
        
        # Access allowed, continue normally
        return None 