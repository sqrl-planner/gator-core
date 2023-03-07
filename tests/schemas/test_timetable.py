"""Test the Marshmallow schemas for the timetable models."""
from collections import OrderedDict

import gator.core.models.timetable as models
import gator.core.schemas.timetable as schemas
from tests.schemas.test_institution import (TestBuildingSchema,
                                            TestInstitutionSchema,
                                            TestLocationSchema)

# The number of milliseconds in an hour
HOUR_MS = 60 * 60 * 1000
# The number of milliseconds in a minute
MINUTE_MS = 60 * 1000


class TestSessionSchema:
    """Test the :class:`gator.core.schemas.timetable.SessionSchema` class.

    Class Attributes:
        SESSIONS: A list of sessions to test with.
        DUMPED_SESSIONS: The dumped data for the sessions in `SESSIONS`.
    """
    SESSIONS: list[models.Session] = [
        models.Session(2020, 'fall'),
        models.Session(2019, 'winter'),
        models.Session(1966, 'summer')
    ]

    DUMPED_SESSIONS: list[dict] = [
        {'year': session.year, 'season': session.season}  # type: ignore
        for session in SESSIONS
    ]

    def setup_class(self) -> None:
        """Initialize the test class."""
        self.schema = schemas.SessionSchema()

    def test_load(self) -> None:
        """Test that the schema can load a Session object."""
        for session, datum in zip(self.SESSIONS, self.DUMPED_SESSIONS):
            assert self.schema.load(datum) == session

    def test_dump(self) -> None:
        """Test that the schema can dump a Session object."""
        for session, datum in zip(self.SESSIONS, self.DUMPED_SESSIONS):
            assert OrderedDict(self.schema.dump(session)) == datum


class TestWeeklyRepetitionScheduleSchema:
    """Test the :class:`gator.core.schemas.timetable.WeeklyRepetitionScheduleSchema` class.

    Class Attributes:
        SCHEDULES: A list of schedules to test with.
        DUMPED_SCHEDULES: The dumped data for the schedules in `SCHEDULES`.
    """
    SCHEDULES = [
        models.WeeklyRepetitionSchedule(schedule=int('1', 2)),  # Every week
        models.WeeklyRepetitionSchedule(schedule=int('10', 2)),  # Every other week
        models.WeeklyRepetitionSchedule(schedule=int('101', 2)),  # Every first and third week
        models.WeeklyRepetitionSchedule(schedule=int('1010', 2)),  # Every second and fourth week
        models.WeeklyRepetitionSchedule(schedule=int('1111', 2)),  # Every week
    ]

    DUMPED_SCHEDULES = [
        {'schedule': 1, 'schedule_bits': '1', 'is_alternating': False, 'weeks': [1]},
        {'schedule': 2, 'schedule_bits': '10', 'is_alternating': True, 'weeks': [2]},
        {'schedule': 5, 'schedule_bits': '101', 'is_alternating': True, 'weeks': [1, 3]},
        {'schedule': 10, 'schedule_bits': '1010', 'is_alternating': True, 'weeks': [2, 4]},
        {'schedule': 15, 'schedule_bits': '1111', 'is_alternating': False, 'weeks': [1, 2, 3, 4]},
    ]

    def setup_class(self) -> None:
        """Initialize the test class."""
        self.schema = schemas.WeeklyRepetitionScheduleSchema()

    def test_load(self) -> None:
        """Test that the schema can load a WeeklyRepetitionSchedule object."""
        for schedule, datum in zip(self.SCHEDULES, self.DUMPED_SCHEDULES):
            assert self.schema.load(datum) == schedule

    def test_dump(self) -> None:
        """Test that the schema can dump a WeeklyRepetitionSchedule object."""
        for schedule, datum in zip(self.SCHEDULES, self.DUMPED_SCHEDULES):
            assert OrderedDict(self.schema.dump(schedule)) == datum


class TestSectionMeetingSchema:
    """Test the :class:`gator.core.schemas.timetable.SectionMeetingSchema` class.

    Class Attributes:
        SECTION_MEETINGS: A list of section meetings to test with.
        DUMPED_SECTION_MEETINGS: The dumped data for the section meetings in `SECTION_MEETINGS`.
    """
    # Private Class Attributes:
    #     _DUMPED_SCHEDULES: The dumped data for the schedule in each section meeting.
    _DUMPED_SCHEDULES: list[dict] = [
        TestWeeklyRepetitionScheduleSchema.DUMPED_SCHEDULES[0],
        TestWeeklyRepetitionScheduleSchema.DUMPED_SCHEDULES[0],
        TestWeeklyRepetitionScheduleSchema.DUMPED_SCHEDULES[1]
    ]

    SECTION_MEETINGS = [
        # Monday 12:30-13:30 in ABC 123 for 2020 fall
        models.SectionMeeting(
            day=0,
            start_time=12 * HOUR_MS + 30 * MINUTE_MS,
            end_time=13 * HOUR_MS + 30 * MINUTE_MS,
            session=TestSessionSchema.SESSIONS[0],  # Fall 2020
            location=TestLocationSchema.LOCATIONS[0]
        ),
        # Tuesday 14:00-15:00 in DEF 456 for 2019 winter
        models.SectionMeeting(
            day=1,
            start_time=14 * HOUR_MS,
            end_time=15 * HOUR_MS,
            session=TestSessionSchema.SESSIONS[1],  # Winter 2019
            location=TestLocationSchema.LOCATIONS[1]
        ),
        # Friday 09:00-12:00 in GHI 789 for 1966 summer, every other week
        models.SectionMeeting(
            day=4,
            start_time=9 * HOUR_MS,
            end_time=12 * HOUR_MS,
            session=TestSessionSchema.SESSIONS[2],  # Summer 1966
            location=TestLocationSchema.LOCATIONS[2],
            repetition_schedule=TestWeeklyRepetitionScheduleSchema.SCHEDULES[1]  # Every other week
        )
    ]

    DUMPED_SECTION_MEETINGS = [
        {
            'day': section.day,  # type: ignore
            'start_time': section.start_time,  # type: ignore
            'end_time': section.end_time,  # type: ignore
            'session': dumped_session,
            'location': dumped_location,
            'repetition_schedule': dumped_schedule
        }
        for section, dumped_session, dumped_location, dumped_schedule in zip(
            SECTION_MEETINGS,
            TestSessionSchema.DUMPED_SESSIONS,
            TestLocationSchema.DUMPED_LOCATIONS,
            _DUMPED_SCHEDULES
        )
    ]

    def setup_class(self) -> None:
        """Initialize the test class."""
        self.schema = schemas.SectionMeetingSchema()

    def test_load(self) -> None:
        """Test that the schema can load a SectionMeeting object."""
        # TODO: We need to create a test MongoDB instance to test this
        # for section, datum in zip(self.SECTION_MEETINGS, self.DUMPED_SECTION_MEETINGS):
        #     assert self.schema.load(datum) == section

    def test_dump(self) -> None:
        """Test that the schema can dump a SectionMeeting object."""
        for section, datum in zip(self.SECTION_MEETINGS, self.DUMPED_SECTION_MEETINGS):
            assert OrderedDict(self.schema.dump(section)) == datum
