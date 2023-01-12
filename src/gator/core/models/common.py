"""Shared models used by the API."""
import datetime
from typing import Any

import mongoengine as db


class Time(db.EmbeddedDocument):
    """A class representing an HH:MM time in 24-hour format."""

    hour: int = db.IntField(min_value=0, max_value=23, required=True)
    minute: int = db.IntField(min_value=0, max_value=59, required=True)


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

    id: str = db.StringField(primary_key=True)
    doc: Any = db.GenericReferenceField(required=True)
    created_at: Time = db.DateTimeField(required=True, default=datetime.datetime.now)
    updated_at: Time = db.DateTimeField(required=True, default=datetime.datetime.now)
    hash: str = db.StringField(required=True, unique=True)
    name: str = db.StringField(required=False)
