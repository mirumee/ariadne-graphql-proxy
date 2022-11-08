# ariadne-graphql-proxy

Ariadne toolkit for building GraphQL proxies.


## Example:

`make_proxy_schema(graphql_url: str)` creates a copy of remote GraphQL schema.

Use `setup_root_resolver` returns GraphQL root resolver that proxies queries upstream.

This remote schema can be mutated before exposing:

```python
from ariadne.asgi import GraphQL
from ariadne_graphql_proxy import make_proxy_schema, setup_root_resolver

GRAPHQL_URL = "http://127.0.0.1:8000/graphql/"


schema = make_proxy_schema("http://127.0.0.1:8000/graphql/")

# Set custom resolving logic for a field
def resolve_user_email(user, _):
    return "HIDDEN!"

schema.type_map["User"].fields["email"].resolve = resolve_user_email


# Run GraphQL Proxy
app = GraphQL(schema, debug=True, root_value=setup_root_resolver(GRAPHQL_URL))
```