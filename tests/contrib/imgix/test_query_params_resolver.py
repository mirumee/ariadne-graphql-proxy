import pytest

from ariadne_graphql_proxy.contrib.imgix import get_query_params_resolver


def test_resolver_returns_url_from_given_attribute():
    resolver = get_query_params_resolver(get_url="a.b.c.url")

    assert (
        resolver({"a": {"b": {"c": {"url": "http://test.url"}}}}, None)
        == "http://test.url"
    )


def test_resolver_calls_get_url_callable(mocker):
    get_url = mocker.MagicMock(side_effect=lambda obj, info, **kwargs: obj["url"])
    resolver = get_query_params_resolver(get_url=get_url)

    assert resolver({"url": "http://test.url"}, None) == "http://test.url"
    assert get_url.call_count == 1


def test_resolver_passes_all_args_to_get_url_callable(mocker):
    get_url = mocker.MagicMock(side_effect=lambda obj, info, **kwargs: obj["url"])
    resolver = get_query_params_resolver(get_url=get_url)
    obj = {"url": "http://test.url"}
    info = {"xyz": "XYZ"}

    resolver(obj, info, a="AA", b="BB")
    assert get_url.call_count == 1
    assert get_url.call_args.args == (obj, info)
    assert get_url.call_args.kwargs == {"a": "AA", "b": "BB"}


@pytest.mark.parametrize("get_url", ("url", lambda obj, info, **kwargs: obj["url"]))
def test_resolver_adds_predefined_query_param_to_url(get_url):
    resolver = get_query_params_resolver(
        get_url=get_url, extra_params={"abc": "test_value"}
    )

    assert (
        resolver({"url": "http://test.url"}, None) == "http://test.url?abc=test_value"
    )


@pytest.mark.parametrize("get_url", ("url", lambda obj, info, **kwargs: obj["url"]))
def test_resolver_adds_params_from_kwargs(get_url):
    resolver = get_query_params_resolver(get_url=get_url)

    assert (
        resolver({"url": "http://test.url"}, None, xyz="XYZ")
        == "http://test.url?xyz=XYZ"
    )


@pytest.mark.parametrize("get_url", ("url", lambda obj, info, **kwargs: obj["url"]))
def test_resolver_calls_get_params_on_given_kwargs(get_url, mocker):
    get_params = mocker.MagicMock(side_effect=lambda **kwargs: kwargs["params"])
    resolver = get_query_params_resolver(get_url=get_url, get_params=get_params)

    assert (
        resolver({"url": "http://test.url"}, None, params={"a": "AAA"})
        == "http://test.url?a=AAA"
    )


@pytest.mark.parametrize("get_url", ("url", lambda obj, info, **kwargs: obj["url"]))
def test_resolver_adds_both_predefined_and_provided_in_kwargs_params(get_url):
    resolver = get_query_params_resolver(
        get_url=get_url, extra_params={"a": "AAA", "b": "BBB"}
    )

    assert (
        resolver({"url": "http://test.url"}, None, b="REPLACED-BBB", c="CCC")
        == "http://test.url?a=AAA&b=REPLACED-BBB&c=CCC"
    )


@pytest.mark.parametrize("get_url", ("url", lambda obj, info, **kwargs: obj["url"]))
def test_resolver_calls_provided_serialize_url_on_modified_url(get_url, mocker):
    serialize_url = mocker.MagicMock(side_effect=lambda url: url + "-serialized")

    resolver = get_query_params_resolver(
        get_url=get_url, extra_params={"a": "AAA"}, serialize_url=serialize_url
    )

    assert (
        resolver({"url": "http://test.url"}, None, b="BBB")
        == "http://test.url?a=AAA&b=BBB-serialized"
    )
