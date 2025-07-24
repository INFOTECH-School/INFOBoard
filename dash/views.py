from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View

from collab.models import ExcalidrawRoom, BoardGroups, CustomUser
from collab.utils import get_or_create_room
from draw.utils import validate_room_name
from draw.utils.auth import require_group_owner, is_creator_or_in_staff, owner_required


def login(request):
    if request.user.is_authenticated:
        return redirect(reverse('my'))
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

@method_decorator(is_creator_or_in_staff, name='dispatch')
class MyBoardView(View):
    template_name = 'my_whiteboards.html'

    def get(self, request):
        tables = ExcalidrawRoom.objects.filter(room_created_by=request.user).all()
        # Annotate each board with the comma-separated list of group IDs that contain the board.
        for board in tables:
            board.group_ids = ",".join(str(group.group_id) for group in board.boards.all())
        groups = BoardGroups.objects.filter(owner=request.user).all()
        users = [] #definitly should be done better, but for our use it's enough :)
        users_w_permissions = []

        for group in groups:
            users+=group.users.all()

        for table in tables:
            users_w_permissions+=table.users_that_can_draw.all()

        #This can be done better  ¯\_(ツ)_/¯
        users = list(set(users))
        users_w_permissions = list(set(users_w_permissions))
        users_without_permission = [x for x in users if x not in users_w_permissions]
        #trzeba zrobić coś żeby html wiedział kto już jest zaznaczony :))))
        return render(request, self.template_name, {'tables': tables, 'groups': groups, 'users': list(set(users_without_permission)), 'users_that_can_draw': list(set(users_w_permissions))})

    def post(self, request):
        if request.POST.get('_method') == 'DELETE':
            return self.delete(request)

        if request.POST.get('_method') == 'PUT':
            return self.put(request)

        if request.POST.get('_method') == 'PATCH':
            return self.patch(request)

        room_name = request.POST.get('room_name')
        if not room_name:
            messages.error(request, _("Nie podano nazwy tablicy."))
            return redirect('my')

        # Create the board; get_or_create returns a tuple (instance, created)
        __, created = ExcalidrawRoom.objects.get_or_create(
            user_room_name=room_name,
            room_created_by=request.user
        )
        if not created:
            messages.error(request, _("Nazwa tablicy została już użyta!"))
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
            messages.error(request, _("Nie znaleziono tablicy o podanej nazwie."))
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
            messages.error(request, _("Nie znaleziono tablicy o podanej nazwie."))
            return redirect('my')

        room.user_room_name = new_room_name
        room.save()
        messages.success(request, _("Pomyślnie zmieniono nazwę tablicy!"))
        return redirect('my')

    def patch(self, request):
        try:
            checked_users = CustomUser.objects.filter(pk__in=request.POST.getlist('users'))
            board_id = request.POST.get('board_id')
            board = get_object_or_404(ExcalidrawRoom, room_name=board_id)
            board.users_that_can_draw.set(checked_users)
            board.save()
            messages.success(request, _("Pomyślnie przypisano uprawnienia do pisania!"))
            return redirect('my')
        except Exception as e:
            messages.warning(request, _(f"Wystąpił błąd przy przypisywaniu uprawnień. Błąd: {e}"))
            return redirect('my')
@login_required
def shared_board(request):
    accessible_boards = ExcalidrawRoom.objects.filter(Q(boards__users=request.user)).distinct().prefetch_related('boards').order_by('last_update')
    '''
    formatted_borads = [
        {
            'table': board,
            'can_user_draw': BoardGroups.objects.filter(boards=board, users=request.user, users_that_can_draw=request.user).exists()
        }
        for board in accessible_boards
    ]
    '''
    formatted_borads = [
        {
            'board': board,
            'can_user_draw': request.user in board.users_that_can_draw.all()
        }
        for board in accessible_boards
    ]
    return render(request, 'shered_whiteboards.html', {'tables': formatted_borads})


@method_decorator(is_creator_or_in_staff, name='dispatch')
class MyBoardGroup(View):
    template_name = 'boards_group.html'

    def get(self, request):
        # Get all groups owned by the user and annotate with the count of boards
        groups = BoardGroups.objects.filter(owner=request.user).annotate(board_count=Count('boards')).all()

        # Annotate each group with the comma-separated list of board IDs (for modal checkbox checking)
        for group in groups:
            group.board_ids = ",".join(str(board.room_name) for board in group.boards.all())

        # Get all boards created by the user
        boards = ExcalidrawRoom.objects.filter(room_created_by=request.user).all()

        return render(request, self.template_name, {'groups': groups, 'boards': boards})


    def post(self, request):

        if request.POST.get('_method') == 'DELETE':
            return self.delete(request)

        if request.POST.get('_method') == 'PUT':
            return self.put(request)

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

    @method_decorator(require_group_owner)
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

    @method_decorator(require_group_owner)
    def put(self, request):
        group_id = request.POST.get('group_id')
        new_class_name = request.POST.get('class_name')
        new_class_year = request.POST.get('class_year')
        new_category = request.POST.get('category')

        if not group_id or not new_class_name or not new_class_year or not new_category:
            messages.error(request, 35, _("Nie podano wszystkich danych."), 'danger')
            return redirect('my_board_groups')

        try:
            group = BoardGroups.objects.get(group_id=group_id, owner=request.user)
        except BoardGroups.DoesNotExist:
            messages.add_message(request, 35, _("Nie znaleziono grupy o podanym ID."), 'danger')
            return redirect('my_board_groups')

        group.class_name = new_class_name
        group.class_year = new_class_year
        group.category = new_category
        group.save()

        messages.success(request, _("Pomyślnie zmieniono dane grupy!"))
        return redirect('my_board_groups')

@method_decorator(login_required, name='dispatch')
class SharedBoardGroup(View):
    template_name = 'shared_boards_group.html'

    def get(self, request):
        groups = BoardGroups.objects.filter(users=request.user).annotate(board_count=Count('boards')).all()
        return render(request, self.template_name, {'groups': groups})

    def post(self, request):

        _method = request.POST.get('_method', '').upper()
        if _method == 'LEAVE':
            return self.leave(request)

        # Process join group form submission
        join_code = request.POST.get('join_code')
        if not join_code:
            messages.error(request, 35, _("Nie podano kodu dołączeniowego."), 'danger')
            return redirect('shared_board_groups')

        group = BoardGroups.objects.filter(code=join_code).first()
        if not group:
            messages.add_message(request, 35, _("Nie znaleziono grupy o podanym kodzie."), 'danger')
            return redirect('shared_board_groups')

        # Prevent the owner from joining their own group
        if group.owner == request.user:
            messages.add_message(request, 35, _("Nie możesz dołączyć do własnej grupy."), 'danger')
            return redirect('shared_board_groups')

        group.users.add(request.user)
        messages.success(request, _("Pomyślnie dołączono do grupy!"))
        return redirect('shared_board_groups')

    def leave(self, request):
        group_id = request.POST.get('group_id')
        if not group_id:
            messages.add_message(request, 35, _("Nie podano ID grupy."), 'danger')
            return redirect('shared_board_groups')

        group = BoardGroups.objects.filter(group_id=group_id).first()
        if not group:
            messages.add_message(request, 35, _("Nie znaleziono grupy o podanym ID."), 'danger')
            return redirect('shared_board_groups')
        # Ensure the owner cannot leave their own group
        if group.owner == request.user:
            messages.add_message(request, 35, _("Nie możesz wypisać się z własnej grupy."), 'danger')
            return redirect('shared_board_groups')

        group.users.remove(request.user)
        messages.success(request, _("Pomyślnie wypisano się z grupy!"))
        return redirect('shared_board_groups')


@is_creator_or_in_staff
def share_board(request):
    if request.method == 'POST':
        board_id = request.POST.get('board_id')
        if not board_id:
            messages.error(request, _("Nie podano identyfikatora tablicy."))
            return redirect('my')

        # Get the board; ensure the current user has permission (e.g. is the owner)
        board = get_object_or_404(ExcalidrawRoom, room_name=board_id, room_created_by=request.user)

        # Get the list of selected group IDs from checkboxes; returns an empty list if none are selected.
        selected_group_ids = request.POST.getlist('groups')

        # Retrieve the corresponding BoardGroups objects owned by the current user.
        groups = BoardGroups.objects.filter(group_id__in=selected_group_ids, owner=request.user)

        # Update the many-to-many relation: set board.boards to exactly these groups.
        board.boards.set(groups)

        messages.success(request, _("Udostępnianie tablicy zostało zaktualizowane."))
        return redirect('my')
    else:
        messages.error(request, _("Nieprawidłowa metoda żądania."))
        return redirect('my')

@is_creator_or_in_staff
@require_group_owner
def manage_group_boards(request):
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        if not group_id:
            messages.error(request, _("Nie podano ID grupy."))
            return redirect('my_board_groups')

        group = get_object_or_404(BoardGroups, group_id=group_id, owner=request.user)
        selected_board_ids = request.POST.getlist('boards')
        boards = ExcalidrawRoom.objects.filter(room_created_by=request.user, room_name__in=selected_board_ids)
        group.boards.set(boards)  # Update the many-to-many relationship
        messages.success(request, _("Zaktualizowano tablice w grupie."))
        return redirect('my_board_groups')
    else:
        messages.error(request, _("Nieprawidłowa metoda żądania."))
        return redirect('my_board_groups')

@is_creator_or_in_staff
@require_group_owner
def get_group_users(request, group_id):
    group = get_object_or_404(BoardGroups, group_id=group_id, owner=request.user)
    users = group.users.all()

    user_data = [
        {
            'id': user.id,
            'full_name': user.get_full_name(),
            'username': user.username
        }
        for user in users
    ]

    return JsonResponse({'users': user_data})

@is_creator_or_in_staff
@require_group_owner
def manage_group_users(request):
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        user_ids_to_remove = request.POST.getlist('users')  # List of user IDs to remove

        if not group_id:
            messages.error(request, _("Nie podano ID grupy."))
            return redirect('my_board_groups')

        group = get_object_or_404(BoardGroups, group_id=group_id, owner=request.user)

        # Remove selected users from the group
        users_to_remove = CustomUser.objects.filter(id__in=user_ids_to_remove)
        group.users.remove(*users_to_remove)  # Remove the users from the group

        messages.success(request, _("Użytkownicy zostali usunięci z grupy."))
        return redirect('my_board_groups')
    else:
        messages.error(request, _("Nieprawidłowa metoda żądania."))
        return redirect('my_board_groups')
