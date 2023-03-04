"""Model definitions for timetable data."""
import re
import math
from functools import lru_cache
from dataclasses import dataclass
from typing import Optional, Union

from mongoengine import Document, EmbeddedDocument, fields

from gator.core.models.common import SerializableEnum
from gator.core.models.institution import Institution, Building, Location


class Session(EmbeddedDocument):
    """A formal division of the academic year.

    The regular academic year is divided into three sessions: the fall session,
    which runs from September to December; the winter (spring) session, which
    runs from January to April; and the summer session, which runs from May to
    August.

    The canonical representation of a session is a five-length string where the
    first four characters denote the session year, and the last character denotes
    the session season, 9 for fall, 1 for winter, and 5 for summer. For example,
    the code `20209` denotes the fall session of 2020, and the code `19665`
    denotes the summer session of 1966.

    Instance Attributes:
        year: The year of the session. Must be between 0 and 9999.
        season: The season of the session.
    """
    # Private Class Attributes:
    #     _SEASON_MAP: A mapping from season names to their corresponding
    #         session codes.
    #     _INVERSE_SEASON_MAP: A mapping from session codes to their
    #         corresponding season names.
    _SEASON_MAP: dict[str, int] = {'fall': 9, 'winter': 1, 'summer': 5}
    _INVERSE_SEASON_MAP: dict[int, str] = {v: k for k, v in _SEASON_MAP.items()}

    year = fields.IntField(required=True, min_value=0, max_value=9999)
    season = fields.StringField(required=True, choices=_SEASON_MAP.keys())

    @property
    def code(self) -> str:
        """The canonical representation of this session.

        Returns:
            A five-length string where the first four characters denote the
            session year, and the last character denotes the session season,
            9 for fall, 1 for winter, and 5 for summer.

        Examples:
            >>> Session(2020, season='fall').code
            '20209'
            >>> Session(2019, season='winter').code
            '20191'
            >>> Session(1966, season='summer').code
            '19665'
        """
        return f'{str(self.year).zfill(4)}{self._SEASON_MAP[self.season]}'

    @property
    def human_str(self) -> str:
        """A human-readable representation of this session.

        Examples:
            >>> Session(2020, season='fall').human_str
            'Fall 2020'
            >>> Session(2019, season='winter').human_str
            'Winter 2019'
            >>> Session(1966, season='summer').human_str
            'Summer 1966'
        """
        return f'{self.season.capitalize()} {self.year}'

    def __str__(self) -> str:
        """Return a string representation of this session.

        The output string is the session code. See `code` for more
        information.
        """
        return self.code

    @classmethod
    def parse(cls, session_code: Union[str, int]) -> 'Session':
        """Return an instance Session representing the given session code.

        Raise a ValueError if the session code is not formatted properly.

        Args:
            session_code: The session code to parse as a string or integer.
                If the session code is an integer, it will be converted to a
                string and zero-padded to the left if necessary. E.g. if
                509 is passed, it will be converted to '00509' which corresponds
                to the fall session of the year 50.
        Examples:
            >>> Session.parse(509) == Session(year=50, season='fall')
            True
            >>> Session.parse(20201) == Session(year=2020, season='winter')
            True
            >>> Session.parse('20205') == Session(year=2020, season='summer')
            True
        """
        # Ensure that the session code is a string and zero-padded to the left
        session_code = str(session_code).zfill(5)

        if len(session_code) != 5:
            raise ValueError(
                f'invalid session code ("{session_code}"): expected string of length 5'
                f', not {len(session_code)}')
        elif not session_code.isnumeric():
            raise ValueError(
                f'invalid session code ("{session_code}"): expected numeric string')
        elif int(session_code[-1]) not in cls._INVERSE_SEASON_MAP:
            raise ValueError(
                f'invalid session code ("{session_code}"): expected code to end in '
                f'one of {list(cls._INVERSE_SEASON_MAP.keys())}, not {session_code[-1]}')
        else:
            return Session(
                int(session_code[:4]),
                cls._INVERSE_SEASON_MAP[int(session_code[-1])])


class WeeklyRepetitionSchedule(EmbeddedDocument):
    """A schedule for an event that repeats weekly.

    Represented as an integer whose binary representation is
    interpreted as a set of :math:`k` bits, where :math:`k` is the number of
    weeks in a single repeating period. The :math:`i`-th bit is 1 if the
    meeting occurs in the :math:`i`-th week of the repeating period, and 0
    otherwise. For example, if a meeting occurs every week, then :math:`k = 1`
    and the bit is `1`. If a meeting occurs every other week, then
    :math:`k = 2` and the bits are `10`.

    Instance Attributes:
        schedule: The integer representing the repetition schedule.
    """

    schedule = fields.IntField(min_value=1, default=1)

    @property
    def is_alternating(self) -> bool:
        """Whether this meeting does not regularly occur every week.

        A schedule is alternating (i.e. does not occur every week) if there is
        at least one week :math:`i` such that the :math:`i`-th bit is 0.
        """
        k = math.ceil(math.log2(self.schedule))
        return self.schedule > 1 and self.schedule != (1 << k) - 1

    def to_dict(self) -> dict:
        """Convert this object to a dictionary.

        Returns:
            A dictionary representation of this object, with two additional
            keys: `schedule_bits` and `is_alternating`.
        """
        return {
            'schedule': self.schedule,
            'schedule_bits': bin(self.schedule)[2:],  # Remove the '0b' prefix
            'is_alternating': self.is_alternating
        }


class SectionMeeting(EmbeddedDocument):
    """A single meeting of a section.

    Instance Attributes:
        day: The day of the week that this meeting occurs on, represented as an
            integer, where Monday is 0 and Sunday is 6.
        start_time: The time that this meeting starts, represented as the number
            of milliseconds since midnight(00:00:00).
        end_time: The time that this meeting ends, represented as the number of
            milliseconds since midnight (00:00:00).
        session: The session that this meeting occurs in.
        location: The location of this meeting, or None if this meeting has no
            assigned location.
        repetition_schedule: The repetition schedule of this meeting. Defaults
            to a schedule that occurs every week.
    """

    day = fields.IntField(required=True, min_value=0, max_value=6)
    start_time = fields.IntField(required=True, min_value=0, max_value=86400000)
    end_time = fields.IntField(required=True, min_value=0, max_value=86400000)
    session = fields.EmbeddedDocumentField(Session, required=True)
    location = fields.EmbeddedDocumentField(
        Location, null=True, default=None)
    repetition_schedule = fields.EmbeddedDocumentField(
        WeeklyRepetitionSchedule, default=WeeklyRepetitionSchedule)


class TeachingMethod(SerializableEnum):
    """A class representing the teaching method for a section."""

    LECTURE = 'LEC'
    TUTORIAL = 'TUT'
    PRACTICAL = 'PRA'


class SectionDeliveryMode(SerializableEnum):
    """A class representing mode of delivery for a section."""

    CLASS = 'CLASS'
    ONLINE_SYNC = 'ONLSYNC'
    ONLINE_ASYNC = 'ONLASYNC'
    IN_PERSON = 'INPER'
    SYNC = 'SYNC'
    ASYNC = 'ASYNC'
    # idk why they keep changing delivery modes
    ASYIF = 'ASYIF'
    SYNIF = 'SYNIF'


class Instructor(EmbeddedDocument):
    """A course instructor.

    Instance Attributes:
        first_name: The first name of this instructor.
        last_name: The last name of this instructor.
    """

    first_name = fields.StringField(required=True)
    last_name = fields.StringField(required=True)


class EnrolmentInfo(EmbeddedDocument):
    """Enrolment information for a section.

    Instance Attributes:
        current_enrolment: The number of students currently enrolled in this
            section.
        max_enrolment: The maximum number of students that can be enrolled in
            this section.
        has_waitlist: Whether this section has a waitlist.
        current_waitlist: The number of students currently on the waitlist for
            this section.
        enrolment_indicator: A string representing the enrollment indicator
            for this section, or None if there is no enrollment indicator.
    """

    current_enrolment = fields.IntField(null=True, min_value=0, default=None)
    max_enrolment = fields.IntField(null=True, min_value=0, default=None)
    has_waitlist = fields.BooleanField(default=False)
    current_waitlist = fields.IntField(null=True, min_value=0, default=None)
    enrolment_indicator = fields.StringField(null=True, default=None)
    # TODO: Add enrolment controls


class Section(EmbeddedDocument):
    """A section of a course.

    Instance Attributes:
        teaching_method: The teaching method for this section.
        section_number: The number of this section, represented as a string.
        meetings: A list of meetings available for this section.
        instructors: A list of instructors teaching this section.
        delivery_modes: A list of delivery modes for this section. The i-th
            element of this list corresponds to the delivery mode in the
            i-th term that the course runs in.
        subtitle: The subtitle of this section, or None if there is no subtitle.
            Among other things, this is used to distinguish between the content
            matter when a course offers curriculum on multiple topics. For
            example, an introductory algorithms course might have a section
            that uses Python and another section that uses Java.
        cancelled: Whether this section is cancelled.
        enrolment_info: The enrolment information for this section.
        notes: A list of HTML strings.
    """

    teaching_method = fields.EnumField(TeachingMethod, required=True)
    section_number = fields.StringField(required=True)
    meetings = fields.EmbeddedDocumentListField('SectionMeeting', required=True)
    instructors = fields.EmbeddedDocumentListField('Instructor', required=True)
    delivery_modes = fields.ListField(fields.EnumField(SectionDeliveryMode), required=True)
    subtitle = fields.StringField(null=True, default=None)
    cancelled = fields.BooleanField(default=False)
    enrolment_info = fields.EmbeddedDocumentField(EnrolmentInfo, default=EnrolmentInfo)
    notes = fields.ListField(fields.StringField(), default=list)
    # TODO: Section dependencies. This should be represented as a graph, where
    # each node is a section and each edge is a dependency (which may or may not
    # be bidirectional).
    linked_sections = fields.ListField(fields.StringField(), default=list)

    @property
    def code(self) -> str:
        """Return a string representing the code of this section.

        This is a combination of the teaching method and the section
        number, separated by a hyphen.

        If the teaching method is None, then the section number is returned
        instead.
        """
        if self.teaching_method is None:
            return self.section_number
        else:
            return f'{self.teaching_method.value}-{self.section_number}'


class Term(SerializableEnum):
    """The term in which a course is offered.

    Class Attributes:
        FIRST_SEMESTER: The first semester of the academic year.
        SECOND_SEMESTER: The second semester of the academic year.
        FULL_YEAR: The full academic year. Spans both semesters.
    """
    FIRST_SEMESTER = 'F'
    SECOND_SEMESTER = 'S'
    FULL_YEAR = 'Y'


class InstructionLevel(SerializableEnum):
    """The level of instruction for a course."""
    UNDERGRADUATE = 'undergraduate'


class BreadthRequirement(EmbeddedDocument):
    """A breadth or distribution requirement.

    Instance Attributes:
        code: A unique code for this breadth requirement.
        type: The type of this breadth requirement.
        description: A description of this breadth requirement.
        is_distribution_requirement: Whether this breadth requirement is a
            distribution requirement.
        institution: The institution that this breadth requirement belongs to.
    """

    code = fields.StringField(unique=True, primary_key=True)
    type = fields.StringField()
    description = fields.StringField()
    is_distribution_requirement = fields.BooleanField()
    institution: Institution = fields.ReferenceField('Institution')


class Course(Document):
    """An instance of a course offered at UofT for a specific term.

    Instance Attributes:
        id: A unique identifier for this course.
        code: The code of this course.
        name: The name of this course.
        sections: A list of sections available for this course.
        sessions: A list of sessions in which this course is offered.
        term: The term this course is offered in.
        credits: The number of credits this course is worth.
        campus: The campus this course is offered at.
        faculty: The faculty that offers this course.
        department: The department that offers this course.
        title: The title of this course. This is usually the same as the name.
        instruction_level: The level of instruction for this course.
            For example, undergraduate or graduate.
        breadth_requirements: Breadth and distribution requirements that this
            course fulfills.
        description: The description of this course.
        prerequisites: Prerequisties for this course.
        corequisites: Corequisites for this course.
        exclusions: Exclusions for this course.
        recommended_preparation: Recommended preparations to complete before this course.
        cancelled: Whether this course is cancelled.
        tags: Tags for this course.
        notes: A list of HTML strings.
    """

    id = fields.StringField(primary_key=True)
    code = fields.StringField()
    name = fields.StringField()
    sections = fields.EmbeddedDocumentListField('Section')
    sessions = fields.EmbeddedDocumentListField('Session')
    term = fields.EnumField(Term)
    credits = fields.FloatField()
    campus = fields.ReferenceField(Institution)
    faculty = fields.ReferenceField(Institution)
    department = fields.ReferenceField(Institution)
    # Metadata fields
    title = fields.StringField(null=True, default=None)
    instruction_level = fields.EnumField(InstructionLevel, null=True, default=None)
    description = fields.StringField(null=True, default=None)
    breadth_requirements = fields.ListField(
        fields.ReferenceField(BreadthRequirement), default=list)
    prerequisites = fields.StringField(null=True, default=None)
    corequisites = fields.StringField(null=True, default=None)
    exclusions = fields.StringField(null=True, default=None)
    recommended_preparation = fields.StringField(null=True, default=None)
    cancelled = fields.BooleanField(default=False)
    tags = fields.ListField(fields.StringField(), default=list)
    notes = fields.ListField(fields.StringField(), default=list)

    @property
    @lru_cache
    def section_codes(self) -> set[str]:
        """Return a set of section codes for this course."""
        return {section.code for section in self.sections}

    @property
    @lru_cache
    def level(self) -> int:
        """Return the level of this course.

        If the course is not a level course, return 0.
        """
        m = re.search(r'(?:[^\d]*)(\d+)', self.code)
        if not m:
            return 0
        else:
            return int(math.floor(int(m.group(1)) / 100.0)) * 100
