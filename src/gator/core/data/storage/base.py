"""Persistent record storage."""
import uuid
from abc import ABC, abstractmethod
from typing import Optional


class BaseRecordStorage(ABC):
    """The base class for all record storage implementations.

    A storage implementation is responsible for storing and retrieving
    records from a (possibly persistent) storage medium. All subclasses
    must implement the `get`, `get_all`, `put`, and `delete` methods to
    provide the necessary functionality.
    """

    def make_bucket(self, bucket_id: Optional[str] = None) -> str:
        """Create a new bucket.

        Args:
            bucket_id: The ID of the bucket to create. If None, a UUID will be
                generated.

        Returns:
            str: The ID of the bucket that was created.

        Raises:
            ValueError: If the bucket already exists.
        """
        if bucket_id is None:
            bucket_id = self._gen_bucket_id()

        if self.bucket_exists(bucket_id):
            raise ValueError(f"Bucket '{bucket_id}' already exists.")

        self._bucket_new(bucket_id)
        return bucket_id

    def delete_bucket(self, bucket_id: str) -> bool:
        """Delete a bucket.

        Args:
            bucket_id: The ID of the bucket to delete.

        Returns:
            True if the bucket was deleted, False if the bucket did not exist
            or could not be deleted.
        """
        if not self.bucket_exists(bucket_id):
            return False

        try:
            return self._bucket_del(bucket_id)
        except:  # noqa: E722
            return False

    @abstractmethod
    def get_buckets(self) -> list[str]:
        """Return a list of all bucket IDs."""
        raise NotImplementedError

    def delete_all_buckets(self) -> None:
        """Delete all buckets.

        By default, this is an O(n) operation, where n is the number of
        buckets. Subclasses may override this method to provide a more
        efficient implementation.
        """
        for bucket_id in self.get_buckets():
            self.delete_bucket(bucket_id)

    def clear(self, bucket_id: str) -> None:
        """Delete all records from a bucket.

        Args:
            bucket_id: The ID of the bucket to clear.

        Raises:
            ValueError: If the bucket does not exist.
        """
        if not self.bucket_exists(bucket_id):
            raise ValueError(f"Bucket '{bucket_id}' does not exist.")

        self._bucket_clear(bucket_id)

    def get(self, bucket_id: str, record_id: str) -> Optional[dict]:
        """Get a record with the given ID from the given bucket.

        Args:
            bucket_id: The ID of the bucket to get the record from.
            record_id: The ID of the record to get.

        Returns:
            The record, or None if the record does not exist.
        """
        if not self.record_exists(bucket_id, record_id):
            return None

        return self._record_get(bucket_id, record_id)

    def get_all(self, bucket_id: str) -> Optional[dict]:
        """Get all records from the given bucket.

        Args:
            bucket_id: The ID of the bucket to get all records from.

        Returns:
            A dictionary of all records in the bucket, mapped by
            their IDs, or None if the bucket does not exist. If the
            bucket exists but is empty, an empty dictionary will be
            returned.
        """
        if not self.bucket_exists(bucket_id):
            return None

        return self._bucket_get(bucket_id)

    def put(self, bucket_id: str, record_id: str, record: dict,
            overwrite: bool = False, auto_create: bool = False) -> bool:
        """Put a record with the given ID into the given bucket.

        Args:
            bucket_id: The ID of the bucket to put the record in.
            record_id: The ID of the record to put.
            record: The record to put.
            overwrite: Whether to overwrite the record if it already
                exists.
            auto_create: Whether to automatically create the bucket if it
                does not exist.

        Returns:
            A boolean indicating whether the record was successfully stored in
            the bucket; False if the bucket does not exist or the record already
            exists and `overwrite` is False, and True otherwise.
        """
        if not self.bucket_exists(bucket_id):
            if auto_create:
                self.make_bucket(bucket_id)
            else:
                return False

        return self._record_put(bucket_id, record_id, record, overwrite)

    def delete(self, bucket_id: str, record_id: str) -> bool:
        """Delete a record with the given ID from the given bucket.

        Args:
            bucket_id: The ID of the bucket to delete the record from.
            record_id: The ID of the record to delete.

        Returns:
            A boolean indicating whether the record was successfully deleted
            from the bucket; False if the record does not exist, and True otherwise.
        """
        if not self.record_exists(bucket_id, record_id):
            return False

        return self._record_del(bucket_id, record_id)

    @abstractmethod
    def bucket_exists(self, bucket_id: str) -> bool:
        """Check if a bucket exists.

        Args:
            bucket_id: The ID of the bucket to check.

        Returns:
            True if the bucket exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def record_exists(self, bucket_id: str, record_id: str) -> bool:
        """Check if a record exists.

        Args:
            bucket_id: The ID of the bucket to check.
            record_id: The ID of the record to check.

        Returns:
            True if the record exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def _bucket_new(self, bucket_id: str) -> None:
        """Create a new bucket with the given ID.

        Note that this is an internal method and should not be called
        directly. Use `make_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to create. Assumes that the bucket
            does not already exist.
        """
        raise NotImplementedError

    @abstractmethod
    def _bucket_del(self, bucket_id: str) -> bool:
        """Delete a bucket with the given ID.

        Note that this is an internal method and should not be called
        directly. Use `delete_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to delete.
                Assumes that the bucket exists.

        Returns:
            True if the bucket was deleted, False if the bucket could not be
            deleted.
        """
        raise NotImplementedError

    @abstractmethod
    def _bucket_clear(self, bucket_id: str) -> None:
        """Delete all records from a bucket.

        Note that this is an internal method and should not be called
        directly. Use `clear` instead.

        Args:
            bucket_id: The ID of the bucket to clear. Assumes that the
                bucket exists.
        """
        raise NotImplementedError

    @abstractmethod
    def _record_get(self, bucket_id: str, record_id: str) -> dict:
        """Get a record with the given ID from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `get` instead.

        Args:
            bucket_id: The ID of the bucket to get the record from. Assumes
                that the bucket exists.
            record_id: The ID of the record to get. Assumes that the record
                exists.

        Returns:
            The record.
        """
        raise NotImplementedError

    @abstractmethod
    def _bucket_get(self, bucket_id: str) -> dict:
        """Get all records from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `get_all` instead.

        Args:
            bucket_id: The ID of the bucket to get all records from. Assumes
                that the bucket exists.

        Returns:
            A dictionary of all records in the bucket, mapped by
            their IDs. If the bucket is empty, an empty dictionary
            will be returned.
        """
        raise NotImplementedError

    @abstractmethod
    def _record_put(self, bucket_id: str, record_id: str, record: dict,
                    overwrite: bool = False) -> bool:
        """Put a record with the given ID into the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `put` instead.

        Args:
            bucket_id: The ID of the bucket to put the record in. Assumes
                that the bucket exists.
            record_id: The ID of the record to put. May or may not already
                exist.
            record: The record to put.
            overwrite: Whether to overwrite the record if it already
                exists.

        Returns:
            A boolean indicating whether the record was successfully stored in
            the bucket; False if the record already exists, and True otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def _record_del(self, bucket_id: str, record_id: str) -> bool:
        """Delete a record with the given ID from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `delete` instead.

        Args:
            bucket_id: The ID of the bucket to delete the record from. Assumes
                that the bucket exists.
            record_id: The ID of the record to delete. Assumes that the record
                exists.

        Returns:
            True if the record was deleted, False if the record could not be
            deleted.
        """
        raise NotImplementedError

    def _gen_bucket_id(self) -> str:
        """Generate a new bucket ID as an alphanumeric string.

        Returns:
            str: A new bucket ID.
        """
        return uuid.uuid4().hex


class InMemoryRecordStorage(BaseRecordStorage):
    """An in-memory record storage implementation.

    This will store all records in memory using a dictionary. Note that
    this implementation is not persistent and will be lost when the
    application is restarted. This implementation is useful for testing
    purposes, but should not be used in production.
    """
    # Private Instance Attributes:
    #     _buckets: A dictionary of buckets, where each bucket is a
    #         dictionary of records, mapped by their IDs.
    _buckets: dict[str, dict[str, dict]]

    def __init__(self) -> None:
        """Initialize the storage."""
        self._buckets = {}

    def bucket_exists(self, bucket_id: str) -> bool:
        """Check if a bucket exists.

        Args:
            bucket_id: The ID of the bucket to check.

        Returns:
            True if the bucket exists, False otherwise.
        """
        return bucket_id in self._buckets

    def record_exists(self, bucket_id: str, record_id: str) -> bool:
        """Check if a record exists.

        Args:
            bucket_id: The ID of the bucket to check.
            record_id: The ID of the record to check.

        Returns:
            True if the record exists, False otherwise.
        """
        return record_id in self._buckets[bucket_id]

    def get_buckets(self) -> list[str]:
        """Return a list of all bucket IDs."""
        return list(self._buckets.keys())

    def _bucket_new(self, bucket_id: str) -> None:
        """Create a new bucket with the given ID.

        Note that this is an internal method and should not be called
        directly. Use `make_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to create. Assumes that the bucket
            does not already exist.
        """
        self._buckets[bucket_id] = {}

    def _bucket_del(self, bucket_id: str) -> bool:
        """Delete a bucket with the given ID.

        Note that this is an internal method and should not be called
        directly. Use `delete_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to delete. Assumes that the bucket
                exists.

        Returns:
            True if the bucket was deleted, False if the bucket could not be
            deleted.
        """
        del self._buckets[bucket_id]
        return True

    def _bucket_clear(self, bucket_id: str) -> None:
        """Clear all records from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `clear` instead.

        Args:
            bucket_id: The ID of the bucket to clear. Assumes that the
                bucket exists.
        """
        self._buckets[bucket_id] = {}

    def _record_get(self, bucket_id: str, record_id: str) -> dict:
        """Get a record with the given ID from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `get` instead.

        Args:
            bucket_id: The ID of the bucket to get the record from. Assumes
                that the bucket exists.
            record_id: The ID of the record to get. Assumes that the record
                exists.

        Returns:
            The record.
        """
        return self._buckets[bucket_id][record_id]

    def _bucket_get(self, bucket_id: str) -> dict:
        """Get all records from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `get_all` instead.

        Args:
            bucket_id: The ID of the bucket to get all records from. Assumes
                that the bucket exists.

        Returns:
            A dictionary of all records in the bucket, mapped by
            their IDs. If the bucket is empty, an empty dictionary
            will be returned.
        """
        return self._buckets[bucket_id]

    def _record_put(self, bucket_id: str, record_id: str, record: dict,
                    overwrite: bool = False) -> bool:
        """Put a record with the given ID into the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `put` instead.

        Args:
            bucket_id: The ID of the bucket to put the record in. Assumes
                that the bucket exists.
            record_id: The ID of the record to put. May or may not already
                exist.
            record: The record to put.
            overwrite: Whether to overwrite the record if it already
                exists.

        Returns:
            A boolean indicating whether the record was successfully stored in
            the bucket; False if the record already exists, and True otherwise.
        """
        if record_id in self._buckets[bucket_id] and not overwrite:
            return False
        self._buckets[bucket_id][record_id] = record
        return True

    def _record_del(self, bucket_id: str, record_id: str) -> bool:
        """Delete a record with the given ID from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `delete` instead.

        Args:
            bucket_id: The ID of the bucket to delete the record from. Assumes
                that the bucket exists.
            record_id: The ID of the record to delete. Assumes that the record
                exists.

        Returns:
            True if the record was deleted, False if the record could not be
            deleted.
        """
        del self._buckets[bucket_id][record_id]
        return True
