import json
import mimetypes
from functools import cached_property
from hashlib import sha256
from sqlite3 import IntegrityError
from typing import Optional, TypeVar
from urllib.request import urlopen

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from pylti1p3.contrib.django.lti1p3_tool_config.models import LtiTool

from draw.utils import (JSONType, bytes_to_data_uri, dump_content, load_content, pick,
                        user_id_for_room, validate_room_name)
from ltiapi.models import CustomUser

from .types import ALLOWED_IMAGE_MIME_TYPES, ExcalidrawBinaryFile

TPseudonym = TypeVar('TPseudonym', bound='Pseudonym')
TRoom = TypeVar('TRoom', bound='ExcalidrawRoom')


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
    room_name = models.CharField(max_length=24, validators=[validate_room_name])
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
        return len(json.dumps(self.content, ensure_ascii=False).encode('utf-8'))

    @property
    def compression_degree(self):
        comp = 100 - self.compressed_size / self.uncompressed_size * 100
        return f"{comp:.2f} %"

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
        self.user_pseudonym = user_id_for_room(user.pk, self.room_name)

# trust me
EMPTY_JSON_LIST_ZLIB_COMPRESSED = b'x\x9c\x8b\x8e\x05\x00\x01\x15\x00\xb9'

class ExcalidrawRoom(models.Model):
    """
    Contains the latest ``ExcalidrawElement`` s of a room.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    room_name = models.CharField(
        primary_key=True, max_length=24,
        validators=[validate_room_name])
    room_created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    room_consumer = models.ForeignKey(LtiTool, on_delete=models.SET_NULL, null=True)
    room_course_id = models.CharField(max_length=255, null=True, blank=True)
    _elements = models.BinaryField(blank=True, default=EMPTY_JSON_LIST_ZLIB_COMPRESSED)

    @property
    def elements(self):
        return load_content(self._elements, compressed=True)

    @elements.setter
    def elements(self, val: JSONType = None):
        self._elements = dump_content(val, force_compression=True)


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
