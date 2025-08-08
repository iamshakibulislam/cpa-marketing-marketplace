from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
]
