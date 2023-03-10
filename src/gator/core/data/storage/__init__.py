"""All record storage backends."""
from gator.core.data.storage.base import BaseRecordStorage
from gator.core.data.storage.disk import FileRecordStorage
from gator.core.data.storage.mem import DictRecordStorage

__all__ = [
    'BaseRecordStorage',
    'FileRecordStorage',
    'DictRecordStorage',
]
