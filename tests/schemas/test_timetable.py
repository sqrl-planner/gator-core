"""Test the Marshmallow schemas for the timetable models."""
from collections import OrderedDict

import gator.core.models.timetable as models
import gator.core.schemas.timetable as schemas
from tests.schemas.test_institution import (TestInstitutionSchema,
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
        models.Session(2022, 'regular', 'first'),  # Fall 2022
        models.Session(2023, 'regular', 'second'),  # Winter 2023
        models.Session(2022, 'regular', 'whole'),  # Fall 2022 - Winter 2023
        models.Session(2023, 'summer', 'first'),  # Summer 2023 (First Subsession)
        models.Session(2023, 'summer', 'second'),  # Summer 2023 (Second Subsession)
        models.Session(2023, 'summer', 'whole'),  # Summer 2023 (Whole Session)
    ]

    DUMPED_SESSIONS: list[dict] = [{
        'year': session.year,
        'season': session.season,
        'subsession': session.subsession
    } for session in SESSIONS]

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
        # Tuesday 14:00-15:00 in DEF 456 for 2021 winter
        models.SectionMeeting(
            day=1,
            start_time=14 * HOUR_MS,
            end_time=15 * HOUR_MS,
            session=TestSessionSchema.SESSIONS[1],  # Winter 2021
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
        for section, datum in zip(self.SECTION_MEETINGS, self.DUMPED_SECTION_MEETINGS):
            assert self.schema.load(datum) == section

    def test_dump(self) -> None:
        """Test that the schema can dump a SectionMeeting object."""
        for section, datum in zip(self.SECTION_MEETINGS, self.DUMPED_SECTION_MEETINGS):
            assert OrderedDict(self.schema.dump(section)) == datum


class TestInstructorSchema:
    """Test the :class:`gator.core.schemas.timetable.InstructorSchema` class.

    Class Attributes:
        INSTRUCTORS: A list of instructors to test with.
        DUMPED_INSTRUCTORS: The dumped data for the instructors in `INSTRUCTORS`.
    """
    INSTRUCTORS: list[models.Instructor] = [
        models.Instructor(first_name='Jane', last_name='Doe'),
        models.Instructor(first_name='John', last_name='Doe'),
        models.Instructor(first_name='John', last_name='Smith'),
    ]
    DUMPED_INSTRUCTORS = [{
        'first_name': instructor.first_name,
        'last_name': instructor.last_name
    } for instructor in INSTRUCTORS]

    def setup_class(self) -> None:
        """Initialize the test class."""
        self.schema = schemas.InstructorSchema()

    def test_load(self) -> None:
        """Test that the schema can load an Instructor object."""
        for instructor, datum in zip(self.INSTRUCTORS, self.DUMPED_INSTRUCTORS):
            assert self.schema.load(datum) == instructor

    def test_dump(self) -> None:
        """Test that the schema can dump an Instructor object."""
        for instructor, datum in zip(self.INSTRUCTORS, self.DUMPED_INSTRUCTORS):
            assert OrderedDict(self.schema.dump(instructor)) == datum


class TestEnrolmentInfoSchema:
    """Test the :class:`gator.core.schemas.timetable.EnrolmentInfoSchema` class.

    Class Attributes:
        ENROLMENT_INFO: An enrolment info to test with.
        DUMPED_ENROLMENT_INFO: The dumped data for `ENROLMENT_INFO`.
    """
    ENROLMENT_INFO: models.EnrolmentInfo = models.EnrolmentInfo(
        current_enrolment=10,
        max_enrolment=20,
        has_waitlist=True,
        current_waitlist_size=5
    )
    DUMPED_ENROLMENT_INFO = {
        'current_enrolment': ENROLMENT_INFO.current_enrolment,
        'max_enrolment': ENROLMENT_INFO.max_enrolment,
        'has_waitlist': ENROLMENT_INFO.has_waitlist,
        'current_waitlist_size': ENROLMENT_INFO.current_waitlist_size
    }

    def setup_class(self) -> None:
        """Initialize the test class."""
        self.schema = schemas.EnrolmentInfoSchema()

    def test_load(self) -> None:
        """Test that the schema can load an EnrolmentInfo object."""
        assert self.schema.load(self.DUMPED_ENROLMENT_INFO) == self.ENROLMENT_INFO

    def test_dump(self) -> None:
        """Test that the schema can dump an EnrolmentInfo object."""
        assert OrderedDict(self.schema.dump(self.ENROLMENT_INFO)) == self.DUMPED_ENROLMENT_INFO


class TestSectionSchema:
    """Test the :class:`gator.core.schemas.timetable.SectionSchema` class.

    Class Attributes:
        SECTION: A section to test with.
        DUMPED_SECTION: The dumped data for `SECTION`.
    """
    SECTION: models.Section = models.Section(
        teaching_method=models.TeachingMethod.LECTURE,
        section_number="0101",
        meetings=TestSectionMeetingSchema.SECTION_MEETINGS,
        instructors=TestInstructorSchema.INSTRUCTORS,
        delivery_modes=[
            models.SectionDeliveryMode.IN_PERSON,  # Fall 2020
            models.SectionDeliveryMode.IN_PERSON   # Winter 2021
        ],
        enrolment_info=TestEnrolmentInfoSchema.ENROLMENT_INFO
    )
    DUMPED_SECTION = {
        'teaching_method': SECTION.teaching_method.name,
        'section_number': SECTION.section_number,
        'meetings': TestSectionMeetingSchema.DUMPED_SECTION_MEETINGS,
        'instructors': TestInstructorSchema.DUMPED_INSTRUCTORS,
        'delivery_modes': [mode.name for mode in SECTION.delivery_modes],
        'cancelled': SECTION.cancelled,
        'enrolment_info': TestEnrolmentInfoSchema.DUMPED_ENROLMENT_INFO,
    }

    def setup_class(self) -> None:
        """Initialize the test class."""
        self.schema = schemas.SectionSchema()

    def test_load(self) -> None:
        """Test that the schema can load a Section object."""
        assert self.schema.load(self.DUMPED_SECTION) == self.SECTION

    def test_dump(self) -> None:
        """Test that the schema can dump a Section object."""
        assert OrderedDict(self.schema.dump(self.SECTION)) == self.DUMPED_SECTION


class TestCategoricalRequirementSchema:
    """Test the :class:`gator.core.schemas.timetable.CategoricalRequirementSchema` class.

    Class Attributes:
        CATEGORICAL_REQUIREMENT: A categorical requirement to test with.
        DUMPED_CATEGORICAL_REQUIREMENT: The dumped data for `CATEGORICAL_REQUIREMENT`.
    """
    CATEGORICAL_REQUIREMENT: models.CategoricalRequirement = models.CategoricalRequirement(
        code='BR=1',
        type='breadth',
        name='Creative Cultural',
        description='BR=1 Creative and Cultural Representation',
        institutions=[TestInstitutionSchema.FACULTY_INSTITUTION]
    )
    DUMPED_CATEGORICAL_REQUIREMENT = {
        'code': CATEGORICAL_REQUIREMENT.code,
        'type': CATEGORICAL_REQUIREMENT.type,
        'name': CATEGORICAL_REQUIREMENT.name,
        'description': CATEGORICAL_REQUIREMENT.description,
        'institutions': [TestInstitutionSchema.FACULTY_INSTITUTION.code]
    }

    def setup_class(self) -> None:
        """Initialize the test class."""
        self.schema = schemas.CategoricalRequirementSchema()

    def test_load(self) -> None:
        """Test that the schema can load a CategoricalRequirement object."""
        assert self.schema.load(self.DUMPED_CATEGORICAL_REQUIREMENT) == self.CATEGORICAL_REQUIREMENT

    def test_dump(self) -> None:
        """Test that the schema can dump a CategoricalRequirement object."""
        assert OrderedDict(self.schema.dump(self.CATEGORICAL_REQUIREMENT)) == self.DUMPED_CATEGORICAL_REQUIREMENT


class TestCourseSchema:
    """Test the :class:`gator.core.schemas.timetable.CourseSchema` class.

    Class Attributes:
        COURSE: A course to test with.
        DUMPED_COURSE: The dumped data for `COURSE`.
    """
    COURSE: models.Course = models.Course(
        id='6e1c6b5c-1b1d-4b1e-9c1c-1b1d4b1e9c1c',
        code='XYZ300Y1',
        name='Introduction to XYZ',
        sections=[TestSectionSchema.SECTION],
        sessions=[TestSessionSchema.SESSIONS[0], TestSessionSchema.SESSIONS[1]],  # Fall 2020, Winter 2021
        term=models.Term.FULL_YEAR,
        credits=1.0,
        institution=models.Institution(
            code='XYZ',
            name='XYZ Department',
            type='department',
            parent=TestInstitutionSchema.FACULTY_INSTITUTION
        ),
        instruction_level=models.InstructionLevel.UNDERGRADUATE,
        description='This course introduces students to XYZ.',
        categorical_requirements=[TestCategoricalRequirementSchema.CATEGORICAL_REQUIREMENT],
        prerequisites='XYZ100Y1',
        corequisites='XYZ200Y1',
        exclusions='XYZ400Y1',
        cancelled=False,
        tags=['xyz', 'introductory', 'third-year'],
        notes=['This course is only offered for students in the XYZ program.']
    )
    DUMPED_COURSE = {
        'uuid': COURSE.uuid,
        'code': COURSE.code,
        'name': COURSE.name,
        'sections': [TestSectionSchema.DUMPED_SECTION],
        'sessions': [dumped_session for dumped_session in TestSessionSchema.DUMPED_SESSIONS[:2]],
        'term': COURSE.term.name,
        'credits': COURSE.credits,
        'institution': COURSE.institution.code,
        'instruction_level': COURSE.instruction_level.name,  # type: ignore
        'description': COURSE.description,
        'categorical_requirements': [TestCategoricalRequirementSchema.DUMPED_CATEGORICAL_REQUIREMENT],
        'prerequisites': COURSE.prerequisites,
        'corequisites': COURSE.corequisites,
        'exclusions': COURSE.exclusions,
        'cancelled': COURSE.cancelled,
        'tags': COURSE.tags,
        'notes': COURSE.notes
    }

    def setup_class(self) -> None:
        """Initialize the test class."""
        self.schema = schemas.CourseSchema()
        self.COURSE.save(cascade=True)

    def test_load(self) -> None:
        """Test that the schema can load a Course object."""
        assert self.schema.load(self.DUMPED_COURSE) == self.COURSE

    def test_dump(self) -> None:
        """Test that the schema can dump a Course object."""
        assert OrderedDict(self.schema.dump(self.COURSE)) == self.DUMPED_COURSE
