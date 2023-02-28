class GraphQLProxyError(Exception):
    pass


class MissingOperationNameError(GraphQLProxyError):
    message = "Operation name is required when query contains multiple operations."


class InvalidOperationNameError(GraphQLProxyError):
    def __init__(self, operation_name: str):
        self.message = f"Invalid operation: '{operation_name}'"
