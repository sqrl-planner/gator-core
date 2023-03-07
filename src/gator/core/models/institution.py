"""Model definitions for data about an academic institution."""
from typing import Optional

import mongoengine
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

    code: str = fields.StringField(unique=True, primary_key=True)  # type: ignore
    name: str = fields.StringField(required=True)  # type: ignore
    type: str = fields.StringField(required=True)  # type: ignore
    # Institution hierarchy
    parent: 'Institution' = fields.ReferenceField('self', default=None, reverse_delete_rule=mongoengine.NULLIFY)  # type: ignore
    sub_institutions: list['Institution'] = fields.ListField(
        fields.ReferenceField('self'), default=list, reverse_delete_rule=mongoengine.NULLIFY)  # type: ignore


class Building(Document):
    """A building on a campus of the University of Toronto.

    Instance Attributes:
        code: A unique string code that identifies this building.
        institution: The institution that this building belongs to.
        name: The name of this building. Can be None if unknown.
        map_url: The URL of this building's map. Can be None if unknown.
    """

    code: str = fields.StringField(unique=True, primary_key=True)  # type: ignore
    institution: Institution = fields.ReferenceField(Institution, required=True)  # type: ignore
    name: Optional[str] = fields.StringField(null=True, default=None)  # type: ignore
    map_url: Optional[str] = fields.URLField(null=True, default=None)  # type: ignore


class Location(EmbeddedDocument):
    """A location on campus represented as a building-room pair.

    Instance Attributes:
        building: The building that the section meets in.
        room: The room that the section meets in, not including the building
            code.
    """

    building: Building = fields.ReferenceField(Building, required=True)  # type: ignore
    room: str = fields.StringField(required=True)  # type: ignore
