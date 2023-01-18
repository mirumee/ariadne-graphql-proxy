import pytest


@pytest.fixture
def gql():
    return lambda x: x
