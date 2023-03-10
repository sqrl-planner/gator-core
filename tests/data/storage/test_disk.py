"""Test disk-based record storage backends."""
import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from gator.core.data.storage import FileRecordStorage
from tests.data.storage.base_test import BaseRecordStorageTestSuite


class TestFileRecordStorage(BaseRecordStorageTestSuite[FileRecordStorage]):
    """Test the file-based record storage backend."""
    _ROOT_DIR: str = './fs-storage/'

    @pytest.fixture
    def storage(self, fs: FakeFilesystem) -> FileRecordStorage:
        """Fixture to create a new storage instance."""
        fs.create_dir(self._ROOT_DIR)
        return FileRecordStorage(self._ROOT_DIR)
