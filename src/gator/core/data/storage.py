"""Persistent record storage."""
import re
import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

import msgpack


class BaseRecordStorage(ABC):
    """The base class for all record storage implementations.

    A storage implementation is responsible for storing and retrieving
    records from a (possibly persistent) storage medium. All subclasses
    must implement the `get`, `get_all`, `put`, and `delete` methods to
    provide the necessary functionality.
    """

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def delete_bucket(self, bucket_id: str) -> bool:
        """Delete a bucket.

        Args:
            bucket_id: The ID of the bucket to delete.

        Returns:
            True if the bucket was deleted, False if the bucket did not exist
            or could not be deleted.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, bucket_id: str, record_id: str) -> Optional[dict]:
        """Get a record with the given ID from the given bucket.

        Args:
            bucket_id: The ID of the bucket to get the record from.
            record_id: The ID of the record to get.

        Returns:
            The record, or None if the record does not exist.
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def delete(self, bucket_id: str, record_id: str) -> bool:
        """Delete a record with the given ID from the given bucket.

        Args:
            bucket_id: The ID of the bucket to delete the record from.
            record_id: The ID of the record to delete.

        Returns:
            A boolean indicating whether the record was successfully deleted
            from the bucket; False if the bucket or record does not exist, and
            True otherwise.
        """
        raise NotImplementedError

    def _gen_bucket_id(self) -> str:
        """Generate a new bucket ID.

        Returns:
            str: A new bucket ID.
        """
        return str(uuid.uuid4())


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

        if bucket_id in self._buckets:
            raise ValueError(f"Bucket '{bucket_id}' already exists.")

        self._buckets[bucket_id] = {}
        return bucket_id

    def delete_bucket(self, bucket_id: str) -> bool:
        """Delete a bucket.

        Args:
            bucket_id: The ID of the bucket to delete.

        Returns:
            True if the bucket was deleted, False if the bucket did not exist.
        """
        if bucket_id in self._buckets:
            del self._buckets[bucket_id]
            return True

        return False

    def get(self, bucket_id: str, record_id: str) -> Optional[dict]:
        """Get a record with the given ID from the given bucket.

        Args:
            bucket_id: The ID of the bucket to get the record from.
            record_id: The ID of the record to get.

        Returns:
            The record, or None if the record does not exist.
        """
        bucket = self._buckets.get(bucket_id)
        if bucket is None:
            return None

        return bucket.get(record_id)

    def get_all(self, bucket_id: str) -> Optional[dict]:
        """Get all records from the given bucket.

        Args:
            bucket_id: The ID of the bucket to get all records from.

        Returns:
            A dictionary of all records in the bucket, mapped by their IDs, or
            None if the bucket does not exist. If the bucket exists but is
            empty, an empty dictionary will be returned.
        """
        return self._buckets.get(bucket_id)

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
        bucket = self._buckets.get(bucket_id)
        if bucket is None:
            if not auto_create:
                return False

            self.make_bucket(bucket_id)
            bucket = self._buckets[bucket_id]

        if record_id in bucket and not overwrite:
            return False

        bucket[record_id] = record
        return True

    def delete(self, bucket_id: str, record_id: str) -> bool:
        """Delete a record with the given ID from the given bucket.

        Args:
            bucket_id: The ID of the bucket to delete the record from.
            record_id: The ID of the record to delete.

        Returns:
            A boolean indicating whether the record was successfully deleted
            from the bucket; False if the bucket or record does not exist, and
            True otherwise.
        """
        bucket = self._buckets.get(bucket_id)
        if bucket is None or record_id not in bucket:
            return False

        del bucket[record_id]
        return True


class FileRecordStorage(BaseRecordStorage):
    """A file-based record storage implementation.

    Each record is stored in a separate file on disk using the MessagePack
    format. Its path is determined by the bucket ID and record ID. Each bucket
    is a subdirectory of the root directory, and each record is a file in that
    subdirectory.

    Note that this implementation is not thread-safe and should not be used
    in a multi-threaded environment.
    """
    # Private Instance Attributes:
    #     _root_dir: The root directory to store the buckets in.
    _root_dir: Path

    def __init__(self, root_dir: Union[str, Path]) -> None:
        """Initialize the storage.

        Args:
            root_dir: The root directory to store the buckets in.
        """
        self._root_dir = Path(root_dir)

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

        bucket_dir = self._get_bucket_dir(bucket_id)
        if bucket_dir.exists():
            raise ValueError(f"Bucket '{bucket_id}' already exists.")

        bucket_dir.mkdir(parents=True)
        return bucket_id

    def delete_bucket(self, bucket_id: str) -> bool:
        """Delete a bucket.

        Args:
            bucket_id: The ID of the bucket to delete.

        Returns:
            True if the bucket was deleted, False if the bucket did not exist.
        """
        bucket_dir = self._get_bucket_dir(bucket_id)
        if not bucket_dir.exists():
            return False

        try:
            shutil.rmtree(bucket_dir)
            return True
        except OSError:
            return False

    def get(self, bucket_id: str, record_id: str) -> Optional[dict]:
        """Get a record with the given ID from the given bucket.

        Args:
            bucket_id: The ID of the bucket to get the record from.
            record_id: The ID of the record to get.

        Returns:
            The record, or None if the record does not exist.
        """
        record_path = self._get_record_path(bucket_id, record_id)
        if not record_path.exists():
            return None

        return self._unpack_record(record_path)

    def get_all(self, bucket_id: str) -> Optional[dict]:
        """Get all records from the given bucket.

        Args:
            bucket_id: The ID of the bucket to get all records from.

        Returns:
            A dictionary of all records in the bucket, mapped by their IDs, or
            None if the bucket does not exist. If the bucket exists but is
            empty, an empty dictionary will be returned.
        """
        bucket_dir = self._get_bucket_dir(bucket_id)
        if not bucket_dir.exists():
            return None

        records = {}
        for record_path in bucket_dir.iterdir():
            record_id = record_path.stem
            records[record_id] = self._unpack_record(record_path)

        return records

    def _unpack_record(self, record_path: Path) -> dict:
        """Unpack the record at the given path.

        Args:
            record_path: The path to the record file.

        Returns:
            The unpacked record.
        """
        with record_path.open("rb") as f:
            return msgpack.unpackb(
                f.read(),
                use_list=False,  # Don't convert to lists
                strict_map_key=False,  # Allow map keys to be non-strings/bytes
                raw=False  # Don't return raw bytes
            )

    def put(self, bucket_id: str, record_id: str, record: dict,
            overwrite: bool = False, auto_create: bool = False) -> bool:
        """Put a record with the given ID into the given bucket.

        Args:
            bucket_id: The ID of the bucket to put the record into.
            record_id: The ID of the record to put.
            record: The record to put.
            overwrite: Whether to overwrite the record if it already exists.
            auto_create: Whether to create the bucket if it does not exist.

        Returns:
            True if the record was successfully put into the bucket, False otherwise.
        """
        # Create the bucket if it does not exist
        bucket_dir = self._get_bucket_dir(bucket_id)
        if not bucket_dir.exists():
            if not auto_create:
                return False

            self.make_bucket(bucket_id)

        # Check if the record already exists
        record_path = self._get_record_path(bucket_id, record_id)
        if record_path.exists():
            if not overwrite:
                return False

        # Write the record to disk
        with record_path.open("wb+") as f:
            b = msgpack.packb(record, use_bin_type=True)
            f.write(b)  # type: ignore

        return True

    def delete(self, bucket_id: str, record_id: str) -> bool:
        """Delete a record with the given ID from the given bucket.

        Args:
            bucket_id: The ID of the bucket to delete the record from.
            record_id: The ID of the record to delete.

        Returns:
            True if the record was successfully deleted, False otherwise.
        """
        record_path = self._get_record_path(bucket_id, record_id)
        if not record_path.exists():
            return False

        record_path.unlink()
        return True

    def _get_bucket_dir(self, bucket_id: str) -> Path:
        """Get the bucket directory for the given bucket ID.

        Args:
            bucket_id: The ID of the bucket to get the directory for.

        Returns:
            Path: The bucket directory.
        """
        return self._root_dir / self._safe_filename(bucket_id)

    def _get_record_path(self, bucket_id: str, record_id: str) -> Path:
        """Get the path to the file for the given record.

        Args:
            bucket_id: The ID of the bucket to get the record from.
            record_id: The ID of the record to get.

        Returns:
            Path: The path to the record file.
        """
        return self._get_bucket_dir(bucket_id) / self._safe_filename(record_id)

    def _safe_filename(self, fn: str) -> str:
        """Escape the given string for use in a filename.

        This will replace any non-alphanumeric characters with an underscore.
        """
        return re.sub(r"[^a-zA-Z0-9_]", "_", fn)
