from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib import messages
from .models import ReferralLink


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