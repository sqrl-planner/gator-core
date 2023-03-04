"""Model definitions for data about an academic institution."""
from typing import Optional

from mongoengine import Document, EmbeddedDocument, fields


class Institution(Document):
    """An academic institution.

    This is represented as a recursive tree structure, where each institution
    can have multiple sub-institutions. For example, the University of Toronto
    is the parent institution of the St. George campus of the University of
    Toronto, which is the parent institution of many faculties and departments.

    Instance Attributes:
        code: A unique string representing this institution.
        name: The full name of this institution.
        type: The type of this institution. For example, `university` or
            `campus`.
        parent: The parent institution of this institution. For example, the
            University of Toronto is the parent institution of the St. George
            campus of the University of Toronto. If None, this institution is
            a top-level institution.
        sub_institutions: A list of institutions that are sub-institutions of
            this institution. For example, the St. George campus of the
            University of Toronto is a sub-institution of the University of
            Toronto.
    """

    code = fields.StringField(unique=True, primary_key=True)
    name = fields.StringField(required=True)
    type = fields.StringField(required=True)
    # Institution hierarchy
    parent = fields.ReferenceField('self', default=None)
    sub_institutions = fields.ListField(
        fields.ReferenceField('self'), default=list)


class Building(Document):
    """A building on a campus of the University of Toronto.

    Instance Attributes:
        code: A unique string code that identifies this building.
        institution: The institution that this building belongs to.
        name: The name of this building. Can be None if unknown.
        map_url: The URL of this building's map. Can be None if unknown.
    """

    code = fields.StringField(unique=True, primary_key=True)
    institution = fields.ReferenceField(Institution, required=True)
    name = fields.StringField(null=True, default=None)
    map_url = fields.URLField(null=True, default=None)


class Location(EmbeddedDocument):
    """A location on campus represented as a building-room pair.

    Instance Attributes:
        building: The building that the section meets in.
        room: The room that the section meets in, not including the building
            code.
    """

    building = fields.ReferenceField(Building, required=True)
    room = fields.StringField(required=True)
