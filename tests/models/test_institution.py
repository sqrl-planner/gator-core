"""Test the :mod:`gator.core.models.institution` module."""
from typing import Optional

import pytest

import gator.core.models.institution as institution


class TestSubInstitutionsList:
    """Test the :class:`gator.core.models.institution._SubInstitutionsList` class."""

    @classmethod
    @pytest.fixture
    def parent_inst(cls) -> institution.Institution:
        """Return a parent institution."""
        return institution.Institution(code='p', name='p', type='uni')

    @classmethod
    @pytest.fixture
    def child_insts(cls) -> list[institution.Institution]:
        """Return a list of child institutions."""
        return [
            institution.Institution(code=f'c{i}', name=f'c{i}', type='uni')
            for i in range(5)
        ]

    @classmethod
    @pytest.fixture
    def child_inst(cls) -> institution.Institution:
        """Return a child institution."""
        return institution.Institution(code='c', name='c', type='uni')

    def test_append(self, parent_inst: institution.Institution,
                    child_inst: institution.Institution) -> None:
        """Test appending to the list.

        Expect that the given `child_inst` is added to the sub-institutions
        list of `parent_inst` and that the parent of `child_inst` is set to
        `parent_inst`.
        """
        sub_inst_list = institution._SubInstitutionsList(parent_inst)
        sub_inst_list.append(child_inst)

        assert child_inst in parent_inst.sub_institutions
        assert child_inst.parent == parent_inst

    def test_extend(self, parent_inst: institution.Institution,
                    child_insts: list[institution.Institution]) -> None:
        """Test extending the list.

        Expect that the given `child_insts` are added to the sub-institutions
        list of `parent_inst` and that the parent of each `child_inst` is set to
        `parent_inst`.
        """
        sub_inst_list = institution._SubInstitutionsList(parent_inst)
        sub_inst_list.extend(child_insts)

        for child_inst in child_insts:
            assert child_inst in parent_inst.sub_institutions
            assert child_inst.parent == parent_inst

    def test_insert(self, parent_inst: institution.Institution,
                    child_inst: institution.Institution) -> None:
        """Test inserting into the list.

        Expect that the given `child_inst` is added to the sub-institutions
        list of `parent_inst` and that the parent of `child_inst` is set to
        `parent_inst`.
        """
        sub_inst_list = institution._SubInstitutionsList(parent_inst)
        sub_inst_list.insert(0, child_inst)

        assert child_inst in parent_inst.sub_institutions
        assert child_inst.parent == parent_inst

    def test_remove(self, parent_inst: institution.Institution,
                    child_inst: institution.Institution) -> None:
        """Test removing from the list.

        Expect that the given `child_inst` is removed from the sub-institutions
        list of `parent_inst` and that the parent of `child_inst` is set to
        None.
        """
        sub_inst_list = institution._SubInstitutionsList(parent_inst)
        sub_inst_list.append(child_inst)
        sub_inst_list.remove(child_inst)

        assert child_inst not in parent_inst.sub_institutions
        assert child_inst.parent is None

    def test_pop(self, parent_inst: institution.Institution,
                 child_insts: list[institution.Institution]) -> None:
        """Test popping from the list.

        Expect that the given `child_inst` is removed from the sub-institutions
        list of `parent_inst` and that the parent of `child_inst` is set to
        None.
        """
        sub_inst_list = institution._SubInstitutionsList(parent_inst)
        sub_inst_list.extend(child_insts)

        for i in range(len(child_insts) - 1, 0, -1):
            # Remove the last child (child_insts[i])
            sub_inst_list.pop()
            assert child_insts[i] not in parent_inst.sub_institutions
            assert child_insts[i].parent is None

            # Check that the remaining children are still in the list
            # and have the correct parent
            for j in range(i):
                assert child_insts[j] in parent_inst.sub_institutions
                assert child_insts[j].parent == parent_inst


class TestInstitution:
    """Test the :class:`gator.core.models.institution.Institution` class."""

    @classmethod
    @pytest.fixture
    def inst(cls) -> institution.Institution:
        """Return an institution with a nested hierarchy."""
        return institution.Institution(
            code='a1',
            name='a1',
            type='root',
            sub_institutions=[
                institution.Institution(
                    code='b1',
                    name='b1',
                    type='child-level-1',
                ),
                institution.Institution(
                    code='b2',
                    name='b2',
                    type='child-level-1',
                    sub_institutions=[
                        institution.Institution(
                            code='c1',
                            name='c1',
                            type='child-level-2',
                        )
                    ]
                ),
                institution.Institution(
                    code='b3',
                    name='b3',
                    type='child-level-1',
                    sub_institutions=[
                        institution.Institution(
                            code='c2',
                            name='c2',
                            type='child-level-2',
                        )
                    ]
                )
            ]
        )

    def test_init(self, inst: institution.Institution) -> None:
        """Test the initialization of an institution.

        Expect that the institution is initialized with the given code,
        name, type, and sub-institutions. Each sub-institution should have
        the proper parent set.
        """
        def _check_sub_insts(curr_inst: institution.Institution) -> None:
            """Recursively check the sub-institutions."""
            for sub_inst in curr_inst.sub_institutions:
                assert sub_inst.parent == curr_inst
                _check_sub_insts(sub_inst)

        _check_sub_insts(inst)

    def test_set_parent(self, inst: institution.Institution) -> None:
        """Test setting the parent of an institution.

        Expect that the parent of the institution is set to the given
        parent institution.
        """
        new_parent_inst = institution.Institution(
            code='a2', name='a2', type='root')
        assert inst.parent is None

        inst.parent = new_parent_inst
        assert inst.parent == new_parent_inst
        assert inst in new_parent_inst.sub_institutions

    def test_set_sub_institutions(self, inst: institution.Institution) -> None:
        """Test setting the sub-institutions of an institution.

        Expect that the sub-institutions of the institution are set to the
        given sub-institutions and that the parent of each sub-institution
        is set to the institution.
        """
        new_sub_insts = [
            institution.Institution(code='b4', name='b4', type='child-level-1'),
            institution.Institution(code='b5', name='b5', type='child-level-1'),
        ]
        assert inst.sub_institutions != new_sub_insts

        inst.sub_institutions = new_sub_insts
        assert inst.sub_institutions == new_sub_insts
        for sub_inst in inst.sub_institutions:
            assert sub_inst.parent == inst

    @pytest.mark.parametrize('type, expected', [
        ('root', ['a1']),
        ('child-level-1', ['b1', 'b2', 'b3']),
        ('child-level-2', ['c1', 'c2']),
        ('child-level-3', [])
    ])
    def test_find_children(self, inst: institution.Institution,
                           type: str, expected: list[str]) -> None:
        """Test finding the children of an institution of a given type.

        Expect that the children of the institution are returned.
        """
        children = inst.find_children(type)
        assert len(children) == len(expected)
        assert {child.code for child in children} == set(expected)

    @pytest.mark.parametrize('start_type, parent_type, expected', [
        ('root', 'root', None),
        ('child-level-1', 'root', 'a1'),
        ('child-level-2', 'root', 'a1'),
        ('child-level-2', 'child-level-1', 'b2')
    ])
    def test_find_parent(self, inst: institution.Institution,
                         start_type: str, parent_type: str,
                         expected: list[str]) -> None:
        """Test finding the parent of an institution of a given type.

        Expect that the parent of the institution is returned.
        """
        start_inst = inst.find_children(start_type)[0]
        parent_inst = start_inst.find_parent(parent_type)

        if parent_inst is None:
            assert expected is None
        else:
            assert parent_inst.code == expected
