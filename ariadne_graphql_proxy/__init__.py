from .copy_schema import copy_schema
from .proxy_resolver import setup_root_resolver
from .remote_schema import GraphQLRemoteSchema

__all__ = ["GraphQLRemoteSchema", "copy_schema", "setup_root_resolver"]
