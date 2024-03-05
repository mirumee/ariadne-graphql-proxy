from typing import List, Optional

from ariadne.types import BaseProxyRootValue, GraphQLResult


class ProxyRootValue(BaseProxyRootValue):
    __slots__ = ("root_value", "errors", "extensions")

    def __init__(
        self,
        root_value: Optional[dict] = None,
        errors: Optional[List[dict]] = None,
        extensions: Optional[dict] = None,
    ):
        super().__init__(root_value)
        self.errors = errors
        self.extensions = extensions

    def update_result(self, result: GraphQLResult) -> GraphQLResult:
        success, data = super().update_result(result)

        if self.errors:
            data.setdefault("errors", [])
            data["errors"] += self.errors

        if self.extensions:
            data.setdefault("extensions", {})
            data["extensions"].update(self.extensions)

        return success, data
