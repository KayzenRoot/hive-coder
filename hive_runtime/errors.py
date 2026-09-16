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


class ControlPlaneError(HiveRuntimeError):
    pass


class AuthorizationDenied(ControlPlaneError):
    pass


class ApprovalError(ControlPlaneError):
    pass


class PermitError(ControlPlaneError):
    pass


class SessionStateError(ControlPlaneError):
    pass


class WorkspaceFileError(HiveRuntimeError):
    """Base error for the governed workspace-file capability boundary."""


class WorkspaceBoundaryError(WorkspaceFileError):
    """Target/path/identity validation failed closed before safe mutation."""


class WorkspaceMutationError(WorkspaceFileError):
    """A permit-gated OS mutation primitive failed closed."""
