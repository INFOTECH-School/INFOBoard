from functools import wraps
from typing import Callable, Protocol, Union

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from collab.models import BoardGroups, ExcalidrawRoom
from draw.utils import async_get_object_or_404

User = Union[AbstractBaseUser, AnonymousUser]


class Room(Protocol):
    room_consumer_id: int
    room_course_id: str


class Unauthenticated(PermissionDenied):
    pass


class Unauthorized(PermissionDenied):
    pass


def create_json_response_forbidden(e: PermissionDenied):
    return JsonResponse({'detail': str(e)}, status=403)


def create_html_response_forbidden(e: PermissionDenied):
    return HttpResponseForbidden(e)


@sync_to_async
def user_is_staff(user: User):
    return user.is_superuser or user.is_staff


async def staff_access_check(request: HttpRequest, *args, **kwargs):
    if not await user_is_staff(request.user):
        raise PermissionDenied(
            _("You need to be logged in as staff or as admin."))


def require_staff_user(json=False):
    """
    Creates an async decorator for testing if the current user is a staff user.

    Decorator is to be applied to view functions. Works
    with both django views and django ninja routes.

    :param json: whether to return a ``JsonResponse``, defaults to False
    :type json: bool, optional
    """
    create_response = create_json_response_forbidden if json else create_html_response_forbidden

    def decorator(async_func: Callable[..., HttpResponse]):

        @wraps(async_func)
        async def inner(request: HttpRequest, *args, **kwargs):
            try:
                await staff_access_check(request)
                return await async_func(request, *args, **kwargs)
            except PermissionDenied as e:
                return create_response(e)

        return inner

    return decorator


@sync_to_async
def user_is_authenticated(user: User) -> bool:
    return user.is_authenticated


@sync_to_async
def user_is_authorized(user: User, room: Room, session: SessionBase) -> bool:
    """
    Tests if the user is authorized to access a room.
    """
    # the course_id is set, when the user clicks a deep link. it is always submitted in a signed
    # token from the LMS. the deep linking message launch then sets it on the session for internal
    # usage. this has the advantage that the users courses don't have to be saved to the database
    # if the session middleware is cookie based.
    allowed_course_ids = session.get('course_ids', [])

    # is_authenticated is needed because AnonymousUser don't has the attrs below.
    return user.is_authenticated and (
        (user.is_staff and user.has_perm("collab.view_excalidrawroom"))
        or user.is_superuser)


def require_login(async_func: Callable[..., HttpResponse]):
    """
    Async decorator to test is the user is logged in.
    """

    @wraps(async_func)
    async def inner(request: HttpRequest, *args, **kwargs):
        if not await user_is_authenticated(request.user):
            return HttpResponseForbidden(_("You need to be logged in."))
        return await async_func(request, *args, **kwargs)

    return inner


@require_staff_user()
async def user_is_staff_view(request):
    return HttpResponse('', status=200)


@sync_to_async
def user_in_board_group(room_obj, user):
    return BoardGroups.objects.filter(boards=room_obj, users=user).exists()

@sync_to_async
def user_in_board_group_w_drawing_permissions(room_obj, user):
    return BoardGroups.objects.filter(boards=room_obj, users=user, users_that_can_draw=user).exists()

@sync_to_async
def user_in_room_w_drawing_permissions(room_obj, user):
    return user in room_obj.users_that_can_draw.all()


@sync_to_async
def check_is_owner(room_obj, user):
    return room_obj.room_created_by == user

def group_and_login_required(view_func):
    """
    Dekorator sprawdzający, czy użytkownik jest zalogowany oraz czy jest właścicielem tablicy
    lub należy do grupy, w której znajduje się dana tablica.
    """

    @wraps(view_func)
    async def _wrapped_view(request, room_name, *args, **kwargs):
        # Sprawdź, czy użytkownik jest zalogowany
        if not await sync_to_async(lambda: request.user.is_authenticated)():
            messages.add_message(request, 30, _("Użytkownik musi być zalogowany!"), 'danger')
            return redirect('custom_login')

        # Pobierz obiekt tablicy – zakładamy, że async_get_object_or_404 jest dostępny
        room_obj = await async_get_object_or_404(ExcalidrawRoom, room_name=room_name)

        # Sprawdź, czy użytkownik jest właścicielem tablicy
        is_owner = await check_is_owner(room_obj, request.user)
        # Sprawdź, czy użytkownik należy do grupy, która zawiera tę tablicę
        is_in_group = await user_in_board_group(room_obj, request.user)

        if not (is_owner or is_in_group):
            messages.add_message(request, 30, _("Nie masz uprawnień do tej tablicy!"), 'danger')
            return redirect('my')

        return await view_func(request, room_name, *args, **kwargs)

    return _wrapped_view

def owner_required(view_func):
    @wraps(view_func)
    async def _wrapped_view(request, room_name, *args, **kwargs):
        # Sprawdzenie, czy użytkownik jest zalogowany
        is_authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
        if not is_authenticated:
            return HttpResponseForbidden("Użytkownik musi być zalogowany.")

        # Pobranie obiektu tablicy asynchronicznie
        room_obj = await async_get_object_or_404(ExcalidrawRoom, room_name=room_name)

        # Sprawdzenie, czy użytkownik jest właścicielem tablicy
        is_owner = await sync_to_async(lambda: room_obj.room_created_by == request.user)()

        # Sprawdzenie, czy użytkownik może grzebać w tablicy :)
        #can_user_draw = await user_in_board_group_w_drawing_permissions(room_obj, request.user)
        can_user_draw = await user_in_room_w_drawing_permissions(room_obj, request.user)

        if not is_owner and not request.user.is_staff and not can_user_draw:   #can_user_draw:
            messages.add_message(request, 30, _("Nie jesteś upoważniony do edycji!"), 'danger')
            return redirect('shared_board_groups')

        return await view_func(request, room_name, *args, **kwargs)
    return _wrapped_view


def is_creator_or_in_staff(view_func):
    """
    Decorator that ensures the user is either a creator (is_creator) or a staff member (is_staff).
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            messages.add_message(request, 30, _("Użytkownik musi być zalogowany."), 'danger')
            return redirect('custom_login')

        # Check if the user is in the staff or is the creator
        user = request.user
        if not (user.is_creator or user.is_staff):
            messages.add_message(request, 30, _("You don't have permission to access this board."), 'danger')
            return redirect('shared_board_groups')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def require_group_owner(view_func):
    """
    Decorator to ensure the user is the owner of the group before allowing changes.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Get the group_id from URL parameters or POST data
        group_id = kwargs.get('group_id') or request.POST.get('group_id')
        if not group_id:
            messages.add_message(request, 30, _("Nie podano ID grupy."), 'danger')
            return redirect('shared_board_groups')

        # Get the group object, making sure it exists and belongs to the current user
        group = get_object_or_404(BoardGroups, group_id=group_id)

        if group.owner != request.user:
            # If the user is not the owner, return a Forbidden response
            messages.add_message(request, 30, _("Nie masz uprawnień do zarządzania tą grupą."), 'danger')
            return redirect('shared_board_groups')

        # If the user is the owner, proceed with the view
        return view_func(request, *args, **kwargs)

    return _wrapped_view
