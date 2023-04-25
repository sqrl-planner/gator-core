"""Test the :mod:`gator.core.models.institution` module."""
import pytest

import gator.core.models.institution as institution


class TestInstitution:
    """Test the :class:`gator.core.models.institution.Institution` class."""

    @classmethod
    @pytest.fixture
    def inst(cls) -> institution.Institution:
        """Return an institution with a nested hierarchy."""
        a1 = institution.Institution(
            code='a1',
            name='a1',
            type='root'
        ).save()
        institution.Institution(
            code='b1',
            name='b1',
            type='child-level-1',
            parent=a1
        ).save()

        b2 = institution.Institution(
            code='b2',
            name='b2',
            type='child-level-1',
            parent=a1
        ).save()
        institution.Institution(
            code='c1',
            name='c1',
            type='child-level-2',
            parent=b2
        ).save()

        b3 = institution.Institution(
            code='b3',
            name='b3',
            type='child-level-1',
            parent=a1
        ).save()
        institution.Institution(
            code='c2',
            name='c2',
            type='child-level-2',
            parent=b3
        ).save()

        return a1

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
            code='a2', name='a2', type='root').save()
        assert inst.parent is None

        inst.parent = new_parent_inst
        inst.save()

        assert inst.parent == new_parent_inst
        assert inst in new_parent_inst.sub_institutions

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
