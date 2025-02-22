from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.views import View

from collab.models import ExcalidrawRoom
from collab.utils import get_or_create_room
from draw.utils import validate_room_name


def login(request):
    # Pobierz parametr 'next' z GET; jeśli jest pusty, użyj domyślnego URL-a.
    next_url = request.GET.get('next')
    if not next_url:
        next_url = reverse('my')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Pomyślnie zalogowano!')
            return redirect(next_url)
        else:
            messages.add_message(request, 35, 'Nieprawidłowa nazwa lub hasło', 'danger')

    return render(request, 'login.html', {'next': next_url})

def redirect_to_my(request):
    return redirect('my')

@method_decorator(login_required, name='dispatch')
class MyBoardView(View):
    template_name = 'my_whiteboards.html'

    def get(self, request):
        tables = ExcalidrawRoom.objects.filter(room_created_by=request.user).all()
        year = datetime.now().year
        return render(request, self.template_name, {'tables': tables})

    def post(self, request):

        if request.POST.get('_method') == 'DELETE':
            return self.delete(request)

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
            user_room_name=room_name,
            room_created_by=request.user
        )
        if not created:
            messages.add_message(request, 30, _("Nazwa tablicy została już użyta!") % {'room_name': room_name})
        else:
            messages.success(request, _('Pomyślnie utworzono tablicę!'))
        return redirect('my')

    def delete(self, request):
        room_name = request.POST.get('room_name')
        if not room_name:
            messages.error(request, _("Nie podano nazwy tablicy."))
            return redirect('my')

        try:
            room = ExcalidrawRoom.objects.get(room_name=room_name, room_created_by=request.user)
        except ExcalidrawRoom.DoesNotExist:
            messages.add_message(request, 35, _("Nie znaleziono tablicy o podanej nazwie."), 'danger')
            return redirect('my')

        room.delete()
        messages.success(request, _("Pomyślnie usunięto tablicę!"))
        return redirect('my')


