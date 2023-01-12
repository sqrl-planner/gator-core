"""Marshmallow schemas for timetable models."""
from typing import Any

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField

from gator.models.timetable import (Campus, Course, CourseTerm, Instructor,
                                    MeetingDay, Organisation, Section,
                                    SectionDeliveryMode, SectionMeeting,
                                    SectionTeachingMethod)
from gator.schemas.common import TimeSchema


class SectionMeetingSchema(Schema):
    """Marshmallow schema for SectionMeeting model."""

    day = EnumField(MeetingDay, required=True)
    start_time = fields.Nested(TimeSchema, required=True)
    end_time = fields.Nested(TimeSchema, required=True)
    assigned_room_1 = fields.String(load_default=None)
    assigned_room_2 = fields.String(load_default=None)

    @post_load
    def make_section_meeting(self, data: dict, **_: Any) -> SectionMeeting:
        """Create a SectionMeeting object."""
        return SectionMeeting(**data)


class InstructorSchema(Schema):
    """Marshmallow schema for Instructor model."""

    first_name = fields.String(required=True)
    last_name = fields.String(required=True)

    @post_load
    def make_instructor(self, data: dict, **_: Any) -> Instructor:
        """Create a Instructor object."""
        return Instructor(**data)


class SectionSchema(Schema):
    """Marshmallow schema for Section model."""

    teaching_method = EnumField(SectionTeachingMethod, load_default=None)
    section_number = fields.String(required=True)
    subtitle = fields.String(load_default=None)
    instructors = fields.Nested(InstructorSchema, many=True)
    meetings = fields.Nested(SectionMeetingSchema, many=True)
    delivery_mode = EnumField(SectionDeliveryMode, load_default=None)
    cancelled = fields.Boolean()
    has_waitlist = fields.Boolean()
    enrolment_capacity = fields.Integer(load_default=None)
    actual_enrolment = fields.Integer(load_default=None)
    actual_waitlist = fields.Integer(load_default=None)
    enrolment_indicator = fields.String(load_default=None)

    @post_load
    def make_section(self, data: dict, **_: Any) -> Section:
        """Create a Section object."""
        return Section(**data)


class OrganisationSchema(Schema):
    """Marshmallow schema for Organisation model."""

    code = fields.String(required=True)
    name = fields.String(required=True)
    campus = EnumField(Campus, required=True)

    @post_load
    def make_organisation(self, data: dict, **_: Any) -> Organisation:
        """Create a Organisation object."""
        return Organisation(**data)


class CourseSchema(Schema):
    """Marshmallow schema for Course model."""

    id = fields.String(required=True)
    organisation = fields.Nested(OrganisationSchema)
    code = fields.String()
    title = fields.String()
    description = fields.String()
    term = EnumField(CourseTerm)
    session_code = fields.String()
    sections = fields.Nested(SectionSchema, many=True)
    prerequisites = fields.String()
    corequisites = fields.String()
    exclusions = fields.String()
    recommended_preparation = fields.String()
    breadth_categories = fields.String()
    distribution_categories = fields.String()
    web_timetable_instructions = fields.String()
    delivery_instructions = fields.String()
    campus = EnumField(Campus)

    @post_load
    def make_course(self, data: dict, **_: Any) -> Course:
        """Create a Course object."""
        return Course(**data)
