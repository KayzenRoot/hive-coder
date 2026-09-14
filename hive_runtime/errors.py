class HiveRuntimeError(Exception):
    """Base error for Hive-owned runtime bridge failures."""


class ProcessLaunchError(HiveRuntimeError):
    pass


class ProcessExitedError(HiveRuntimeError):
    pass


class RpcProtocolError(HiveRuntimeError):
    pass


class RpcTimeoutError(HiveRuntimeError):
    pass


class RpcRemoteError(HiveRuntimeError):
    def __init__(self, code: int, message: str, data=None):
        super().__init__(f"remote JSON-RPC error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data


class AdapterStateError(HiveRuntimeError):
    pass


class RuntimePreflightError(HiveRuntimeError):
    pass
