"""Configure the test suite."""
from doctest import ELLIPSIS

import mongomock
import pytest
from mongoengine import connect
from sybil import Sybil
from sybil.parsers.rest import DocTestParser, PythonCodeBlockParser

# The name of the test database. This is used by the `mongo_client` fixture.
TEST_DB = 'mongotest'


pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(optionflags=ELLIPSIS),
        PythonCodeBlockParser(),
    ],
    patterns=['*.rst', '*.py'],
).pytest()


@pytest.fixture(autouse=True, scope='module')
def mongo_client(request: pytest.FixtureRequest) -> mongomock.MongoClient:
    """Return a MongoDB client for testing."""
    # Explicitly set the UUID representation to standard, since mongomock
    # defaults to Python's legacy representation which will raise a warning
    connection = connect(db=TEST_DB, host='mongomock://localhost',
                          uuidRepresentation='standard')
    # Add a handler to drop the test database after the test is complete
    request.addfinalizer(lambda: connection.drop_database(TEST_DB))

    return connection
