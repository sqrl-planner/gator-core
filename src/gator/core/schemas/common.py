"""Marshmallow schemas for common models."""
from typing import Any

from marshmallow import Schema, fields, post_load

from gator.core.models.common import Time


class TimeSchema(Schema):
    """Marshmallow schema for the Time model."""

    hour = fields.Integer(required=True)
    minute = fields.Integer(required=True)

    @post_load
    def make_time(self, data: dict, **_: Any) -> Time:
        """Create a SectionMeeting object."""
        return Time(**data)
