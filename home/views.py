from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import datetime, time, timedelta
from offers.models import Conversion

def index(request):
    return render(request, 'home/index.html')

def terms_and_conditions(request):
    return render(request, 'home/termsandconditions.html')

@staff_member_required
def admin_dashboard(request):
    # Get dates or default to today
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = end_date = timezone.now().date()
    else:
        start_date = end_date = timezone.now().date()
    
    # Get conversions for date range
    conversions = Conversion.objects.filter(
        conversion_date__date__gte=start_date,
        conversion_date__date__lte=end_date
    )
    
    # Calculate stats
    total_leads = conversions.count()
    total_earnings = conversions.aggregate(Sum('payout'))['payout__sum'] or 0
    
    return render(request, 'home/admin_dashboard.html', {
        'total_leads': total_leads,
        'total_earnings': total_earnings,
        'start_date': start_date,
        'end_date': end_date,
    })
    
