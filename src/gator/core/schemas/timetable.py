"""Marshmallow schemas for timetable models.

Autogenerated with marshmallow-mongoengine.
"""
from marshmallow import EXCLUDE, fields
from marshmallow_mongoengine import ModelSchema

import gator.core.models.timetable as timetable


class SessionSchema(ModelSchema):
    """Marshmallow schema for the :class:`Session` model."""

    class Meta:
        """Meta class for SessionSchema."""

        model = timetable.Session


class WeeklyRepetitionScheduleSchema(ModelSchema):
    """Marshmallow schema for the :class:`WeeklyRepetitionSchedule` model."""

    class Meta:
        """Meta class for WeeklyRepetitionScheduleSchema."""

        model = timetable.WeeklyRepetitionSchedule
        # Exclude unknown fields so that we can add the 'schedule_bits' and
        # 'is_alternating' fields without breaking the API. We want these
        # fields to be present when dumping the data, but we don't want to
        # allow them to be set when loading the data (as they are derived from
        # the 'schedule' field and are not actually stored in the database).
        unknown = EXCLUDE

    schedule_bits = fields.String(dump_only=True)
    is_alternating = fields.Boolean(dump_only=True)
    weeks = fields.List(fields.Integer(), dump_only=True)


class SectionMeetingSchema(ModelSchema):
    """Marshmallow schema for the :class:`SectionMeeting` model."""

    class Meta:
        """Meta class for SectionMeetingSchema."""

        model = timetable.SectionMeeting

    repetition_schedule = fields.Nested(WeeklyRepetitionScheduleSchema)


class InstructorSchema(ModelSchema):
    """Marshmallow schema for the :class:`Instructor` model."""

    class Meta:
        """Meta class for InstructorSchema."""

        model = timetable.Instructor


class EnrolmentInfoSchema(ModelSchema):
    """Marshmallow schema for the :class:`EnrolmentInfo` model."""

    class Meta:
        """Meta class for EnrolmentInfoSchema."""

        model = timetable.EnrolmentInfo


class SectionSchema(ModelSchema):
    """Marshmallow schema for the :class:`Section` model."""

    class Meta:
        """Meta class for SectionSchema."""

        model = timetable.Section

    meetings = fields.Nested(SectionMeetingSchema, many=True)


class CategoricalRequirementSchema(ModelSchema):
    """Marshmallow schema for the :class:`CategoricalRequirement` model."""

    class Meta:
        """Meta class for CategoricalRequirementSchema."""

        model = timetable.CategoricalRequirement


class CourseSchema(ModelSchema):
    """Marshmallow schema for the :class:`Course` model."""

    class Meta:
        """Meta class for CourseSchema."""

        model = timetable.Course

    sections = fields.Nested(SectionSchema, many=True)
