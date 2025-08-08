from django.shortcuts import render

def index(request):
    return render(request,'home/index.html')

def terms_and_conditions(request):
    return render(request, 'home/termsandconditions.html')
    
