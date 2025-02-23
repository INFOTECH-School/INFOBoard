import asyncio
import logging
from typing import Literal
from urllib.parse import urlunsplit

from channels.db import database_sync_to_async
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponseBadRequest, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from draw.utils import absolute_reverse, async_get_object_or_404, make_room_name, reverse_with_query, validate_room_name
from draw.utils.auth import Unauthenticated, require_staff_user, user_is_authenticated, user_is_staff, \
    group_and_login_required, owner_required

from . import models as m
from .utils import get_or_create_room, room_access_check

logger = logging.getLogger('draw.collab')


@database_sync_to_async
def get_username(user):
    return (user.first_name or user.username) if user.pk else _("Anonymous")


def reverse_ws_url(request: HttpRequest, route: Literal["replay", "collaborate"], room_name: str):
    return urlunsplit((
        'wss' if request.is_secure() else 'ws',
        request.get_host(),
        f'/ws/collab/{room_name}/{route}',
        None,
        None))


@database_sync_to_async
def get_file_dicts(room_obj: m.ExcalidrawRoom):
    return {f.element_file_id: f.to_excalidraw_file_schema().dict() for f in room_obj.files.all()}


@database_sync_to_async
def course_exists(room_obj: m.ExcalidrawRoom):
    return hasattr(room_obj, 'course')


def custom_messages():
    return {
        'NOT_LOGGED_IN': _("You need to be logged in."),
        'FILE_TOO_LARGE': _("The file you've added is too large."),
    }

@owner_required
async def room(request: HttpRequest, room_name: str):
    room_obj, username = await asyncio.gather(
        async_get_object_or_404(m.ExcalidrawRoom, room_name=room_name),
        get_username(request.user))

    is_lti_room, is_staff, file_dicts = await asyncio.gather(
        course_exists(room_obj),
        user_is_staff(request.user),
        get_file_dicts(room_obj))

    return render(request, 'collab/room.html', {
        'excalidraw_config': {
            'FILE_URL_TEMPLATE': absolute_reverse(request, 'api-1:put_file', kwargs={
                'room_name': room_name, 'file_id': 'FILE_ID'}),
            'BROADCAST_RESOLUTION_THROTTLE_MSEC': settings.BROADCAST_RESOLUTION_THROTTLE_MSEC,
            'ELEMENT_UPDATES_BEFORE_FULL_RESYNC': 100,
            'LANGUAGE_CODE': settings.LANGUAGE_CODE,
            'LIBRARY_RETURN_URL': absolute_reverse(request, 'collab:add-library'),
            'ROOM_NAME': room_name,
            'SAVE_ROOM_MAX_WAIT_MSEC': settings.SAVE_ROOM_MAX_WAIT_MSEC,
            'SHOW_QR_CODE': not is_lti_room,
            'SOCKET_URL': reverse_ws_url(request, "collaborate", room_name),
            'USER_NAME': username,
            'USER_IS_STAFF': is_staff,
        },
        'custom_messages': custom_messages(),
        'initial_elements': room_obj.elements,
        'files': file_dicts,
        'room': room_obj,
        'show_privacy_notice': not is_lti_room and room_obj.tracking_enabled
    })


@require_staff_user()
async def replay(request: HttpRequest, room_name: str, **kwargs):
    room_obj = await async_get_object_or_404(m.ExcalidrawRoom, room_name=room_name)
    return render(request, 'collab/room.html', {
        'excalidraw_config': {
            'FILE_URL_TEMPLATE': absolute_reverse(request, 'api-1:put_file', kwargs={
                'room_name': room_name, 'file_id': '{file_id}'}),
            'IS_REPLAY_MODE': True,
            'LANGUAGE_CODE': settings.LANGUAGE_CODE,
            'LIBRARY_RETURN_URL': absolute_reverse(request, 'collab:add-library'),
            'ROOM_NAME': room_name,
            'SOCKET_URL': reverse_ws_url(request, "replay", room_name),
        },
        'custom_messages': custom_messages(),
        'initial_elements': [],
        'files': await get_file_dicts(room_obj)
    })

@group_and_login_required
async def read_only(request: HttpRequest, room_name: str, **kwargs):
    room_obj = await async_get_object_or_404(m.ExcalidrawRoom, room_name=room_name)
    return render(request, 'collab/room.html', {
        'excalidraw_config': {
            'FILE_URL_TEMPLATE': absolute_reverse(request, 'api-1:put_file', kwargs={
                'room_name': room_name, 'file_id': '{file_id}'}),
            'IS_READONLY_MODE': True,
            'LANGUAGE_CODE': settings.LANGUAGE_CODE,
            'LIBRARY_RETURN_URL': absolute_reverse(request, 'collab:add-library'),
            'ROOM_NAME': room_name,
            'SOCKET_URL': reverse_ws_url(request, "collaborate", room_name),
        },
        'custom_messages': custom_messages(),
        'initial_elements': room_obj.elements,
        'files': await get_file_dicts(room_obj),
        'room': room_obj,
    })
