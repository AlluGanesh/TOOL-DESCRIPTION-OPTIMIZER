"""Custom exception classes for application and Ollama services."""

class AppBaseException(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class OllamaConnectionError(AppBaseException):
    """Raised when the Ollama host is unreachable."""
    def __init__(self, message: str = "Ollama server is unreachable.", host: str = ""):
        full_msg = f"{message} (Host: {host})" if host else message
        super().__init__(full_msg, status_code=503)
        self.host = host

class OllamaModelNotFoundError(AppBaseException):
    """Raised when the requested or configured model is missing in Ollama."""
    def __init__(self, model: str, host: str = ""):
        super().__init__(f"Configured model '{model}' is not available on Ollama host '{host}'.", status_code=404)
        self.model = model
        self.host = host

class OllamaAPIError(AppBaseException):
    """Raised when Ollama returns an operational error during inference."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, status_code=status_code)

class ToolDefinitionError(AppBaseException):
    """Raised when tool definitions fail validation or cannot be loaded."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class EvaluatorError(AppBaseException):
    """Raised when evaluation parameters or execution fail validation."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code=status_code)

class OptimizerError(AppBaseException):
    """Raised when optimization parameters, generation, or validation fail."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code=status_code)

