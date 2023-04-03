"""Test the Marshmallow schemas for the institution models."""
from collections import OrderedDict

import gator.core.models.institution as models
import gator.core.schemas.institution as schemas


class TestInstitutionSchema:
    """Test the :class:`gator.core.schemas.institution.InstitutionSchema` class.

    Class Attributes:
        FACULTY_INSTITUTION: A faculty institution to test with.
        CAMPUS_INSTITUTION: A campus institution to test with.
        UNI_INSTITUTION: A university institution to test with.
        DUMPED_FACULTY_INSTITUTION: The dumped data for `FACULTY_INSTITUTION`.
        DUMPED_CAMPUS_INSTITUTION: The dumped data for `CAMPUS_INSTITUTION`.
        DUMPED_UNI_INSTITUTION: The dumped data for `UNI_INSTITUTION`.
    """

    FACULTY_INSTITUTION: models.Institution = models.Institution(
        code='ARTSC',
        name='Faculty of Arts and Science',
        type='faculty',
        parent=None,
    )
    CAMPUS_INSTITUTION: models.Institution = models.Institution(
        code='UTSG',
        name='St. George Campus',
        type='campus',
    )
    UNI_INSTITUTION: models.Institution = models.Institution(
        code='UofT',
        name='University of Toronto',
        type='university',
    )
    DUMPED_FACULTY_INSTITUTION: dict = {
        'code': 'ARTSC',
        'name': 'Faculty of Arts and Science',
        'type': 'faculty',
        '_parent': 'UTSG'
    }
    DUMPED_CAMPUS_INSTITUTION: dict = {
        'code': 'UTSG',
        'name': 'St. George Campus',
        'type': 'campus',
        '_parent': 'UofT',
        '_sub_institutions': ['ARTSC']
    }
    DUMPED_UNI_INSTITUTION: dict = {
        'code': 'UofT',
        'name': 'University of Toronto',
        'type': 'university',
        '_sub_institutions': ['UTSG']
    }

    def setup_class(self):
        """Set up the tests."""
        self.schema = schemas.InstitutionSchema()
        # Setup the parent-child relationships
        self.FACULTY_INSTITUTION.parent = self.CAMPUS_INSTITUTION
        self.CAMPUS_INSTITUTION.parent = self.UNI_INSTITUTION
        self.UNI_INSTITUTION.parent = None

        # Setup the sub-institution relationships
        self.FACULTY_INSTITUTION.sub_institutions = []
        self.CAMPUS_INSTITUTION.sub_institutions.append(self.FACULTY_INSTITUTION)
        self.UNI_INSTITUTION.sub_institutions.append(self.CAMPUS_INSTITUTION)

    def test_load_faculty_institution(self):
        """Test loading a faculty institution."""
        # TODO: We need to create a test MongoDB instance to test this
        # loaded = self.schema.load(self.DUMPED_FACULTY_INSTITUTION)
        # assert loaded == self.FACULTY_INSTITUTION

    def test_load_campus_institution(self):
        """Test loading a campus institution."""
        # TODO: We need to create a test MongoDB instance to test this
        # loaded = self.schema.load(self.DUMPED_CAMPUS_INSTITUTION)
        # assert loaded == self.CAMPUS_INSTITUTION

    def test_load_uni_institution(self):
        """Test loading a university institution."""
        # TODO: We need to create a test MongoDB instance to test this
        # loaded = self.schema.load(self.DUMPED_UNI_INSTITUTION)
        # assert loaded == self.UNI_INSTITUTION

    def test_dump_faculty_institution(self):
        """Test dumping a faculty institution."""
        dumped = OrderedDict(self.schema.dump(self.FACULTY_INSTITUTION))
        assert dumped == self.DUMPED_FACULTY_INSTITUTION

    def test_dump_campus_institution(self):
        """Test dumping a campus institution."""
        dumped = OrderedDict(self.schema.dump(self.CAMPUS_INSTITUTION))
        assert dumped == self.DUMPED_CAMPUS_INSTITUTION

    def test_dump_uni_institution(self):
        """Test dumping a university institution."""
        dumped = OrderedDict(self.schema.dump(self.UNI_INSTITUTION))
        assert dumped == self.DUMPED_UNI_INSTITUTION


class TestBuildingSchema:
    """Test the :class:`gator.core.schemas.institution.BuildingSchema` class.

    Class Attributes:
        BUILDINGS: A list of buildings to test with: Bahen, Robarts, and Sanford Fleming.
        DUMPED_BUILDINGS: A list of dictionaries containing the dumped building objects,
            in the same order as `BUILDINGS`.
    """

    BUILDINGS: list[models.Building] = [
        models.Building(
            code='BAH',
            name='Bahen Centre for Information Technology',
            institution=TestInstitutionSchema.CAMPUS_INSTITUTION,
            map_url='https://path.com/to/bahen/map'
        ),
        models.Building(
            code='ROB',
            name='Robarts Library',
            institution=TestInstitutionSchema.CAMPUS_INSTITUTION,
            map_url='https://path.com/to/robarts/map'
        ),
        models.Building(
            code='SF',
            name='Sanford Fleming Building',
            institution=TestInstitutionSchema.CAMPUS_INSTITUTION,
            map_url='https://path.com/to/sanford_fleming/map'
        )
    ]
    DUMPED_BUILDINGS: list[dict] = [{
        'code': building.code,
        'name': building.name,
        'institution': building.institution.code,
        'map_url': building.map_url
    } for building in BUILDINGS]

    def setup_class(self):
        """Set up the tests."""
        self.schema = schemas.BuildingSchema()

    def test_load_building(self):
        """Test loading a building."""
        # TODO: We need to create a test MongoDB instance to test this
        # for building, datum in zip(self.BUILDINGS, self.DUMPED_BUILDINGS):
        #     assert self.schema.load(datum) == building

    def test_dump_building(self):
        """Test dumping a building."""
        for building, datum in zip(self.BUILDINGS, self.DUMPED_BUILDINGS):
            assert OrderedDict(self.schema.dump(building)) == datum


class TestLocationSchema:
    """Test the :class:`gator.core.schemas.institution.LocationSchema` class.

    Class Attributes:
        LOCATIONS: A list of locations to test with: Bahen, Robarts, and Sanford Fleming.
        DUMPED_LOCATIONS: A list of dictionaries containing the dumped location objects,
            in the same order as `LOCATIONS`.
    """

    LOCATIONS: list[models.Location] = [
        models.Location(building=building, room=room)
        for building, room in zip(TestBuildingSchema.BUILDINGS, ['123', '456', '789'])
    ]
    DUMPED_LOCATIONS: list[dict] = [{
        'building': location.building.code,
        'room': location.room
    } for location in LOCATIONS]

    def setup_class(self):
        """Set up the tests."""
        self.schema = schemas.LocationSchema()

    def test_load_location(self):
        """Test loading a location."""
        # TODO: We need to create a test MongoDB instance to test this
        # for location, datum in zip(self.LOCATIONS, self.DUMPED_LOCATIONS):
        #     assert self.schema.load(datum) == location

    def test_dump_location(self):
        """Test dumping a location."""
        for location, datum in zip(self.LOCATIONS, self.DUMPED_LOCATIONS):
            assert OrderedDict(self.schema.dump(location)) == datum
