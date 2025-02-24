from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.views import View

from collab.models import ExcalidrawRoom, BoardGroups
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

        if request.POST.get('_method') == 'PUT':
            return self.put(request)

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

    def put(self, request):
        room_name = request.POST.get('room_name')
        new_room_name = request.POST.get('new_room_name')

        if not room_name or not new_room_name:
            messages.error(request, _("Nie podano nazwy tablicy."))
            return redirect('my')

        try:
            room = ExcalidrawRoom.objects.get(room_name=room_name, room_created_by=request.user)
        except ExcalidrawRoom.DoesNotExist:
            messages.add_message(request, 35, _("Nie znaleziono tablicy o podanej nazwie."), 'danger')
            return redirect('my')

        try:
            validate_room_name(new_room_name)
        except ValidationError:
            messages.add_message(request, 30, _("Nieprawidłowa nazwa tablicy!"), 'danger')
            return redirect('my')

        room.user_room_name = new_room_name
        room.save()
        messages.success(request, _("Pomyślnie zmieniono nazwę tablicy!"))

        return redirect('my')



def shared_board(request):
    accessible_boards = ExcalidrawRoom.objects.filter(Q(boards__users=request.user)).distinct().prefetch_related('boards')
    return render(request, 'shered_whiteboards.html', {'tables': accessible_boards})


@method_decorator(login_required, name='dispatch')
class MyBoardGroup(View):
    template_name = 'boards_group.html'

    def get(self, request):
        groups = BoardGroups.objects.filter(owner=request.user).annotate(board_count=Count('boards')).all()
        return render(request, self.template_name, {'groups': groups})

    def post(self, request):

        if request.POST.get('_method') == 'DELETE':
            return self.delete(request)

        class_name = request.POST.get('class_name')
        if not class_name:
            messages.error(request, _("Nie podano nazwy grupy."))
            return redirect('my_board_groups')

        class_year = request.POST.get('class_year')
        if not class_year:
            messages.error(request, _("Nie podano roku klasy."))
            return redirect('my_board_groups')

        category = request.POST.get('category')
        if not category:
            messages.error(request, _("Nie podano kategorii."))
            return redirect('my_board_groups')

        # Create the group; join code will be generated automatically
        BoardGroups.objects.create(
            class_name=class_name,
            class_year=class_year,
            category=category,
            owner=request.user
        )
        messages.success(request, _("Pomyślnie utworzono grupę!"))
        return redirect('my_board_groups')

    def delete(self, request):
        group_id = request.POST.get('group_id')
        if not group_id:
            messages.error(request, _("Nie podano ID grupy."))
            return redirect('my_board_groups')

        try:
            group = BoardGroups.objects.get(group_id=group_id, owner=request.user)
        except BoardGroups.DoesNotExist:
            messages.add_message(request, 35, _("Nie znaleziono grupy o podanym ID."), 'danger')
            return redirect('my_board_groups')

        group.delete()
        messages.success(request, _("Pomyślnie usunięto grupę!"))
        return redirect('my_board_groups')


class SharedBoardGroup(View):
    template_name = 'shared_boards_group.html'

    def get(self, request):
        groups = BoardGroups.objects.filter(users=request.user).all()
        return render(request, self.template_name, {'groups': groups})

    def post(self, request):
        group_id = request.POST.get('group_id')
        if not group_id:
            messages.error(request, _("Nie podano ID grupy."))
            return redirect('shared_board_groups')

        try:
            group = BoardGroups.objects.get(id=group_id, users=request.user)
        except BoardGroups.DoesNotExist:
            messages.add_message(request, 35, _("Nie znaleziono grupy o podanym ID."), 'danger')
            return redirect('shared_board_groups')

        group.users.add(request.user)
        messages.success(request, _("Pomyślnie dołączono do grupy!"))
        return redirect('shared_board_groups')

    def delete(self, request):
        group_id = request.POST.get('group_id')
        if not group_id:
            messages.error(request, _("Nie podano ID grupy."))
            return redirect('shared_board_groups')

        try:
            group = BoardGroups.objects.get(id=group_id, users=request.user)
        except BoardGroups.DoesNotExist:
            messages.add_message(request, 35, _("Nie znaleziono grupy o podanym ID."), 'danger')
            return redirect('shared_board_groups')

        group.users.remove(request.user)
        messages.success(request, _("Pomyślnie opuszczono grupę!"))
        return redirect('shared_board_groups')
