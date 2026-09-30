"""Exceptions raised by the application for errors it expects and handles."""


class PortfolioError(Exception):
    """Base class for the application's own errors."""


class DataFileError(PortfolioError):
    """A data file (cv.yaml, projects.yaml, ...) could not be read or parsed."""


class DataFileNotFoundError(DataFileError):
    """A data file does not exist in the data directory."""


class LLMServiceError(PortfolioError):
    """The model provider could not produce a response."""


class LLMConfigurationError(LLMServiceError):
    """No model is configured, or the provider's API key is missing."""
