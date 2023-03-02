"""Model data classes for timetable."""
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from mongoengine import Document, EmbeddedDocument, fields

from gator.core.models.common import SerializableEnum


class Campus(SerializableEnum):
    """The different campuses of the University of Toronto."""

    ST_GEORGE = 'UTSG'
    SCARBOROUGH = 'UTSC'
    MISSISSAUGA = 'UTM'


class Building(Document):
    """A building on a campus of the University of Toronto.

    Instance Attributes:
        code: A unique string code that identifies this building.
        campus: The campus that this building is on.
        name: The name of this building. Can be None if unknown.
        map_url: The URL of this building's map. Can be None if unknown.
        campus: The campus that this building is on.
    """

    code: str = fields.StringField(unique=True, primary_key=True)
    campus: Campus = fields.EnumField(Campus)
    name: Optional[str] = fields.StringField(required=False, default=None)
    map_url: Optional[str] = fields.URLField(required=False, default=None)


class Location(EmbeddedDocument):
    """A location on campus represented as a building-room pair.

    Instance Attributes:
        building: The building that the section meets in.
        room: The room that the section meets in, not including the building
            code.
    """

    building: Building = fields.ReferenceField(Building, required=True)
    room: str = fields.StringField(required=True)


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

    schedule: int = fields.IntField(required=True, min_value=1, default=1)

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
    """A class representing a meeting of a section.

    Instance Attributes:
        day: The day of the week that this meeting occurs on, represented as an
            integer, where Monday is 0 and Sunday is 6.
        start_time: The time that this meeting starts, represented as the number
            of milliseconds since midnight(00:00:00).
        end_time: The time that this meeting ends, represented as the number of
            milliseconds since midnight (00:00:00).
        terms: The terms that this meeting occurs in.
        location: The location of this meeting, or None if this meeting has no
            assigned location.
        repetition_schedule: The repetition schedule of this meeting. Defaults
            to a schedule that occurs every week.
    """

    day: int = fields.IntField(required=True, min_value=0, max_value=6)
    start_time: int = fields.IntField(required=True, min_value=0, max_value=86400000)
    end_time: int = fields.IntField(required=True, min_value=0, max_value=86400000)
    terms: list[Term] = fields.ListField(fields.ReferenceField(Term), required=True)
    location: Optional[Location] = fields.EmbeddedDocumentField(
        Location, required=False, default=None)
    repetition_schedule: WeeklyRepetitionSchedule = fields.EmbeddedDocumentField(
        WeeklyRepetitionSchedule, required=True, default=WeeklyRepetitionSchedule())


class SectionTeachingMethod(SerializableEnum):
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
    """A class representing a course instructor.

    Instance Attributes:
        first_name: The first name of this instructor.
        last_name: The last name of this instructor.
    """

    first_name: str = fields.StringField(required=True)
    last_name: str = fields.StringField(required=True)


class EnrolmentInfo(EmbeddedDocument):
    """A class representing enrolment information for a section.

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

    current_enrolment: Optional[int] = fields.IntField(null=True)
    max_enrolment: Optional[int] = fields.IntField(null=True)
    has_waitlist: Optional[bool] = fields.BooleanField(default=False)
    current_waitlist: Optional[int] = fields.IntField(null=True)
    enrolment_indicator: Optional[str] = fields.StringField(null=True)
    # TODO: Add enrolment controls


class Section(EmbeddedDocument):
    """A class representing a course section/meeting.

    Instance Attributes:
        teaching_method: The teaching method for this section.
        section_number: The number of this section, represented as a string.
        meetings: A list of meetings available for this section.
        instructors: A list of instructors teaching this section.
        current_enrolment: The number of students currently enrolled in this
            section.
        max_enrolment: The maximum number of students that can be enrolled in
            this section.
        subtitle: The subtitle of this section, or None if there is no subtitle.
            Among other things, this is used to distinguish between the content
            matter when a course offers curriculum on multiple topics. For
            example, an introductory algorithms course might have a section
            that uses Python and another section that uses Java.
        cancelled: Whether this section is cancelled.
        delivery_modes: A list of delivery modes for this section. The i-th
            element of this list corresponds to the delivery mode in the
            i-th term that the course runs in.
        enrolment_info: The enrolment information for this section.
        notes: A list of HTML strings.
    """

    teaching_method: SectionTeachingMethod = fields.EnumField(SectionTeachingMethod)
    section_number: str = fields.StringField()
    meetings: list[SectionMeeting] = fields.EmbeddedDocumentListField('SectionMeeting')
    instructors: list[Instructor] = fields.EmbeddedDocumentListField('Instructor')
    subtitle: Optional[str] = fields.StringField(null=True)
    cancelled: bool = fields.BooleanField()
    delivery_modes: list[SectionDeliveryMode] = fields.ListField(fields.EnumField(SectionDeliveryMode))
    enrolment_info: EnrolmentInfo = fields.EmbeddedDocumentField(EnrolmentInfo)
    notes: Optional[list[str]] = fields.ListField(fields.StringField())
    linked_sections: Optional[list[str]] = fields.ListField(fields.StringField())
    # TODO: Section dependencies. This should be represented as a graph, where
    # each node is a section and each edge is a dependency (which may or may not
    # be bidirectional).

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


class CourseTerm(SerializableEnum):
    """The course term."""

    FIRST_SEMESTER = 'F'
    SECOND_SEMESTER = 'S'
    FULL_YEAR = 'Y'


class Organisation(Document):
    """A class representing a department (which offers courses).

    Instance Attributes:
        code: A unique string representing this organisation.
        name: The full name of this organisation.
        campus: The campus this organisation is located at.
    """

    code: str = fields.StringField(primary_key=True)
    name: str = fields.StringField(required=True)
    campus: Campus = fields.EnumField(Campus, required=True)


@dataclass(frozen=True, eq=True)
class Session:
    """A class representing a session of a calendar year.

    Instance Attributes:
        year: The year of the session.
        summer: Whether this is a summer session. Defaults to False, meaning that this is a
            fall/winter session.
    """

    year: int
    summer: bool = False

    @property
    def code(self) -> str:
        """Return the session code for this Session.

        The session code is a five-length string where the first four characters denote the session
        year, and the last character denotes whether it is a fall/winter (9) or summer session (5).
        For example, the code `20209` denotes the fall/winter session of 2020.

        Examples:
            >>> Session(2020, summer=False).code
            '20209'
            >>> Session(1966, summer=True).code
            '19665'
            >>> Session(1, summer=False).code
            '00019'
        """
        suffix = 5 if self.summer else 9
        return f'{str(self.year).zfill(4)}{suffix}'

    @property
    def human_str(self) -> str:
        """Return this session as a human-readable string.

        Examples:
            >>> Session(2020, summer=False).human_str
            'Fall/Winter 2020'
            >>> Session(1966, summer=True).human_str
            'Summer 1966'
            >>> Session(2019, summer=False).human_str
            'Fall/Winter 2019'
        """
        term = 'Summer' if self.summer else 'Fall/Winter'
        return f'{term} {self.year}'

    def __str__(self) -> str:
        """Return this session as a string.

        The output string is the session code. See `code` for more
        information.
        """
        return self.code

    @classmethod
    def parse(cls, session_code: str) -> 'Session':
        """Return an instance Session representing the given session code.

        Raise a ValueError if the session code is not formatted properly.

        Examples:
            >>> Session.parse('20205') == Session(year=2020, summer=True)
            True
            >>> Session.parse('00509') == Session(year=50, summer=False)
            True
        """
        if len(session_code) != 5:
            raise ValueError(
                f'invalid session code ("{session_code}"): expected string of length 5'
                f', not {len(session_code)}')
        elif not session_code.isnumeric():
            raise ValueError(
                f'invalid session code ("{session_code}"): expected numeric string'
            )
        elif int(session_code[-1]) not in {9, 5}:
            raise ValueError(
                f'invalid session code ("{session_code}"): expected code to end in '
                f'one of {{9, 5}}, not {session_code[-1]}')
        else:
            return Session(int(session_code[:4]),
                           int(session_code[-1]) == 5)


class Course(Document):
    """A class representing a course.

    Instance Attributes:
        id: The full code of the course.
            Formatted as "{code}-{term}-{session_code}".
        organisation: The Organisation that this course is associated with.
        code: The course code.
        title: The title of this course.
        description: The description of this course.
        term: The term in which the course takes place.
        session: The session in which the course takes place.
        sections: A list of sections available for this course.
        prerequisites: Prerequisties for this course.
        corequisites: Corequisites for this course.
        exclusions: Exclusions for this course.
        recommended_preparation: Recommended preparations to complete before this course.
        breadth_categories: The breadth categories this course can fulfill.
        distribution_categories: The distribution categories this course can fulfill.
        web_timetable_instructions: Additional timetable information.
        delivery_instructions: Additional delivery instruction information.
    """

    id: str = fields.StringField(primary_key=True)
    organisation: Organisation = fields.ReferenceField('Organisation')
    code: str = fields.StringField()
    title: str = fields.StringField()
    description: str = fields.StringField()
    term: CourseTerm = fields.EnumField(CourseTerm)
    session_code: str = fields.StringField(min_length=5, max_length=5)
    sections: list[Section] = fields.EmbeddedDocumentListField('Section')
    prerequisites: str = fields.StringField()  # TODO: Parse this
    corequisites: str = fields.StringField()  # TODO: Parse this
    exclusions: str = fields.StringField()  # TODO: Parse this
    recommended_preparation: str = fields.StringField()
    breadth_categories: str = fields.StringField()  # TODO: Parse this
    distribution_categories: str = fields.StringField()  # TODO: Parse this
    web_timetable_instructions: str = fields.StringField()
    delivery_instructions: str = fields.StringField()
    campus: Campus = fields.EnumField(Campus, required=True)

    meta = {
        'indexes': [
            {
                'fields': ['$title', '$description'],
                'default_language': 'english',
                'weights': {'title': 1.5, 'description': 1},
            }
        ]
    }

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

    @property
    @lru_cache
    def session(self) -> Session:
        """Return the session of this course."""
        return Session.parse(self.session_code)

    def __str__(self):
        """Return a string representation of this course."""
        return f'{self.code}: {self.title}'
