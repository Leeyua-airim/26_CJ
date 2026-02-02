from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def app_home(request):
    return HttpResponse("Welcome to the protected app home page!")
