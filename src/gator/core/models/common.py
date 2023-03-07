"""Shared models used by the API."""
from datetime import datetime
from enum import Enum
from typing import Any

from mongoengine import Document, fields

from gator.core.models.mongoengine_typing import QuerySetManager


class SerializableEnum(Enum):
    """An enum that can be serialized to a JSON object."""

    def __str__(self):
        """Return the name of the enum."""
        return self.name


class Record(Document):
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

    id: str = fields.StringField(primary_key=True)  # type: ignore
    doc: Any = fields.GenericReferenceField(required=True)  # type: ignore
    created_at: datetime = fields.DateTimeField(required=True, default=datetime.now)  # type: ignore
    updated_at: datetime = fields.DateTimeField(required=True, default=datetime.now)  # type: ignore
    hash: str = fields.StringField(required=True, unique=True)  # type: ignore
    name: str = fields.StringField(required=False)  # type: ignore
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
            record.updated_at = datetime.now()
            record.hash = self.hash
            record.save(cascade=True)
            return 'updated'
        else:
            # Skip the record
            return 'skipped'
