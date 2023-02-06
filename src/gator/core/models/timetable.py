"""Model data classes for timetable."""
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import mongoengine as db

from gator.core.models.base_types import SerializableEnum
from gator.core.models.common import Time


class MeetingDay(SerializableEnum):
    """A class representing the day of the week."""

    MONDAY = 'MO'
    TUESDAY = 'TU'
    WEDNESDAY = 'WE'
    THURSDAY = 'TH'
    FRIDAY = 'FR'
    SATURDAY = 'SA'
    SUNDAY = 'SU'


class SectionMeeting(db.EmbeddedDocument):
    """A class representing a meeting of a section.

    Instance Attributes:
        day: The day of this meeting.
        start_time: The start time of this meeting.
        end_time: The end time of this meeting.
        assigned_room_1: A string representing the first assigned room for this
            meeting, or None if there is no first assigned room.
        assigned_room_2: A string representing the second assigned room for
            this meeting, or None if there is no second assigned room.
    """

    day: MeetingDay = db.EnumField(MeetingDay, required=True)
    start_time: Time = db.EmbeddedDocumentField(Time, required=True)
    end_time: Time = db.EmbeddedDocumentField(Time, required=True)
    assigned_room_1: Optional[str] = db.StringField(null=True)
    assigned_room_2: Optional[str] = db.StringField(null=True)


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


class Instructor(db.EmbeddedDocument):
    """A class representing a course instructor.

    Instance Attributes:
        id: A unique integer id representing this instructor.
        first_name: The first name of this instructor.
        last_name: The last name of this instructor.
    """

    first_name: str = db.StringField(required=True)
    last_name: str = db.StringField(required=True)


class Section(db.EmbeddedDocument):
    """A class representing a course section/meeting.

    Instance Attributes:
        teaching_method: The teaching method for this section, or None if this
            section has no teaching method.
        section_number: The number of this section, representing as a string.
        subtitle: The section subtitle, or None if there is no subtitle.
        instructors: A list of instructors teaching this section.
        meetings: A list of meetings available for this section.
        delivery_mode: The delivery mode for this section, or None if this
            section has no delivery mode.
        cancelled: Whether this section is cancelled.
        has_waitlist: Whether this section has a waitlist.
        enrolment_capacity: The total number of students that can be enrolled
            in this section.
        actual_enrolment: The number of students enrolled in this section.
        actual_waitlist: The number of students waitlisted for this section.
        enrolment_indicator: A string representing the enrollment indicator
            for this section, or None if there is no enrollment indicator.
    """

    teaching_method: Optional[SectionTeachingMethod] = db.EnumField(
        SectionTeachingMethod, null=True
    )
    section_number: str = db.StringField()
    subtitle: Optional[str] = db.StringField(null=True)
    instructors: list[Instructor] = db.EmbeddedDocumentListField('Instructor')
    meetings: list[SectionMeeting] = db.EmbeddedDocumentListField(
        'SectionMeeting')
    delivery_mode: Optional[SectionDeliveryMode] = db.EnumField(
        SectionDeliveryMode, null=True)
    cancelled: bool = db.BooleanField()
    has_waitlist: bool = db.BooleanField()
    enrolment_capacity: Optional[int] = db.IntField(null=True)
    actual_enrolment: Optional[int] = db.IntField(null=True)
    actual_waitlist: Optional[int] = db.IntField(null=True)
    enrolment_indicator: Optional[str] = db.StringField(null=True)

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


class Campus(SerializableEnum):
    """University campus."""

    ST_GEORGE = 'UTSG'
    SCARBOROUGH = 'UTSC'
    MISSISSAUGA = 'UTM'


class Organisation(db.Document):
    """A class representing a department (which offers courses).

    Instance Attributes:
        code: A unique string representing this organisation.
        name: The full name of this organisation.
        campus: The campus this organisation is located at.
    """

    code: str = db.StringField(primary_key=True)
    name: str = db.StringField(required=True)
    campus: Campus = db.EnumField(Campus, required=True)


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


class Course(db.Document):
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

    id: str = db.StringField(primary_key=True)
    organisation: Organisation = db.ReferenceField('Organisation')
    code: str = db.StringField()
    title: str = db.StringField()
    description: str = db.StringField()
    term: CourseTerm = db.EnumField(CourseTerm)
    session_code: str = db.StringField(min_length=5, max_length=5)
    sections: list[Section] = db.EmbeddedDocumentListField('Section')
    prerequisites: str = db.StringField()  # TODO: Parse this
    corequisites: str = db.StringField()  # TODO: Parse this
    exclusions: str = db.StringField()  # TODO: Parse this
    recommended_preparation: str = db.StringField()
    breadth_categories: str = db.StringField()  # TODO: Parse this
    distribution_categories: str = db.StringField()  # TODO: Parse this
    web_timetable_instructions: str = db.StringField()
    delivery_instructions: str = db.StringField()
    campus: Campus = db.EnumField(Campus, required=True)

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
