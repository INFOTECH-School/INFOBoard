import mimetypes
import random
import string
import uuid
from functools import cached_property
from hashlib import sha256
from sqlite3 import IntegrityError
from typing import Optional, TypeVar
from urllib.request import urlopen

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from draw.utils import (JSONType, bytes_to_data_uri, compression_ratio, dump_content, load_content, make_room_name,
                        pick, uncompressed_json_size, user_id_for_room, validate_room_name)

from .types import ALLOWED_IMAGE_MIME_TYPES, ExcalidrawBinaryFile

TPseudonym = TypeVar('TPseudonym', bound='Pseudonym')
TRoom = TypeVar('TRoom', bound='ExcalidrawRoom')

class CustomUser(AbstractUser):
    """
    Custom User model.

    The model is needed to generate the user alias per room.
    This enables us to alias user for better privacy.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_creator = models.BooleanField(default=False, verbose_name=_("Twórca"), help_text="Użytkownik, który utworzył pokój")
    profile_image = models.ImageField(upload_to='profile_images', default='profile_images/default.png', verbose_name=_("Zdjęcie profilowe"))


class ExcalidrawLogRecordManager(models.Manager):
    def records_for_pseudonym(self, pseudonym: TPseudonym):
        return self.get_queryset().filter(user_pseudonym=pseudonym.user_pseudonym)

    def records_for_user_in_room(self, user: CustomUser, room: TRoom):
        return self.get_queryset().filter(user_pseudonym=models.Subquery(
            Pseudonym.objects.filter(user=user, room=room).values('user_pseudonym')[:1]
        ))


class ExcalidrawLogRecord(models.Model):
    """
    Contains events from the Websocket Collab endpoint.

    The content field may be compressed via zlib. The ``_compressed`` field holds the information
    if the content has been compressed. The decompression does not have to take place manually. Use
    the properties of this model therefore.
    """
    # dates are sorted after field size. this reduces table size in postgres.
    _compressed = models.BooleanField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    room_name = models.UUIDField()
    event_type = models.CharField(max_length=50)
    # if a user is deleted, keep the foreign key to be able to keep the action log
    user_pseudonym = models.CharField(
        max_length=64, validators=[MinLengthValidator(64)], null=True,
        help_text=_("this is generated from draw.utils.user_id_for_room"))
    _content = models.BinaryField(blank=True)

    objects = ExcalidrawLogRecordManager()

    @property
    def content(self):
        return load_content(self._content, self._compressed)

    @content.setter
    def content(self, val: JSONType = None):
        self._content, self._compressed = dump_content(val)

    @cached_property
    def compressed_size(self):
        return len(self._content)

    @cached_property
    def uncompressed_size(self):
        return uncompressed_json_size(self.content)

    @property
    def compression_degree(self):
        return compression_ratio(self)

    @property
    def user(self) -> Optional[CustomUser]:
        """
        :returns: user if there is one in the pseudonym table
        """
        try:
            return Pseudonym.objects.get(user_pseudonym=self.user_pseudonym).user
        except Pseudonym.DoesNotExist:
            return None

    @user.setter
    def user(self, user: CustomUser):
        self.user_pseudonym = user_id_for_room(user.pk, self.room_name) if user else None

# trust me
EMPTY_JSON_LIST_ZLIB_COMPRESSED = b'x\x9c\x8b\x8e\x05\x00\x01\x15\x00\xb9'

class ExcalidrawRoom(models.Model):
    """
    Contains the latest ``ExcalidrawElement`` s of a room.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    room_name = models.UUIDField(
        primary_key=True, default=uuid.uuid4)
    room_created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    tracking_enabled = models.BooleanField(_("track users' actions"), default=settings.ENABLE_TRACKING_BY_DEFAULT)
    _elements = models.BinaryField(blank=True, default=EMPTY_JSON_LIST_ZLIB_COMPRESSED)
    user_room_name = models.CharField(max_length=24, editable=True, null=False, blank=False, default=make_room_name(17))
    users_that_can_draw = models.ManyToManyField(CustomUser, related_name='drawing_users_in_table', blank=True)

    @property
    def elements(self):
        return load_content(self._elements, compressed=True)

    @elements.setter
    def elements(self, val: JSONType = None):
        self._elements = dump_content(val, force_compression=True)

    @cached_property
    def compressed_size(self):
        return len(self._elements)

    @cached_property
    def uncompressed_size(self):
        return uncompressed_json_size(self.elements)

    @property
    def compression_degree(self):
        return compression_ratio(self)

    def clone(self, *, room_course_id: str, room_created_by: CustomUser):
        """
        Clone a room and its associated files.

        This will insert the room as a new log record. So the replay of the
        cloned room will begin from the moment where the clone was created.
        """
        # get the files from the original room
        files = list(self.files.all())

        # clone the board
        old_name = self.room_name
        self.pk = None
        self.room_name = make_room_name(24)
        self.save()

        # clone the files
        for f in files:
            f.pk = None
            f.belongs_to = self
        ExcalidrawFile.objects.bulk_create(files)

        # make visible that this room was cloned
        record = ExcalidrawLogRecord(room_name=self.room_name, event_type="cloned")
        record.user = room_created_by
        record.content = {'clonedFrom': old_name}
        record.save()

        # insert the room as a new log record. the replay
        # will begin from the moment the room is cloned.
        record = ExcalidrawLogRecord(room_name=self.room_name, event_type="full_sync")
        record.user = room_created_by
        record.content = self.elements
        record.save()

        return self

    def __str__(self):
        return f"{self.user_room_name} -- {self.room_created_by}"


class Pseudonym(models.Model):
    """
    Table that stores which user belongs to which pseudonym.

    Delete all records in this table to restore anonymity. No
    record will be available for users who joined anonymously.
    """
    room = models.ForeignKey(ExcalidrawRoom, on_delete=models.CASCADE, verbose_name=_("room name"))
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name=_("user"))
    user_pseudonym = models.CharField(
        primary_key=True, max_length=64, validators=[MinLengthValidator(64)],
        help_text=_("this is generated from draw.utils.user_id_for_room"))

    class Meta:
        unique_together = [('room', 'user')]

    @classmethod
    def create_for_user_in_room(cls, user: CustomUser, room: ExcalidrawRoom):
        return cls(room=room, user=user, user_pseudonym=user_id_for_room(user.pk, room.room_name))

    @classmethod
    def stored_pseudonym_for_user_in_room(cls, user: CustomUser, room: ExcalidrawRoom) -> str:
        self = cls.create_for_user_in_room(user, room)
        try:
            self.save()
        except IntegrityError:
            # if the pseudonym is already stored, this error
            # can be ignored because the data will never change.
            pass
        return self.user_pseudonym


class ExcalidrawFile(models.Model):
    """
    File store

    WARNING: don't delete the content file until there is no room which uses it anymore.

    Orphaned files can be deleted from the admin view.
    """
    belongs_to = models.ForeignKey(
        ExcalidrawRoom, on_delete=models.SET_NULL, null=True,
        related_name="files", verbose_name=_("belongs to room"))
    # we don't use the hash that's submitted by excalidraw as the pk
    # because it is a sha1 hash and sha1 is broken. for filtering, this
    # should therefore only be used on the relation manager of belongs_to.
    element_file_id = models.CharField(max_length=40)
    # file content will be stored as file, not to db
    content = models.FileField(upload_to='excalidraw-uploads')
    # this will not be compressed, as the file meta data is always relatively small in size.
    meta = models.JSONField(verbose_name=_("excalidraw meta data"))

    ALLOWED_META_KEYS = {'created', 'mimeType'}

    class Meta:
        unique_together = [('belongs_to', 'element_file_id')]

    @classmethod
    def from_excalidraw_file_schema(cls, room_name: str, file_data: ExcalidrawBinaryFile):
        mime_from_data_uri, _ = mimetypes.guess_type(file_data.dataURL)
        if mime_from_data_uri not in ALLOWED_IMAGE_MIME_TYPES:
            raise ValidationError({
                "content": _("The content MIME type of %s is not allowed") % (mime_from_data_uri,)
            })
        file_data.mimeType = mime_from_data_uri # consider data from the client as being unsafe
        with urlopen(file_data.dataURL) as response:
            content_bytes = response.read()
        file_hash = sha256(content_bytes)
        file_name = file_hash.hexdigest() + (mimetypes.guess_extension(mime_from_data_uri) or "")

        self = cls(
            belongs_to_id=room_name,
            content=ContentFile(content_bytes, name=file_name),
            element_file_id=file_data.id,
            meta=pick(file_data.dict(), cls.ALLOWED_META_KEYS))
        return self

    def to_excalidraw_file_schema(self) -> ExcalidrawBinaryFile:
        return ExcalidrawBinaryFile(
            **self.meta,
            id=self.element_file_id,
            dataURL=bytes_to_data_uri(self.content.read(), self.meta['mimeType']),
            filePath=self.content.url)

    def __repr__(self) -> str:
        return f"<ExcalidrawFile {self.element_file_id} for room {self.belongs_to_id}>"


def generate_join_code(length=8):
    """Generate a random join code composed of uppercase letters and digits."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

def generate_unique_join_code(length=8):
    code = generate_join_code(length)
    while BoardGroups.objects.filter(code=code).exists():
        code = generate_join_code(length)
    return code


class BoardGroups(models.Model):
    """
    Groups of boards.

    This is used to group boards together. This is useful for
    example to group boards by course.
    """
    group_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class_name = models.CharField(max_length=50, default='default')
    class_year = models.IntegerField(default=2025)
    code = models.CharField(max_length=10, unique=True, editable=False, default="")
    category = models.CharField(max_length=50, choices=[('podstawowy', 'podstawowy'), ('średnio-zaawansowany', 'średnio-zaawansowany'), ('zaawansowany', 'zaawansowany')], default='podstawowa')
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owner_group', default=None)
    users = models.ManyToManyField(CustomUser, related_name='users_group', blank=True)
    users_that_can_draw = models.ManyToManyField(CustomUser, related_name='drawing_users_group', blank=True)
    boards = models.ManyToManyField(ExcalidrawRoom, related_name='boards', blank=True)

    def __str__(self):
        return f"{self.class_name} {self.class_year} {self.category} {self.owner}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_unique_join_code()
        super().save(*args, **kwargs)
