from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect

from collab.models import ExcalidrawRoom
from collab.utils import get_or_create_room
from draw.utils import validate_room_name


@login_required
def my_tables(request):
    tables = ExcalidrawRoom.objects.filter(room_created_by=request.user).all()
    year = datetime.now().year
    return render(request, 'my_whiteboards.html', {'tables': tables, 'year': year})

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.add_message(request, 20, f'Pomyślnie zalogowano!')
            return redirect('my')  # Zmień na właściwy URL po zalogowaniu
        else:
            messages.add_message(request, 30, 'Nieprawidłowa nazwa lub hasło', 'danger')
            return render(request, 'login.html')

    return render(request, 'login.html')

@login_required
def new_table(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        if not room_name:
            messages.error(request, _("Nie podano nazwy tablicy."))
            return redirect('my')

        try:
            # Próba walidacji; jeśli nazwa jest niepoprawna, zostanie rzucony ValidationError
            validate_room_name(room_name)
        except ValidationError:
            messages.add_message(request, 30, _("Nieprawidłowa nazwa tablicy!"), 'danger')
            return redirect('my')

        # Próba utworzenia pokoju; jeśli już istnieje, get_or_create zwróci created=False
        __, created = ExcalidrawRoom.objects.get_or_create(
            room_name=room_name,
            room_created_by=request.user
        )
        if not created:
            messages.add_message(request, 30, _("Nazwa tablicy została już użyta!") % {'room_name': room_name})
        else:
            messages.success(request, _('Pomyślnie utworzono tablicę!'))
        return redirect('my')
    # Jeśli metoda nie jest POST – można przekierować lub wyświetlić formularz
    return redirect('my')
