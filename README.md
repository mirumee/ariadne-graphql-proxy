[![Ariadne](https://ariadnegraphql.org/img/logo-horizontal-sm.png)](https://ariadnegraphql.org)

- - - - -

# Ariadne GraphQL Proxy

Ariadne toolkit for building GraphQL proxies.

Features:

- Combining multiple local and remote GraphQL schemas into single GraphQL schema.
- Routing GraphQL queries to local and remote GraphQL schemas.
- Foreign keys system for modeling relationships between separate services schemas.
- Cache framework for caching of GraphQL query results per query fields.
- Low-level utilities for GraphQL Schema manipulation: adding, removing and copying schema items.


## Installation

Ariadne GraphQL Proxy can be installed with pip:

```console
pip install ariadne-graphql-proxy
```

Ariadne GraphQL Proxy requires Python 3.10 or higher.


## Example

Following code combines two remote schemas into one:

```python
from ariadne.asgi import GraphQL
from ariadne_graphql_proxy import ProxySchema, get_context_value

proxy_schema = ProxySchema()

proxy_schema.add_remote_schema("https://example.com/first-graphql/")
proxy_schema.add_remote_schema("https://example.com/second-graphql/")

final_schema = proxy_schema.get_final_schema()

app = GraphQL(
    final_schema,
    context_value=get_context_value,
    root_value=proxy_schema.root_resolver,
)
```


## Usage guide

For guide on using Ariadne GraphQL Proxy, please see the [GUIDE.md](./GUIDE.md) file.

> **Note:** Ariadne GraphQL Proxy is currently in prototyping stages. Library's API can and will change!


## Contributing

We are welcoming contributions to Ariadne GraphQL Proxy!

If you've found a bug or issue, feel free to open [GitHub issue](https://github.com/mirumee/ariadne-graphql-proxy/issues).

If you have any questions or feedback, don't hesitate to catch us on [GitHub discussions on main Ariadne repo](https://github.com/mirumee/ariadne/discussions/).

Pull requests are also welcome! We only request that PRs providing new features and extending existing implementation are proceeded by discussion in dedicated GitHub issue with a proposal or on  [`ariadne/discussions`](https://github.com/mirumee/ariadne/discussions/).

Also make sure you follow [@AriadneGraphQL](https://twitter.com/AriadneGraphQL) on Twitter for latest updates, news and random musings!

**Crafted with ❤️ by [Mirumee Software](http://mirumee.com)**
hello@mirumee.com