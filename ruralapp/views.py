from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.urls import reverse
import json
from django.db.models import Max, Q
from collections import defaultdict, OrderedDict, Counter
from .models import Salad, OtherDish, WeeklyMenu, Order, SideDish, AppState, Organization, Membership
from django.contrib.auth.models import User
from django.db import transaction
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from datetime import datetime, time, timedelta
import logging
from django.utils.timezone import localtime, now as timezone_now



@login_required
def mis_ordenes(request):
    start_date, end_date = calculate_time_range()
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'Clients/misordenes.html', {'orders': orders, 'start_date': start_date, 'end_date': end_date})


logger = logging.getLogger(__name__)


def get_current_week():
    """Obtiene la semana actual desde AppState sin modificarla."""
    app_state, _ = AppState.objects.get_or_create(id=1)
    return app_state.current_weeks


def advance_week():
    """Avanza la semana actual en el ciclo de 4 semanas si es lunes."""
    app_state, _ = AppState.objects.get_or_create(id=1)
    current_time = timezone.localtime(timezone.now())

    # Verificar si hoy es lunes
    if current_time.weekday() == 0:  # Lunes = 0
        # Verificar si ya se avanzó esta semana
        if app_state.last_week_advance:
            last_advance = timezone.localtime(app_state.last_week_advance)
            if last_advance.date() == current_time.date():  # Ya se avanzó hoy
                return app_state.current_week

        # Avanzar a la siguiente semana
        app_state.current_week = (app_state.current_week % 4) + 1
        app_state.last_week_advance = current_time
        app_state.save()

    return app_state.current_week


# Función auxiliar para calcular el rango de tiempo válido
def calculate_time_range():
    now = timezone.localtime(timezone.now())
    current_hour = now.hour
    current_minute = now.minute
    today_weekday = now.weekday()

    if current_hour > 13 or (current_hour == 13 and current_minute >= 10):
        start_date = now.replace(hour=13, minute=10, second=0, microsecond=0)
    else:
        if today_weekday == 0:  # Lunes antes de las 13:10
            last_friday = now - timedelta(days=3)
            start_date = last_friday.replace(hour=13, minute=10, second=0, microsecond=0)
        elif today_weekday in [5, 6]:  # Sábado o domingo
            last_friday = now - timedelta(days=(today_weekday - 4))
            start_date = last_friday.replace(hour=13, minute=10, second=0, microsecond=0)
        else:
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=13, minute=10, second=0, microsecond=0)

    end_date = start_date + timedelta(days=1)
    return start_date, end_date

# Función auxiliar para determinar el menú diario
def get_menu_day_and_week():
    now = timezone.localtime(timezone.now())
    current_hour = now.hour
    current_minute = now.minute
    today_weekday = now.weekday()

    menu_days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    current_week = advance_week()
    displayed_week = current_week

    if today_weekday in (0, 1, 2, 3, 4):  # Lunes a Viernes
        if current_hour > 13 or (current_hour == 13 and current_minute >= 10):
            if today_weekday == 4:  # Viernes después de las 13:10
                menu_day_name = "Lunes"
                displayed_week = (current_week % 4) + 1
            else:
                menu_day_name = menu_days[today_weekday + 1]
        else:
            menu_day_name = menu_days[today_weekday]
    else:  # Fin de semana
        menu_day_name = "Lunes"
        displayed_week = (current_week % 4) + 1

    return menu_day_name, displayed_week




@login_required
def ruralapp(request):
    start_date, _ = calculate_time_range()

    recent_orders = Order.objects.filter(order_date__gte=start_date).order_by('-order_date')
    total_orders = recent_orders.count()

    # Validar si el usuario ya realizó un pedido en este rango
    error_message = None
    if not (request.user.is_staff and request.user.is_superuser):
        user_orders = recent_orders.filter(user=request.user)
        if user_orders.exists():
            error_message = "Ya has realizado un pedido en este periodo. No puedes realizar otro."

    # Obtener el último pedido de cada usuario en el período
    latest_orders_by_user = {}
    for order in recent_orders:
        user_id = order.user_id
        if user_id not in latest_orders_by_user:
            latest_orders_by_user[user_id] = order

    # Obtener la última fecha de pedido con repeat_for_week=True para cada usuario
    last_repeat_orders = Order.objects.filter(repeat_for_week=True).values('user_id').annotate(
        last_repeat_date=Max('order_date')
    )
    last_repeat_orders_dict = {entry['user_id']: entry['last_repeat_date'] for entry in last_repeat_orders}

    # Marcar qué pedidos deben mostrar "(Auto)"
    for order in recent_orders:
        user_id = order.user_id
        is_latest_for_user = latest_orders_by_user.get(user_id) == order
        
        # Solo el último pedido del usuario puede mostrar "(Auto)"
        if is_latest_for_user:
            last_repeat_date = last_repeat_orders_dict.get(user_id, None)
            
            # Mostrar "(Auto)" si:
            # 1. El pedido actual tiene repeat_for_week=True, O
            # 2. El pedido fue creado automáticamente (después de la última fecha de repetición)
            if order.repeat_for_week or (last_repeat_date and order.order_date > last_repeat_date):
                order.show_auto = True
            else:
                order.show_auto = False
        else:
            order.show_auto = False

    return render(request, 'Restaurant/ruralapp.html', {
        'orders': recent_orders,
        'total_orders': total_orders,
        'error_message': error_message,
    })



@login_required
def order_view(request):
    start_date, end_date = calculate_time_range()

    # Verificar si el usuario ya hizo un pedido hoy (excepto admins/superusuarios)
    if not request.user.is_superuser:
        user_orders = Order.objects.filter(
            user=request.user,
            order_date__range=(start_date, end_date)
        )
        if user_orders.exists():

            url = reverse('ruralapp') + '?pedido_existente=1'
            return HttpResponseRedirect(url)


    menu_day_name, displayed_week = get_menu_day_and_week()
    try:
        daily_menu = WeeklyMenu.objects.get(week=displayed_week, day=menu_day_name)
        main_dishes = [daily_menu.main_dish_1, daily_menu.main_dish_2]
        dessert = daily_menu.dessert
    except WeeklyMenu.DoesNotExist:
        main_dishes = []
        dessert = "No disponible"

    salads = Salad.objects.all()
    other_dishes = OtherDish.objects.values('id', 'name', 'plus_side')
    side_dishes = SideDish.objects.all()


    if request.method == 'POST':
        main_dish = request.POST.get('main_dish')
        salad_id = request.POST.get('salad')
        other_dish_id = request.POST.get('other_dish')
        side_dish_id = request.POST.get('side_dish')
        comments = request.POST.get('comments', '')
        repeat_for_week = request.POST.get('repeat_for_week') == 'on'

        # Desactivar repetición en otros pedidos
        if repeat_for_week:
            Order.objects.filter(user=request.user, repeat_for_week=True).update(repeat_for_week=False)

        # Obtener objetos relacionados
        salad = Salad.objects.filter(id=salad_id).first() if salad_id else None
        other_dish = OtherDish.objects.filter(id=other_dish_id).first() if other_dish_id else None
        side_dish = SideDish.objects.filter(id=side_dish_id).first() if side_dish_id else None

        # Crear y validar pedido
        order = Order(
            user=request.user,
            main_dish=main_dish or None,
            salad=salad,
            other_dish=other_dish,
            side_dish=side_dish,
            comments=comments,
            repeat_for_week=repeat_for_week
        )

        try:
            order.full_clean()
            order.save()
            return JsonResponse({'success': True, 'message': 'Pedido registrado correctamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'Clients/order.html', {
        'main_dishes': main_dishes,
        'salads': salads,
        'other_dishes': other_dishes,
        'side_dishes': side_dishes,
        'dessert': dessert,
        'menu_day_name': menu_day_name
    })


@login_required
def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Validar que solo se puedan editar pedidos del rango de tiempo actual
    start_date, end_date = calculate_time_range()
    if not (start_date <= order.order_date <= end_date):
        return JsonResponse({'success': False, 'error': 'No puedes editar pedidos fuera del rango de tiempo permitido.'})


    if request.method == 'POST':
        main_dish = request.POST.get('main_dish')
        salad_id = request.POST.get('salad')
        other_dish_id = request.POST.get('other_dish')
        side_dish_id = request.POST.get('side_dish')
        comments = request.POST.get('comments', '')
        repeat_for_week = 'repeat_for_week' in request.POST

        # Desactivar repetición en otros pedidos
        if repeat_for_week:
            Order.objects.filter(user=request.user, repeat_for_week=True).exclude(pk=order.pk).update(repeat_for_week=False)

        # Actualizar campos
        order.main_dish = main_dish or None
        order.salad = Salad.objects.filter(id=salad_id).first() if salad_id else None
        order.other_dish = OtherDish.objects.filter(id=other_dish_id).first() if other_dish_id else None
        order.side_dish = SideDish.objects.filter(id=side_dish_id).first() if side_dish_id else None
        order.comments = comments
        order.repeat_for_week = repeat_for_week

        try:
            order.full_clean()
            order.save()
            return JsonResponse({'success': True, 'message': 'Pedido actualizado correctamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # Datos para el formulario
    menu_day_name, displayed_week = get_menu_day_and_week()
    try:
        daily_menu = WeeklyMenu.objects.get(week=displayed_week, day=menu_day_name)
        main_dishes = [daily_menu.main_dish_1, daily_menu.main_dish_2]
        dessert = daily_menu.dessert
    except WeeklyMenu.DoesNotExist:
        main_dishes = []
        dessert = "No disponible"

    salads = Salad.objects.all()
    other_dishes = OtherDish.objects.values('id', 'name', 'plus_side')
    side_dishes = SideDish.objects.all()

    return render(request, 'Clients/edit_order.html', {
        'order': order,
        'main_dishes': main_dishes,
        'salads': salads,
        'other_dishes': other_dishes,
        'side_dishes': side_dishes,
        'dessert': dessert,
    })



@login_required
def resumen_pedidos(request):
    now = timezone.localtime(timezone.now())
    current_hour = now.hour
    today_weekday = now.weekday()

    # Determinar el rango de tiempo
    if current_hour >= 13:
        start_date = now.replace(hour=13, minute=0, second=0, microsecond=0)
    else:
        if today_weekday == 0:
            last_friday = now - timedelta(days=3)
            start_date = last_friday.replace(hour=13, minute=0, second=0, microsecond=0)
        else:
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=13, minute=0, second=0, microsecond=0)

    # Filtrar pedidos
    orders = Order.objects.filter(order_date__gte=start_date)

    # Inicializar secciones y contadores
    section_1 = defaultdict(lambda: {'count': 0, 'comments': []})
    section_2 = defaultdict(lambda: {'count': 0, 'comments': []})
    section_3 = defaultdict(lambda: {'count': 0, 'comments': []})
    unique_orders = set()

    for order in orders:
        # Sección 1: main_dish, salad y other_dish sin guarnición
        if order.main_dish or order.salad or (order.other_dish and not order.other_dish.plus_side):
            dish_name = " + ".join(
                filter(None, [
                    order.main_dish,
                    f"Ensalada {order.salad.id}" if order.salad else None,
                    order.other_dish.name if order.other_dish and not order.other_dish.plus_side else None,
                ])
            )
            section_1[dish_name]['count'] += 1
            if order.comments:
                section_1[dish_name]['comments'].append(order.comments)
            unique_orders.add(order.id)

        # Sección 2: other_dish con guarnición
        if order.other_dish and order.other_dish.plus_side:
            dish_name = order.other_dish.name
            section_2[dish_name]['count'] += 1
            if order.comments:
                section_2[dish_name]['comments'].append(order.comments)
            unique_orders.add(order.id)

        # Sección 3: guarniciones
        if order.side_dish:
            dish_name = order.side_dish.name
            section_3[dish_name]['count'] += 1
            if order.comments:
                section_3[dish_name]['comments'].append(order.comments)
            if not order.other_dish or not order.other_dish.plus_side:
                unique_orders.add(order.id)
        else:
            # Caso donde no hay guarnición
            print(f"El pedido {order.id} no tiene guarnición asignada.")

    # Ordenar las secciones
    section_1 = sorted(section_1.items(), key=lambda x: x[1]['count'], reverse=True)
    section_2 = sorted(section_2.items(), key=lambda x: x[1]['count'], reverse=True)
    section_3 = sorted(section_3.items(), key=lambda x: x[1]['count'], reverse=True)

    # Generar mensaje para WhatsApp
    menu_day, displayed_week = get_menu_day_and_week()  # Obtener el día del menú y la semana
    whatsapp_message = f"*BITFARMS*             Semana {displayed_week} / {menu_day}```\n\n"

    for section in [section_1, section_2, section_3]:
        for dish, data in section:
            whatsapp_message += f"{data['count']} {dish[:40]:<40}\n"
        whatsapp_message += "---------------\n"

    total_orders = len(unique_orders)
    
    whatsapp_message += f"```{total_orders} Pedidos en total.\n\nPor favor agregar __ menus adicionales.\nSerían ** pedidos para hoy.\n\nMuchas gracias."
    
    # Preparar datos para la plantilla
    summary_list = []
    for section in [section_1, section_2, section_3]:
        for dish, data in section:
            summary_list.append({
                'main_dish': dish,
                'count': data['count'],
                'comments': data['comments'],
            })

    # Renderizar vista
    if "generate_whatsapp" in request.GET:
        return render(request, 'Clients/whatsapp_preview.html', {
            'whatsapp_message': whatsapp_message,
        })

    return render(request, 'Clients/resumen_pedidos.html', {
        'summary_list': summary_list,
        'current_day': now.strftime('%A'),
        'total_orders': total_orders,
    })


@login_required
def restoboard(request):
    """Dashboard para Restaurant_Manager.
    Permite crear nuevas organizaciones de tipo CLIENT y listar existentes.
    """
    # Control de acceso básico (superusers también pueden entrar)
    if not (request.user.is_superuser or request.user.groups.filter(name="Restaurant_Manager").exists()):
        return HttpResponseForbidden("No autorizado")

    creation_error = None
    creation_success = False

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            creation_error = "El nombre es requerido"
        else:
            try:
                Organization.objects.create(name=name, type=Organization.OrgType.CLIENT)
                creation_success = True
            except IntegrityError:
                creation_error = "Ya existe una organización con ese nombre"

    clients = Organization.objects.filter(type=Organization.OrgType.CLIENT).order_by('-created_at')[:50]

    return render(request, 'Restaurant/restoboard.html', {
        'clients': clients,
        'creation_error': creation_error,
        'creation_success': creation_success,
    })


@login_required
def restaurant_clients(request):
    """Pantalla de gestión de clientes (organizaciones tipo CLIENT)."""
    if not (request.user.is_superuser or request.user.groups.filter(name="Restaurant_Manager").exists()):
        return HttpResponseForbidden("No autorizado")

    creation_error = None
    creation_success = False

    # Soporte creación AJAX
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'ok': False, 'error': 'El nombre es requerido'}, status=400)
        try:
            org = Organization.objects.create(name=name, type=Organization.OrgType.CLIENT)
            return JsonResponse({
                'ok': True,
                'id': org.id,
                'name': org.name,
                'created_at': org.created_at.strftime('%d/%m %H:%M'),
                'is_active': org.is_active,
            })
        except IntegrityError:
            return JsonResponse({'ok': False, 'error': 'Ya existe una organización con ese nombre'}, status=400)

    # Búsqueda
    q = request.GET.get('q', '').strip()
    base_qs = Organization.objects.filter(type=Organization.OrgType.CLIENT)
    if q:
        base_qs = base_qs.filter(name__icontains=q)
    clients = base_qs.order_by('-created_at')[:300]

    return render(request, 'Restaurant/clientes.html', {
        'clients': clients,
        'q': q,
        'creation_error': creation_error,
        'creation_success': creation_success,
    })


@login_required
def new_client(request):
    if not (request.user.is_superuser or request.user.groups.filter(name="Restaurant_Manager").exists()):
        return HttpResponseForbidden("No autorizado")
    context = {}
    if request.method == 'POST':
        org_name = request.POST.get('org_name', '').strip()
        admin_first = request.POST.get('admin_first', '').strip()
        admin_last = request.POST.get('admin_last', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        errors = []
        if not org_name:
            errors.append('Nombre de la organización es requerido')
        if not admin_first:
            errors.append('Nombre del admin requerido')
        if not admin_last:
            errors.append('Apellido del admin requerido')
        if not password:
            errors.append('Contraseña requerida')
        if errors:
            context['errors'] = errors
        else:
            with transaction.atomic():
                org = Organization.objects.create(name=org_name, type=Organization.OrgType.CLIENT, phone_number=phone, is_active=is_active)
                username = (admin_first + admin_last).lower()
                base_username = username
                i = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{i}"
                    i += 1
                user = User.objects.create_user(
                    username=username,
                    first_name=admin_first,
                    last_name=admin_last,
                    password=password,
                    is_active=is_active
                )
                # Asegurar unicidad de Client_Admin por organización
                Membership.objects.create(user=user, organization=org, role=Membership.Role.CLIENT_ADMIN)
            return redirect('restaurant_clients')
    return render(request, 'Restaurant/new_client.html', context)


@login_required
def edit_client(request, org_id: int):
    if not (request.user.is_superuser or request.user.groups.filter(name="Restaurant_Manager").exists()):
        return HttpResponseForbidden("No autorizado")
    org = get_object_or_404(Organization, pk=org_id, type=Organization.OrgType.CLIENT)
    # Obtener admin (puede no existir todavía)
    admin_membership = org.memberships.filter(role=Membership.Role.CLIENT_ADMIN).select_related('user').first()
    admin_user = admin_membership.user if admin_membership else None
    context = { 'org': org, 'admin_user': admin_user }
    if request.method == 'POST':
        if 'delete' in request.POST:
            with transaction.atomic():
                # Eliminar user admin primero (opcional conservar?)
                if admin_user:
                    admin_user.delete()
                org.delete()
            return redirect('restaurant_clients')
        org_name = request.POST.get('org_name', '').strip()
        admin_first = request.POST.get('admin_first', '').strip()
        admin_last = request.POST.get('admin_last', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        errors = []
        if not org_name:
            errors.append('Nombre de la organización es requerido')
        if not admin_first:
            errors.append('Nombre del admin requerido')
        if not admin_last:
            errors.append('Apellido del admin requerido')
        if errors:
            context['errors'] = errors
        else:
            with transaction.atomic():
                org.name = org_name
                org.phone_number = phone
                org.is_active = is_active
                org.save()
                # Crear o actualizar admin
                if not admin_user:
                    username = (admin_first + admin_last).lower()
                    base_username = username
                    i = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{i}"
                        i += 1
                    admin_user = User.objects.create_user(
                        username=username,
                        first_name=admin_first,
                        last_name=admin_last,
                        password=password or User.objects.make_random_password(),
                        is_active=is_active
                    )
                    Membership.objects.create(user=admin_user, organization=org, role=Membership.Role.CLIENT_ADMIN)
                else:
                    admin_user.first_name = admin_first
                    admin_user.last_name = admin_last
                    if password:
                        admin_user.set_password(password)
                    admin_user.is_active = is_active
                    admin_user.save()
            return redirect('restaurant_clients')
    return render(request, 'Restaurant/edit_client.html', context)

