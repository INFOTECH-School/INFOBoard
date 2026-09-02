from django.contrib import admin
from django.contrib.admin.actions import delete_selected
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin, Group
from django.db.models.functions import Length
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from . import models as m

admin.site.unregister(Group)

@admin.register(m.CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    'is_creator',
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = UserAdmin.list_display + ('is_creator',)
    list_filter = UserAdmin.list_filter + ('is_creator',)


@admin.register(m.ExcalidrawLogRecord)
class ExcalidrawLogRecordAdmin(admin.ModelAdmin):
    list_display = ["__str__", "room_name", "short_user_pseudonym", "event_type", "created_at"]
    fields = [
        "room_name",
        "event_type",
        ("short_user_pseudonym", "user_pseudonym"),
        ("_compressed", "compressed_size", "uncompressed_size", "compression_degree"),
        "view_json",
        "created_at",
    ]
    readonly_fields = [
        "content", "_compressed", "compressed_size", "view_json", "created_at",
        "short_user_pseudonym", "compression_degree", "uncompressed_size"]

    @admin.display(description=_("View Record in Browser JSON Viewer"))
    def view_json(self, obj: m.ExcalidrawLogRecord):
        if obj.pk:
            json_link = reverse('api-1:get_record', kwargs={
                'room_name': obj.room_name, 'pk': obj.pk
            })
            return format_html(
                "<a href={json_link} target='_blank'>{text}</a>",
                json_link=json_link, text=_("Go to JSON"))
        return _('will be generated after saving')

    @admin.display(description=_("shortened pseudonym"))
    def short_user_pseudonym(self, obj: m.ExcalidrawLogRecord):
        return obj.user and obj.user_pseudonym[:16]


@admin.register(m.ExcalidrawRoom)
class ExcalidrawRoomAdmin(admin.ModelAdmin):
    fields = [
        "room_name",
        "user_room_name",
        "room_created_by",
        "users_that_can_draw",
        "tracking_enabled",
        "archived_at",
        ("created_at", "last_update"),
        "room_link",
        "room_json",
        "replay_link"
    ]
    readonly_fields = [
        "room_name", "room_json", "replay_link", "room_link", "last_update", "created_at",
        "compressed_size", "uncompressed_size", "compression_degree"]
    list_display = ["user_room_name", "room_link", "compressed_size_display", "created_at", "last_update", "archived_at"]
    list_filter = ["archived_at"]
    actions = ["discard_unused_rooms", "clone_rooms", "archive_rooms", "restore_rooms"]
    filter_horizontal = ['users_that_can_draw']

    def get_queryset(self, request):
        # The changelist only needs the byte size of ``_elements``, not its content.
        # Defer the (potentially large) blob and compute its length in the database
        # so the list view does not transfer every room's drawing data.
        qs = super().get_queryset(request)
        return qs.defer("_elements").annotate(_elements_len=Length("_elements"))

    @admin.display(description=_("compressed size"), ordering="_elements_len")
    def compressed_size_display(self, obj: m.ExcalidrawRoom):
        return filesizeformat(getattr(obj, "_elements_len", 0) or 0)

    @admin.display(description=_("View Room"))
    def room_link(self, obj: m.ExcalidrawRoom):
        if obj.pk:
            room_link = reverse('collab:room', kwargs={'room_name': obj.room_name})
            return format_html(
                "<a href='{room_link}' target='_blank'>{text}</a>",
                room_link=room_link,
                text=_('Go to room'))
        return _('will be generated after saving')

    @admin.display(description=_("View Room in Browser JSON Viewer"))
    def room_json(self, obj: m.ExcalidrawRoom):
        if obj.pk:
            room_link = reverse('api-1:get_room', kwargs={'room_name': obj.room_name})
            return format_html(
                "<a href='{room_link}' target='_blank'>{text}</a>",
                room_link=room_link,
                text=_('Go to room JSON'))
        return _('will be generated after saving')

    @admin.display(description=_("Replay Mode"))
    def replay_link(self, obj: m.ExcalidrawRoom):
        if obj.pk:
            room_link = reverse('collab:replay-room', kwargs={'room_name': obj.room_name})
            return format_html(
                "<a href='{room_link}' target='_blank'>{text}</a>",
                room_link=room_link, text=_("Replay this room"))
        return _('will be generated after saving')

    @admin.display(description=_("Discard all empty rooms (ONLY USE THIS ON TEST INSTANCES)"))
    def discard_unused_rooms(self, request, queryset):
        empty_rooms = queryset.filter(_elements=m.EMPTY_JSON_LIST_ZLIB_COMPRESSED)
        return delete_selected(self, request, empty_rooms)

    @admin.display(description=_("Clone room(s)"))
    def clone_rooms(self, request, queryset):
        new_rooms = []
        # Re-fetch full instances: the changelist queryset defers ``_elements``,
        # but cloning needs the drawing content.
        full_rooms = m.ExcalidrawRoom.objects.filter(
            pk__in=list(queryset.values_list("pk", flat=True)))
        for room in full_rooms:
            new_rooms.append(room.clone(None, request.user))
        self.message_user(
            request,
            _("Rooms created: %s") % ", ".join([r.room_name for r in new_rooms]),
            messages.SUCCESS)

    @admin.display(description=_("Archive selected rooms"))
    def archive_rooms(self, request, queryset):
        updated = 0
        for room in queryset:
            if not room.is_archived:
                room.archive()
                updated += 1
        self.message_user(request, _("Archived %d room(s).") % updated, messages.SUCCESS)

    @admin.display(description=_("Restore selected rooms"))
    def restore_rooms(self, request, queryset):
        updated = 0
        for room in queryset:
            if room.is_archived:
                room.restore()
                updated += 1
        self.message_user(request, _("Restored %d room(s).") % updated, messages.SUCCESS)


@admin.register(m.Pseudonym)
class ExcalidrawPseudonymAdmin(admin.ModelAdmin):
    readonly_fields = ['room', 'user', 'user_pseudonym']
    list_display = ['__str__', 'room_id', 'user_id']


@admin.register(m.ExcalidrawFile)
class ExcalidrawFileAdmin(admin.ModelAdmin):
    readonly_fields = ['image']
    list_display = ['__str__', 'belongs_to_id', 'element_file_id']

    @admin.display(description=_("image"))
    def image(self, obj: m.ExcalidrawFile):
        return format_html(
            '<img src="{src}" title="{title}" style="max-width: 100%"/>',
            src=obj.content.url,
            title=_("image %s for room %s") % (obj.element_file_id, obj.belongs_to_id))

@admin.register(m.BoardGroups)
class BoardGroupsAdmin(admin.ModelAdmin):
    readonly_fields = ['code']
    fields = [
        'class_name',
        'class_year',
        'code',
        'owner',
        'users',
        'users_that_can_draw',
        'boards',
        'archived_at',
    ]
    list_display = ['__str__', 'class_name', 'class_year', 'owner', 'archived_at']
    list_filter = ['archived_at']
    actions = ['archive_groups', 'restore_groups']
    filter_horizontal = ['users', 'users_that_can_draw', 'boards']

    @admin.display(description=_("Archive selected groups (with their boards)"))
    def archive_groups(self, request, queryset):
        updated = 0
        for group in queryset:
            if not group.is_archived:
                group.archive()
                updated += 1
        self.message_user(request, _("Archived %d group(s).") % updated, messages.SUCCESS)

    @admin.display(description=_("Restore selected groups (with their boards)"))
    def restore_groups(self, request, queryset):
        updated = 0
        for group in queryset:
            if group.is_archived:
                group.restore()
                updated += 1
        self.message_user(request, _("Restored %d group(s).") % updated, messages.SUCCESS)
