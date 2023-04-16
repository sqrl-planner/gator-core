"""Model definitions for timetable data."""
import math
import re
from functools import lru_cache
from typing import Any, Optional

from mongoengine import Document, EmbeddedDocument, fields

from gator.core.models.common import SerializableEnum
from gator.core.models.institution import Institution, Location


class Session(EmbeddedDocument):
    """A formal division of the academic year.

    The academic year is divided into two seasons: the regular season, which
    runs from September to April, and the summer season, which runs from May
    to August.

    Each season is divided into two subsessions: the first subsession, which
    runs from September to December for the regular season, and from May to
    June for the summer season; and the second subsession, which runs from
    January to April for the regular season, and from July to August for the
    summer season. The whole subsession is the combination of the first and
    second subsessions (e.g. September to April for the regular season and
    May to August for the summer season).

    An offering of a course is associated with a list of sessions, where
    each session corresponds to a specific subsession of a specific season.
    For example, an offering of a course that runs from September to April
    would have two sessions: one for the regular season's first subsession,
    and one for the regular season's second subsession.

    Instance Attributes:
        year: The year in which the season of the session starts. This is the
            year in which the first subsession of the season starts.
        season: The season of the session.
        subsession: The subsession of the session. Can be first, second, or whole.
    """

    # Private Class Attributes:
    #   _SUBSESSION_MAP: A mapping from season name to a mapping from subsession
    #       name to its code (canonical representation).
    #   _INVERSE_SUBSESSION_MAP: The inverse of `_SUBSESSION_MAP`. A mapping
    #       from season name to a mapping from subsession code to its name.
    #   _SUBSESSION_TO_SEASON_MAP: A mapping from subsession code to season
    #       name.
    #   _SEASON_ORDER: A mapping from season name to its sort order.
    #   _SUBSESSION_ORDER: A mapping from subsession name to its sort order.
    _SUBSESSION_MAP: dict[str, dict[str, str]] = {
        'regular': {'first': '9', 'second': '1'},
        'summer': {'first': '5F', 'second': '5S', 'whole': '5'}
    }
    _INVERSE_SUBSESSION_MAP: dict[str, dict[str, str]] = {
        s: {v: k for k, v in d.items()} for s, d in _SUBSESSION_MAP.items()
    }
    _SUBSESSION_TO_SEASON_MAP: dict[str, str] = {
        v: k for k, d in _SUBSESSION_MAP.items() for v in d.values()
    }
    _SEASON_ORDER: dict[str, int] = {
        'regular': 0,
        'summer': 1
    }
    _SUBSESSION_ORDER: dict[str, int] = {
        'first': 0,
        'second': 1,
        'whole': 2
    }

    year: int = fields.IntField(required=True, min_value=0)  # type: ignore
    season: str = fields.StringField(
        required=True, choices=['regular', 'summer'])  # type: ignore
    subsession: str = fields.StringField(
        required=True, choices=['first', 'second', 'whole'])  # type: ignore

    def __init__(self, year: int, season: str, subsession: str, *args: Any, **kwargs: Any) -> None:
        """Initialize a session with the given year, season, and subsession.

        Args:
            year: The year of the session.
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

        The canonical representation of a session is a string that uniquely
        identifies the subsession for a given season in a given year in
        accordance with the University of Toronto's academic calendar.

        For non-whole subsessions, this representation is a string of the form
        `YYYYX`, where `YYYY` is the year of the session, and `X` is the
        subsession code of the session. The subsession code is a unique
        identifier for the subsession of the session, and is defined as
        follows:
            - `9` for the first (fall) subsession of the regular season.
            - `1` for the second (winter) subsession of the regular season.
            - `5F` for the first subsession of the summer season.
            - `5S` for the second subsession of the summer season.
            - `5` for the whole subsession of the summer season.

        The whole (fall-winter) subsession of the regular season is a special
        case, and is represented as a range of two sessions, one for the first
        subsession (in year :math:`Y`) and one for the second subsession (in
        year :math:`Y+1`), separated by a hyphen. For example, the whole
        subsession of the regular season in 2022 is represented as the string
        `20229-20231`.

        Remarks:
            - Years will be zero-padded up to four digits. For example, the
                year 2022 will be represented as `2022`, and the year 1 will be
                represented as `0001`.

        Examples:
            >>> Session(2022, 'regular', 'first').code  # Fall 2022
            '20229'
            >>> Session(2023, 'regular', 'second').code  # Winter 2023
            '20231'
            >>> Session(2022, 'regular', 'whole').code  # Fall 2022 - Winter 2023
            '20229-20231'
            >>> Session(2023, 'summer', 'first').code  # Summer 2023 (First Subsession)
            '20235F'
            >>> Session(2023, 'summer', 'second').code  # Summer 2023 (Second Subsession)
            '20235S'
            >>> Session(2023, 'summer', 'whole').code  # Summer 2023 (Whole Session)
            '20235'
        """
        if self.season == 'regular' and self.subsession == 'whole':
            # Recursively call the code property on the first and second
            return '-'.join([
                Session(self.year, self.season, 'first').code,
                Session(self.year + 1, self.season, 'second').code
            ])

        year = str(self.year).zfill(4)
        return f'{year}{self._SUBSESSION_MAP[self.season][self.subsession]}'

    @property
    def human_str(self) -> str:
        """A human-readable representation of this session.

        Examples:
            >>> Session(2022, 'regular', 'first').human_str  # Fall 2022
            'Fall 2022'
            >>> Session(2023, 'regular', 'second').human_str  # Winter 2023
            'Winter 2023'
            >>> Session(2022, 'regular', 'whole').human_str  # Fall 2022 - Winter 2023
            'Fall 2022 - Winter 2023'
            >>> Session(2023, 'summer', 'first').human_str  # Summer 2023 (First Subsession)
            'Summer 2023 (First Subsession)'
            >>> Session(2023, 'summer', 'second').human_str  # Summer 2023 (Second Subsession)
            'Summer 2023 (Second Subsession)'
            >>> Session(2023, 'summer', 'whole').human_str  # Summer 2023 (Whole Session)
            'Summer 2023 (Whole Session)'
        """
        if self.season == 'regular' and self.subsession == 'whole':
            # Recursively call the human_str property on the first and second
            return ' - '.join([
                Session(self.year, self.season, 'first').human_str,
                Session(self.year + 1, self.season, 'second').human_str,
            ])

        subsession = {
            'regular': {
                'first': 'Fall %s',
                'second': 'Winter %s'
            },
            'summer': {
                'first': 'Summer %s (First Subsession)',
                'second': 'Summer %s (Second Subsession)',
                'whole': 'Summer %s (Whole Session)',
            },
        }[self.season][self.subsession]
        return subsession % str(self.year).zfill(4)

    def __str__(self) -> str:
        """Return a string representation of the session."""
        return self.code

    def __repr__(self) -> str:
        """Return a string representation of the session."""
        return f'Session({self.year}, {self.season!r}, {self.subsession!r})'

    def __eq__(self, other: 'Session') -> bool:
        """Return whether this session is the same as another session.

        Equality is defined as having the same year, season, and subsession.

        Examples:
            >>> Session(2022, 'regular', 'first') == Session(2022, 'regular', 'first')
            True
            >>> Session(1999, 'summer', 'whole') == Session(1999, 'summer', 'whole')
            True
            >>> Session(2022, 'regular', 'first') == Session(2022, 'regular', 'second')
            False
            >>> Session(2022, 'regular', 'first') == Session(2022, 'summer', 'first')
            False
        """
        return all([
            self.year == other.year,
            self.season == other.season,
            self.subsession == other.subsession,
        ])

    def __ne__(self, other: 'Session') -> bool:
        """Return whether this session is not the same as another session.

        Remarks:
            This is the inverse of the :meth:`__eq__` method. See the
            documentation of that method for more details.
        """
        return not self == other

    def __lt__(self, other: 'Session') -> bool:
        """Return whether this session occurs before the other session.

        A session occurs before another if it is in an earlier year, same year
        but in an earlier season (i.e. regular before summer), or same year and
        season but in an earlier subsession (i.e. first before second or whole).

        Examples:
            >>> Session(2022, 'regular', 'first') < Session(2022, 'regular', 'second')
            True
            >>> Session(2022, 'regular', 'second') < Session(2022, 'regular', 'whole')
            True
            >>> Session(2022, 'regular', 'first') < Session(2022, 'summer', 'first')
            True
            >>> Session(2022, 'regular', 'first') < Session(2023, 'regular', 'first')
            True
            >>> Session(2022, 'regular', 'first') < Session(2022, 'regular', 'first')
            False
        """
        return any([
            # This session is in an EARLIER YEAR
            self.year < other.year,
            # This session is in the SAME YEAR but in an EARLIER SEASON
            all([
                self.year == other.year,
                self._SEASON_ORDER[self.season] < self._SEASON_ORDER[other.season]
            ]),
            # This session is in the SAME YEAR and SEASON but in an EARLIER SUBSESSION
            all([
                self.year == other.year,
                self._SEASON_ORDER[self.season] == self._SEASON_ORDER[other.season],
                self._SUBSESSION_ORDER[self.subsession] < self._SUBSESSION_ORDER[other.subsession]
            ])
        ])

    def __le__(self, other: 'Session') -> bool:
        """Return whether this session occurs before or at the same time as another session."""
        return self < other or self == other

    def __gt__(self, other: 'Session') -> bool:
        """Return whether this session occurs after the other session.

        Remarks:
            This is the inverse of the :meth:`__lt__` method. See the
            documentation of that method for more details.
        """
        return not self < other

    def __ge__(self, other: 'Session') -> bool:
        """Return whether this session occurs after or at the same time as another session."""
        return self > other or self == other

    @classmethod
    def from_code(cls, code: str) -> 'Session':
        """Return a session from its canonical representation.

        Args:
            code: The canonical representation of the session. This is case
                insensitive as the input will be converted to uppercase.

        Raises:
            ValueError: If the given code is invalid or malformed.

        Examples:
            >>> Session.from_code('20229')  # Fall 2022
            Session(2022, 'regular', 'first')
            >>> Session.from_code('20231')  # Winter 2023
            Session(2023, 'regular', 'second')
            >>> Session.from_code('20229-20231')  # Fall 2022 - Winter 2023
            Session(2022, 'regular', 'whole')
            >>> Session.from_code('20235F')  # Summer 2023 (First Subsession)
            Session(2023, 'summer', 'first')
            >>> Session.from_code('20235S')  # Summer 2023 (Second Subsession)
            Session(2023, 'summer', 'second')
            >>> Session.from_code('20235')  # Summer 2023 (Whole Session)
            Session(2023, 'summer', 'whole')
        """
        if '-' in code:
            start, end = (cls.from_code(c) for c in code.split('-'))
            # Ensure that the start and end sessions are consecutive;
            # in the same season; and the subsessions are consecutive
            if start.year != end.year - 1 or start.season != end.season or \
                    start.subsession != 'first' or end.subsession != 'second':
                raise ValueError(f'Invalid session code: {code}')

            return cls(start.year, start.season, 'whole')

        # Validate the code (must be 4 digits followed by a subsession code)
        code = code.upper()
        all_subsession_codes = [code for v in cls._SUBSESSION_MAP.values() for code in v.values()]
        quoted_subsession_codes = [f'"{code}"' for code in all_subsession_codes]
        if not re.match(fr'^\d{{4}}(?:{"|".join(all_subsession_codes)})$', code):
            raise ValueError(
                f'invalid session code: {code}; expected a 4-digit year '
                f'followed by one of the following subsession codes: '
                f'{", ".join(quoted_subsession_codes)}')

        # Get the year from the code
        year = int(code[:4])
        # Get the subsession code from the code
        subsession_code = code[4:]
        # Get the season and subsession from the subsession code
        # These are guaranteed to exist because of the validation above
        season = cls._SUBSESSION_TO_SEASON_MAP[subsession_code]
        subsession = cls._INVERSE_SUBSESSION_MAP[season][subsession_code]
        return cls(year, season, subsession)


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
            of milliseconds since midnight (00:00:00).
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
        linked_sections: A list of sections that are linked to this section.
            These are strings of the form 'LEC 001' or 'TUT 001' (i.e. teaching
            method and section number).
    """

    teaching_method: TeachingMethod = fields.EnumField(TeachingMethod, required=True)  # type: ignore
    section_number: str = fields.StringField(required=True)  # type: ignore
    meetings: list[SectionMeeting] = fields.EmbeddedDocumentListField('SectionMeeting', default=list)  # type: ignore
    instructors: list[Instructor] = fields.EmbeddedDocumentListField('Instructor', default=list)  # type: ignore
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

    code: str = fields.StringField(primary_key=True)  # type: ignore
    type: str = fields.StringField(required=True, choices=['breadth', 'distribution'])  # type: ignore
    name: str = fields.StringField()  # type: ignore
    description: str = fields.StringField()  # type: ignore
    institutions: list[Institution] = fields.ListField(
        fields.ReferenceField(Institution), required=True)  # type: ignore


class Course(Document):
    """An instance of a course offered at UofT for a specific term.

    Instance Attributes:
        uuid: A unique identifier for this course.
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

    uuid: str = fields.StringField(primary_key=True)  # type: ignore
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
