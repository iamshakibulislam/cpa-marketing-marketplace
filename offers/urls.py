from django.urls import path
from . import views

urlpatterns = [
    path('',views.offers,name='offers'),
    path('request-access/', views.request_offer_access, name='request_offer_access'),
]