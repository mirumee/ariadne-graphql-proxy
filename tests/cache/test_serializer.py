import pytest

from ariadne_graphql_proxy.cache import JSONCacheSerializer, NoopCacheSerializer


@pytest.fixture
def mocked_lib(mocker):
    return mocker.patch("ariadne_graphql_proxy.cache.serializer.json")


@pytest.fixture
def mocked_json(mocker, mocked_lib):
    mocker.patch("ariadne_graphql_proxy.cache.serializer.USING_ORJSON", False)
    return mocked_lib


@pytest.fixture
def mocked_orjson(mocker, mocked_lib):
    mocker.patch("ariadne_graphql_proxy.cache.serializer.USING_ORJSON", True)
    return mocked_lib


def test_noop_serialize_returns_not_changed_value():
    assert NoopCacheSerializer().serialize("abc") == "abc"


def test_noop_deserialize_returns_not_changed_value():
    assert NoopCacheSerializer().deserialize("abc") == "abc"


def test_json_serialize_calls_json_dumps_with_decode_if_orjson_is_available(
    mocked_orjson,
):
    JSONCacheSerializer().serialize("test value")

    assert mocked_orjson.dumps.called_with("test value")
    assert mocked_orjson.dumps().decode.called


def test_json_serialize_calls_json_dumps_if_orjson_is_not_available(mocked_json):
    JSONCacheSerializer().serialize("test value")

    assert mocked_json.dumps.called_with("test value")


def test_json_deserialize_calls_orjson_loads_if_orjson_is_available(mocked_orjson):
    JSONCacheSerializer().deserialize("test value")

    assert mocked_orjson.loads.called_with("test value")


def test_json_deserialize_calls_json_loads_if_orjson_is_not_available(mocked_json):
    JSONCacheSerializer().deserialize("test value")

    assert mocked_json.loads.called_with("test value")
