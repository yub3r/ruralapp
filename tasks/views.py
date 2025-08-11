from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Sum, F, Func, IntegerField
from django.db.models.functions import ExtractMonth
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .models import Task, CryptoPrice, Guardia, Sorteo, Ganador, HoraExtra
from .forms import TaskForm, GuardiaForm, SorteoForm, RepetirSorteoForm, HoraExtraForm
from datetime import date, timedelta
from django.utils.timezone import now 
from django.http import JsonResponse
import ccxt, calendar, random, re, locale, requests
import yfinance as yf
from django.contrib.sessions.backends.db import SessionStore
from django.core.cache import cache
from django.views.generic.base import RedirectView



favicon_view = RedirectView.as_view(url='/media/favicon.ico', permanent=True)


def admin_o_ususario(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    try:
        user = user.objects.get(user=user.id)
    except ObjectDoesNotExist:
        user = None
    return user is not None


def es_admin(user):
    return user.is_authenticated and user.is_superuser

def sobremi(request):
    return render(request, "about.html")



########################  LOGIN  ######################################################  LOGIN  ##############################

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {"form": UserCreationForm})
    else:
        if request.POST["password1"] == request.POST["password2"]:
            try:
                user = User.objects.create_user(
                    request.POST["username"], password=request.POST["password1"])
                user.save()
                login(request, user)
                return redirect('tasks')
            except IntegrityError:
                return render(request, 'signup.html', {"form": UserCreationForm, "error": "Username ya existe."})
        return render(request, 'signup.html', {"form": UserCreationForm, "error": "Contraseña no coincide"})


@login_required
def signout(request):
    logout(request)
    return render(request, 'logout.html')
    # return redirect('home')


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {"form": AuthenticationForm})
    else:
        identifier = request.POST['username']
        password = request.POST['password']

        # Verificamos si el input es un email y si corresponde a un usuario
        if '@' in identifier:
            try:
                user_obj = User.objects.get(email=identifier)
                username = user_obj.username
            except User.DoesNotExist:
                username = None
        else:
            username = identifier

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, 'signin.html', {
                "form": AuthenticationForm,
                "error": "Usuario o contraseña incorrecta."
            })

        login(request, user)
        messages.success(request, f"Bienvenido {user.first_name or user.username}")
        return redirect('home')

@login_required
def home(request):
    return render(request, "home.html")

########################  TAREAS  ######################################################  TAREAS  ##############################



########################  Crypto_Prices  ######################################################  Crypto_Prices  ##############################

@login_required
def home_view(request):
    """Vista principal que lee los datos ya cacheados."""
    current_price = cache.get('bitf_price')
    dolar_data = cache.get('dolar_data')
    
    return render(request, 'home.html', {
        'bitf_price': current_price,
        'dolar_data': dolar_data
    })