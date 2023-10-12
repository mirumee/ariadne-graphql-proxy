# Ariadne GraphQL Proxy Guide


## Combining remote schemas

Below example illustrates simple GraphQL proxy combining two remote GraphQL schemas into single API:

```python
from ariadne.asgi import GraphQL
from ariadne_graphql_proxy import ProxySchema, get_context_value

proxy_schema = ProxySchema()

proxy_schema.add_remote_schema("https://example.com/e-commerce/")
proxy_schema.add_remote_schema("https://example.com/product-reviews/")

final_schema = proxy_schema.get_final_schema()

app = GraphQL(
    final_schema,
    context_value=get_context_value,
    root_value=proxy_schema.root_resolver,
    debug=True,
)
```

Let's walk this code step by step:


### Proxy schema

`ProxySchema` is a factory object provided by Ariadne GraphQL Proxy. This objects stores GraphQL schemas, rules for modifying them, and then gives you back final schema and root resolver that knows how to split GraphQL query received by proxy between schemas that combine.

Creating an instance of `ProxySchema` is first step to creating GraphQL proxy:

```python
from ariadne_graphql_proxy import ProxySchema

proxy_schema = ProxySchema()
```


### Adding schemas to `ProxySchema`

`ProxySchema` has two methods that can be used to add schemas to proxy: `add_remote_schema` and `add_schema`.

Our proxy uses `add_remote_schema` method to combine two GraphQL remote schemas into final schema:


```python
from ariadne_graphql_proxy import ProxySchema

proxy_schema = ProxySchema()

proxy_schema.add_remote_schema("https://example.com/e-commerce/")
proxy_schema.add_remote_schema("https://example.com/product-reviews/")
```

When application starts, `add_remote_schema` takes the URL of remote GraphQL API **supporting introspection**, runs introspection query, and then includes its result schema in `ProxySchema`.

`add_remote_schema` also accepts optional arguments that can be used to exclude parts of remote schema from final schema used by proxy. Those are documented in later part of this document.


### Creating final schema

`get_final_schema` method of `ProxySchema` produces final `GraphQLSchema` instance from schemas previously added to proxy with either `add_remote_schema` or `add_schema`:

```python
from ariadne_graphql_proxy import ProxySchema

proxy_schema = ProxySchema()

proxy_schema.add_remote_schema("https://example.com/e-commerce/")
proxy_schema.add_remote_schema("https://example.com/product-reviews/")

final_schema = proxy_schema.get_final_schema()
```

Final schema:

- merges schemas into single `GraphQLSchema`
- records data about those schemas fields origin
- created query filter that `root_resolver` uses to split query into smaller queries sent to remote schemas and local schema.


### Creating GraphQL server

Ariadne GraphQL Proxy doesn't provide it's own server component. Instead you should use Ariadne's `asgi.GraphqL` app to create server:

```python
from ariadne.asgi import GraphQL
from ariadne_graphql_proxy import ProxySchema, get_context_value

proxy_schema = ProxySchema()

proxy_schema.add_remote_schema("https://example.com/e-commerce/")
proxy_schema.add_remote_schema("https://example.com/product-reviews/")

final_schema = proxy_schema.get_final_schema()

app = GraphQL(
    final_schema,
    context_value=get_context_value,
    root_value=proxy_schema.root_resolver,
    debug=True,
)
```

Note that this server is initialized with `context_value` and `root_value`. Those are required by proxy to work:

- `context_value` exposes request data such as headers to `root_resolver`.
- `root_resolver` acts as top level resolver that uses query filter to split GraphQL query received by proxy and call remote schemas to retrieve their data.

You can start your server using any ASGI server. For example, using [Uvicorn](https://www.uvicorn.org/):

```
pip install uvicorn

uvicorn my-proxy:app -p 8000
```

Assuming the above Python code is living in `my-proxy.py`, uvicorn will start the proxy server on 127.0.0.:8000 address on your computer.


## Setting custom resolvers

`ProxySchema.get_final_schema` returns `GraphQLSchema` instance which can be additionally mutated to set custom resolvers on it's fields.

`ariadne_graphql_proxy` exports `set_resolver` and `unset_resolver` utils that can be used to set custom resolver functions on `GraphQLSchema` schema fields:

```python
final_schema = proxy_schema.get_final_schema()


def custom_resolver(obj, info):
    ...


set_resolver(final_schema, "Query", "products", custom_resolver)
```

If field you are setting custom resolver for comes from remote schema, this field will be queried by root resolver before your resolver will be ran for it.

If you want to exclude the field from root resolver, set this field as delayed using `ProxySchema`'s `add_delayed_fields` method:

```python
proxy_schema.add_delayed_fields({"Query": ["products"]})

final_schema = proxy_schema.get_final_schema()


def custom_resolver(obj, info):
    ...


set_resolver(final_schema, "Query", "products", custom_resolver)
```

If field you are setting resolver on already has a resolver on it, this resolver will be replaced with new one.


## Setting custom resolvers for remote schemas

If field you are setting custom resolver for comes from remote schema, you will have to first set this field as delayed, using `ProxySchema`'s `add_delayed_fields` method:

```python
proxy_schema.add_delayed_fields({"Query": ["products"]})

final_schema = proxy_schema.get_final_schema()


def custom_products_resolver(obj, info):
    ...


set_resolver(final_schema, "Query", "products", custom_products_resolver)
```


## Proxy resolver

`ProxyResolver` can be used to proxy portion of query from `GraphQLResolveInfo` (`info` argument) to given GraphQL's server:

```python
resolve_products = ProxyResolver(
    "https://example.com/e-commerce/",
    proxy_headers=True,
)

set_resolver(final_schema, "Query", "products", resolve_products)
```

`ProxyResolver` rewrites the GraphQL Query received by the server to only contain fields and arguments that apply for the selected field.

It requires single argument:

- `url`: a `str` with URL to GraphQL API to which query should be proxied to.

It takes following optional arguments:

- `proxy_headers`: `Union[bool, Callable, List[str]]`
- `cache`: `CacheBackend`
- `cache_key`: `Union[str, Callable[[GraphQLResolveInfo], str]]`
- `cache_ttl`: `int`

`proxy_headers` option is documented in "Proxying headers" section of this guide.

`cache`, `cache_key` and `cache_ttl` arguments are documented in cache section of this guide.


## Foreign keys

Ariadne GraphQL Proxy supports relations between combined GraphQL Schemas. For example, one schema may implement a mutation returning a type, which is defined and retrieved from other schema:

```graphql
type Query {
    order(id: ID!): Order
}

type Order {
    id: ID!
    customer: Custom
    billingAddress: Address!
    shippingAddres: Address
    payments: [Payment]
}
```

```graphql
type Mutation {
    checkoutComplete(checkoutId: ID!): CheckoutComplete!
}

type CheckoutComplete {
    order: Order
    errors: [String!]
}

type Order {
    id: ID!
}
```

Notice how one service implements `Order` type and `order` `Query` field while the other defines only small `Order` type defining its ID, but also a mutation that may return this `Order`.

Once those schemas are combined in `ProxySchema`, following schema will be produced:

```graphql
type Query {
    order(id: ID!): Order
}

type Mutation {
    checkoutComplete(checkoutId: ID!): CheckoutComplete!
}

type Order {
    id: ID!
    customer: Custom
    billingAddress: Address!
    shippingAddres: Address
    payments: [Payment!]!
}

type CheckoutComplete {
    order: Order
    errors: [String!]
}
```

But there is a problem now. Because GraphQL API implementing `checkoutComplete` only returns `id` field for order, querying order's other non-nullable fields like `billingAddress` or `payments` will result in GraphQL proxy raising error about those non-nullable fields receiving `None` as value. This is because proxy knows that order field on `CheckoutComplete` doesn't support those fields, so it excludes them from query.

We can solve this error by implementing those fields in both schemas, but we can also tell `ProxySchema` to retrieve remaining fields from other type, using order's id already returned from other service.


### Relations in GraphQL Proxy

In the GraphQL Proxy relations are resolved in two steps:

- A field in schema that returns object is set as foreign key, making the root resolver rewrite queries with this field to always query for requested object's identifier, and identifier only.
- After root resolver retrieved related object's identifier from one query, it passes this identifier to field's resolver, in order for it to retrieve remaining data from other service.

Looking at above example, this query:

```graphql
mutation CompleteCheckout {
    checkoutComplete(id: "dsa987dsa97dsa98") {
        order {
            id
            billingAddress
            shippingAddress
            payments {
                id
                method
                status
                amount {
                    currency
                    amount
                }
            }
        }
        errors
    }
}
```

Will be slit into two queries, first one being executed by root resolver:

```graphql
mutation CompleteCheckout {
    checkoutComplete(id: "dsa987dsa97dsa98") {
        order {
            id
        }
        errors
    }
}
```

And then order's id together with its fields from first query will be passed to `CheckoutComplete`'s `order` resolver, which's goal will be to execute following query to retrieve remaining data:

```graphql
query GetForeignKeyOrder($id: ID!) {
    order(id: $id) {
        id
        billingAddress
        shippingAddress
        payments {
            id
            method
            status
            amount {
                currency
                amount
            }
        }
    }
}
```

Finally GraphQL's query executor implemented by the `graphql-core` library will combine both data from root resolver and data from field's resolver into final query result.


### Adding foreign key to schema

We start with using the `add_foreign_key` method to tell `ProxySchema` to always request an `id` field when `order` field is queried on `CheckoutComplete`:

```python
from ariadne_graphql_proxy import ProxySchema

proxy_schema = ProxySchema()

proxy_schema.add_remote_schema("https://example.com/store/")
proxy_schema.add_remote_schema("https://example.com/checkout/")

proxy_schema.add_foreign_key("CheckoutComplete", "order", "id")

final_schema = proxy_schema.get_final_schema()
```

This will guarantee that when `order` field is on `CheckoutComplete` is queried, this part of query will be always rewritten by root resolver to `order { id }` before being sent to the checkout service.


### Resolving foreign key object

Relation is now missing the logic that will take the order id retrieved by the root resolver and other queried fields for `order` and query the other service to retrieve those fields values.

You can implement this logic completely by yourself in custom resolver for `CheckoutComplete.order` field, but Ariadne GraphQL Proxy already provides an utility `ForeignKeyResolver` that implements this logic:

```python
from ariadne_graphql_proxy import ForeignKeyResolver, ProxySchema, set_resolver

proxy_schema = ProxySchema()

proxy_schema.add_remote_schema("https://example.com/store/")
proxy_schema.add_remote_schema("https://example.com/checkout/")

proxy_schema.add_foreign_key("CheckoutComplete", "order", "id")

final_schema = proxy_schema.get_final_schema()

fk_order_resolver = ForeignKeyResolver(
    "https://example.com/store/",
    """
    query GetForeignKeyOrder($id: ID!) {
        order(id: $id) {
            __FIELDS
        }
    }
    """
)

set_resolver(final_schema, "CheckoutComplete", "order", fk_order_resolver)
```

`ForeignKeyResolver` class requires two configuration options to work:

- an URL of GraphQL API to query to retrieve the related object.
- The GraphQL query to use to retrieve the related object.

The query provided to `ForeignKeyResolver` is a template. `__FIELDS` field in it is not magical feature of GraphQL - it is in fact a placeholder in template that is replaced with final requested fields before query is sent to the service. `__FIELDS` will be replaced with whatever fields were originally requested for `order`.


### Final implementation

Final GraphQL proxy implementation implementing a foreign key looks like this:

```python
from ariadne.asgi import GraphQL
from ariadne_graphql_proxy import (
    ForeignKeyResolver,
    ProxySchema,
    get_context_value,
    set_resolver,
)


proxy_schema = ProxySchema()

proxy_schema.add_remote_schema("https://example.com/e-commerce/")
proxy_schema.add_remote_schema("https://example.com/product-reviews/")

proxy_schema.add_foreign_key("CheckoutComplete", "order", "id")

final_schema = proxy_schema.get_final_schema()

fk_order_resolver = ForeignKeyResolver(
    "https://example.com/store/",
    """
    query GetForeignKeyOrder($id: ID!) {
        order(id: $id) {
            __FIELDS
        }
    }
    """
)

set_resolver(final_schema, "CheckoutComplete", "order", fk_order_resolver)

app = GraphQL(
    final_schema,
    context_value=get_context_value,
    root_value=proxy_schema.root_resolver,
    debug=True,
)
```


## imgix query params resolver

`get_query_params_resolver` returns a preconfigured resolver that takes URL string and passed arguments to generate a URL with arguments as query params. It can be used to add [rendering options](https://docs.imgix.com/apis/rendering) to [imgix.com](https://imgix.com) image URL.


### Function arguments:

- `get_url`: a `str` or `Callable` which returns `str`. If `get_url` is a `str` then the resolver will split it by `.` and use substrings as keys to get value from `obj` dict or as attribute names for non dict objects, e.g. with `get_url` set to `"imageData.url"` the resolver will use one of: `obj["imageData"]["url"]`, `obj["imageData"].url`, `obj.imageData["url"]`, `obj.imageData.url` as URL string. If `get_url` is a callable, then resolver will call it with `obj`, `info` and `**kwargs` and use result as URL string.
- `extra_params`: an optional `dict` of query params to be added to the URL string. These can be overridden by kwargs passed to the resolver.
- `get_params`: an optional `Callable` to be called on passed `**kwargs` before they are added to the URL string.
- `serialize_url`: an optional `Callable` to be called on URL string with query params already added. Result is returned directly by the resolver.


### Example with `insert_field`

In this example we assume there is a graphql server which provides following schema:

```gql
type Query {
  product: Product!
}

type Product {
  imageUrl: String!
}
```

`imageUrl` returns URL string served by [imgix.com](https://imgix.com) and we want to add another field with thumbnail URL.

```python
from ariadne_graphql_proxy import ProxySchema, get_context_value, set_resolver
from ariadne_graphql_proxy.contrib.imgix import get_query_params_resolver


proxy_schema = ProxySchema()
proxy_schema.add_remote_schema("https://remote-schema.local")
proxy_schema.insert_field(
    type_name="Product",
    field_str="thumbnailUrl(w: Int, h: Int): String!",
)

final_schema = proxy_schema.get_final_schema()

set_resolver(
    final_schema,
    "Product",
    "thumbnailUrl",
    get_query_params_resolver(
        "imageUrl",
        extra_params={"h": 128, "w": 128, "fit": "min"},
    ),
)
```

With an added resolver, `thumbnailUrl` will return `imageUrl` with additional query parameters. `fit` is always set to `min`. `w` and `h` are set to `128` by default, but can be changed by query argument, e.g.

```gql
query getProduct {
    product {
        imageUrl
        thumbnailUrl
        smallThumbnailUrl: thumbnailUrl(w: 32, h: 32)
    }
}
```

```json
{
  "data": {
    "product": {
      "imageUrl": "https://test-imageix.com/product-image.jpg",
      "thumbnailUrl": "https://test-imageix.com/product-image.jpg?h=128&w=128&fit=min",
      "smallThumbnailUrl": "https://test-imageix.com/product-image.jpg?h=32&w=32&fit=min"
    }
  }
}
```


## Proxying headers

Ariadne GraphQL Proxy requires that `GraphQLResolveInfo.context` attribute is a dictionary containing `headers` key, which in itself is a `Dict[str, str]` dictionary.

`get_context_value` utility importable form `ariadne_graphql_proxy` is a convenience utility which is compatible with Ariadne's ASGI application and returns a `dict` with `request` and `headers` keys. Header names are normalized to lowercase, eg.: `Authorization` header will be available as `context["headers"]["authorization"]` if it was included in request to the GraphQL server.


### `ProxySchema`

Proxy schema doesn't include any custom headers in requests used to introspect remote schemas.

`root_resolver` includes `authorization` in header proxied requests if it's present in context's `headers` dictionary.


### `ForeignKeyResolver` and `ProxyResolver`

Both foreign key and proxy resolvers constructors take `proxy_headers` as second option. This option controls which headers from `context["headers"]` are proxied to services and which aren't.

If this option is not set, only `authorization` header is proxied, if it was sent to the proxy.

If `proxy_headers` is a `List[str]`, its assumed to be a list of names of headers that should be proxied if sent by client.

If `proxy_headers` is a callable, it will be called with three arguments:

- `obj`: `Any` value that was passed to resolved field's first argument. 
- `info`: a `GraphQLResolveInfo` object for field with proxy or foreign key resolver.
- `payload`: a `dict` with GraphQL JSON payload that will be sent to a proxy server (`operationName`, `query`, `variables`).

Callable should return `None` or `Dict[str, str]` with headers to send to other server.

If `proxy_headers` is `None` or `False`, no headers are proxied to the other service.


## Cache framework

Ariadne GraphQL Proxy implements basic cache framework that enables of caching parts of GraphQL queries.

Currently only a simple in memory cache backend is provided, but developers may implement their own backends.

All cache utilities are importable from the `ariadne_graphql_proxy.cache` package.

> **Note:** If you are using `ProxySchema`, remember to exclude fields you are going to cache from root resolver with `add_delayed_fields` method, or your data will not be cached!


### `simple_cached_resolver`

A decorator for resolvers that caches their results for given resolver arguments:

```python
from ariadne_graphql_proxy.cache import InMemoryCache, simple_cached_resolver

cache_backend = InMemoryCache()

@simple_cached_resolver(cache_backend, "products")
def resolve_products(_, info, **filters):
    # Resolve products using filters
```

It requires two arguments:

- `backend`: a `CacheBackend` subclass instance which will be used to cache resolver's results
- `prefix`: a `str` with cache prefix or `Callable[[GraphQLResolveInfo], str]` used to obtain this prefix `str` from `info`, combined with resolver's arguments to create final cache key.

It also has following optional arguments:

- `ttl`: an `int` with a time to live for cache value, in seconds.


### `cached_resolver`

A decorator for resolvers that caches their results for given resolver arguments and selected fields:

```python
from ariadne_graphql_proxy.cache import InMemoryCache, cached_resolver

cache_backend = InMemoryCache()

@cached_resolver(cache_backend, "products")
def resolve_products(_, info, **filters):
    # Resolve products using filters
```

It requires two arguments:

- `backend`: a `CacheBackend` subclass instance which will be used to cache resolver's results
- `prefix`: a `str` with cache prefix or `Callable[[GraphQLResolveInfo], str]` used to obtain this prefix `str` from `info`, combined with resolver's arguments and queried fields to create final cache key.

It also has following optional arguments:

- `ttl`: an `int` with a time to live for cache value, in seconds.


### `ForeignKeyResolver` and `ProxyResolver`

Both `ForeignKeyResolver` and `ProxyResolver` accept caching options:

- `cache`: `Optional[CacheBackend]`: `CacheBackend` to use to cache results.
- `cache_key`: `str` with cache prefix or `Callable[[GraphQLResolveInfo], str]` used to obtain this prefix `str` from `info`, combined with resolver's arguments and queried fields to create final cache key.
- `cache_ttl`: an `int` with a time to live for cache value, in seconds.

To enable cache, `cache` and `cache_key` need to be set.


### Custom cache backends

Custom cache backends should extend `ariadne_graphql_proxy.cache.CacheBackend` class and need to implement `set` and `get` methods:

```python
class CacheBackend:
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        ...

    async def get(self, key: str, default: Any = None) -> Any:
        ...
```

`__init__` methods takes `serializer` argument which defaults to `NoopCacheSerializer()` and can be overriden:

```python
class CacheBackend:
    def __init__(self, serializer: Optional[CacheSerializer] = None) -> None:
        self.serializer: CacheSerializer = serializer or NoopCacheSerializer()
```


They can also optionally implement `clear_all` method, but its not used by Ariadne GraphQL Proxy outside of tests:

```python
class CacheBackend:
    async def clear_all(self):
        ...
```


### Cche serializers

Currently only `NoopCacheSerializer` and `JSONCacheSerializer` are provided, but developers may implement their own serializers.

Custom cache serializers should extend `ariadne_graphql_proxy.cache.CacheSerializer` class and need to implement `serialize` and `deserialize` methods:

```python
class CacheSerializer:
    def serialize(self, value: Any) -> str:
        ...

    def deserialize(self, value: str) -> Any:
        ...
```


### `CloudflareCacheBackend`

`CloudflareCacheBackend` uses Cloudflare's [key value storage](https://developers.cloudflare.com/workers/learning/how-kv-works/) for caching. It can be imported from `ariadne_graphql_proxy.contrib.cloudflare` and requires following arguments:

- `account_id`: `str`: Id of Cloudflare account.
- `namespace_id`: `str`: Id of worker's KV Namespace.
- `headers`: `Optional[Dict[str, str]]`: Headers attached to every api call, defaults to `{}`.
- `base_url`: `str`: Cloudflare API base url, defaults to `"https://api.cloudflare.com/client/v4"`.
- `serializer`: `Optional[CacheSerializer]`: serialiser used to process cached and retrieved values, defaults to `ariadne_graphql_proxy.cache.JSONCacheSerializer()`.

```python
from ariadne_graphql_proxy.contrib.cloudflare import CloudflareCacheBackend

cache = CloudflareCacheBackend(
    account_id="account id",
    namespace_id="workers kv namespace id",
    headers={"Authorization": "Bearer ..."},
    base_url="https://cloudflare_api_url/client/v4",
)
```

`CloudflareCacheBackend` [lists existing keys](https://developers.cloudflare.com/api/operations/workers-kv-namespace-list-a-namespace'-s-keys) in given namespace on initialization to ensure it can be accessed, if this check fails it throws `CloudflareCacheError`. To store value it performs [PUT request](https://developers.cloudflare.com/api/operations/workers-kv-namespace-write-key-value-pair-with-metadata), and to retrieve saved value it uses [GET](https://developers.cloudflare.com/api/operations/workers-kv-namespace-read-key-value-pair).


### `DynamoDBCacheBackend`

`DynamoDBCacheBackend` uses [Amazon DynamoDB](https://aws.amazon.com/dynamodb) for storing cached values. It requires [`boto3`](https://github.com/boto/boto3) package, which can be installed using pip:

```
pip install ariadne-graphql-proxy[aws]
```

It can be imported from `ariadne_graphql_proxy.contrib.aws` and requires following arguments:

- `table_name`: `str`: Name of DynamoDB table.
- `partition_key`: `str`: Partition key, defaults to `key`.
- `ttl_attribute`: `str`: TTL attribute, defaults to `ttl`.
- `session`: `Optional[Session]`: Instance of `boto3.session.Session`, defaults to `Session()` which reads configuration values according to these [docs](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#guide-configuration).
- `serializer`: `Optional[CacheSerializer]`: serialiser used to process cached and retrieved values, defaults to `ariadne_graphql_proxy.cache.JSONCacheSerializer()`.

```python
from ariadne_graphql_proxy.contrib.aws import DynamoDBCacheBackend
from boto3.session import Session

cache = DynamoDBCacheBackend(
    table_name="table name",
    partition_key="partition key",
    ttl_attribute="ttl attribute",
    session=Session(
        aws_access_key_id="access key id",
        aws_secret_access_key="secret",
        region_name="region name",
    ),
)
```

`DynamoDBCacheBackend` checks status of given table on initialization to ensure it can be accessed, if this check fails due to unavailable table it throws `DynamoDBCacheError`.

`DynamoDBCacheBackend` sets given ttl in [Unix epoch time format](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/time-to-live-ttl-before-you-start.html#time-to-live-ttl-before-you-start-formatting). Expired items are excluded from results, but they aren't deleted from table, this is left to [DynamoDB engine](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/howitworks-ttl.html).


## `ProxySchema`

`ProxySchema` class importable from `ariadne_graphql_proxy` is a factory class for proxy GraphQL schemas.

It has following methods:

### `__init__`

```python
def __init__(self, root_value: Optional[RootValue] = None):
    ...
```

Constructor for `ProxySchema` takes single optional argument, `root_value`.

This argument's behavior is identical to `root_value` option from Ariadne's `GraphQL` server.

Its either root value to pass to `Query` and `Mutation` fields resolvers or first argument, or a callable that should return this value. 


### `add_remote_schema`

```python
def add_remote_schema(
    self,
    url: str,
    *,
    exclude_types: Optional[List[str]] = None,
    exclude_args: Optional[Dict[str, Dict[str, List[str]]]] = None,
    exclude_fields: Optional[Dict[str, List[str]]] = None,
    exclude_directives: Optional[List[str]] = None,
    exclude_directives_args: Optional[Dict[str, List[str]]] = None,
    extra_fields: Optional[Dict[str, List[str]]] = None,
) -> int:
    ...
```

Downloads remote GraphQL schema from the address in `url` argument, modifies it using the specified options and adds it to the final schema.

Returns `int` with sub schema ID that can be used to retrieve the schema using `get_sub_schema` method.


#### Required arguments

- `url`: a `str` with URL to remote GraphQL API that supports introspection.


#### Optional arguments

- `exclude_types`: a `List[str]` with names of GraphQL types from remote schema that should be excluded from downloaded schema. Eg. `["CheckoutCreate", "CheckoutComplete"]` will remove both `CheckoutCreate` and `CheckoutComplete` types, and all fields that use them as input values or return values.
- `exclude_args`: a `Dict[str, Dict[str, List[str]]]` with names of arguments of fields that should be removed from downloaded schema. Eg. `{"Query": {"users": ["search"]}}` will remove the `search` argument from `users` field on `Query` type.
- `exclude_fields`: a `Dict[str, List[str]]` with names of fields that should be removed from downloaded schema. Eg. `{"Query": ["webhooks"]}` will remove the `webhooks` field from the `Query` type.
- `exclude_directives`: a `List[str]` with names of directives that should be removed from downloaded schema. Eg. `["auth"]` will remove the `@auth` directive.
- `exclude_directives_args`: a `Dict[str, List[str]]` with names of directives arguments that should be removed from downloaded schema. Eg. `{"auth": ["roles"]}` will remove the `roles` argument from `@auth` directive.
- `extra_fields`: a `Dict[str, List[str]]` with list of types fields that have been excluded from downloaded schema, but should still be queried, because their return values are compatible with final schema's field. Eg. `{"CheckoutResult": ["error"]}` will make the root resolver still query the `error` field on `CheckoutResult` type, even if it was excluded using one of above options.


### `add_schema`

```python
def add_schema(
    self,
    schema: GraphQLSchema,
    url: Optional[str] = None,
    *,
    exclude_types: Optional[List[str]] = None,
    exclude_args: Optional[Dict[str, Dict[str, List[str]]]] = None,
    exclude_fields: Optional[Dict[str, List[str]]] = None,
    exclude_directives: Optional[List[str]] = None,
    exclude_directives_args: Optional[Dict[str, List[str]]] = None,
    extra_fields: Optional[Dict[str, List[str]]] = None,
) -> int:
    ...
```

Adds `GraphQLSchema` instance as sub schema to include in final schema.

Returns `int` with sub schema ID that can be used to retrieve the schema using `get_sub_schema` method.


#### Required arguments

- `schema`: a `GraphQLSchema` instance to include in final schema.


#### Optional arguments

- `url`: a `str` with URL to remote GraphQL API this schema fields should be resolved against. Used when sub schema represents a remote schema or its part.
- `exclude_types`: a `List[str]` with names of GraphQL types from remote schema that should be excluded from added schema. Eg. `["CheckoutCreate", "CheckoutComplete"]` will remove both `CheckoutCreate` and `CheckoutComplete` types, and all fields that use them as input values or return values.
- `exclude_args`: a `Dict[str, Dict[str, List[str]]]` with names of arguments of fields that should be removed from added schema. Eg. `{"Query": {"users": ["search"]}}` will remove the `search` argument from `users` field on `Query` type.
- `exclude_fields`: a `Dict[str, List[str]]` with names of fields that should be removed from added schema. Eg. `{"Query": ["webhooks"]}` will remove the `webhooks` field from the `Query` type.
- `exclude_directives`: a `List[str]` with names of directives that should be removed from added schema. Eg. `["auth"]` will remove the `@auth` directive.
- `exclude_directives_args`: a `Dict[str, List[str]]` with names of directives arguments that should be removed from added schema. Eg. `{"auth": ["roles"]}` will remove the `roles` argument from `@auth` directive.
- `extra_fields`: a `Dict[str, List[str]]` with list of types fields that have been excluded from added schema, but should still be queried, because their return values are compatible with final schema's field. Eg. `{"CheckoutResult": ["error"]}` will make the root resolver still query the `error` field on `CheckoutResult` type, even if it was excluded using one of above options.


### `add_delayed_fields`

```python
def add_delayed_fields(self, delayed_fields: Dict[str, List[str]]):
```

Sets specific fields in schema as delayed. Delayed fields are excluded from queries ran by `root_resolver` against the remote GraphQL APIs.


### `add_foreign_key`

```python
def add_foreign_key(
    self, type_name: str, field_name: str, on: Union[str, List[str]]
):
```

Sets specific field in schema as foreign key.


#### Required arguments

- `type_name`: a `str` with name of type which's field will be set as foreign key.
- `field_name`: a `str` with name of field which will be set as foreign key.
- `on`: a `str` or `List[str]]` with names of fields which should be queried when this field is included in query.


### `get_sub_schema`

```python
def get_sub_schema(self, schema_id: int) -> GraphQLSchema:
```

Returns sub schema with given id. If schema doesn't exist, raises `IndexError`.


### `insert_field`

```python
def insert_field(self, type_name: str, field_str: str):
```

Inserts field into all schemas with given `type_name`. The field is automatically delayed - excluded from queries run by `root_resolver` against the remote GraphQL APIs.


#### Required arguments

- `type_name`: a `str` with the name of the type into which the field will be inserted.
- `field_str`: a `str` with SDL field representation, e.g. `"fieldA(argA: String!) Int"`.


### `get_final_schema`

```python
def get_final_schema(self) -> GraphQLSchema:
    ...
```

Combines sub schemas into the single `GraphQLSchema` object that can then be used with Ariadne GraphQL app to run a GraphQL server.


### `root_resolver`

```python
async def root_resolver(
    self,
    context_value: dict,
    operation_name: Optional[str],
    variables: Optional[dict],
    document: DocumentNode,
) -> Optional[dict]:
    ...
```

An callable that should be passed to Ariadne GraphQL server's `root_value` option. It retrieves the root value, splitting the original query and calling the remote GraphQL servers.
