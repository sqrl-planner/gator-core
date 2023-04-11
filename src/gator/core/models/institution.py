"""Model definitions for data about an academic institution."""
from queue import Queue
from typing import Any, List, Optional

import gator._vendor.hooky as hooky
import mongoengine
from mongoengine import Document, EmbeddedDocument, fields


class _SubInstitutionsList(hooky.List, List['Institution']):
    """A list of sub-institutions for a wrapped institution.

    This list is used to ensure that the parent of each sub-institution is
    updated when the list is modified. This is done by intercepting calls to
    `append` and `remove`.
    """

    # Private Instance Attributes:
    #   _institution: The wrapped institution whose sub-institutions this list
    #       represents.
    _institution: 'Institution'

    def __init__(self, institution: 'Institution', **kwargs: Any) -> None:
        """Initialize a list of sub-institutions.

        Args:
            institution: The wrapped institution whose sub-institutions this
                list represents.
        """
        self._institution = institution
        super().__init__(self._institution._sub_institutions, **kwargs)

    def _after_add(self, key: Any, item: Any) -> None:
        """Call after an item is added to the list.

        This will set the parent of the added institution to the institution
        that this list was created for.
        """
        super()._after_add(key, item)
        assert isinstance(key, int), 'Only integer keys are allowed'
        assert isinstance(item, Institution), 'Only institutions are allowed'
        item.parent = self._institution

    def _after_del(self, key: Any, item: Any) -> None:
        """Call after an item is removed from the list.

        This will set the parent of the removed institution to None.
        """
        super()._after_del(key, item)
        assert isinstance(key, int), 'Only integer keys are allowed'
        assert isinstance(item, Institution), 'Only institutions are allowed'
        item.parent = None


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
    """

    code: str = fields.StringField(unique=True, primary_key=True)  # type: ignore
    name: str = fields.StringField(required=True)  # type: ignore
    type: str = fields.StringField(required=True)  # type: ignore

    # Private Instance Attributes:
    #   _parent: The parent institution of this institution. For example, the
    #       University of Toronto is the parent institution of the St. George
    #       campus of the University of Toronto. If None, this institution is
    #       a top-level institution.
    #   _sub_institutions: A list of institutions that are sub-institutions of
    #       this institution. For example, the St. George campus of the
    #       University of Toronto is a sub-institution of the University of
    #       Toronto.
    _parent: Optional['Institution'] = fields.ReferenceField(
        'self',
        default=None,
        reverse_delete_rule=mongoengine.NULLIFY
    )  # type: ignore
    _sub_institutions: list['Institution'] = fields.ListField(
        fields.ReferenceField('self'),
        default=list,
        reverse_delete_rule=mongoengine.NULLIFY
    )  # type: ignore

    def __init__(self, **kwargs: Any) -> None:
        """Initialize an institution."""
        # Prefer the parent and sub-institutions arguments over the
        # _parent and _sub_institutions arguments
        parent = kwargs.pop('parent', None)
        if parent is None:
            parent = kwargs.pop('_parent', None)

        sub_institutions = kwargs.pop('sub_institutions', [])
        if not sub_institutions:
            sub_institutions = kwargs.pop('_sub_institutions', [])

        super().__init__(**kwargs)

        # Set the parent and sub-institutions
        self.parent = parent
        for sub_inst in sub_institutions:
            self.sub_institutions.append(sub_inst)

    @property
    def parent(self) -> Optional['Institution']:
        """Get the parent of this institution."""
        return self._parent

    @parent.setter
    def parent(self, new_parent: Optional['Institution']) -> None:
        """Set the parent of this institution.

        Args:
            new_parent: The new parent of this institution. If None, this
                institution will become a top-level institution.

        Examples:
            >>> foo = Institution(code='foo', name='Foo', type='university')
            >>> bar = Institution(code='bar', name='Bar', type='campus')
            >>> baz = Institution(code='baz', name='Baz', type='department')
            >>> bar.parent = foo
            >>> baz.parent = foo
            >>> bar.parent  # doctest: +ELLIPSIS
            Institution(code='foo', ...)
            >>> baz.parent  # doctest: +ELLIPSIS
            Institution(code='foo', ...)
            >>> foo.sub_institutions  # doctest: +ELLIPSIS
            [Institution(code='bar', ...), Institution(code='baz', ...)]
        """
        old_parent = self.parent
        if old_parent is not None:
            # Remove this institution from the old parent's list of
            # sub-institutions
            old_parent._sub_institutions.remove(self)

        self._parent = new_parent
        if new_parent is not None:
            # Add this institution to the new parent's list of sub-institutions
            new_parent._sub_institutions.append(self)

    @property
    def sub_institutions(self) -> _SubInstitutionsList:
        """Get the sub-institutions of this institution.

        >>> foo = Institution(code='foo', name='Foo', type='university')
        >>> bar = Institution(code='bar', name='Bar', type='campus')
        >>> baz = Institution(code='baz', name='Baz', type='department')
        >>> foo.sub_institutions.append(bar)
        >>> foo.sub_institutions.append(baz)
        >>> foo.sub_institutions  # doctest: +ELLIPSIS
        [Institution(code='bar', ...), Institution(code='baz', ...)]
        >>> bar.parent  # doctest: +ELLIPSIS
        Institution(code='foo', ...)
        >>> baz.parent  # doctest: +ELLIPSIS
        Institution(code='foo', ...)
        """
        return _SubInstitutionsList(self, hook_when_init=False)

    @sub_institutions.setter
    def sub_institutions(self, new_sub_institutions: list['Institution']) \
            -> None:
        """Set the sub-institutions of this institution.

        Args:
            new_sub_institutions: The new sub-institutions of this
                institution.
        """
        self._sub_institutions.clear()
        for sub_inst in new_sub_institutions:
            self.sub_institutions.append(sub_inst)

    def find_children(self, institution_type: str) -> list['Institution']:
        """Find all sub-institutions of the given type.

        This function recursively searches through all sub-institutions of this
        institution, performing a queue-based breadth-first search, and returns
        a list of all institutions of the given type.

        Args:
            institution_type: The type of institution to search for. For
                example, `university` or `campus`.

        Returns:
            A list of institutions of the given type.
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
        """Find the first strictly parent institution of the given type.

        This function recursively searches through all parent institutions of
        this institution, performing a queue-based breadth-first search, and
        returns the first institution of the given type. This function does not
        include this institution in the search.

        Args:
            institution_type: The type of institution to search for. For
                example, `university` or `campus`.

        Returns:
            The first (closest) parent institution of the given type, or None
            if no such institution exists.
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
            >>> uoft = Institution(code='uoft', name='University of Toronto', type='university')
            >>> stgeorge = Institution(code='stgeorge', name='St. George', type='campus', parent=uoft)
            >>> uoft.print_hierarchy()
            University of Toronto (uoft, university)
            └── St. George (stgeorge, campus)

            >>> artsci = Institution(code='artsci', name='Faculty of Arts and Science', type='faculty', parent=stgeorge)
            >>> cs = Institution(code='cs', name='Department of Computer Science', type='department', parent=artsci)
            >>> uoft.print_hierarchy()
            University of Toronto (uoft, university)
            └── St. George (stgeorge, campus)
                └── Faculty of Arts and Science (artsci, faculty)
                    └── Department of Computer Science (cs, department)

            >>> utm = Institution(code='utm', name='Mississauga', type='campus', parent=uoft)
            >>> uoft.print_hierarchy()
            University of Toronto (uoft, university)
            ├── St. George (stgeorge, campus)
            │   └── Faculty of Arts and Science (artsci, faculty)
            │       └── Department of Computer Science (cs, department)
            └── Mississauga (utm, campus)

            >>> mat_at_utm = Institution(code='mat_at_utm', name='Department of Mathematics', type='department', parent=utm)
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
            "Institution(code='uoft', name='University of Toronto', type='university', parent=None, sub_institutions=[])"
        """
        parent_code = self.parent.code if self.parent is not None else None
        sub_inst_codes = [inst.code for inst in self.sub_institutions]
        return f'Institution(code={self.code!r}, name={self.name!r}, ' \
            f'type={self.type!r}, parent={parent_code!r}, ' \
            f'sub_institutions={sub_inst_codes!r})'


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
