"""Model definitions for timetable data."""
import math
import re
from functools import lru_cache
from typing import Any, Optional, Union

from mongoengine import Document, EmbeddedDocument, fields

from gator.core.models.common import SerializableEnum
from gator.core.models.institution import Institution, Location

class Session(EmbeddedDocument):
    """A formal division of the academic year.

    The regular academic year is divided into two seasons:
        - the regular season, which runs from September to April
        - the summer season, which runs from May to August
    
    Each season is divided into two subsessions:
        - the first subsession
            The first subsession runs from September to December for the regular
            season, and from May to June for the summer season.
        - the second subsession
            The second subsession runs from January to April for the regular
            season, and from July to August for the summer season.
    
    An offering of a course has a list of sessions, where each session
    corresponds to a specific subsession of a specific season. For example,
    an offering of a course that runs from September to April would have
    two sessions: one for the regular season's first subsession, and one
    for the regular season's second subsession.

    Instance Attributes:
        year: The year in which the season of the session starts.
            This is the year in which the first subsession of the season starts.
        season: The season of the session.
        subsession: The subsession of the session. Can be first, second, or whole.
    """
    year: int = fields.IntField(required=True, min_value=0, max_value=9999)  # type: ignore
    season: str = fields.StringField(required=True, choices=['regular', 'summer'])  # type: ignore
    subsession: str = fields.StringField(required=True, choices=['first', 'second', 'whole'])  # type: ignore

    def __init__(self, year: int, season: str, subsession: str, *args: Any, **kwargs: Any) -> None:
        """Initialize a session with the given year, season, and subsession.

        Args:
            year: The year of the session. Must be between 0 and 9999.
            season: The season of the session.
            subsession: The subsession of the session.
            
        Note:
            The year, season, and subsession are passed as positional arguments
            for convenience, but they are actually stored as keyword arguments
            in the `kwargs` dictionary. If `year`, `season`, or `subsession`
            are passed as keyword arguments, they will be ignored, meaning that
            the positional arguments always take precedence.
        """
        kwargs['year'] = year
        kwargs['season'] = season
        kwargs['subsession'] = subsession
        super().__init__(*args, **kwargs)
    
    @property
    def code(self) -> str:
        """Return the canonical representation of the session.

        The canonical representation of a session is a string whose format depends on the
        season of the session.

        Examples:
            >>> Session(2022, 'regular', 'first').code
            '20229'
            >>> Session(2022, 'regular', 'second').code
            '20231'
            >>> Session(2022, 'regular', 'whole').code
            '20229-20231'
            >>> Session(2023, 'summer', 'first').code
            '20235F'
            >>> Session(2023, 'summer', 'second').code
            '20235S'
            >>> Session(2023, 'summer', 'whole').code
            '20235'
        """
        assert self.season in ['regular', 'summer']

        if self.season == 'regular':
            if self.subsession == 'first':
                return f'{self.year}9'
            elif self.subsession == 'second':
                return f'{self.year}1'
            else:
                return f'{self.year}9-{self.year}1'
        else:
            if self.subsession == 'first':
                return f'{self.year}5F'
            elif self.subsession == 'second':
                return f'{self.year}5S'
            else:
                return f'{self.year}5'
        
    def __str__(self) -> str:
        """Return a string representation of the session."""
        return self.code
    
    @classmethod
    def from_code(cls, code: str) -> 'Session':
        """Return a session from its canonical representation.

        Args:
            code: The canonical representation of the session.
        
        Raises:
            ValueError: If the given code is not a valid session code.
        """
        if re.match(r'^\d{4}[9|1]$', code):
            return cls(int(code[:4]), 'regular', 'first' if code[4] == '9' else 'second')
        elif re.match(r'^\d{4}9-\d{4}1$', code):
            return cls(int(code[:4]), 'regular', 'whole')
        elif re.match(r'^\d{4}5(F|S)$', code):
            return cls(int(code[:4]), 'summer', 'first' if code[4] == 'F' else 'second')
        elif re.match(r'^\d{4}5$', code):
            return cls(int(code[:4]), 'summer', 'whole')
        else:
            raise ValueError(f'Invalid session code: {code}')
        

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

    schedule: int = fields.IntField(min_value=1, default=1)  # type: ignore

    @property
    def is_alternating(self) -> bool:
        """Whether this meeting does not regularly occur every week.

        A schedule is alternating (i.e. does not occur every week) if there is
        at least one week :math:`i` such that the :math:`i`-th bit is 0.

        Examples:
            >>> WeeklyRepetitionSchedule(schedule=0b1010).is_alternating
            True
            >>> WeeklyRepetitionSchedule(schedule=0b1111).is_alternating
            False
        """
        k = math.ceil(math.log2(self.schedule))
        return self.schedule > 1 and self.schedule != (1 << k) - 1

    @property
    def schedule_bits(self) -> str:
        """The binary representation of the schedule.

        Examples:
            >>> WeeklyRepetitionSchedule(schedule=0b1).schedule_bits
            '1'
            >>> WeeklyRepetitionSchedule(schedule=0b1010).schedule_bits
            '1010'
        """
        return bin(self.schedule)[2:]  # Remove the '0b' prefix

    @property
    def weeks(self) -> list[int]:
        """A list of the weeks in which this meeting occurs.

        Each week is represented as an integer between 1 and the number of
        weeks in a repeating period, inclusive. The weeks are sorted in
        ascending order.

        Examples:
            >>> WeeklyRepetitionSchedule(schedule=0b1).weeks
            [1]
            >>> WeeklyRepetitionSchedule(schedule=0b1010).weeks
            [2, 4]
        """
        return [i + 1 for i, bit in enumerate(reversed(self.schedule_bits)) if bit == '1']


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

    day: int = fields.IntField(required=True, min_value=0, max_value=6)  # type: ignore
    start_time: int = fields.IntField(required=True, min_value=0, max_value=86400000)  # type: ignore
    end_time: int = fields.IntField(required=True, min_value=0, max_value=86400000)  # type: ignore
    session: Session = fields.EmbeddedDocumentField(Session, required=True)  # type: ignore
    location: Location = fields.EmbeddedDocumentField(Location, null=True, default=None)  # type: ignore
    repetition_schedule: WeeklyRepetitionSchedule = fields.EmbeddedDocumentField(
        WeeklyRepetitionSchedule, default=WeeklyRepetitionSchedule)  # type: ignore


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

    first_name: str = fields.StringField(required=True)  # type: ignore
    last_name: str = fields.StringField(required=True)  # type: ignore


class EnrolmentInfo(EmbeddedDocument):
    """Enrolment information for a section.

    Instance Attributes:
        current_enrolment: The number of students currently enrolled in this
            section.
        max_enrolment: The maximum number of students that can be enrolled in
            this section.
        has_waitlist: Whether this section has a waitlist.
        current_waitlist_size: The number of students currently on the waitlist
            for this section.
        enrolment_indicator: A string representing the enrollment indicator
            for this section, or None if there is no enrollment indicator.
    """

    current_enrolment: Optional[int] = fields.IntField(null=True, min_value=0, default=None)  # type: ignore
    max_enrolment: Optional[int] = fields.IntField(null=True, min_value=0, default=None)  # type: ignore
    has_waitlist: bool = fields.BooleanField(default=False)  # type: ignore
    current_waitlist_size: Optional[int] = fields.IntField(null=True, min_value=0, default=None)  # type: ignore
    enrolment_indicator: Optional[str] = fields.StringField(null=True, default=None)  # type: ignore
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

    teaching_method: TeachingMethod = fields.EnumField(TeachingMethod, required=True)  # type: ignore
    section_number: str = fields.StringField(required=True)  # type: ignore
    meetings: list[SectionMeeting] = fields.EmbeddedDocumentListField('SectionMeeting', required=True)  # type: ignore
    instructors: list[Instructor] = fields.EmbeddedDocumentListField('Instructor', required=True)  # type: ignore
    delivery_modes: list[SectionDeliveryMode] = fields.ListField(
        fields.EnumField(SectionDeliveryMode), required=True)  # type: ignore
    subtitle: Optional[str] = fields.StringField(null=True, default=None)  # type: ignore
    cancelled: bool = fields.BooleanField(default=False)  # type: ignore
    enrolment_info: EnrolmentInfo = fields.EmbeddedDocumentField(EnrolmentInfo, default=EnrolmentInfo)  # type: ignore
    notes: list[str] = fields.ListField(fields.StringField(), default=list)  # type: ignore
    # TODO: Section dependencies. This should be represented as a graph, where
    # each node is a section and each edge is a dependency (which may or may not
    # be bidirectional).
    linked_sections: list[str] = fields.ListField(fields.StringField(), default=list)  # type: ignore

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


class CategoricalRequirement(EmbeddedDocument):
    """A breadth or distribution requirement.

    Instance Attributes:
        code: A unique code for this categorical requirement.
        type: The type of this categorical requirement. Either 'breadth' or
            'distribution'.
        name: The name of this categorical requirement.
        description: A description of this categorical requirement.
        institutions: A list of institutions where this categorical requirement
            applies. For example, a breadth requirement might only apply to
            students in the Faculty of Arts and Science, while a distribution
            requirement might apply to all students. There should be at least
            one institution in this list.
    """

    code: str = fields.StringField(unique=True, primary_key=True)  # type: ignore
    type: str = fields.StringField(required=True, choices=['breadth', 'distribution'])  # type: ignore
    name: str = fields.StringField()  # type: ignore
    description: str = fields.StringField()  # type: ignore
    institutions: list[Institution] = fields.ListField(
        fields.ReferenceField(Institution), required=True)  # type: ignore


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
        institution: The institution that offers this course. This is a sub-tree
            of the institution hierarchy.
        title: The title of this course. This is usually the same as the name.
        instruction_level: The level of instruction for this course.
            For example, undergraduate or graduate.
        categorical_requirements: Breadth and distribution requirements that this
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

    id: str = fields.StringField(primary_key=True)  # type: ignore
    code: str = fields.StringField()  # type: ignore
    name: str = fields.StringField()  # type: ignore
    sections: list[Section] = fields.EmbeddedDocumentListField('Section')  # type: ignore
    sessions: list[Session] = fields.EmbeddedDocumentListField('Session')  # type: ignore
    term: Term = fields.EnumField(Term)  # type: ignore
    credits: float = fields.FloatField()  # type: ignore
    institution: Institution = fields.ReferenceField(Institution)  # type: ignore
    # Metadata fields
    title: Optional[str] = fields.StringField(null=True, default=None)  # type: ignore
    instruction_level: Optional[InstructionLevel] = fields.EnumField(
        InstructionLevel, null=True, default=None)  # type: ignore
    description: Optional[str] = fields.StringField(null=True, default=None)  # type: ignore
    categorical_requirements: list[CategoricalRequirement] = fields.EmbeddedDocumentListField(
        CategoricalRequirement, default=list)  # type: ignore
    prerequisites: Optional[str] = fields.StringField(null=True, default=None)  # type: ignore
    corequisites: Optional[str] = fields.StringField(null=True, default=None)  # type: ignore
    exclusions: Optional[str] = fields.StringField(null=True, default=None)  # type: ignore
    recommended_preparation: Optional[str] = fields.StringField(null=True, default=None)  # type: ignore
    cancelled: bool = fields.BooleanField(default=False)  # type: ignore
    tags: list[str] = fields.ListField(fields.StringField(), default=list)  # type: ignore
    notes: list[str] = fields.ListField(fields.StringField(), default=list)  # type: ignore

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
