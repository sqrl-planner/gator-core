# type: ignore
"""Base classes for a datasets."""
import fnmatch
from abc import ABC, abstractclassmethod, abstractmethod, abstractproperty
from typing import Any, Iterator, Optional, Type, Union

from gator.core.models.common import Record
from gator.core.models.timetable import Session


class Dataset(ABC):
    """A dataset that returns :class:`gator.models.Record` instances.

    All subclasses should implement the `get` method to return a list of
    records. The `slug`, `name`, and `description` properties should also be
    implemented to provide metadata about the dataset.
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
    def get(self) -> Iterator[Record]:
        """Return an iterator that lazily yields records from this dataset."""
        raise NotImplementedError()


class SessionalDataset(Dataset):
    """A dataset that is specific to a session.

    For example, a dataset of courses offered in a particular session, or a
    dataset of clubs that are active in a particular session.

    All subclasses must implement the `_get_latest_session` method to return
    the most up-to-date session for this dataset.

    Instance Attributes:
        session: The session that this dataset is specific to.
    """

    session: Session

    def __init__(self, session: Optional[Union[Session, str]] = None) -> None:
        """Initialize a SessionalDataset.

        Args:
            session: An optional session that can be supplied instead of the
                default. This can be an instance of Session or a string providing
                the session code. If None, the latest session will be used.
        """
        super().__init__()
        if isinstance(session, str):
            self.session = Session.parse(session)
        elif session is None:
            self.session = self._get_latest_session()
        else:
            self.session = session

    @abstractclassmethod
    def _get_latest_session(cls) -> Session:
        """Return the most up-to-date session for this dataset.

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
