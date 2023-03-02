"""Shared models used by the API."""
import datetime
from enum import Enum
from typing import Any
from datetime import datetime

from mongoengine import Document, EmbeddedDocument, fields

from gator.core.models.mongoengine import QuerySetManager


class SerializableEnum(Enum):
    """An enum that can be serialized to a JSON object."""

    def __str__(self):
        """Return the name of the enum."""
        return self.name


class Time(db.EmbeddedDocument):
    """A class representing an HH:MM time in 24-hour format."""

    hour: int = fields.IntField(min_value=0, max_value=23, required=True)
    minute: int = fields.IntField(min_value=0, max_value=59, required=True)


class Record(db.Document):
    """A class representing a record.

    Instance Attributes:
        id: The unique ID of the record. This should be consistent across all
            changes made to the underlying data.
        doc: The underlying data of the record.
        created_at: The time when the record was created.
        updated_at: The time when the record was last updated.
        hash: The hash of the underlying data.
        name: A short string that gives a human-readable name for the record.
            This is used for display purposes only. If not provided, the ID
            will be used.
    """

    id: str = fields.StringField(primary_key=True)
    doc: Any = fields.GenericReferenceField(required=True)
    created_at: datetime = fields.DateTimeField(required=True, default=datetime.now)
    updated_at: datetime = fields.DateTimeField(required=True, default=datetime.now)
    hash: str = fields.StringField(required=True, unique=True)
    name: str = fields.StringField(required=False)
    objects: QuerySetManager['Record'] = QuerySetManager['Record']()

    def sync(self, force: bool = False) -> str:
        """Sync the record with the database.

        Args:
            force: If True, force the sync even if the data is already up-to-date.

        Returns:
            One of 'created', 'updated', or 'skipped'.
        """
        # TODO: Better syncing logic that can handle batch updates

        # Check if the record is already in the database
        record = Record.objects(id=self.id).first()
        if record is None:
            # Create a new record
            self.save(cascade=True)
            return 'created'
        elif force or record.hash != self.hash:
            # Update the record
            record.doc = self.doc
            record.updated_at = datetime.datetime.now()
            record.hash = self.hash
            record.save(cascade=True)
            return 'updated'
        else:
            # Skip the record
            return 'skipped'
