"""Test the :mod:`gator.core.models.timetable` module."""
import pytest

import gator.core.models.timetable as timetable


class TestSession:
    """Test the :class:`gator.core.models.timetable.Session` class."""

    # Private Class Attributes
    #   _ALL_YEARS: A list of all possible years for a session for the
    #       `__eq__` and `__ne__` tests.
    #   _ALL_SEASONS: A list of all possible seasons for a session for the
    #       `__eq__` and `__ne__` tests.
    #   _ALL_SUBSESSIONS: A list of all possible subsessions for a session for
    #       the `__eq__` and `__ne__` tests.
    _ALL_YEARS = [1996, 1997, 37]
    _ALL_SEASONS = ['regular', 'summer']
    _ALL_SUBSESSIONS = ['first', 'second', 'whole']

    @pytest.mark.parametrize('session, expected_code', [
        (timetable.Session(1996, 'regular', 'first'), '19969'),
        (timetable.Session(1997, 'regular', 'second'), '19971'),
        (timetable.Session(1996, 'regular', 'whole'), '19969-19971'),
        (timetable.Session(1997, 'summer', 'first'), '19975F'),
        (timetable.Session(1997, 'summer', 'second'), '19975S'),
        (timetable.Session(1997, 'summer', 'whole'), '19975'),
        (timetable.Session(37, 'regular', 'first'), '00379')
    ])
    def test_code(self, session: timetable.Session, expected_code: str) -> None:
        """Test the :attr:`gator.core.models.timetable.Session.code` property."""
        assert session.code == expected_code

    @pytest.mark.parametrize('session, expected_human_str', [
        (timetable.Session(1996, 'regular', 'first'), 'Fall 1996'),
        (timetable.Session(1997, 'regular', 'second'), 'Winter 1997'),
        (timetable.Session(1996, 'regular', 'whole'), 'Fall 1996 - Winter 1997'),
        (timetable.Session(1997, 'summer', 'first'), 'Summer 1997 (First Subsession)'),
        (timetable.Session(1997, 'summer', 'second'), 'Summer 1997 (Second Subsession)'),
        (timetable.Session(1997, 'summer', 'whole'), 'Summer 1997 (Whole Session)'),
        (timetable.Session(37, 'regular', 'first'), 'Fall 0037')
    ])
    def test_human_str(self, session: timetable.Session,
                       expected_human_str: str) -> None:
        """Test the :attr:`gator.core.models.timetable.Session.human_str` property."""
        assert session.human_str == expected_human_str

    def test_eq(self) -> None:
        """Test the :meth:`gator.core.models.timetable.Session.__eq__` method."""
        for year in self._ALL_YEARS:
            for season in self._ALL_SEASONS:
                for subsession in self._ALL_SUBSESSIONS:
                    session = timetable.Session(year, season, subsession)
                    # Test equality with itself
                    assert session == session
                    # Test equality with a copy
                    assert session == timetable.Session(year, season, subsession)

    def test_ne(self) -> None:
        """Test the :meth:`gator.core.models.timetable.Session.__ne__` method."""
        for year in self._ALL_YEARS:
            for season in self._ALL_SEASONS:
                for subsession in self._ALL_SUBSESSIONS:
                    session = timetable.Session(year, season, subsession)
                    # Test inequality with a different year
                    assert session != timetable.Session(year + 1, season, subsession)
                    # Test inequality with a different season
                    season_not_equal = 'summer' if season == 'regular' else 'regular'
                    assert session != timetable.Session(
                        year, season_not_equal, subsession)
                    # Test inequality with a different subsession
                    subsession_not_equal = 'second' if subsession == 'first' else 'first'
                    assert session != timetable.Session(
                        year, season, subsession_not_equal)

    def test_lt(self) -> None:
        """Test the :meth:`gator.core.models.timetable.Session.__lt__` method."""
        # Test that a session is less than another session with a greater year
        for season in self._ALL_SEASONS:
            for subsession in self._ALL_SUBSESSIONS:
                assert timetable.Session(1996, season, subsession) < \
                    timetable.Session(1997, season, subsession)
        # Test that a session is less than another session with a greater season
        for subsession in self._ALL_SUBSESSIONS:
            assert timetable.Session(1997, 'regular', subsession) < \
                timetable.Session(1997, 'summer', subsession)
        # Test that a session is less than another session with a greater subsession
        assert timetable.Session(1997, 'regular', 'first') < \
            timetable.Session(1997, 'regular', 'second') < \
            timetable.Session(1997, 'regular', 'whole')
        assert timetable.Session(1997, 'summer', 'first') < \
            timetable.Session(1997, 'summer', 'second') < \
            timetable.Session(1997, 'summer', 'whole')

    def test_sort(self) -> None:
        """Test the :meth:`gator.core.models.timetable.Session.sort` method."""
        sessions = [
            timetable.Session(1996, 'regular', 'first'),
            timetable.Session(1997, 'regular', 'second'),
            timetable.Session(1996, 'regular', 'whole'),
            timetable.Session(1997, 'summer', 'first'),
            timetable.Session(2023, 'regular', 'first'),
            timetable.Session(1997, 'summer', 'second'),
            timetable.Session(1997, 'summer', 'whole'),
            timetable.Session(37, 'regular', 'first')
        ]
        assert sorted(sessions) == [
            timetable.Session(37, 'regular', 'first'),
            timetable.Session(1996, 'regular', 'first'),
            timetable.Session(1996, 'regular', 'whole'),
            timetable.Session(1997, 'regular', 'second'),
            timetable.Session(1997, 'summer', 'first'),
            timetable.Session(1997, 'summer', 'second'),
            timetable.Session(1997, 'summer', 'whole'),
            timetable.Session(2023, 'regular', 'first')
        ]
