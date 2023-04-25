"""Test the :mod:`gator.core.data.utils.hash` module."""
import base64
from typing import Any

import pytest

from gator.core.data.utils.hash import make_hash_sha256, make_hashable


class TestMakeHashSha256:
    """Test the :meth:`gator.core.data.utils.hash.make_hash_sha256` function."""

    @pytest.mark.parametrize('x', [1, 1.0, 'hello world', b'test', [], (), {}])
    def test_b64_encoded(self, x: Any) -> None:
        """Test that the hash is base64 encoded."""
        h = make_hash_sha256(x)
        # Decoding and re-encoding a base64 string should result in the same string
        assert h == base64.b64encode(base64.b64decode(h)).decode()

    @pytest.mark.parametrize('x', [1, 1.0, 'hello world', b'test', [], (), {}])
    def test_same_input_same_output(self, x: Any) -> None:
        """Test that the same input always results in the same output."""
        assert make_hash_sha256(x) == make_hash_sha256(x)

    def test_dict_order_agnostic(self) -> None:
        """Test that the hash is order agnostic."""
        d1 = {'a': 1, 'b': 2, 'c': 3}
        d2 = {'c': 3, 'b': 2, 'a': 1}
        assert make_hash_sha256(d1) == make_hash_sha256(d2)


class TestMakeHashable:
    """Test the :meth:`gator.core.data.utils.hash.make_hashable` function."""

    def test_list(self) -> None:
        """Test that a list is converted to a tuple."""
        assert make_hashable([1, 2, 3]) == (1, 2, 3)

    def test_dict(self) -> None:
        """Test that a dict is converted to a tuple of tuples."""
        assert make_hashable({'a': 1, 'b': 2, 'c': 3}) == (('a', 1), ('b', 2), ('c', 3))

    def test_dict_sorted(self) -> None:
        """Test that a dict is sorted by key."""
        assert make_hashable({'c': 3, 'b': 2, 'a': 1}) == (('a', 1), ('b', 2), ('c', 3))

    def test_set(self) -> None:
        """Test that a set is converted to a tuple."""
        assert make_hashable({1, 2, 3}) == (1, 2, 3)

    def test_set_sorted(self) -> None:
        """Test that a set is sorted."""
        assert make_hashable({3, 2, 1}) == (1, 2, 3)

    @pytest.mark.parametrize('x', [1, 1.0, 'hello world', b'test'])
    def test_unchanged(self, x: Any) -> None:
        """Test that an object that is already hashable is returned unchanged."""
        assert make_hashable(x) == x

    def test_recursive(self) -> None:
        """Test that a nested structure is converted recursively."""
        assert make_hashable({
            'a': [1, 2, 3],
            'b': {3, 2, 1},
            'c': {'a': 1, 'b': 2, 'c': {'zyx', 'wvu', 'tsr'}}
        }) == (
            ('a', (1, 2, 3)),
            ('b', (1, 2, 3)),
            ('c', (('a', 1), ('b', 2), ('c', ('tsr', 'wvu', 'zyx'))))
        )
