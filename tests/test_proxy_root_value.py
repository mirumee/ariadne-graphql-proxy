from ariadne_graphql_proxy import ProxyRootValue


def test_proxy_root_value_without_errors_or_extensions_skips_result_update():
    result = False, {"data": "ok"}
    root_value = ProxyRootValue()
    assert root_value.update_result(result) == result


def test_proxy_root_value_with_errors_extends_result():
    result = False, {"data": "ok"}
    root_value = ProxyRootValue(errors=[{"message": "Test"}])
    assert root_value.update_result(result) == (
        False,
        {
            "data": "ok",
            "errors": [
                {
                    "message": "Test",
                },
            ],
        },
    )


def test_proxy_root_value_with_extensions_extends_result():
    result = False, {"data": "ok"}
    root_value = ProxyRootValue(extensions={"score": "100"})
    assert root_value.update_result(result) == (
        False,
        {
            "data": "ok",
            "extensions": {
                "score": "100",
            },
        },
    )


def test_proxy_root_value_with_errors_and_extensions_extends_result():
    result = False, {"data": "ok"}
    root_value = ProxyRootValue(
        errors=[{"message": "Test"}],
        extensions={"score": "100"},
    )
    assert root_value.update_result(result) == (
        False,
        {
            "data": "ok",
            "errors": [
                {
                    "message": "Test",
                },
            ],
            "extensions": {
                "score": "100",
            },
        },
    )


def test_proxy_root_value_with_errors_updates_result():
    result = False, {"data": "ok", "errors": [{"message": "Org"}]}

    root_value = ProxyRootValue(errors=[{"message": "Test"}])
    assert root_value.update_result(result) == (
        False,
        {
            "data": "ok",
            "errors": [
                {
                    "message": "Org",
                },
                {
                    "message": "Test",
                },
            ],
        },
    )


def test_proxy_root_value_with_extensions_updates_result():
    result = False, {"data": "ok", "extensions": {"core": True}}
    root_value = ProxyRootValue(extensions={"score": "100"})
    assert root_value.update_result(result) == (
        False,
        {
            "data": "ok",
            "extensions": {
                "core": True,
                "score": "100",
            },
        },
    )


def test_proxy_root_value_with_errors_and_extensions_updates_result():
    result = (
        False,
        {
            "data": "ok",
            "errors": [{"message": "Org"}],
            "extensions": {"core": True},
        },
    )

    root_value = ProxyRootValue(
        errors=[{"message": "Test"}],
        extensions={"score": "100"},
    )
    assert root_value.update_result(result) == (
        False,
        {
            "data": "ok",
            "errors": [
                {
                    "message": "Org",
                },
                {
                    "message": "Test",
                },
            ],
            "extensions": {
                "core": True,
                "score": "100",
            },
        },
    )
