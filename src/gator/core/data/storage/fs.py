"""Record storage implementations that rely on the filesystem."""
import re
import shutil
from pathlib import Path
from typing import Union

import msgpack

from gator.core.data.storage.base import BaseRecordStorage


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

    def bucket_exists(self, bucket_id: str) -> bool:
        """Check if a bucket exists.

        Args:
            bucket_id: The ID of the bucket to check.

        Returns:
            True if the bucket exists, False otherwise.
        """
        bucket_dir = self._get_bucket_dir(bucket_id)
        return bucket_dir.exists()

    def record_exists(self, bucket_id: str, record_id: str) -> bool:
        """Check if a record exists.

        Args:
            bucket_id: The ID of the bucket to check.
            record_id: The ID of the record to check.

        Returns:
            True if the record exists, False otherwise.
        """
        record_path = self._get_record_path(bucket_id, record_id)
        return record_path.exists()

    def get_buckets(self) -> list[str]:
        """Return a list of all bucket IDs."""
        return [bucket_dir.name for bucket_dir in self._root_dir.iterdir()]

    def _bucket_new(self, bucket_id: str) -> None:
        """Create a new bucket with the given ID.

        Note that this is an internal method and should not be called
        directly. Use `make_bucket` instead.

        Args:
            bucket_id: The ID of the bucket to create. Assumes that the bucket
            does not already exist.
        """
        bucket_dir = self._get_bucket_dir(bucket_id)
        bucket_dir.mkdir(parents=True)

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
        bucket_dir = self._get_bucket_dir(bucket_id)
        try:
            shutil.rmtree(bucket_dir)
            return True
        except OSError:
            return False

    def _bucket_clear(self, bucket_id: str) -> None:
        """Clear all records from the given bucket.

        Note that this is an internal method and should not be called
        directly. Use `clear` instead.

        Args:
            bucket_id: The ID of the bucket to clear. Assumes that the
                bucket exists.
        """
        bucket_dir = self._get_bucket_dir(bucket_id)
        for record_path in bucket_dir.iterdir():
            record_path.unlink()

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
        record_path = self._get_record_path(bucket_id, record_id)
        return self._unpack_record(record_path)

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
        bucket_dir = self._get_bucket_dir(bucket_id)

        records = {}
        for record_path in bucket_dir.iterdir():
            record_id = record_path.stem
            records[record_id] = self._unpack_record(record_path)

        return records

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
        record_path = self._get_record_path(bucket_id, record_id)
        if record_path.exists():
            if not overwrite:
                return False

        with record_path.open('wb+') as f:
            f.write(msgpack.packb(record, use_bin_type=True))  # type: ignore

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
        record_path = self._get_record_path(bucket_id, record_id)
        try:
            record_path.unlink()
            return True
        except OSError:
            return False

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
