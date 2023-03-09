"""Shared models used by the API."""
from enum import Enum


class SerializableEnum(Enum):
    """An enum that can be serialized to a JSON object."""

    def __str__(self):
        """Return the name of the enum."""
        return self.name
