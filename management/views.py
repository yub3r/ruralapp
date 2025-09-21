import pandas as pd
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import UploadFileForm
from .models import Client
from ruralapp.models import UserProfile

def is_administrator (user):
    return user.userprofile.is_admin

def is_staff (user):
    return user.is_staff

@login_required
@user_passes_test(is_administrator)
def index (req):
    return render(req, 'panel.html')

@login_required
@user_passes_test(is_administrator)
def add_client (req):
    if (req.method == 'GET'):
        return render(req, 'create_client.html')
    
    name = req.POST['name']

    new_client = Client.objects.create(name = name)
    new_group = Group.objects.get_or_create(name = name)

    return redirect('/management')

@login_required
@user_passes_test(is_administrator)
def upload_data (req):
    if (req.method == 'POST'):
        form = UploadFileForm(req.POST, req.FILES)
        if (form.is_valid()):
            file = req.FILES['file']
            df = pd.read_excel(file)

            for _, row in df.iterrows():
                user, created = User.objects.get_or_create(
                    email = row['Email'],
                    username = row['Nombre'][0].lower() + row['Apellido'].lower(),
                    first_name = row['Nombre'],
                    last_name = row['Apellido'],
                    password = row['DNI'],
                    is_staff = False,
                    is_superuser = False
                )

                group = Group.objects.get(name = row['Code'])

                user.groups.add(group)

                user.save()
                f = UploadFileForm()

                return render(req, 'upload_file.html', { 'form': f, 'upload_success': True })
    else:
        form = UploadFileForm()
    
    return render(req, 'upload_file.html', { 'form': form })

def download_excel (req):
    file_path = 'management/media/RuralApp.xlsx'

    return FileResponse(open(file_path, 'rb'), as_attachment = True, filename = 'RuralApp.xlsx')

@login_required
@user_passes_test(is_administrator)
@user_passes_test(is_staff)
def clients_management (req):
    clients = Client.objects.all();

    return render(req, 'clients_management.html', { 'clients': clients })

@login_required
@user_passes_test(is_administrator)
def create_user (req):
    if (req.method == 'GET'):
        return render(req, 'create_user.html')

    nu = User(
        email = req.POST['email'],
        username = req.POST['first_name'][0].lower() + req.POST['last_name'].lower(),
        first_name = req.POST['first_name'],
        last_name = req.POST['last_name'],
        password = req.POST['password'],
        is_staff = False,
        is_superuser = False
    )

    nu.save()
    
    group = req.user.groups.all()
    nu.groups.add(group)

    new_user = UserProfile(
        user = nu,
        menu = True,
        is_admin = False
    )

    new_user.save()


    return redirect('/management')
