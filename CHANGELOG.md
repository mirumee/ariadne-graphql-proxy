# CHANGELOG

## UNRELEASED

- Added `CacheSerializer`, `NoopCacheSerializer` and `JSONCacheSerializer`. Changed `CacheBackend`, `InMemoryCache`, `CloudflareCacheBackend` and `DynamoDBCacheBackend` to accept `serializer` initialization option.
- Fixed schema proxy returning an error when variable defined in an operation is missing from its variables.
- Improved custom headers handling in `ProxyResolver` and `ProxySchema`.


## 0.2.0 (2023-09-25)

- Added `CloudflareCacheBackend`.
- Added `DynamoDBCacheBackend`.
- Changed `QueryFilter` and `root_resolver` to split variables between schemas.
- Added `insert_field` utility to `ProxySchema`. Added `get_query_params_resolver` as factory for `imgix` resolvers. 


## 0.1.0 (2023-06-13)

- Initial release.
