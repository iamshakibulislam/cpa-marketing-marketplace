from django.urls import path
from . import views

urlpatterns = [
    path('', views.offers, name='offers'),
    path('request-access/', views.request_offer_access, name='request_offer_access'),
    path('offer/', views.track_click, name='track_click'),
    path('tracking-domains/', views.get_tracking_domains, name='get_tracking_domains'),
]