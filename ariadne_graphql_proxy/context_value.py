from starlette.requests import Request


def get_context_value(request: Request) -> dict:
    return {
        "request": request,
        "headers": {k.lower(): v for k, v in request.headers.items()},
    }
