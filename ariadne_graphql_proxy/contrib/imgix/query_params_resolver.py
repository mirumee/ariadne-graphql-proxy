from functools import partial
from typing import Any, Callable, Optional, Union, cast
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from graphql import GraphQLResolveInfo


def get_attribute_value(
    obj: Any, info: GraphQLResolveInfo, attribute_str: str, **kwargs
) -> Any:
    value = obj
    for attr in attribute_str.split("."):
        try:
            value = value.get(attr)
        except AttributeError:
            value = getattr(value, attr, None)
    return value


def get_query_params_resolver(
    get_url: Union[str, Callable[..., str]],
    extra_params: Optional[dict[str, Any]] = None,
    get_params: Optional[Callable[..., dict[str, Any]]] = None,
    serialize_url: Optional[Callable[[str], Any]] = None,
):
    get_source_url = cast(
        Callable[..., str],
        (
            get_url
            if callable(get_url)
            else partial(get_attribute_value, attribute_str=get_url)
        ),
    )
    params = cast(dict[str, Any], extra_params if extra_params is not None else {})
    get_params_from_kwargs = cast(
        Callable[..., dict[str, Any]],
        get_params if get_params is not None else lambda **kwargs: kwargs,
    )
    serialize = cast(
        Callable[[str], Any],
        serialize_url if serialize_url is not None else lambda url: url,
    )

    def resolver(obj: Any, info: GraphQLResolveInfo, **kwargs):
        source_url = get_source_url(obj, info, **kwargs)
        parse_result = urlparse(source_url)
        query_params = parse_qs(parse_result.query)
        query_params.update(params)
        query_params.update(get_params_from_kwargs(**kwargs))
        result_url = urlunparse(
            (
                parse_result.scheme,
                parse_result.netloc,
                parse_result.path,
                parse_result.params,
                urlencode(query_params),
                parse_result.fragment,
            )
        )
        return serialize(result_url)

    return resolver
