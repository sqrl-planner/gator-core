# type: ignore
"""Base classes for datasets."""
import fnmatch
from abc import ABC, abstractclassmethod, abstractmethod, abstractproperty
from typing import Any, Iterator, Optional, Type, Union

from mongoengine import Document

from gator.core.models.timetable import Session


class Dataset(ABC):
    """A dataset that converts free-form data into mongoengine documents.

    All subclasses should implement functionality for a) pulling data from a
    source (e.g. a database, a file, or an API) and returning it as a list of
    `(id, data)` records via the `get` method, and b) processing each record
    into a :class:`mongoengine.Document` object via the `process` method.
    The `slug`, `name`, and `description` properties should also be implemented
    to provide metadata about the dataset.
    """

    @abstractproperty
    def slug(self) -> str:
        """Return the slug of this dataset."""
        raise NotImplementedError()

    @abstractproperty
    def name(self) -> str:
        """Return the name of this dataset."""
        raise NotImplementedError()

    @abstractproperty
    def description(self) -> str:
        """Return the description of this dataset."""
        raise NotImplementedError()

    @abstractmethod
    def get(self) -> Iterator[tuple[str, Any]]:
        """Return an iterator that lazily yields `(id, data)` records.

        The `id` should be a unique identifier for the record, and the `data`
        can be any hashable object. A hash of the `data` object will be compared
        with a hash stored in the database for the record with the given `id`.
        """
        raise NotImplementedError()

    @abstractmethod
    def process(self, id: str, data: Any) -> Document:
        """Process the given record into a :class:`mongoengine.Document`.

        Args:
            id: The unique identifier for the record.
            data: The data for the record.
        """
        raise NotImplementedError()


class SessionalDataset(Dataset):
    """A dataset that is specific to one or more sessions.

    For example, a dataset of courses offered in a set of particular sessions,
    or a dataset of clubs that are active in a single session.

    All subclasses must implement the `_get_latest_sessions` method to return
    the most up-to-date sessions for this dataset.

    Instance Attributes:
        sessions: The sessions that this dataset is specific to.
    """

    sessions: list[Session]

    def __init__(self,
                 sessions: Optional[list[Union[str, Session]]] = None,
                 session: Optional[Union[str, Session]] = None) -> None:
        """Initialize a SessionalDataset.

        Args:
            sessions: The sessions that this dataset tracks. Each element can
                either be a session code, which will be parsed into a Session
                object, or a Session object itself. If no sessions are provided,
                the most up-to-date sessions will be used.
            session: Instead of providing a list of sessions, a single session
                can be provided. This is equivalent to providing a list with a
                single session. If both `sessions` and `session` are provided,
                `sessions` will take precedence.
        """
        super().__init__()
        # Prefer the `sessions` argument. In the case it is None, use the
        # `session` argument if it is provided, otherwise default to None.
        sessions = sessions or ([session] if session is not None else None)
        if sessions is None:
            # Use the most up-to-date sessions
            self.sessions = self._get_latest_sessions()
        else:
            # Parse the sessions
            self.sessions = [
                Session.from_code(session) if not isinstance(session, Session) else session
                for session in sessions]

    @abstractclassmethod
    def _get_latest_sessions(cls) -> list[Session]:
        """Return the most up-to-date sessions for this dataset.

        Raise a ValueError if the session could not be found.
        """
        raise NotImplementedError()


class Registry:
    """A registry tracking one or more datasets.

    Each dataset is identified by a unique slug. The registry can be used to
    retrieve datasets by their slug, or to filter datasets by a pattern.
    """

    # Private Instance Attributes:
    #     _datasets: A list of datasets to track.
    _datasets: list[Dataset]

    def __init__(self, datasets: Optional[list[Dataset]] = None) -> None:
        """Initialize a Registry.

        Args:
            datasets: A list of datasets to track.
        """
        self._datasets = datasets or []

    def register(self, dataset: Union[Type[Dataset], Dataset], **kwargs: Any) \
            -> None:
        """Register a dataset with the registry.

        Args:
            dataset: A dataset to register. This can either be a class or an
                instance of a dataset. If a class is provided, it will be
                instantiated with the provided keyword arguments.
            **kwargs: Keyword arguments to pass to the dataset initializer
                in the case that `dataset` is a class.
        """
        if isinstance(dataset, type):
            dataset = dataset(**kwargs)
        self._datasets.append(dataset)

    def filter(self, pattern: str) -> Iterator[Dataset]:
        """Filter the datasets by a pattern.

        Args:
            pattern: A Unix-style glob pattern to filter the datasets by.

        Yields:
            Datasets that match the pattern.
        """
        for dataset in self._datasets:
            if fnmatch.fnmatch(dataset.slug, pattern):
                yield dataset

    def all(self) -> Iterator[Dataset]:
        """Return an iterator that yields all datasets."""
        yield from self._datasets
