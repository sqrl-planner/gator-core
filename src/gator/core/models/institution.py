"""Model definitions for data about an academic institution."""
from queue import Queue
from typing import Any, List, Optional

import gator._vendor.hooky as hooky
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
        type: The type of this institution. For example, `university` or
            `campus`.
        name: The full name of this institution. Can be None if the name is
            unknown.
        parent: The parent institution of this institution. For example, the
          University of Toronto is the parent institution of the St. George
          campus of the University of Toronto. If None, this institution is
          a top-level institution.
    """

    code: str = fields.StringField(primary_key=True)  # type: ignore
    type: str = fields.StringField(required=True)  # type: ignore
    name: Optional[str] = fields.StringField(null=True)  # type: ignore
    parent: Optional['Institution'] = fields.ReferenceField(
        'self',
        default=None,
        reverse_delete_rule=mongoengine.NULLIFY
    )  # type: ignore

    @property
    def sub_institutions(self) -> List['Institution']:
        """A list of sub-institutions of this institution.

        This will perform a database query to find all institutions whose
        parent is this institution.

        Returns:
            A list of sub-institutions of this institution, or an empty list if
            this institution has no sub-institutions.
        """
        return list(Institution.objects(parent=self))

    def find_children(self, institution_type: str) -> list['Institution']:
        """Find all sub-institutions of the given type.

        This function recursively searches through all sub-institutions of this
        institution, performing a queue-based breadth-first search, and returns
        a list of all institutions of the given type.

        Args:
            institution_type: The type of institution to search for. For
                example, `university` or `campus`.

        Returns:
            A list of institutions of the given type, not including this
            institution (even if this institution is of type `institution_type`).
        """
        q = Queue()
        q.put(self)

        visited = set()
        children = []

        while not q.empty():
            curr = q.get()
            if curr.code in visited:
                continue
            visited.add(curr.code)

            if curr.type == institution_type:
                children.append(curr)

            for sub_inst in curr.sub_institutions:
                q.put(sub_inst)

        return children

    def find_parent(self, institution_type: str) -> Optional['Institution']:
        """Find the first (closest) parent institution of the given type.

        This function recursively searches through all parent institutions of
        this institution, performing a queue-based breadth-first search, and
        returns the first institution of the given type. This function does not
        include this institution in the search.

        Args:
            institution_type: The type of institution to search for. For
                example, `university` or `campus`.

        Returns:
            The first (closest) parent institution of the given type, or None
            if no such institution exists. It is guaranteed that the returned
            institution is not this institution, even if this institution is of
            type `institution_type`.
        """
        q = Queue()
        q.put(self)

        visited = set()

        while not q.empty():
            curr = q.get()
            if curr.code in visited:
                continue
            visited.add(curr.code)

            if curr.type == institution_type and curr != self:
                return curr

            if curr.parent is not None:
                q.put(curr.parent)

        return None

    def print_hierarchy(self) -> None:
        """Visualize this institution's hierarchy as a tree.

        This function prints a tree representation of this institution's
        hierarchy starting from this institution.

        Examples:
            >>> uoft = Institution(code='uoft', name='University of Toronto', type='university').save()
            >>> stgeorge = Institution(code='stgeorge', name='St. George', type='campus', parent=uoft).save()
            >>> uoft.print_hierarchy()
            University of Toronto (uoft, university)
            └── St. George (stgeorge, campus)

            >>> artsci = Institution(code='artsci', name='Faculty of Arts and Science', type='faculty', parent=stgeorge).save()
            >>> cs = Institution(code='cs', name='Department of Computer Science', type='department', parent=artsci).save()
            >>> uoft.print_hierarchy()
            University of Toronto (uoft, university)
            └── St. George (stgeorge, campus)
                └── Faculty of Arts and Science (artsci, faculty)
                    └── Department of Computer Science (cs, department)

            >>> utm = Institution(code='utm', name='Mississauga', type='campus', parent=uoft).save()
            >>> uoft.print_hierarchy()
            University of Toronto (uoft, university)
            ├── St. George (stgeorge, campus)
            │   └── Faculty of Arts and Science (artsci, faculty)
            │       └── Department of Computer Science (cs, department)
            └── Mississauga (utm, campus)

            >>> mat_at_utm = Institution(code='mat_at_utm', name='Department of Mathematics', type='department', parent=utm).save()
            >>> uoft.print_hierarchy()
            University of Toronto (uoft, university)
            ├── St. George (stgeorge, campus)
            │   └── Faculty of Arts and Science (artsci, faculty)
            │       └── Department of Computer Science (cs, department)
            └── Mississauga (utm, campus)
                └── Department of Mathematics (mat_at_utm, department)
        """
        def _helper(institution: 'Institution', prefix: str = '',
                    is_last: bool = True) -> None:
            """Print the hierarchy starting from the given institution.

            Args:
                institution: The root of the institution hierarchy.
                prefix: The prefix to print before the root institution's name.
                is_last: Whether this institution is the last child of its
                    parent.
            """
            has_parent = institution.parent is not None
            if has_parent:
                print(f'{prefix}└── ' if is_last else f'{prefix}├── ', end='')
                prefix += '    ' if is_last else '│   '

            print(str(institution))

            for i, sub_inst in enumerate(institution.sub_institutions):
                _helper(
                    sub_inst,
                    prefix=prefix,
                    is_last=i == len(institution.sub_institutions) - 1
                )

        _helper(self)

    def __str__(self) -> str:
        """Return a string representation of this institution.

        Returns:
            A string representation of this institution.
        """
        return f'{self.name} ({self.code}, {self.type})'

    def __repr__(self) -> str:
        """Return a string representation of this institution.

        Returns:
            A string representation of this institution.

        Examples:
            >>> uoft = Institution(code='uoft', name='University of Toronto', type='university')
            >>> repr(uoft)
            "Institution(code='uoft', name='University of Toronto', type='university', parent=None)"
        """
        parent_code = self.parent.code if self.parent is not None else None
        return f'Institution(code={self.code!r}, name={self.name!r}, ' \
            f'type={self.type!r}, parent={parent_code!r})'


class Building(Document):
    """A building on a campus of the University of Toronto.

    Instance Attributes:
        code: A unique string code that identifies this building.
        institution: The institution that this building belongs to.
        name: The name of this building. Can be None if unknown.
        map_url: The URL of this building's map. Can be None if unknown.
    """

    code: str = fields.StringField(primary_key=True)  # type: ignore
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
