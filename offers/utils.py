from .models import ReferralLink, Referral


def get_referral_data(request):
    """
    Get referral data from both session and cookies.
    Returns tuple of (referral_code, referrer_id) or (None, None)
    """
    # Check session first (for immediate use)
    referral_code = request.session.get('referral_code')
    referrer_id = request.session.get('referrer_id')
    
    # If not in session, check cookies (for persistent tracking)
    if not referral_code:
        referral_code = request.COOKIES.get('referral_code')
    if not referrer_id:
        referrer_id = request.COOKIES.get('referrer_id')
    
    return referral_code, referrer_id


def is_referral_active(request):
    """
    Check if user has an active referral tracking.
    """
    referral_code, referrer_id = get_referral_data(request)
    return referral_code is not None and referrer_id is not None


def get_referral_link_info(request):
    """
    Get referral link information if user has an active referral.
    """
    referral_code, referrer_id = get_referral_data(request)
    
    if referral_code and referrer_id:
        try:
            referral_link = ReferralLink.objects.get(
                referral_code=referral_code,
                user_id=referrer_id,
                is_active=True
            )
            return referral_link
        except ReferralLink.DoesNotExist:
            return None
    
    return None 