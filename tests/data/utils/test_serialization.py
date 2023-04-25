"""Test the :mod:`gator.core.data.utils.serialization` module."""
from typing import Any, Callable

import pytest

from gator.core.data.utils.serialization import nullable_convert, without_keys


class TestNullableConvert:
    """Test the :func:`gator.core.data.utils.serialization.nullable_convert` function."""

    @pytest.mark.parametrize('value, func', [
        (1, int),
        (1.0, float),
        ('hello world', str),
        (b'test', bytes),
        ([1, 2, 3], list),
        ((1, 2, 3), tuple),
        ({'a': 1, 'b': 2, 'c': 3}, dict),
        ({1, 2, 3}, set),
    ])
    def test_identity(self, value: Any, func: Callable) -> None:
        """Test that the function returns the input value."""
        assert nullable_convert(value, func) == value

    @pytest.mark.parametrize('func', [int, float, str, bytes, list, tuple, dict, set])
    def test_handle_none(self, func: Callable) -> None:
        """Test that the function handles None inputs."""
        assert nullable_convert(None, func) is None


class TestWithoutKeys:
    """Test the :func:`gator.core.data.utils.serialization.without_keys` function."""

    def test_empty(self) -> None:
        """Test that the function returns an empty dict when given an empty dict."""
        assert without_keys({}, {'a', 'b'}) == {}

    def test_no_keys(self) -> None:
        """Test that the function returns the input dict when given no keys."""
        d = {'a': 1, 'b': 2, 'c': 3}
        assert without_keys(d, set()) == d

    def test_remove_keys(self) -> None:
        """Test that the function removes the given keys."""
        d = {'a': 1, 'b': 2, 'c': 3}
        assert without_keys(d, {'a', 'c'}) == {'b': 2}

    def test_handles_invalid_keys(self) -> None:
        """Test that the function handles invalid keys."""
        d = {'a': 1, 'b': 2, 'c': 3}
        assert without_keys(d, {'x', 'y'}) == d
