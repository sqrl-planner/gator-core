"""Monkey patching for mongoengine."""
import types
from typing import Generic, Type, TypeVar

from mongoengine import Document, QuerySet

U = TypeVar('U', bound=Document)
# Register a no-op __class_getitem__ method on QuerySet to make it compatible with generic types
QuerySet.__class_getitem__ = types.MethodType(lambda self, x: self, QuerySet)


class QuerySetManager(Generic[U]):
    """A manager that returns a QuerySet of the given type."""

    def __get__(self, _: object, cls: Type[U]) -> QuerySet[U]:
        """Return a QuerySet of the given type."""
        return QuerySet(cls, cls._get_collection())
